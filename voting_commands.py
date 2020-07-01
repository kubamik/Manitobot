import random

from discord.ext import commands

import globals
import votings
from utility import manitou_cmd, get_nickname, get_player_role, \
    get_searched_role


class Glosowania(commands.Cog, name="Głosowania"):

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

    @commands.command(name='vote')
    @manitou_cmd
    async def glosowanie_custom(self, ctx, title, count, *options):
        """ⓂRozpoczyna customowe głosowanie:
        Argumentami są:
          -tytuł głosowania.
          -wymagana liczba głosów.
          -nazwy kandydatów"""
        options_parsed = []
        for option in options:
            options_parsed.append(option.split(','))
        await votings.glosowanie(ctx, title, int(count), options_parsed)

    @commands.command(name='duel')
    @manitou_cmd
    async def pojedynek(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kto ma wygrać pojedynek?
        Argumentami są nazwy kandydatów."""
        if len(kandydaci) < 1:
            await ctx.send(
                "Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(
                    len(kandydaci), 1))
            return
        await self.glosowanie_custom(ctx,
                                     "**Pojedynek\nGłosujecie na osobę, która chcecie aby wygrała.**",
                                     "1", *kandydaci, "3,Wstrzymuję_Się")

    @commands.command(name='duel_vote', aliases=['vdl'])
    @manitou_cmd
    async def duel_vote(self, ctx):
        """Ⓜ/&vdl/Rozpoczyna głosowanie: kto ma wygrać pojedynek na podstawie automatycznie rozpoczętego pojedynku"""
        if not globals.current_game.days[-1].duel:
            await ctx.send("Nie rozpoczęto pojedynku")
            return
        agresor = globals.current_game.days[-1].participants[0]
        victim = globals.current_game.days[-1].participants[1]
        options_parsed = [["1", get_nickname(agresor.id)],
                          ["2", get_nickname(victim.id)],
                          ["3", "Wstrzymuję_Się"]]
        await votings.glosowanie(ctx,
                                 "**Pojedynek\nGłosujecie na osobę, która chcecie aby wygrała.**",
                                 1, options_parsed, (agresor, victim))

    @commands.command(name='search')
    @manitou_cmd
    async def przeszukania(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kogo przeszukać?
        Argumentami są nazwy kandydatów.
        Wymaganych jest tyle głosów ile wynosi zdefiniowana ilość preszukań (domyślnie 2)."""
        if len(kandydaci) < globals.current_game.searches:
            await ctx.send(
                "Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(
                    len(kandydaci), globals.current_game.searches))
            return
        await self.glosowanie_custom(ctx,
                                     "**Przeszukania\nGłosujecie na osoby, które mają być przeszukane**",
                                     globals.current_game.searches, *kandydaci)

    @commands.command(name='search_vote', aliases=['vsch'])
    @manitou_cmd
    async def search_vote(self, ctx):
        '''Ⓜ/&vsch/Rozpoczyna głosowanie kogo przeszukać na podstawie zgłoszonych kandydatur'''
        globals.current_game.days[-1].to_search = []
        if globals.current_game.night:
            await ctx.send("Nie można rozpocząć głosowania w nocy")
            return
        if globals.current_game.days[-1].hang_time:
            await ctx.send("Przeszukania już były")
            return
        try:
            if globals.current_game.nights[-1].herbed.alive():
                await ctx.send("Nie zapomniałeś o czymś:herb:?")
                return
        except AttributeError:
            pass
        for member in get_searched_role().members:
            await member.remove_roles(get_searched_role())
        globals.current_game.days[-1].search = True
        kandydaci = list(globals.current_game.days[-1].searched.keys())
        while len(kandydaci) < globals.current_game.searches:
            kandydaci.append(random.choice(
                list(set(get_player_role().members) - set(kandydaci))))
        if len(kandydaci) == globals.current_game.searches:
            await globals.current_game.days[-1].search_end(kandydaci)
            return
        options_parsed = [['{}'.format(number + 1), get_nickname(member.id)] for
                          number, member in enumerate(kandydaci)]
        await votings.glosowanie(ctx,
                                 "**Przeszukania\nGłosujecie na osoby, które mają być przeszukane**",
                                 globals.current_game.searches, options_parsed)

    @commands.command(name='revote', aliases=['vre'])
    @manitou_cmd
    async def revote(self, ctx):
        '''Ⓜ/&vre/Uruchamia głosowanie uzupełniające'''
        revote = False
        try:
            hrevote = globals.current_game.days[-1].to_hang
            if len(hrevote) > 0:
                revote = True
                kandydaci = hrevote
                options_parsed = [
                    ['{}'.format(number + 1), get_nickname(member.id)] for
                    number, member in enumerate(kandydaci)]
                await votings.glosowanie(ctx,
                                         "**Głosowanie uzupełniające na wieszanie\nGłosujecie na osobę, która ma zginąć**",
                                         1, options_parsed)
        except AttributeError:
            srevote = globals.current_game.days[-1].to_revote
            if len(srevote) > 0:
                kandydaci = srevote
                revote = True
                options_parsed = [
                    ['{}'.format(number + 1), get_nickname(member.id)] for
                    number, member in enumerate(kandydaci)]
                await votings.glosowanie(ctx,
                                         "**Głosowanie uzupełniające na przeszukanie\nGłosujecie na osoby, które mają być przeszukane**",
                                         globals.current_game.searches - len(
                                             globals.current_game.days[
                                                 -1].to_search), options_parsed)
        if not revote:
            await ctx.send("Nie ma kandydatur na takie głosowanie")

    @commands.command(name='hangif', aliases=['vhif'])
    @manitou_cmd
    async def czy_wieszamy(self, ctx):
        """Ⓜ/&vhif/Rozpoczyna głosowanie: czy powiesić?"""
        if not globals.current_game.days[-1].hang_time:
            await ctx.send(
                "Najpierw przeszukania. Jeżeli chcesz wymusić głosowanie użyj `&fhangif`")
            return
        await votings.glosowanie(ctx, "**Czy wieszamy?**", 1,
                                 [["t", "Tak"], ["n", "Nie"]])

    @commands.command(name='force_hangif', aliases=['fhangif'])
    @manitou_cmd
    async def hanging(self, ctx):
        """Ⓜ/&fhangif/Rozpoczyna głosowanie: czy powiesić?"""
        await votings.glosowanie(ctx, "**Czy wieszamy?**", 1,
                                 [["t", "Tak"], ["n", "Nie"]])

    @commands.command(name='hang')
    @manitou_cmd
    async def kogo_wieszamy(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kogo powiesić?
        Argumentami są nazwy kandydatów"""
        if len(kandydaci) < 1:
            await ctx.send(
                "Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(
                    len(kandydaci), 1))
            return
        await self.glosowanie_custom(ctx,
                                     "**Kogo wieszamy?\nGłosujecie na tego kogo chcecie powiesić**",
                                     "1", *kandydaci)

    @commands.command(name='hang_vote', aliases=['vhg'])
    @manitou_cmd
    async def hang_vote(self, ctx):
        '''Ⓜ/&vhg/Rozpoczyna głosowanie kogo powiesić na podstawie przeszukiwanych osób'''
        if not globals.current_game.days[-1].hang_time or \
                globals.current_game.days[-1].hang is None:
            await ctx.send("Najpierw głosowanie `hangif`")
            return
        globals.current_game.days[-1].hang = True
        kandydaci = globals.current_game.days[-1].candidates
        options_parsed = [['{}'.format(number + 1), get_nickname(member.id)] for
                          number, member in enumerate(kandydaci)]
        await votings.glosowanie(ctx,
                                 "**Wieszanie\nGłosujecie na osobę, która ma być powieszona**",
                                 1, options_parsed)

    @commands.command(name='votend', aliases=['vend'])
    @manitou_cmd
    async def glosowanie_koniec(self, ctx):
        """Ⓜ/&vend/Kończy głosowanie, wypisuje podsumowanie głosów na kanale głosowanie"""
        await votings.see_voting(ctx, True)

    @commands.command(name='votesee', aliases=['vs'])
    @manitou_cmd
    async def glosowanie_podgląd(self, ctx):
        """Ⓜ/&vs/Pisze do wszystkich manitou obecne wyniki głosowania"""
        await votings.see_voting(ctx, False)
