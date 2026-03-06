import typing
from typing import override

import discord.ext.commands
from discord.ext import commands

from .errors import GameNotStarted
from .interactions import ComponentCallback
from .muting import Muting

if typing.TYPE_CHECKING:
    from .game import Game
    from .mafia import Mafia


class NotAGame:
    def __getattr__(self, name: str):
        raise GameNotStarted('This command can be run only during game')


class ManiBot(discord.ext.commands.Bot):
    muting: Muting | None = None
    
    def __init__(self, *args, **kwargs):
        super(ManiBot, self).__init__(*args, **kwargs)
        self.game: typing.Union[Game, Mafia, NotAGame] = NotAGame()
        self.component_callbacks = dict()
        
    def initialize_muting(self, muting_tokens: list[str]):
        """Initialize muting clients with given tokens"""
        if not self.muting and muting_tokens:
            self.muting = Muting(muting_tokens)
        else:
            raise RuntimeError('Muting already initialized')
        
    @override
    async def start(self, token: str, *, reconnect: bool = True):
        if self.muting:
            await self.muting.login_bots()
        await super().start(token, reconnect=reconnect)
        

    def add_component_callback(self, callback):
        if not isinstance(callback, ComponentCallback):
            raise TypeError('callback has to be ComponentCallback')

        if callback.custom_id in self.component_callbacks:
            raise commands.CommandRegistrationError(callback.custom_id)

        self.component_callbacks[callback.custom_id] = callback

    def remove_component_callback(self, custom_id):
        if custom_id in self.component_callbacks:
            self.component_callbacks.pop(custom_id)

    def component_callback(self, custom_id, component_type=discord.ComponentType.button):
        """Decorator converting function passed into ComponentCallback and registering it into bot"""

        def decorator(func):
            callback = ComponentCallback(custom_id, func, component_type)
            self.add_component_callback(callback)
            return callback

        return decorator

    def button_callback(self, custom_id):
        return self.component_callback(custom_id, discord.ComponentType.button)

    def select_callback(self, custom_id):
        return self.component_callback(custom_id, discord.ComponentType.select)
