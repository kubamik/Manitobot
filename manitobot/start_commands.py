from collections import Counter

import discord
from discord.ext import commands

from .cheks import manitou_cmd, game_check
from .errors import NoSuchSet
from .game import Game
from .starting import start_game
from .utility import playerhelp, manitouhelp, get_admin_role, clear_nickname, \
    get_spectator_role, get_dead_role, \
    get_player_role
from . import control_panel, duels_commands, roles_commands, \
    search_hang_commands, sklady, voting_commands


class Starting(commands.Cog, name='Początkowe'):

    def __init__(self, bot):
        self.bot = bot

    async def add_cogs(self):
        try:
            self.bot.add_cog(voting_commands.Glosowania(self.bot))
            self.bot.add_cog(roles_commands.PoleceniaPostaci(self.bot))
            self.bot.add_cog(duels_commands.Pojedynki(self.bot))
            self.bot.add_cog(search_hang_commands.Przeszukania(self.bot))
            self.bot.add_cog(search_hang_commands.Wieszanie(self.bot))
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
            self.bot.add_cog(voting_commands.Glosowania(self.bot))
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

    @commands.command(name='start_mafia')
    @manitou_cmd()
    @game_check(rev=True)
    async def mafia_start(self, _, *postacie: str):
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
        await self.add_cogs_lite()
        await start_game(*roles_list.elements(), mafia=True,
                         faction_data=(list(roles_list)[: stop], list(roles_list)[stop:]))

    @commands.command(aliases=['składy'])
    @game_check(rev=True)
    async def setlist(self, ctx):
        """/&składy/Wypisuje listę predefiniowanych składów.
        """
        await ctx.send(sklady.list_sets())

    @commands.command(name='set', aliases=['skład'])
    @game_check(rev=True)
    async def set_(self, ctx, nazwa_skladu):
        """/&skład/Wypisuje listę postaci w składzie podanym jako argument.
        """
        set_name = nazwa_skladu
        await ctx.send(sklady.print_set(set_name).replace('_', ' '))

    @commands.command(name='start')
    @manitou_cmd()
    @game_check(rev=True)
    async def start_game(self, ctx, *postacie):
        """ⓂRozpoczyna grę ze składem podanym jako argumenty funkcji.
        """
        roles = postacie
        async with ctx.typing():
            await self.add_cogs()
            await start_game(*roles)

    @commands.command(aliases=['start_skład'])
    @manitou_cmd()
    @game_check(rev=True)
    async def startset(self, ctx, nazwa_skladu, *dodatkowe):
        """Ⓜ/&start_skład/Rozpoczyna grę jednym z predefiniowanych składów
        Argumentami są:
            -Nazwa predefiniowanego składu (patrz komenda składy)
            -opcjonalnie dodatkowe postacie oddzielone białymi znakami
        """
        set_name = nazwa_skladu
        if not sklady.set_exists(set_name):
            raise NoSuchSet('<--')
        async with ctx.typing():
            await self.add_cogs()
            await start_game(*(sklady.get_set(set_name) + list(dodatkowe)))

    @commands.command(name='resume')
    @manitou_cmd()
    @game_check(rev=True)
    async def come_back(self, _):
        """ⓂUdaje rozpoczęcie gry, używać gdy bot się wykrzaczy a potrzeba zrobić głosowanie
        """
        self.bot.game = Game()
        await self.add_cogs()

    @commands.command(name='gram')
    @game_check(rev=True)
    async def register(self, ctx):
        """Służy do zarejestrowania się do gry.
        """
        member = ctx.author
        await clear_nickname(member)
        await member.remove_roles(get_spectator_role(), get_dead_role())
        await member.add_roles(get_player_role())

    @commands.command(name='nie_gram', aliases=['niegram'])
    @game_check(rev=True)
    async def deregister(self, ctx):
        """Służy do wyrejestrowania się z gry.
        """
        await ctx.author.remove_roles(get_player_role(), get_dead_role())
