import asyncio
import inspect
import logging
import re
import typing

import discord
from discord.ext import commands

import slash_args


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
        return {
            'name': self.name,
            'description': self.help,
            'options': [option.to_dict() for option in self.params.values()]
        }


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


commands.GroupMixin.slash = bot_slash
commands.GroupMixin.add_slash_command = add_slash_command
commands.Bot.invoke_slash = invoke_slash
commands.Bot.overwrite_slash_commands = overwrite_slash_commands
