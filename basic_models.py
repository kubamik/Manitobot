"""For models that are needed to be used in tree before utility"""
from typing import NoReturn

from discord.ext import commands

class GameNotStarted(commands.CommandError):
  pass


class NotAGame(object):
  def __getattr__(self, name):
    raise GameNotStarted('This command can be run only during game')