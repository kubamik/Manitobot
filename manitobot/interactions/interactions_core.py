import asyncio
import functools
import inspect
import logging
import re
import typing
from collections import namedtuple

import discord
from discord.abc import MISSING
from discord.ext import commands

from . import slash_args
from .components import Components
from .commands_types import CommandsTypes

Permissions = namedtuple('Permissions', ['id', 'permission', 'type'])


class ApplicationCommand(commands.Command):
    def __init__(self, callback, **kwargs):
        self.guild_id = kwargs.get('guild')
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
        self.type = kwargs.get('type_', 1)
        if self.type != 1 and not isinstance(self.type, CommandsTypes):
            raise TypeError('type_ has to be interactions.CommandsTypes')
        self.type = int(self.type)
        self.default_permission = kwargs.get('default_permission', True)
        self.id = None
        if self.type == 1 and not (1 <= len(self.help) <= 100):
            raise ValueError('Description for a command should have 1-100 characters')
        if re.match(r'^[\w-]{1,32}$', self.name) is None:
            raise ValueError('Command names can contain only [A-Za-z0-9] and dashes or underscores'
                             ' and have 1-32 characters')

    @property
    def qualified_name(self):
        name = self.name
        if self.guild_id:
            name += ' ' + str(self.guild_id)
        if self.type == 2:
            name += ' user'
        if self.type == 3:
            name += ' message'
        return name

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

        if hasattr(function, '__permissions__') and not self.guild_id:
            raise commands.CommandRegistrationError('Only guild commands can have permissions')

        self.permissions = function.__permissions__ if hasattr(function, '__permissions__') else list()

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
        args = [ctx.target] if ctx.target else []
        await injected(ctx, *args, **ctx.kwargs)

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
            'type': self.type,
            'default_permission': self.default_permission,
        }
        if self.type == 1:
            d['options'] = [option.to_dict() for option in self.params.values()]
            d['description'] = self.help
        return d

    def permissions_list(self):
        return {'id': self.id, 'permissions': [dict(perms._asdict()) for perms in self.permissions]}

    @staticmethod
    def get_guild_name(data):
        name = data.get('name', '')
        guild = data.get('guild_id')
        if guild:
            name += ' ' + guild
            guild = int(guild)
        type_ = data.get('type')
        if type_ == 2:
            name += ' user'
        if type_ == 3:
            name += ' message'
        return guild, name


def app_command(name=None, **attrs):
    """A decorator which converts coroutine passed into ApplicationCommand. This not registers command
    """
    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return ApplicationCommand(func, name=name, **attrs)

    return decorator


def command_role_permissions(role_id, allow=True):
    def decorator(func):

        if isinstance(func, ApplicationCommand):
            if not func.guild_id:
                raise commands.CommandRegistrationError('Only guild commands can have permissions')
            func.permissions.append(Permissions(role_id, allow, 1))
        else:
            if not hasattr(func, '__permissions__'):
                func.__permissions__ = list()
            func.__permissions__.append(Permissions(role_id, allow, 1))
        return func

    return decorator


def command_user_permissions(user_id, allow=True):
    def decorator(func):
        if isinstance(func, ApplicationCommand):
            if not func.guild_id:
                raise commands.CommandRegistrationError('Only guild commands can have permissions')
            func.permissions.append(Permissions(user_id, allow, 2))
        else:
            if not hasattr(func, '__permissions__'):
                func.__permissions__ = list()
            func.__permissions__.append(Permissions(user_id, allow, 2))
        return func

    return decorator


def send_decorator(func):
    @functools.wraps(func)
    async def wrapper(*args, components=MISSING, **kwargs):
        if components:
            kwargs['view'] = Components(components)
        return await func(*args, **kwargs)
    return wrapper


async def message_edit_decorator(func):
    @functools.wraps(func)
    async def wrapper(*args, components=MISSING, **kwargs):
        if isinstance(components, list):
            kwargs['view'] = Components(components)
        else:
            kwargs['view'] = components
        return await func(*args, **kwargs)
    return wrapper


discord.abc.Messageable.send = send_decorator(discord.abc.Messageable.send)
discord.Message.edit = message_edit_decorator(discord.Message.edit)
