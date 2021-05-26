from typing import Callable

from discord.ext import commands

from . import game
from . import mafia
from .basic_models import NotAGame
from .bot_basics import bot
from .errors import AuthorNotPlaying, GameNotStarted, WrongGameType, \
    GameStartedException, DayOnly, VotingInProgress, \
    VotingNotInProgress, NightOnly, AuthorPlaying, AuthorNotOnVoice, \
    NotTownChannel, DuelInProgress
from .starting import if_game
from .utility import czy_manitou, get_manitou_role, get_player_role, on_voice, \
    get_town_channel


# ===================== Game checks =====================

def game_check(rev=False) -> Callable:
    async def predicate(_):
        if not if_game() and not rev:
            raise GameNotStarted('This command can be used only during game')
        elif if_game() and rev:
            raise GameStartedException('Command can\'t be used during game.')
        return True

    return commands.check(predicate)


def ktulu_check() -> Callable:
    async def predicate(_):
        if isinstance(bot.game, NotAGame):
            raise GameNotStarted('Game hasn\'t been started.')
        if not isinstance(bot.game, game.Game):
            raise WrongGameType('This game type does not support this command.')
        return True

    return commands.check(predicate)


def mafia_check() -> Callable:
    async def predicate(_):
        if isinstance(bot.game, NotAGame):
            raise GameNotStarted('Game hasn\'t been started.')
        if not isinstance(bot.game, mafia.Mafia):
            raise WrongGameType('This game type does not support this command.')
        return True

    return commands.check(predicate)


# ===================== Author checks =====================

def manitou_cmd() -> Callable:
    async def predicate(ctx: commands.Context) -> bool:
        if not czy_manitou(ctx):
            raise commands.MissingRole(get_manitou_role())
        return True

    return commands.check(predicate)


def player_cmd() -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if ctx.author not in get_player_role().members:
            raise AuthorNotPlaying('Author have to be playing to run this command.')
        return True

    return commands.check(predicate)


def playing_cmd(rev=False) -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not rev and ctx.author not in bot.game.player_map:
            raise AuthorNotPlaying('<--')
        elif rev and if_game() and ctx.author in bot.game.player_map:
            raise AuthorPlaying('<--')
        return True

    return commands.check(predicate)


def on_voice_check() -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not on_voice(ctx):
            raise AuthorNotOnVoice('<--')
        return True

    return commands.check(predicate)


# ===================== Time and events checks =====================

def day_only(rev=False):
    def predicate(_):
        if not rev and bot.game.night:
            raise DayOnly('<--')
        elif rev and not bot.game.night:
            raise NightOnly('<--')
        return True

    return commands.check(predicate)


def voting_check(rev=False):
    def predicate(_):
        if bot.game.voting_in_progress and not rev:
            raise VotingInProgress('<--')
        elif not bot.game.voting_in_progress and rev:
            raise VotingNotInProgress('<--')
        return True

    return commands.check(predicate)


def duel_check():
    def predicate(_):
        if bot.game.days[-1].duel:
            raise DuelInProgress('Can\'t use this command during duel')
        return True

    return commands.check(predicate)

# ===================== Place checks =====================

def town_only():
    def predicate(ctx):
        if ctx.channel != get_town_channel():
            raise NotTownChannel
        return True

    return commands.check(predicate)
