import discord.ext.commands

from .errors import GameNotStarted


class NotAGame:
    def __getattr__(self, name: str):
        raise GameNotStarted('This command can be run only during game')


class ManiBot(discord.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        super(ManiBot, self).__init__(*args, **kwargs)
        self.game = NotAGame()
