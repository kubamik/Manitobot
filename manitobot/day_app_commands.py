import discord
from discord.ext import commands

from settings import GUILD_ID, PLAYER_ROLE_ID, MANITOU_ROLE_ID
from .bot_basics import bot
from .my_checks import game_check, town_only, state_check
from .errors import MemberNotPlaying, DayOnly, WrongState
from .interactions.slash_args import Arg
from .interactions import command_role_permissions, CommandsTypes
from .utility import get_player_role


def setup(_):
    """Do nothing while loading extension
    """
    pass


def checks(func):
    return command_role_permissions(PLAYER_ROLE_ID)(game_check()(town_only()(state_check()(func))))


async def invoke_state(ctx, *args):
    await getattr(bot.game.day.state, ctx.command.callback.__name__)(*args)


@bot.bot_app_command(name='wyzywam', guild=GUILD_ID, default_permission=False)
@checks
async def add_challenge(ctx, osoba: Arg('Wyzywana osoba')[discord.Member]):
    """Wyzywa podaną osobę na pojedynek"""
    await _add_challenge(ctx, osoba)


@bot.bot_app_command(name='wyzywam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@checks
async def add_challenge(ctx, member):
    """Wyzywa podaną osobę na pojedynek"""
    await _add_challenge(ctx, member)


@bot.bot_app_command(name='przyjmuję', guild=GUILD_ID, default_permission=False)
@checks
async def accept(ctx):
    """Przyjmuje pierwszy w kolejności pojedynek"""
    await invoke_state(ctx, ctx.author)
    await ctx.respond('✅', ephemeral=True)


@bot.bot_app_command(name='odrzucam', guild=GUILD_ID, default_permission=False)
@checks
async def decline(ctx):
    """Odrzuca pierwszy w kolejności pojedynek"""
    await invoke_state(ctx, ctx.author)
    await ctx.respond('✅', ephemeral=True)


@bot.bot_app_command(name='zgłaszam', guild=GUILD_ID, default_permission=False)
@command_role_permissions(MANITOU_ROLE_ID)
@checks
async def add_report(ctx, osoba: Arg('Zgłaszana osoba')[discord.Member]):
    """Zgłasza podaną osobę do przeszukania"""
    await _add_report(ctx, osoba)


@bot.bot_app_command(name='zgłaszam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@command_role_permissions(MANITOU_ROLE_ID)
@checks
async def add_report(ctx, member):
    await _add_report(ctx, member)


@bot.bot_app_command(name='cofam', guild=GUILD_ID, default_permission=False)
@command_role_permissions(MANITOU_ROLE_ID)
@checks
async def remove_report(ctx, osoba: Arg('Zgłoszona osoba')[discord.Member]):
    """Cofa zgłoszenie podanej osoby do przeszukania"""
    await _remove_report(ctx, osoba)


@bot.bot_app_command(name='cofam', guild=GUILD_ID, default_permission=False, type_=CommandsTypes.UserCommand)
@command_role_permissions(MANITOU_ROLE_ID)
@checks
async def remove_report(ctx, member):
    await _remove_report(ctx, member)


async def _add_challenge(ctx, member):
    if member not in get_player_role().members:
        raise MemberNotPlaying(member)
    await invoke_state(ctx, ctx.author, member)
    await ctx.respond('✅', ephemeral=True)


async def _add_report(ctx, member):
    if member not in get_player_role().members:
        raise MemberNotPlaying(member)
    await invoke_state(ctx, ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} zgłosił(a) {member.display_name}')


async def _remove_report(ctx, member):
    if member not in get_player_role().members:
        raise MemberNotPlaying(member)
    await invoke_state(ctx, ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} usunął(-ęła) zgłoszenie {member.display_name}')
