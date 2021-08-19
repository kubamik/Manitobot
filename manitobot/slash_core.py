import asyncio
import inspect
import logging
import re
import typing

import discord
from discord import InvalidArgument
from discord.ext import commands

from . import slash_args
from .components import ComponentTypes, ComponentCallback


class SlashCommand(commands.Command):
    def __init__(self, callback, **kwargs):
        super().__init__(callback, **kwargs)
        del self.aliases
        del self.usage
        del self.brief
        del self.hidden
        del self.rest_is_raw
        del self.description
        del self.require_var_positional
        del self.ignore_extra
        self._max_concurency = None
        self.guild_id = kwargs.get('guild')
        self.type = kwargs.get('type_', 1)
        self.default_permission = kwargs.get('default_permission', True)
        self.id = None
        if not (1 <= len(self.help) <= 100):
            raise discord.InvalidArgument('Description for a command should have 1-100 characters')
        if re.match(r'^[\w-]{1,32}$', self.name) is None:
            raise discord.InvalidArgument('Command names can contain only [A-Za-z0-9] and dashes or underscores'
                                          ' and have 1-32 characters')

    @property
    def guild_name(self):
        if self.guild_id:
            return self.name + ' ' + str(self.guild_id)
        return self.name

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, function):
        self._callback = function
        self.module = function.__module__

        signature = inspect.signature(function)
        params = signature.parameters.copy()
        self.params = {}

        for key, value in list(params.items())[1:]:
            param = value.annotation
            if param is value.empty:  # if type not passed type is str
                param = str
            if isinstance(param, str):
                param = eval(param, function.__globals__)
            if hasattr(param, '__origin__') and param.__origin__ is typing.Union \
                    and len(param.__args__) == 2 and isinstance(None, param.__args__[-1]):  # escape typing.Optional
                optional = True
                param = param.__args__[0]
            elif value.default is not value.empty:  # make arg optional if it has default value
                optional = True
            else:
                optional = False
            if not isinstance(param, type(slash_args.Arg)):
                param = slash_args.Arg[param]
            if param.type is None:
                param = param[str]
            if isinstance(param, type(slash_args.Choice)):
                param.check_types()
            if param.name:
                key = param.name
            else:
                param.name = key
            if param.doc is None:
                param.doc = key
            param.optional = optional
            self.params[key] = param

    async def prepare(self, ctx):
        ctx.command = self
        if not await self.can_run(ctx):
            raise commands.CheckFailure('The check functions for command {0.qualified_name} failed.'.format(self))

    async def call_after_hooks(self, ctx):
        """Overwriting function to do nothing
        """
        pass

    async def invoke(self, ctx):
        await self.prepare(ctx)
        injected = commands.core.hooked_wrapped_callback(self, ctx, self.callback)
        await injected(ctx, **ctx.kwargs)

    async def can_run(self, ctx):
        if not self.enabled:
            raise commands.DisabledCommand('{0.name} command is disabled'.format(self))

        original = ctx.command
        ctx.command = self

        try:
            predicates = self.checks
            if not predicates:
                return True
            return await discord.utils.async_all(predicate(ctx) for predicate in predicates)
        finally:
            ctx.command = original

    async def dispatch_error(self, ctx, error):
        ctx.command_failed = True
        try:
            coro = self.on_error
        except AttributeError:
            pass
        else:
            injected = commands.core.wrap_callback(coro)
            await injected(ctx, error)
        ctx.dispatch('interaction_error', ctx, error)

    def to_dict(self):
        d = {
            'name': self.name,
            'description': self.help,
            'type': self.type,
            'default_permission': self.default_permission,
        }
        if self.type == 1:
            d['options'] = [option.to_dict() for option in self.params.values()]
        return d


def slash(name=None, **attrs):
    """A decorator which converts coroutine passed into SlashCommand. This not registers command
    """
    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return SlashCommand(func, name=name, **attrs)

    return decorator


def bot_slash(self, *args, **kwargs):
    """A decorator which registers and adds slash command
    """
    def decorator(func):
        kwargs.setdefault('parent', self)
        result = slash(*args, **kwargs)(func)
        self.add_slash_command(result)
        return result
    return decorator


def add_slash_command(self, command):
    if not isinstance(command, SlashCommand):
        raise TypeError('The command passed must be a subclass of SlashCommand')

    if isinstance(self, commands.Command):
        command.parent = self

    if not hasattr(self, 'slash_commands'):
        self.slash_commands = {}

    if command.guild_name in self.slash_commands:
        raise commands.CommandRegistrationError(command.name)

    self.slash_commands[command.guild_name] = command


async def invoke_slash(self, ctx):
    try:
        if await self.can_run(ctx, call_once=True):
            await ctx.command.invoke(ctx)
        else:
            raise commands.CheckFailure('The global check once functions failed.')
    except commands.CommandError as exc:
        await ctx.command.dispatch_error(ctx, exc)


async def overwrite_slash_commands(self):
    if not hasattr(self, 'slash_commands'):
        return

    guilds = set()
    for name in self.slash_commands:
        if ' ' in name:
            guilds.add(name.rpartition(' ')[-1])

    http = self._connection.http
    await self.wait_until_ready()
    info = await self.application_info()
    application_id = info.id

    try:
        tasks = []
        slash_commands = {}
        global_commands = await http.get_global_slash_commands(application_id)
        for command in global_commands:
            comm = self.slash_commands.pop(command['name'])
            if not comm:
                tasks.append(http.delete_global_slash_command(application_id, command['id']))
                continue
            if comm.help != command['description'] or \
                    'options' in command and comm.to_dict()['options'] != command['options']:
                command = await http.edit_global_slash_command(application_id, command['id'], comm.to_dict())
            comm.id = int(command['id'])
            slash_commands[comm.id] = comm

        for guild_id in guilds:
            guild_commands = await http.get_guild_slash_commands(application_id, guild_id)
            for command in guild_commands:
                comm = self.slash_commands.pop(command['name'] + ' ' + guild_id, None)
                if not comm:
                    tasks.append(http.delete_guild_slash_command(application_id, guild_id, command['id']))
                    continue
                if comm.help != command['description'] or \
                        'options' in command and comm.to_dict()['options'] != command['options']:
                    command = await http.edit_guild_slash_command(application_id, guild_id,
                                                                  command['id'], comm.to_dict())
                comm.id = int(command['id'])
                slash_commands[comm.id] = comm

        for comm in self.slash_commands.values():
            if comm.guild_id is not None:
                command = await http.create_guild_slash_command(application_id, comm.guild_id, comm.to_dict())
            else:
                command = await http.create_global_slash_command(application_id, comm.to_dict())
            comm.id = int(command['id'])
            slash_commands[comm.id] = comm

        self.slash_commands = slash_commands
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.exception(e)
        await info.owner.send('Command registation error')
    else:
        print('Commands registered')


async def send_with_components(self, content=None, *, tts=False, embed=None, file=None,
                               files=None, delete_after=None, nonce=None,
                               allowed_mentions=None, reference=None,
                               mention_author=None, components=None):
    channel = await self._get_channel()
    state = self._state
    content = str(content) if content is not None else None
    if embed is not None:
        embed = embed.to_dict()

    if allowed_mentions is not None:
        if state.allowed_mentions is not None:
            allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            allowed_mentions = allowed_mentions.to_dict()
    else:
        allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()

    if mention_author is not None:
        allowed_mentions = allowed_mentions or discord.AllowedMentions().to_dict()
        allowed_mentions['replied_user'] = bool(mention_author)

    if reference is not None:
        try:
            reference = reference.to_message_reference_dict()
        except AttributeError:
            raise InvalidArgument('reference parameter must be Message or MessageReference') from None

    if components:
        custom_ids = set()
        for action in components:
            for c in action:
                if c.custom_id in custom_ids:
                    raise discord.InvalidArgument('custom_ids have to be unique in one message')
                custom_ids.add(c.custom_id)
        components = [{'type': ComponentTypes.ActionRow, 'components': [comp.to_dict() for comp in action]}
                      for action in components]

    if file is not None and files is not None:
        raise InvalidArgument('cannot pass both file and files parameter to send()')

    if file is not None:
        if not isinstance(file, discord.File):
            raise InvalidArgument('file parameter must be File')

        try:
            data = await state.http.send_files_components(channel.id, files=[file], allowed_mentions=allowed_mentions,
                                               content=content, tts=tts, embed=embed, nonce=nonce,
                                               message_reference=reference, components=components)
        finally:
            file.close()

    elif files is not None:
        if len(files) > 10:
            raise InvalidArgument('files parameter must be a list of up to 10 elements')
        elif not all(isinstance(file, discord.File) for file in files):
            raise InvalidArgument('files parameter must be a list of File')

        try:
            data = await state.http.send_files_components(channel.id, files=files, content=content, tts=tts,
                                               embed=embed, nonce=nonce, allowed_mentions=allowed_mentions,
                                               message_reference=reference, components=components)
        finally:
            for f in files:
                f.close()
    else:
        data = await state.http.send_message_components(channel.id, content, tts=tts, embed=embed,
                                             nonce=nonce, allowed_mentions=allowed_mentions,
                                             message_reference=reference, components=components)

    ret = state.create_message(channel=channel, data=data)
    if delete_after is not None:
        await ret.delete(delay=delete_after)
    return ret


async def edit(self, **fields):
    try:
        content = fields['content']
    except KeyError:
        pass
    else:
        if content is not None:
            fields['content'] = str(content)

    try:
        embed = fields['embed']
    except KeyError:
        pass
    else:
        if embed is not None:
            fields['embed'] = embed.to_dict()

    try:
        suppress = fields.pop('suppress')
    except KeyError:
        pass
    else:
        flags = discord.MessageFlags._from_value(self.flags.value)
        flags.suppress_embeds = suppress
        fields['flags'] = flags.value

    delete_after = fields.pop('delete_after', None)

    try:
        allowed_mentions = fields.pop('allowed_mentions')
    except KeyError:
        pass
    else:
        if allowed_mentions is not None:
            if self._state.allowed_mentions is not None:
                allowed_mentions = self._state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
            fields['allowed_mentions'] = allowed_mentions

    try:
        custom_ids = set()
        for action in fields['components']:
            for c in action:
                if c.custom_id in custom_ids:
                    raise discord.InvalidArgument('custom_ids have to be unique in one message')
                custom_ids.add(c.custom_id)

        components = [{'type': ComponentTypes.ActionRow, 'components': [comp.to_dict() for comp in action]}
                      for action in fields['components']]
    except KeyError:
        pass
    else:
        fields['components'] = components

    if fields:
        data = await self._state.http.edit_message(self.channel.id, self.id, **fields)
        self._update(data)

    if delete_after is not None:
        await self.delete(delay=delete_after)


def add_component_callback(self, callback):
    if not isinstance(callback, ComponentCallback):
        raise TypeError('callback has to be ComponentCallback')

    if not hasattr(self, 'component_callbacks'):
        self.component_callbacks = {}

    if callback.custom_id in self.component_callbacks:
        raise commands.CommandRegistrationError(callback.custom_id)

    self.component_callbacks[callback.custom_id] = callback


def component_callback(self, custom_id):
    """Decorator converting function passed into ComponentCallback and registering it into bot"""
    def decorator(func):
        callback = ComponentCallback(custom_id, func)
        self.add_component_callback(callback)
        return callback

    return decorator


discord.abc.Messageable.send_with_components = send_with_components
commands.GroupMixin.slash = bot_slash
commands.GroupMixin.add_slash_command = add_slash_command
commands.GroupMixin.add_component_callback = add_component_callback
commands.GroupMixin.component_callback = component_callback
commands.Bot.invoke_slash = invoke_slash
commands.Bot.overwrite_slash_commands = overwrite_slash_commands
discord.Message.edit = edit
