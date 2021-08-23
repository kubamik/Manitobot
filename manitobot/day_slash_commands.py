import discord

from settings import GUILD_ID, PLAYER_ROLE_ID
from .bot_basics import bot
from .cheks import game_check, player_cmd, day_only, town_only, duel_check
from .errors import SelfDareError, MemberNotPlaying
from manitobot.interactions.slash_args import Arg
from .interactions import command_role_permissions, CommandsTypes
from .utility import get_player_role


def setup(_):
    """Do nothing while loading extension
    """
    pass


def checks(func):
    return command_role_permissions(PLAYER_ROLE_ID)(player_cmd()
                                                    (game_check()(day_only()(town_only()(duel_check()(func))))))


@bot.bot_app_command(name='wyzywam', guild=GUILD_ID, default_permission=False)
@checks
async def duel_challenge(ctx, osoba: Arg('Wyzywana osoba')[discord.Member]):
    """Wyzywa podaną osobę na pojedynek"""
    await _duel_challenge(ctx, osoba)


@bot.bot_app_command(name='wyzywam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@checks
async def duel_challenge(ctx, member):
    """Wyzywa podaną osobę na pojedynek"""
    await _duel_challenge(ctx, member)


@bot.bot_app_command(name='przyjmuję', guild=GUILD_ID, default_permission=False)
@checks
async def duel_accept(ctx):
    """Przyjmuje pierwszy w kolejności pojedynek"""
    msg = bot.game.days[-1].accept(ctx.author)
    await ctx.respond(msg)
    await bot.game.days[-1].if_next(True)


@bot.bot_app_command(name='odrzucam', guild=GUILD_ID, default_permission=False)
@checks
async def duel_decline(ctx):
    """Przyjmuje pierwszy w kolejności pojedynek"""
    msg = bot.game.days[-1].remove_dare(ctx.author)
    await ctx.respond(msg)
    await bot.game.days[-1].if_next()


@bot.bot_app_command(name='zgłaszam', guild=GUILD_ID, default_permission=False)
@checks
async def search_dare(ctx, osoba: Arg('Zgłaszana osoba')[discord.Member]):
    """Zgłasza podaną osobę do przeszukania"""
    await _report(ctx, osoba)


@bot.bot_app_command(name='zgłaszam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@checks
async def report(ctx, member):
    await _report(ctx, member)


@bot.bot_app_command(name='cofam', guild=GUILD_ID, default_permission=False)
@checks
async def undo(ctx, osoba: Arg('Zgłoszona osoba')[discord.Member]):
    """Cofa zgłoszenie podanej osoby do przeszukania"""
    await _undo(ctx, osoba)


@bot.bot_app_command(name='cofam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@checks
async def undo(ctx, member):
    await _undo(ctx, member)


async def _duel_challenge(ctx, member):
    if member not in get_player_role().members:
        raise MemberNotPlaying('This person is not playing.')
    if member == ctx.author:
        raise SelfDareError('Player tried to dare itself')
    bot.game.days[-1].add_dare(ctx.author, member)
    await ctx.respond('✅', ephemeral=True)
    await bot.game.days[-1].if_start(ctx.author, member)


async def _report(ctx, member):
    if member not in get_player_role().members:
        raise MemberNotPlaying('This person is not playing.')
    bot.game.days[-1].add_report(ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} zgłosił(a) {member.display_name}')


async def _undo(ctx, member):
    bot.game.days[-1].remove_report(ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} usunął(-ęła) zgłoszenie {member.display_name}')
