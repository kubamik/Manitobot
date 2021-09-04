import random
import typing

from discord.ext import commands

from . import votings
from .my_checks import manitou_cmd, voting_check, day_only
from .errors import TooLessVotingOptions, GameNotStarted
from .starting import if_game
from .utility import get_nickname, get_player_role, get_searched_role


class Glosowania(commands.Cog, name='Głosowania'):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not if_game():
            raise GameNotStarted
        return True

    @commands.command(name='vote_cancel', aliases=['vclc'])
    @manitou_cmd()
    @voting_check(reverse=True)
    async def cancel_vote(self, _):
        """Ⓜ/&vclc/Anuluje trwające głosowanie"""
        self.bot.game.voting = None

    @commands.command(name='vote')
    @manitou_cmd()
    @voting_check()
    async def glosowanie_custom(
            self, _, title,
            count: typing.Optional[int] = 1, *options):
        """ⓂRozpoczyna customowe głosowanie:
        Argumentami są:
          -tytuł głosowania.
          -wymagana liczba głosów.
          -nazwy kandydatów"""
        if '\n' not in title:
            title += '\nWymagana liczba głosów: {}'
        options_parsed = []
        for option in options:
            options_parsed.append(option.split(','))
        await votings.start_voting(title, count, options_parsed)

    @commands.command(name='duel')
    @manitou_cmd()
    @voting_check()
    async def dueling(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kto ma wygrać pojedynek?
        Argumentami są nazwy kandydatów."""
        if len(kandydaci) < 1:
            raise TooLessVotingOptions(len(kandydaci))
        await self.glosowanie_custom(ctx, 'Pojedynek\nMasz {} głos na osobę, która ma **wygrać** pojedynek', 1,
                                     *kandydaci, "3,Wstrzymuję_Się")

    @commands.command(name='duel_vote', aliases=['vdl'])
    @manitou_cmd()
    @voting_check()
    async def duel_vote(self, ctx):
        """Ⓜ/&vdl/Rozpoczyna głosowanie: kto ma wygrać pojedynek na podstawie automatycznie rozpoczętego pojedynku"""
        if not self.bot.game.days[-1].duel:
            await ctx.send("Nie rozpoczęto pojedynku")
            return
        agresor = self.bot.game.days[-1].participants[0]
        victim = self.bot.game.days[-1].participants[1]
        options_parsed = [['1', get_nickname(agresor.id)], ['2', get_nickname(victim.id)], ['3', 'Wstrzymuję_Się']]
        self.bot.game.days[-1].duel_remember_nicks()
        await votings.start_voting('Pojedynek\nMasz {} głos na osobę, która ma **wygrać** pojedynek', 1,
                                   options_parsed, [agresor, victim], "duel")

    @commands.command(name='search')
    @manitou_cmd()
    @voting_check()
    async def searching(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kogo przeszukać?
        Argumentami są nazwy kandydatów.
        Wymaganych jest tyle głosów ile wynosi zdefiniowana ilość preszukań (domyślnie 2)."""
        if len(kandydaci) < self.bot.game.searches:
            await ctx.send("Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(len(kandydaci),
                                                                                                self.bot.game.searches))
            return
        await self.glosowanie_custom(ctx, "Przeszukania\nMasz {} głosy na osoby, które mają **zostać przeszukane**",
                                     self.bot.game.searches, *kandydaci)

    @commands.command(name='search_vote', aliases=['vsch'])
    @manitou_cmd()
    @voting_check()
    @day_only()
    async def search_vote(self, ctx):
        """Ⓜ/&vsch/Rozpoczyna głosowanie kogo przeszukać na podstawie zgłoszonych kandydatur"""
        self.bot.game.days[-1].to_search = []
        if self.bot.game.days[-1].hang_time:
            await ctx.send("Przeszukania już były")
            return
        try:
            if self.bot.game.nights[-1].herbed.alive:
                await ctx.send("Nie zapomniałeś o czymś:herb:?")
                return
        except AttributeError:
            pass
        for member in get_searched_role().members:
            await member.remove_roles(get_searched_role())
        self.bot.game.days[-1].search = True
        kandydaci = list(self.bot.game.days[-1].searched.keys())
        if len(get_player_role().members) < self.bot.game.searches:
            self.bot.game.searches = len(get_player_role().members)
        while len(kandydaci) < self.bot.game.searches:
            kandydaci.append(random.choice(list(set(get_player_role().members) - set(kandydaci))))
        if len(kandydaci) == self.bot.game.searches:
            await self.bot.game.days[-1].search_end(kandydaci)
            return
        self.bot.game.days[-1].search_remember_nicks()
        options_parsed = [['{}'.format(number + 1), member.display_name] for number, member in enumerate(kandydaci)]
        await votings.start_voting("Przeszukania\nMasz {} głosy na osoby, które mają **zostać przeszukane**",
                                   self.bot.game.searches, options_parsed, vtype="search")

    @commands.command(name='revote', aliases=['vre'])
    @manitou_cmd()
    @voting_check()
    @day_only()
    async def revote(self, ctx):
        """Ⓜ/&vre/Uruchamia głosowanie uzupełniające"""
        cand_h_revote = self.bot.game.days[-1].to_hang
        cand_s_revote = self.bot.game.days[-1].to_revote
        if len(cand_h_revote) > 0:
            kandydaci = cand_h_revote
            options_parsed = [['{}'.format(number + 1), get_nickname(member.id)] for number, member in
                              enumerate(kandydaci)]
            await votings.start_voting(
                'Wieszanie - uzupełniające\nPrzeszukania\nMasz {} głos na osobę, która ma zginąć',
                1, options_parsed, vtype="hang")
        elif len(cand_s_revote) > 0:
            kandydaci = cand_s_revote
            options_parsed = [['{}'.format(number + 1), get_nickname(member.id)] for number, member in
                              enumerate(kandydaci)]
            await votings.start_voting(
                'Przeszukania - uzupełniające\nMasz {} głos(-y) na osobę(-y), która(-e) ma(ją) **zostać przeszukana('
                '-e)**', self.bot.game.searches - len(self.bot.game.days[-1].to_search), options_parsed, vtype="search")
        else:
            await ctx.send("Nie ma kandydatur na takie głosowanie")

    @commands.command(name='hangif', aliases=['vhif', 'hiv'])
    @manitou_cmd()
    @voting_check()
    @day_only()
    async def hangif(self, ctx):
        """Ⓜ/&vhif/Rozpoczyna głosowanie: czy powiesić?"""
        if not self.bot.game.days[-1].hang_time:
            await ctx.send("Najpierw przeszukania. Jeżeli chcesz wymusić głosowanie użyj `&fhangif`")
            return
        await votings.start_voting('Czy wieszamy?\nMasz {} głos na wybraną opcję.', 1, [["t", "Tak"], ["n", "Nie"]],
                                   vtype="hangif")

    @commands.command(name='force_hangif', aliases=['fhangif'])
    @manitou_cmd()
    @voting_check()
    async def hanging(self, _):
        """Ⓜ/&fhangif/Rozpoczyna głosowanie: czy powiesić?"""
        await votings.start_voting('Czy wieszamy?\nMasz {} głos na wybraną opcję.', 1, [['t', 'Tak'], ['n', 'Nie']])

    @commands.command(name='hang')
    @manitou_cmd()
    @voting_check()
    async def who_hang(self, ctx, *kandydaci):
        """ⓂRozpoczyna głosowanie: kogo powiesić?
        Argumentami są nazwy kandydatów"""
        if len(kandydaci) < 1:
            await ctx.send("Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(len(kandydaci), 1))
            return
        await self.glosowanie_custom(ctx, 'Wieszanie\nGłosujecie Głosujecie na osobę, która **ma być powieszona**', 1,
                                     *kandydaci)

    @commands.command(name='hang_vote', aliases=['vhg'])
    @manitou_cmd()
    @voting_check()
    @day_only()
    async def hang_vote(self, ctx):
        """Ⓜ/&vhg/Rozpoczyna głosowanie kogo powiesić na podstawie przeszukiwanych osób"""
        if not self.bot.game.days[-1].hang_time or self.bot.game.days[-1].hang is None:
            await ctx.send("Najpierw głosowanie `&hangif`")
            return
        self.bot.game.days[-1].hang = True
        kandydaci = self.bot.game.days[-1].candidates
        self.bot.game.days[-1].hang_remember_nicks()
        if len(kandydaci) == 1:
            await self.bot.game.days[-1].hang_sumarize(ctx, {kandydaci[0].display_name: []})
        else:
            options_parsed = [['{}'.format(number + 1), member.display_name] for number, member in enumerate(kandydaci)]
            await votings.start_voting('Wieszanie\nGłosujecie na osobę, która **ma być powieszona**', 1,
                                       options_parsed, vtype='hang')

    @commands.command(name='votend', aliases=['vend'])
    @manitou_cmd()
    @voting_check(reverse=True)
    async def vote_end(self, ctx):
        """Ⓜ/&vend/Kończy głosowanie, wypisuje podsumowanie głosów,
        uruchamia akcje powiązane (przeszukania, pojedynki, wieszanie)"""
        await votings.see_end_voting(ctx, True)

    @commands.command(name='votesee', aliases=['vs'])
    @manitou_cmd()
    @voting_check(reverse=True)
    async def vote_see(self, ctx):
        """Ⓜ/&vs/Pisze do wszystkich manitou obecne wyniki głosowania"""
        await votings.see_end_voting(ctx, False)
