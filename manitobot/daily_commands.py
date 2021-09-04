from discord.ext import commands

from manitobot.converters import MyMemberConverter
from manitobot.errors import DayOnly
from manitobot.my_checks import manitou_cmd, player_cmd, town_only, player_or_manitou_cmd


class DailyCommands(commands.Cog, name='Polecenia dzienne', description=''):
    """Commands to be used during day or voting, integrated with DayStates
    Command callback name must be the same as name of a function in DayState
    """
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        day = self.bot.game.day
        if day is None:
            raise DayOnly
        return hasattr(day.state, ctx.command.callback.__name__)
        # check if it's possible to invoke command in current state

    async def cog_command_error(self, ctx, error):
        if type(error) is commands.CheckFailure:  # CheckFailure subclasses are handled on `Bot.on_command_error`
            await ctx.send('Na razie nie można używać tego polecenia', delete_after=10)

    async def invoke_state(self, ctx, *args):
        await getattr(self.bot.game.day.state, ctx.command.callback.__name__)(*args)

    # ========================= State management commands ============================

    @commands.command()
    @manitou_cmd()
    async def undo(self, ctx):
        """ⓂZmienia aktualny stan na poprzedni"""
        await self.invoke_state(ctx)

    @commands.command(aliases=['clc'])
    @manitou_cmd()
    async def cancel(self, ctx):
        """Ⓜ/&clc/Anuluje aktualnie trwający stan"""
        await self.invoke_state(ctx)

    @commands.command(name='vote')
    @manitou_cmd()
    async def voting(self, ctx):
        """ⓂUruchamia głosowanie zgodne z aktualnym stanem"""
        await self.invoke_state(ctx)

    @commands.command(name='randomize', aliases=['rand'])
    @manitou_cmd()
    async def random(self, ctx):
        """Ⓜ/&rand/Wyłania przeszukiwaną/wieszaną osobę drogą losową"""
        await self.invoke_state(ctx)

    @commands.command(name='next')
    @manitou_cmd()
    async def end(self, ctx):
        """ⓂUruchamia przejście do następnego stanu"""
        await self.invoke_state(ctx)

    # =========================== Duels' commands ============================

    @commands.command(name='duel')
    @manitou_cmd()
    @town_only()
    async def start_duel(self, ctx, first: MyMemberConverter, second: MyMemberConverter):
        """ⓂRozpoczyna pojedynek pomiędzy wskazanymi osobami lub dodaje taki pojedynek jako następny na liście,
        gdy użyte w trakcie pojedynku, może zostać użyte tylko jeśli można rozpocząć pojedynek lub w czasie
        jego trwania"""
        await self.invoke_state(ctx, first, second)

    @commands.command(name='challenges', aliases=['chls', 'pend'])
    @manitou_cmd()
    async def pen_challenges(self, ctx):
        """Ⓜ/&pend/&chls/Pokazuje aktualne wyzwania"""
        await self.invoke_state(ctx, ctx)  # second ctx as channel to send data

    @commands.command(name='wyzywam')
    @player_cmd()
    @town_only()
    async def add_challenge(self, ctx, *, osoba: MyMemberConverter):
        """Wyzywa wskazaną osobę na pojedynek"""
        await self.invoke_state(ctx, ctx.author, osoba)

    @commands.command(name='przyjmuję', aliases=['pr'])
    @player_cmd()
    @town_only()
    async def accept(self, ctx):
        """/&pr/Służy do przyjęcia pojedynku, który został wyzwany najwcześniej"""
        await self.invoke_state(ctx, ctx.author)

    @commands.command(name='odrzucam', aliases=['od', 'spierdalaj'])
    @player_cmd()
    @town_only()
    async def decline(self, ctx):
        """/&od/Służy do odrzucenia pojedynku, który został wyzwany najwcześniej"""
        await self.invoke_state(ctx, ctx.author)

    # ======================== Reporting commands =========================

    @commands.command(name='reported', aliases=['rpt', 'pens'])
    @manitou_cmd()
    async def pen_reports(self, ctx):
        """Ⓜ/&rpt/&pens/Pokazuje aktualne zgłoszenia"""
        await self.invoke_state(ctx, ctx)  # second ctx as channel to send data

    @commands.command(name='lock_reports', aliases=['repblok'])
    @manitou_cmd()
    async def lock(self, ctx):
        """Ⓜ/&repblok/Blokuje lub odblokowuje dodawanie nowych zgłoszeń"""
        await self.invoke_state(ctx)

    @commands.command(name='zgłaszam')
    @player_or_manitou_cmd()
    @town_only()
    async def add_report(self, ctx, *, osoba: MyMemberConverter):
        """Zgłasza podaną osobę do przeszukania"""
        await self.invoke_state(ctx, ctx.author, osoba)

    @commands.command(name='cofam', aliases=['wycofuję'])
    @player_or_manitou_cmd()
    @town_only()
    async def remove_report(self, ctx, *, osoba: MyMemberConverter):
        """Cofa zgłoszenie podanej osoby"""
        await self.invoke_state(ctx, ctx.author, osoba)
