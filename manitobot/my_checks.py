from typing import Callable

from discord.ext import commands

from . import game
from . import mafia
from .basic_models import NotAGame
from .errors import AuthorNotPlaying, GameNotStarted, WrongGameType, \
    GameStartedException, DayOnly, VotingInProgress, \
    VotingNotInProgress, NightOnly, AuthorPlaying, AuthorNotOnVoice, \
    NotTownChannel, DuelInProgress, NotSetsChannel, NotPollChannel
from .starting import if_game
from .utility import if_manitou, get_manitou_role, get_player_role, on_voice, \
    get_town_channel, if_player, if_qualified_manitou, get_qualified_manitou_role, get_sets_channel, \
    get_ankietawka_channel


# ===================== Game checks =====================

def game_check(reverse=False) -> Callable:
    async def predicate(_):
        if not if_game() and not reverse:
            raise GameNotStarted('This command can be used only during game')
        elif if_game() and reverse:
            raise GameStartedException('Command can\'t be used during game.')
        return True

    return commands.check(predicate)


def ktulu_check() -> Callable:
    async def predicate(ctx):
        if isinstance(ctx.bot.game, NotAGame):
            raise GameNotStarted('Game hasn\'t been started.')
        if not isinstance(ctx.bot.game, game.Game):
            raise WrongGameType('This game type does not support this command.')
        return True

    return commands.check(predicate)


def mafia_check() -> Callable:
    async def predicate(ctx):
        if isinstance(ctx.bot.game, NotAGame):
            raise GameNotStarted('Game hasn\'t been started.')
        if not isinstance(ctx.bot.game, mafia.Mafia):
            raise WrongGameType('This game type does not support this command.')
        return True

    return commands.check(predicate)


# ===================== Author checks =====================

def manitou_cmd() -> Callable:
    async def predicate(ctx: commands.Context) -> bool:
        if not if_manitou(ctx):
            raise commands.MissingRole(get_manitou_role())
        return True

    return commands.check(predicate)


def player_cmd() -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not if_player(ctx):
            raise AuthorNotPlaying
        return True

    return commands.check(predicate)


def player_or_manitou_cmd() -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not (if_player(ctx) or if_manitou(ctx)):
            raise AuthorNotPlaying
        return True

    return commands.check(predicate)


def playing_cmd(reverse=False) -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not reverse and ctx.author not in ctx.bot.game.player_map:
            raise AuthorNotPlaying
        elif reverse and if_game() and ctx.author in ctx.bot.game.player_map:
            raise AuthorPlaying
        return True

    return commands.check(predicate)


def on_voice_check() -> Callable:
    def predicate(ctx: commands.Context) -> bool:
        if not on_voice(ctx):
            raise AuthorNotOnVoice
        return True

    return commands.check(predicate)


def qualified_manitou_cmd() -> Callable:
    async def predicate(ctx: commands.Context) -> bool:
        owner = await ctx.bot.is_owner(ctx.author)
        if not if_qualified_manitou(ctx) and not owner:
            raise commands.MissingRole(get_qualified_manitou_role())
        return True

    return commands.check(predicate)


# ===================== Time and events checks =====================

def day_only(reverse=False):
    def predicate(ctx):
        if not reverse and ctx.bot.game.night_now:
            raise DayOnly
        elif reverse and not ctx.bot.game.night_now:
            raise NightOnly
        return True

    return commands.check(predicate)


def voting_check(reverse=False):
    def predicate(ctx):
        if ctx.bot.game.voting_in_progress and not reverse:
            raise VotingInProgress
        elif not ctx.bot.game.voting_in_progress and reverse:
            raise VotingNotInProgress
        return True

    return commands.check(predicate)

# ===================== Place checks =====================


def town_only():
    def predicate(ctx):
        if ctx.channel != get_town_channel():
            raise NotTownChannel
        return True

    return commands.check(predicate)


def sets_channel_only():
    def predicate(ctx):
        if ctx.channel != get_sets_channel():
            raise NotSetsChannel
        return True

    return commands.check(predicate)


def poll_channel_only():
    def predicate(ctx):
        if ctx.channel != get_ankietawka_channel():
            raise NotPollChannel
        return True

    return commands.check(predicate)
