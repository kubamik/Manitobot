# kolejność, kończenie głosowania przy przerwij, swap
import globals
from utility import *


class Przeszukania(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        try:
            return not globals.current_game.night and not \
            globals.current_game.days[-1].duel
        except:
            return False

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(
                "Tej komendy można używać tylko w dzień i nie w trakcie pojedynku")

    @commands.command(name='zgłaszam')
    async def duel_dare(self, ctx, *, gracz):
        """Zgłasza podaną osobę do przeszukania"""
        gracz = await converter(ctx, gracz)
        member = get_member(ctx.author.id)
        try:
            playing(gracz, author=member)
            globals.current_game.days[-1].add_report(member, gracz)
            await ctx.message.add_reaction('✅')
        except InvalidRequest as err:
            await ctx.send(err.reason)
            return

    @commands.command(name='cofam')
    async def undo(self, ctx, *, gracz):
        """Cofa zgłoszenie podanej osoby do przeszukania"""
        gracz = await converter(ctx, gracz)
        member = get_member(ctx.author.id)
        try:
            playing(gracz, author=member)
            globals.current_game.days[-1].remove_report(member, gracz)
            await ctx.message.add_reaction('✅')
        except InvalidRequest as err:
            await ctx.send(err.reason)
            return

    @commands.command(name='reported')
    @manitou_cmd
    async def reported(self, ctx):
        """ⓂPokazuje aktualne zgłoszenia"""
        await ctx.send(globals.current_game.days[-1].report_print())

    @commands.command(name='searchend', aliases=['snd'])
    @manitou_cmd
    async def search_end(self, ctx):
        '''Ⓜ/&snd/Kończy przeszukania'''
        if globals.current_game.night:
            await ctx.send("Trwa noc!")
            return
        if not globals.current_game.days[-1].search_final:
            await ctx.send("Najpierw musisz przeprowadzić głosowanie")
            return
        if globals.current_game.days[-1].hang_time:
            await ctx.send("Przeszukania już były")
            return
        try:
            await globals.current_game.days[-1].search_finalize(ctx)
            await ctx.message.add_reaction('✅')
        except InvalidRequest:
            pass


class Wieszanie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        try:
            return not globals.current_game.night
        except:
            return False

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Tej komendy można używać tylko w dzień")

    @commands.command(name='hangend', aliases=['hnd'])
    @manitou_cmd
    async def hangend(self, ctx):
        '''Ⓜ/&hnd/Finalizuje wieszanie'''
        if globals.current_game.night:
            await ctx.send("Trwa noc!")
            return
        try:
            await globals.current_game.days[-1].hang_finalize(ctx)
            await ctx.message.add_reaction('✅')
        except InvalidRequest:
            pass
