import discord

from settings import GUILD_ID
from .bot_basics import bot
from .cheks import game_check, player_cmd, day_only, town_only, duel_check
from .errors import SelfDareError, MemberNotPlaying
from .slash_args import Arg
from .utility import get_player_role


def setup(_):
    """Do nothing while loading extension
    """
    pass


@bot.slash(name='wyzywam', guild=GUILD_ID)
@player_cmd()
@game_check()
@day_only()
@town_only()
@duel_check()
async def duel_dare(ctx, osoba: Arg('Wyzywana osoba')[discord.Member]):
    """Wyzywa podaną osobę na pojedynek"""
    member = osoba
    if member not in get_player_role().members:
        raise MemberNotPlaying('This person is not playing.')
    if member == ctx.author:
        raise SelfDareError('Player tried to dare itself')
    bot.game.days[-1].add_dare(ctx.author, member)
    await ctx.respond('✅', ephemeral=True)
    await bot.game.days[-1].if_start(ctx.author, member)


@bot.slash(name='przyjmuję', guild=GUILD_ID)
@player_cmd()
@game_check()
@day_only()
@town_only()
@duel_check()
async def duel_accept(ctx):
    """Przyjmuje pierwszy w kolejności pojedynek"""
    msg = bot.game.days[-1].accept(ctx.author)
    await ctx.respond(msg)
    await bot.game.days[-1].if_next(True)


@bot.slash(name='odrzucam', guild=GUILD_ID)
@player_cmd()
@game_check()
@day_only()
@town_only()
@duel_check()
async def duel_decline(ctx):
    """Przyjmuje pierwszy w kolejności pojedynek"""
    msg = bot.game.days[-1].remove_dare(ctx.author)
    await ctx.respond(msg)
    await bot.game.days[-1].if_next()


@bot.slash(name='zgłaszam', guild=GUILD_ID)
@player_cmd()
@game_check()
@day_only()
@town_only()
@duel_check()
async def search_dare(ctx, osoba: Arg('Zgłaszana osoba')[discord.Member]):
    """Zgłasza podaną osobę do przeszukania"""
    member = osoba
    if member not in get_player_role().members:
        raise MemberNotPlaying('This person is not playing.')
    bot.game.days[-1].add_report(ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} zgłosił(a) {member.display_name}')


@bot.slash(name='cofam', guild=GUILD_ID)
@player_cmd()
@game_check()
@day_only()
@town_only()
@duel_check()
async def undo(ctx, osoba: Arg('Zgłoszona osoba')[discord.Member]):
    """Cofa zgłoszenie podanej osoby do przeszukania"""
    member = osoba
    bot.game.days[-1].remove_report(ctx.author, member)
    await ctx.respond(f'{ctx.author.display_name} usunął(-ęła) zgłoszenie {member.display_name}')
