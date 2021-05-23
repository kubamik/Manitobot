from discord.ext import commands

from .cheks import manitou_cmd, player_cmd
from .converters import MyMemberConverter
from .errors import DayOnly, DuelInProgress, SelfDareError
from .utility import *


class Pojedynki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if bot.game.night:
            raise DayOnly('Can\'t use this command during night')
        if bot.game.days[-1].duel and not czy_manitou(ctx):
            raise DuelInProgress('Can\'t use this command during duel')
        return True

    @commands.command(name='wyzywam')
    @player_cmd()
    @commands.guild_only()
    async def duel_dare(self, ctx, *, gracz: MyMemberConverter):
        """Wyzywa podaną osobę na pojedynek"""
        member = gracz
        if member == ctx.author:
            raise SelfDareError('Player tried to dare itself')
        bot.game.days[-1].add_dare(ctx.author, member)
        await bot.game.days[-1].if_start(ctx.author, member)  # TODO: Implement this line in duels

    @commands.command(name='odrzucam', aliases=['spierdalaj', 'od'])
    @player_cmd()
    @commands.guild_only()
    async def decline(self, ctx):
        """/&od/Służy do odrzucenia pojedynku"""
        msg = bot.game.days[-1].remove_dare(ctx.author)
        await get_town_channel().send(msg)
        await bot.game.days[-1].if_next()

    @commands.command(name='przyjmuję', aliases=['pr'])
    @player_cmd()
    @commands.guild_only()
    async def accept(self, ctx):
        """/&pr/Służy do przyjęcia pojedynku"""
        c = bot.game.days[-1].accept(ctx.author)
        await get_town_channel().send(c)
        await bot.game.days[-1].if_next(True)

    @commands.command(name='break', aliases=['br'])
    @manitou_cmd()
    async def interrupt(self, ctx):
        """Ⓜ/&br/Przerywa trwający pojedynek lub usuwa pierwsze wyzwanie z listy"""
        c = await bot.game.days[-1].interrupt()
        await get_town_channel().send(c)
        await bot.game.days[-1].if_next()

    @commands.command(name='wyzwania', aliases=['pend'])
    @manitou_cmd()
    async def challenges(self, ctx):
        """Ⓜ/&pend/Pokazuje aktualne wyzwania"""
        c = bot.game.days[-1].dares_print()
        await ctx.send(c)

    @commands.command(name='duelend', aliases=['dnd'])
    @manitou_cmd()
    async def duel_end(self, ctx):
        """Ⓜ/&dnd/Kończy pojedynek z wynikiem ogłoszonym automatycznie"""
        await bot.game.days[-1].end_duel(ctx)

    @commands.command(name='search_phase', aliases=['abend'])
    @manitou_cmd()
    async def no_duels(self, _):
        """Ⓜ/&abend/Kończy turę pojedynków"""
        bot.game.days[-1].duels_today = bot.game.duels
        await get_town_channel().send("__Zakończono turę pojedynków__")
