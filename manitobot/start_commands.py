from collections import Counter

import discord
from discord.ext import commands

from .basic_models import ManiBot
from .my_checks import manitou_cmd, game_check
from .errors import NoSuchSet, WrongRolesNumber
from .game import Game
from .starting import start_game
from .utility import clear_nickname, playerhelp, manitouhelp, get_admin_role, get_spectator_role, get_dead_role, \
    get_player_role
from . import control_panel, roles_commands, sklady, daily_commands


class Starting(commands.Cog, name='Początkowe'):

    def __init__(self, bot: ManiBot):
        self.bot = bot

    async def add_cogs(self):
        try:
            self.bot.add_cog(roles_commands.PoleceniaPostaci(self.bot))
            self.bot.add_cog(daily_commands.DailyCommands(self.bot))
            self.bot.add_cog(control_panel.ControlPanel(self.bot))
        except discord.errors.ClientException:
            pass
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions.all()
        p.administrator = False
        try:
            await get_admin_role().edit(permissions=p, colour=0)
        except (NameError, discord.errors.Forbidden):
            pass

    async def add_cogs_lite(self):
        try:
            self.bot.add_cog(daily_commands.DailyCommands(self.bot))
        except discord.errors.ClientException:
            pass
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions().all()
        p.administrator = False
        try:
            await get_admin_role().edit(permissions=p)
        except (NameError, discord.errors.Forbidden):
            pass

    @staticmethod
    def check_quantity(roles, mafia=False):
        players = get_player_role().members
        if mafia and len(roles) != len(players):
            raise WrongRolesNumber(len(players), len(roles))
        elif not mafia and len(set(roles)) != len(players):
            raise WrongRolesNumber(len(players), len(set(roles)))

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def start_mafia(self, ctx, *postacie: str):
        """Rozpoczyna mafię.
        W argumencie należy podać listę postaci (oddzielonych spacją) z liczebnościami w nawiasie (jeśli są różne od 1)
        np. Miastowy(5).
        Ważne jest zachowanie kolejności - rola mafijna jako ostatnia lub w przypadku większej ilości ról mafii
        oddzielenie ich '|'.
        np. &start_mafia Miastowy(7) Detektyw Lekarz | Boss Mafiozo(2) lub
        &start_mafia Miastowy(3) Mafiozo
        """
        roles = list(postacie)
        stop = -1 if '|' not in roles else roles.index('|')
        roles_list = Counter()
        for role in roles:
            if role == '|':
                i = roles.index(role)
                roles.remove(role)
                role = roles[i]
            count = 1
            if role.endswith(')'):
                count = int(role[:-1].rpartition('(')[2])
                role = role[:-3]
            roles_list[role] = count
        self.check_quantity(list(roles_list.elements()), True)
        await self.add_cogs_lite()
        await start_game(ctx, *roles_list.elements(), mafia=True,
                         faction_data=(list(roles_list)[: stop], list(roles_list)[stop:]))

    @commands.command(aliases=['składy'])
    @game_check(reverse=True)
    async def setlist(self, ctx):
        """/&składy/Wypisuje listę predefiniowanych składów.
        """
        await ctx.send(sklady.list_sets())

    @commands.command(name='set', aliases=['skład'])
    @game_check(reverse=True)
    async def set_(self, ctx, nazwa_skladu):
        """/&skład/Wypisuje listę postaci w składzie podanym jako argument.
        """
        set_name = nazwa_skladu
        await ctx.send(sklady.print_set(set_name).replace('_', ' '))

    @commands.command(name='start')
    @manitou_cmd()
    @game_check(reverse=True)
    async def start_game(self, ctx, *postacie):
        """ⓂRozpoczyna grę ze składem podanym jako argumenty funkcji.
        """
        roles = postacie
        self.check_quantity(roles)
        async with ctx.typing():
            await self.add_cogs()
            await start_game(ctx, *roles)

    @commands.command(aliases=['start_set'])
    @manitou_cmd()
    @game_check(reverse=True)
    async def startset(self, ctx, nazwa_skladu, *dodatkowe):
        """Ⓜ/&start_set/Rozpoczyna grę jednym z predefiniowanych składów
        Argumentami są:
            -Nazwa predefiniowanego składu (patrz komenda składy)
            -opcjonalnie dodatkowe postacie oddzielone białymi znakami
        """
        set_name = nazwa_skladu
        if not sklady.set_exists(set_name):
            raise NoSuchSet
        await self.start_game(ctx, *(sklady.get_set(set_name) + list(dodatkowe)))

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def resume(self, _):
        """ⓂUdaje rozpoczęcie gry, używać gdy bot się wykrzaczy a potrzeba zrobić głosowanie
        """
        await self.add_cogs()
        self.bot.game = Game()

    @commands.command(name='gram')
    @game_check(reverse=True)
    async def register(self, ctx):
        """Służy do zarejestrowania się do gry.
        """
        member = ctx.author
        await clear_nickname(member)
        await member.remove_roles(get_spectator_role(), get_dead_role())
        await member.add_roles(get_player_role())

    @commands.command(name='nie_gram', aliases=['niegram'])
    @game_check(reverse=True)
    async def deregister(self, ctx):
        """Służy do wyrejestrowania się z gry.
        """
        await ctx.author.remove_roles(get_player_role(), get_dead_role())
