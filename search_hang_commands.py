from cheks import manitou_cmd, player_cmd
from converters import MyMemberConverter
from errors import DayOnly, DuelInProgress
from utility import *


# kolejność, kończenie głosowania przy przerwij, swap


class Przeszukania(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if bot.game.night:
            raise DayOnly('Can\'t use this command during night')
        if bot.game.days[-1].duel:
            raise DuelInProgress('Can\'t use this command during duel')
        return True

    @commands.command(name='zgłaszam')
    @player_cmd()
    async def duel_dare(self, ctx, *, gracz: MyMemberConverter):
        """Zgłasza podaną osobę do przeszukania"""
        member = gracz
        bot.game.days[-1].add_report(ctx.author, member)

    @commands.command(name='cofam')
    @player_cmd()
    async def undo(self, ctx, *, gracz: MyMemberConverter):
        """Cofa zgłoszenie podanej osoby do przeszukania"""
        member = gracz
        bot.game.days[-1].remove_report(ctx.author, member)

    @commands.command(name='end_reports', aliases=['repblok'])
    @manitou_cmd()
    async def end_reports(self, _):
        """ⓂBlokuje zgłaszanie nowych osób do przeszukania"""
        bot.game.days[-1].search_lock = True

    @commands.command(name='reported', aliases=['rpt'])
    @manitou_cmd()
    async def reported(self, ctx):
        """ⓂPokazuje aktualne zgłoszenia"""
        await ctx.send(bot.game.days[-1].report_print())

    @commands.command(name='searchend', aliases=['snd'])
    @manitou_cmd()
    async def search_end(self, ctx):
        """Ⓜ/&snd/Kończy przeszukania"""
        if not bot.game.days[-1].search_final:
            await ctx.send("Najpierw musisz przeprowadzić głosowanie")
            return
        if bot.game.days[-1].hang_time:
            await ctx.send("Przeszukania już były")
            return
        try:
            await bot.game.days[-1].search_finalize(ctx)
        except InvalidRequest:
            pass

    @commands.command(name='search_random', aliases=['srnd'])
    @manitou_cmd()
    async def searchrand(self, ctx):
        """Ⓜ/&hrnd/Wyłania drogą losową przeszukiwanych osobę"""
        c = await bot.game.days[-1].search_random()
        if c:
            await ctx.send(c)


class Wieszanie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, _):
        if bot.game.night:
            raise DayOnly('Can\'t use this command during night')
        return True

    @commands.command(name='hangend', aliases=['hnd'])
    @manitou_cmd()
    async def hangend(self, ctx):
        """Ⓜ/&hnd/Finalizuje wieszanie"""
        try:
            await bot.game.days[-1].hang_finalize(ctx)
            await ctx.message.add_reaction('✅')
        except InvalidRequest:
            pass

    @commands.command(name='hang_random', aliases=['hrnd'])
    @manitou_cmd()
    async def hangrand(self, ctx):
        """Ⓜ/&hrnd/Wyłania drogą losową wieszaną osobę"""
        c = await bot.game.days[-1].hang_random()
        if c:
            await ctx.send(c)
