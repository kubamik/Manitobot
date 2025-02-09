import discord
from discord import app_commands, AppCommandType
from discord.app_commands import Transform
from discord.ext import commands

from manitobot.basic_models import ManiBot
from manitobot.converters import MyMemberConverter, MyMemberConverterWithUserTransformer
from manitobot.errors import DayOnly, AuthorNotPlaying, NotTownChannel, WrongState, MemberNotPlaying
from manitobot.my_checks import manitou_cmd, player_cmd, town_only, player_or_manitou_cmd
from manitobot.utility import get_player_role, get_manitou_role
from settings import GUILD_ID, TOWN_CHANNEL_ID


class DailyCommands(commands.Cog, name='Polecenia dzienne', description=''):
    """Commands to be used during day or voting, integrated with DayStates
    Command callback name must be the same as name of a function in DayState
    """
    def __init__(self, bot: ManiBot):
        self.bot = bot
        cmds = [
            app_commands.ContextMenu(name="wyzywam", callback=self.context_command_add_challenge,
                                     type=AppCommandType.user, guild_ids=[GUILD_ID]),
            app_commands.ContextMenu(name="zgłaszam", callback=self.context_command_add_report,
                                     type=AppCommandType.user, guild_ids=[GUILD_ID]),
            app_commands.ContextMenu(name="cofam", callback=self.context_command_remove_report,
                                     type=AppCommandType.user, guild_ids=[GUILD_ID]),
        ]
        for cmd in cmds:
            self.bot.tree.add_command(cmd)
            cmd.add_check(self.context_command_check)

    def cog_check(self, ctx: commands.Context | discord.Interaction):
        day = self.bot.game.day
        if day is None:
            raise DayOnly
        return hasattr(day.state, ctx.command.callback.__name__.removeprefix('context_command_'))
        # check if it's possible to invoke command in current state

    async def cog_command_error(self, ctx, error):
        if type(error) is commands.CheckFailure:  # CheckFailure subclasses are handled on `Bot.on_command_error`
            await ctx.send('Na razie nie można używać tego polecenia', delete_after=10)

    async def invoke_state(self, ctx, *args):
        await getattr(self.bot.game.day.state, ctx.command.callback.__name__.removeprefix('context_command_'))(*args)

    async def context_command_check(self, interaction: discord.Interaction):
        if interaction.user not in get_player_role().members and interaction.user not in get_manitou_role().members:
            raise AuthorNotPlaying
        if interaction.channel.id != TOWN_CHANNEL_ID:
            raise NotTownChannel
        if not self.cog_check(interaction):
            raise WrongState
        return True

    @staticmethod
    def check_member(member: discord.Member) -> bool:
        if member not in get_player_role().members:
            raise MemberNotPlaying
        return True

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

    # =========================== Duels management commands ============================

    @commands.command(name='duel')
    @manitou_cmd()
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

    # ======================== Duel commands =========================

    @commands.hybrid_command(name='wyzywam')
    @app_commands.describe(osoba="Wyzywana osoba")
    @player_cmd()
    @town_only()
    async def add_challenge(self, ctx, *, osoba: Transform[discord.Member, MyMemberConverterWithUserTransformer]):
        """Wyzywa wskazaną osobę na pojedynek"""
        await self.invoke_state(ctx, ctx.author, osoba)
        if ctx.interaction:
            await ctx.send('✅', ephemeral=True)

    @commands.hybrid_command(name='przyjmuję', aliases=['akceptuję', 'pr', 'przyjmuje'])
    @player_cmd()
    @town_only()
    async def accept(self, ctx):
        """Służy do przyjęcia pojedynku, który został wyzwany najwcześniej"""
        await self.invoke_state(ctx, ctx.author)
        if ctx.interaction:
            await ctx.send('✅', ephemeral=True)

    @commands.hybrid_command(name='odrzucam', aliases=['spierdalaj', 'od', 'nah'])
    @player_cmd()
    @town_only()
    async def decline(self, ctx: commands.Context):
        """Służy do odrzucenia pojedynku, który został wyzwany najwcześniej"""
        if ctx.invoked_with == 'spierdalaj':
            await ctx.reply('**#STOP MOWIE NIENAWIŚCI**')
        await self.invoke_state(ctx, ctx.author)
        if ctx.interaction:
            await ctx.send('✅', ephemeral=True)

    # ======================== Reporting management commands =========================

    @commands.command(name='reported', aliases=['rpt', 'rep'])
    @manitou_cmd()
    async def pen_reports(self, ctx):
        """Ⓜ/&rpt/&rep/Pokazuje aktualne zgłoszenia"""
        await self.invoke_state(ctx, ctx)  # second ctx as channel to send data

    @commands.command(name='lock_reports', aliases=['repblok'])
    @manitou_cmd()
    async def lock(self, ctx):
        """Ⓜ/&repblok/Blokuje lub odblokowuje dodawanie nowych zgłoszeń"""
        await self.invoke_state(ctx)
        await self.bot.game.panel.change_removable(ctx.command.callback.__name__)

    # ======================== Reporting commands =========================

    @commands.hybrid_command(name='zgłaszam', aliases=['sus'])
    @app_commands.describe(osoba='Zgłaszana osoba')
    @player_or_manitou_cmd()
    @town_only()
    async def add_report(self, ctx, *, osoba: Transform[discord.Member, MyMemberConverterWithUserTransformer]):
        """Zgłasza podaną osobę do przeszukania"""
        await self.invoke_state(ctx, ctx.author, osoba)
        if ctx.interaction:
            await ctx.send(f'{ctx.author.display_name} zgłosił(a) {osoba.display_name}')

    @commands.hybrid_command(name='cofam', aliases=['wycofuję'])
    @app_commands.describe(osoba='Osoba, której zgłoszenie ma zostać cofnięte')
    @player_or_manitou_cmd()
    @town_only()
    async def remove_report(self, ctx, *, osoba: Transform[discord.Member, MyMemberConverterWithUserTransformer]):
        """Cofa zgłoszenie podanej osoby"""
        await self.invoke_state(ctx, ctx.author, osoba)
        if ctx.interaction:
            await ctx.send(f'{ctx.author.display_name} usunął(-ęła) zgłoszenie {osoba.display_name}')

    # ======================== Context commands =========================

    async def context_command_add_challenge(self, interaction: discord.Interaction, member: discord.Member):
        if self.check_member(member):
            await self.invoke_state(interaction, interaction.user, member)
            await interaction.response.send_message('✅', ephemeral=True)

    async def context_command_add_report(self, interaction: discord.Interaction, member: discord.Member):
        if self.check_member(member):
            await self.invoke_state(interaction, interaction.user, member)
            await interaction.response.send_message(f'{interaction.user.display_name} zgłosił(a) {member.display_name}',
                                                    ephemeral=True)

    async def context_command_remove_report(self, interaction: discord.Interaction, member: discord.Member):
        if self.check_member(member):
            await self.invoke_state(interaction, interaction.user, member)
            await interaction.response.send_message(f'{interaction.user.display_name} usunął(-ęła) zgłoszenie '
                                                    f'{member.display_name}', ephemeral=True)




