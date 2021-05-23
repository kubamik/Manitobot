from .bot_basics import bot
from .errors import GameNotStarted


class NotAGame:
    def __getattr__(self, name: str):
        raise GameNotStarted('This command can be run only during game')


bot.game = NotAGame()
