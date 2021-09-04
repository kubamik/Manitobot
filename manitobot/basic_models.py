import asyncio
import logging
import typing
from collections import defaultdict

import discord.ext.commands
from discord.ext import commands

from .errors import GameNotStarted
from .interactions import ApplicationCommand, app_command, ComponentCallback

if typing.TYPE_CHECKING:
    from .game import Game
    from .mafia import Mafia


class NotAGame:
    def __getattr__(self, name: str):
        raise GameNotStarted('This command can be run only during game')


class ManiBot(discord.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        super(ManiBot, self).__init__(*args, **kwargs)
        self.game: typing.Union[Game, Mafia, NotAGame] = NotAGame()
        self.app_commands_names = defaultdict(dict)
        self.app_commands = dict()
        self.component_callbacks = dict()

    def bot_app_command(self, *args, **kwargs):
        """A decorator which registers and adds application command
        :param type_: Optional, interactions.CommandsTypes - type of a command
        """

        def decorator(func):
            kwargs.setdefault('parent', self)
            result = app_command(*args, **kwargs)(func)
            self.add_app_command(result)
            return result

        return decorator

    def add_app_command(self, command):
        if not isinstance(command, ApplicationCommand):
            raise TypeError('The command passed must be a subclass of ApplicationCommand')

        if command.qualified_name in self.app_commands_names[command.guild_id]:
            raise commands.CommandRegistrationError(command.name)

        self.app_commands_names[command.guild_id][command.qualified_name] = command

    async def invoke_app_command(self, ctx):
        try:
            if await self.can_run(ctx, call_once=True):
                await ctx.command.invoke(ctx)
            else:
                raise commands.CheckFailure('The global check once functions failed.')
        except commands.CommandError as exc:
            await ctx.command.dispatch_error(ctx, exc)

    def add_component_callback(self, callback):
        if not isinstance(callback, ComponentCallback):
            raise TypeError('callback has to be ComponentCallback')

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

    async def overwrite_app_commands(self):
        if not self.app_commands_names:
            return

        http = self._connection.http
        await self.wait_until_ready()
        info = await self.application_info()
        application_id = info.id

        try:
            tasks = []
            for guild in self.app_commands_names:
                commands_list = [command.to_dict() for command in self.app_commands_names[guild].values()]
                if guild:
                    tasks.append(http.bulk_overwrite_guild_slash_commands(application_id, guild, commands_list))
                else:
                    tasks.append(http.bulk_overwrite_global_slash_commands(application_id, commands_list))
            commands_list = await asyncio.gather(*tasks)
            for guild_commands in commands_list:
                for data in guild_commands:
                    guild, name = ApplicationCommand.get_guild_name(data)
                    id_ = int(data.get('id', 0))
                    command = self.app_commands_names[guild][name]
                    command.id = id_
                    self.app_commands[id_] = command

            tasks = []
            for guild in self.app_commands_names:
                if not guild:
                    continue
                permissions = []
                for command in self.app_commands_names[guild].values():
                    permissions.append(command.permissions_list())
                tasks.append(http.batch_edit_slash_commands_permissions(application_id, guild, permissions))
            await asyncio.gather(*tasks)
        except Exception as e:
            logging.exception(e)
            await info.owner.send('Command registration error')
