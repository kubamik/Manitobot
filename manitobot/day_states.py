import asyncio
import random
import typing
from contextlib import suppress

import discord

from .base_day_states import DayState, Challenging, Reporting, Undoable, States, SearchSummary, \
    RandomizeSearch, HangSummary, DuelInterface
from .errors import VotingNotAllowed, WrongValidVotesNumber, DuplicateVote, WrongVote, DuelDoublePerson, \
    NotDuelParticipant
from .interactions import Select, SelectOption
from .interactions.components import Button, Components
from discord import ButtonStyle
from .permissions import SPEC_ROLES
from .utility import get_player_role, get_town_channel, add_roles, get_duel_winner_role, get_duel_loser_role, \
    remove_roles


class SearchOnlyState(DayState, Reporting, Undoable):
    title = '**Zgłaszanie**'

    async def lock(self):
        self.locked = not self.locked


class InitialState(Challenging, Reporting, DayState):
    title = '**Zgłaszanie i wyzwania**'

    def __new__(cls, *args, **kwargs):
        game = args[0]
        day = args[1]
        if day.duels >= game.duels:  # ensure duels can be started if using InitialState
            cls = SearchOnlyState
        self = super(DayState, cls).__new__(cls)
        self.__init__(*args, **kwargs)
        return self

    async def end(self):
        await self.day.push_state(States.NEXT)
        await get_town_channel().send('__Zakończono fazę pojedynków__')


class Duel(DuelInterface, DayState):
    title = '**Pojedynek:**'

    def __init__(self, game, day, author, subject):
        super().__init__(game, day)
        self.author = author
        self.subject = subject

    def set_msg_edit_callback(self, callback: typing.Callable) -> typing.Awaitable:
        text = self.title + '\n' + '**{}** vs. **{}**'.format(self.author.display_name, self.subject.display_name)
        return callback(content=text, embed=None)

    async def voting(self):
        metadata = {'author': self.author, 'subject': self.subject}
        await self.day.push_state(
            'vote', title='Pojedynek\nMasz {} głos na osobę, która ma **wygrać pojedynek (przeżyć)**',
            options=[self.author.display_name, self.subject.display_name, 'Wstrzymuję_Się'],
            not_voting=(self.author, self.subject), msg='Głosujesz, aby **wygrał(a)/przeżył(a)** {}',
            metadata=metadata
        )  # options put into __init__ of proper state

    async def cancel(self):
        await get_town_channel().send('Manitou anulował trwający pojedynek')
        await self.day.push_state(States.PREV)


class DuelSummary(DuelInterface, DayState, Undoable):
    title = '**Pojedynek - podsumowanie**'
    special_message = None

    def __init__(self, game, day, *, author, subject, summary):
        super().__init__(game, day)
        self.author = author
        self.subject = subject
        votes = list(summary.values())
        results = []
        players = self.game.player_map
        self.winners = []
        self.losers = []
        for v, member in zip(votes[:2], (author, subject)):
            # In voting options author goes first, then subject, then pass
            rev = players[member].role_class.can_use('revoling')
            results.append((rev, len(v)))
        if results[0] != results[1]:
            self.winners = [author if results[1] < results[0] else subject]
            self.losers = [author if author != self.winners[0] else subject]
        elif results[0][1] == 0:
            self.winners = [author, subject]
        else:
            self.losers = [author, subject]
        self.metadata = {'author': author, 'subject': subject}

    async def async_init(self):
        await add_roles(self.winners, get_duel_winner_role())
        await add_roles(self.losers, get_duel_loser_role())
        if self.losers and self.winners:
            msg = 'Pojedynek ma wygrać **{}**. Zginąć ma **{}**'.format(self.winners[0].display_name,
                                                                        self.losers[0].display_name)
        elif self.winners:
            msg = 'W wyniku pojedynku nikt nie ginie *(na razie)*'
        else:
            msg = 'W wyniku pojedynku mają zginąć obaj pojedynkujący się'
        await get_town_channel().send(msg)
        for role in SPEC_ROLES['duel_change']:
            try:
                can = self.game.role_map[role].can_use('wins')
            except KeyError:
                pass
            else:
                if not can:
                    continue
                self.special_message = await get_town_channel().send(
                    f'Czy {role.replace("_", " ")} chce zmienić wynik pojedynku?', view=Components([[
                        Button(ButtonStyle.primary, label=f'Wygrywa {self.author.display_name}',
                               custom_id='role_wins_first'),
                        Button(ButtonStyle.primary, label=f'Wygrywa {self.subject.display_name}',
                               custom_id='role_wins_second'),
                        Button(ButtonStyle.danger, label='Nie', custom_id='duel_role_action_cancel')
                    ]]))
                break

    async def cleanup(self):
        winner_role = get_duel_winner_role()
        loser_role = get_duel_loser_role()
        members = winner_role.members + loser_role.members
        await remove_roles(members, winner_role, loser_role)
        try:
            await self.special_message.delete(delay=0)
        except AttributeError:
            pass

    def set_msg_edit_callback(self, callback: typing.Callable) -> typing.Awaitable:
        text = self.title + '\n**{}** vs. **{}**'.format(self.author.display_name, self.subject.display_name)
        return callback(content=text, embed=None)

    async def change_winner(self, member: discord.Member):
        participants = self.winners + self.losers
        winner_role = get_duel_winner_role()
        loser_role = get_duel_loser_role()
        tasks = []
        for m in participants:
            new_roles = m.roles
            if m != member:
                with suppress(ValueError):
                    new_roles.remove(winner_role)
                if loser_role not in new_roles:
                    new_roles.append(loser_role)
            else:
                with suppress(ValueError):
                    new_roles.remove(loser_role)
                if winner_role not in new_roles:
                    new_roles.append(winner_role)
            tasks.append(m.edit(roles=new_roles))
        tasks.append(self.special_message.delete(delay=0))
        await asyncio.gather(*tasks)

    async def end(self):
        winner_role = get_duel_winner_role()
        loser_role = get_duel_loser_role()
        losers = loser_role.members
        winners = winner_role.members
        participants = self.losers + self.winners
        for member in winners + losers:
            if member in winners and member in losers:
                raise DuelDoublePerson(member.display_name)
            if member not in participants:
                role = winner_role if member in winners else loser_role
                raise NotDuelParticipant(member.display_name, role.mention)
        self.day.duels += 1
        if len(winners) == 1:
            msg = 'Pojedynek wygrywa **{}**'.format(winners[0].display_name)
        elif len(winners) == 2:
            msg = 'W wyniku pojedynku nikt nie ginie'
        else:
            msg = None
        if msg:
            await get_town_channel().send(msg)
        try:
            for member in losers:
                player = self.game.player_map[member].role_class
                await player.die('duel')  # could raise GameEnd
        finally:
            await self.day.push_state(States.NEXT)


class SearchingSummaryWithRevote(RandomizeSearch, SearchSummary, DayState, Undoable):
    async def voting(self):
        num = self.game.searches - len(self.searches)
        metadata = {'searches': self.searches, 'other': self.other}
        await self.day.push_state(
            'vote', title='Przeszukania - uzupełniające\nMasz {} głos(y) na osoby, które mają **zostać przeszukane**',
            options=[mbr.display_name for mbr in self.other], required_votes=num,
            msg='Głosujesz, aby **przeszukać** {}', resolved=self.other, metadata=metadata
        )  # options put into __init__ of proper state


class SearchingSummaryWithRandom(RandomizeSearch, SearchSummary, DayState, Undoable):
    pass


class SearchingSummary(SearchSummary, DayState, Undoable):
    def __new__(cls, *args, **kwargs):
        summary = kwargs.get('summary')
        searches = kwargs.get('searches', list())
        game = args[0]
        day = args[1]
        reports = day.reports
        players = get_player_role().members
        if game.searches > len(players):
            game.searches = len(players)
        rest_num = game.searches - len(searches)
        if summary:
            for member in summary.copy():
                if member not in players:
                    summary.pop(member)
            summary = [len(v) for v in summary.values()]
            sort_sum = sorted(summary, reverse=True)
            if len(sort_sum) < rest_num:
                cls = SearchingSummaryWithRandom
            elif len(sort_sum) != rest_num and sort_sum[rest_num - 1] == sort_sum[rest_num]:
                cls = SearchingSummaryWithRevote
        else:
            if len(reports) != rest_num != 0:
                cls = SearchingSummaryWithRandom
        self = super(SearchSummary, cls).__new__(cls)
        if cls is not SearchingSummary:
            self.__init__(*args, **kwargs)
        return self


class HangIfable(DayState):
    title = '**Decyzja o wieszaniu**'

    def __init__(self, game, day, *, searched):
        super().__init__(game, day)
        self.searched = searched

    async def voting(self):
        metadata = {'searched': self.searched}
        await self.day.push_state(
            'vote', title='Czy wieszamy?\nMasz {} głos na wybraną opcję', options=['t,Tak', 'n,Nie'], metadata=metadata
        )


class HangIfSummary(DayState, Undoable):
    title = '**Przed wieszaniem**'

    def __init__(self, game, day, *, searched, summary=None):
        super().__init__(game, day)
        self.searched = searched
        if summary:
            self.hang = len(summary['Tak']) > len(summary['Nie'])
        else:  # previous state was HangingSummary or Voting(who to hang) and undo was used
            self.hang = None
        self.metadata = {'searched': self.searched}

    def set_msg_edit_callback(self, callback: typing.Callable) -> typing.Awaitable:
        content = self.title + ' - {}wieszamy'.format('nie ' if self.hang is False else '')
        return callback(content=content, embed=None)

    async def async_init(self):
        msg = ''
        if self.hang:
            msg = 'Decyzją miasta wieszamy.'
        elif self.hang is False:
            msg = 'Decyzją miasta nie wieszamy.'
        if msg:
            await get_town_channel().send(msg)

    async def voting(self):
        for mbr in self.searched.copy():
            if mbr not in get_player_role().members:
                self.searched.remove(mbr)
        if len(self.searched) <= 1:
            await self.day.push_state(States.VOTED, searched=self.searched)
        else:
            await self.day.push_state(
                'vote', title='Wieszanie\nMasz {} głos na osobę, która ma **zostać powieszona**',
                options=[mbr.display_name for mbr in self.searched],
                msg='Głosujesz, aby **zginął(-ęła)** {}', resolved=self.searched, metadata=self.metadata
            )  # options put into __init__ of proper state


class HangingSummaryWithRevote(HangSummary, DayState, Undoable):
    async def random(self):
        member = [random.choice(self.other)]
        await self.day.push_state(States.VOTED, other=member, **self.metadata)

    async def voting(self):
        self.metadata.update(other=self.other)
        await self.day.push_state(
            'vote', title='Wieszanie - uzupełniające\nMasz {} głos na osobę, która ma **zostać powieszona**',
            options=[mbr.display_name for mbr in self.other],
            msg='Głosujesz, aby **zginął(-ęła)** {}', resolved=self.other, metadata=self.metadata
        )  # options put into __init__ of proper state


class HangingSummary(HangSummary, DayState, Undoable):
    def __new__(cls, *args, **kwargs):
        summary = kwargs.get('summary')
        players = get_player_role().members
        if summary:
            for member in summary.copy():
                if member not in players:
                    summary.pop(member)
            summary = [len(v) for v in summary.values()]
            sort_sum = sorted(summary, reverse=True)
            if len(summary) > 1 and sort_sum[0] == sort_sum[1]:
                cls = HangingSummaryWithRevote
        self = super(HangSummary, cls).__new__(cls)
        if cls is not HangingSummary:
            self.__init__(*args, **kwargs)
        return self


class Evening(DayState):
    title = '**Zakończ dzień**'


class Voting(DayState):
    """State representing voting, designed to be used even during night
    """

    state_msg_edit: typing.Callable = None
    vote_msg: typing.Optional[discord.Message] = None
    message = 'Zarejestrowałem twój(-oje) głos(y) na {}'
    V_INSTRUCTION = 'INSTRUKCJA\n' + \
        'Aby zagłosować wyślij tu dowolny wariant dowolnej opcji. ' + \
        'Wiele głosów należy oddzielić przecinkami. Wielkość znaków nie ma znaczenia.'

    def __init__(self, game, day, title: str, options: typing.List[str], required_votes: int = 1, msg: str = None,
                 not_voting: tuple = (), resolved: list = None, *, previous: DayState = None,
                 following: DayState = None, metadata: dict = None):
        super().__init__(game, day)
        if '\n' in title:
            self.title = title.split('\n')
        else:
            self.title = [title, 'Wymagana liczba głosów: {}']
        if all([',' in option for option in options]):
            self.options = [option.split(',') for option in options]
        else:
            self.options = [[str(i+1), option] for i, option in enumerate(options)]
        self.lowered_options = [[o.lower() for o in option] for option in self.options]
        self.votes = {option[-1]: list() for option in self.options}
        self.required_votes = required_votes
        self.participants = set(get_player_role().members) - set(not_voting)
        if msg:
            self.message = msg
        self.resolved = resolved
        self.previous = previous
        self.following = following
        self.metadata = metadata or dict()
        self.voted = set()
        self.voters = {}

    async def async_init(self):
        self.vote_msg: discord.Message = await self.options_message()

    def set_msg_edit_callback(self, callback: typing.Callable) -> typing.Awaitable:
        """Edits state message to display voting
        """
        self.state_msg_edit = callback
        return callback(content=None, embed=self.results_embed())

    def update_message(self) -> typing.Awaitable:
        """Edits state message to display current voting information.
        """
        return self.state_msg_edit(embed=self.results_embed())

    def options_embed(self) -> discord.Embed:
        """Generates embed with information about voting and options
        """
        options_readable = ""
        for option in self.options:
            options_readable += "**{}**\n\n".format(", ".join(option))
        title = self.title
        em_title = "Głosowanie: {}".format(title[0])
        description = title[1].format(self.required_votes) + '\n\n' + options_readable
        embed = discord.Embed(title=em_title, colour=discord.Colour(0x00aaff), description=description)
        embed.set_footer(text=self.V_INSTRUCTION)
        return embed

    async def options_message(self) -> discord.Message:
        title = self.title
        em_title = "Głosowanie: {}".format(title[0])
        description = title[1].format(self.required_votes)
        embed = discord.Embed(title=em_title, colour=discord.Colour(0x00aaff), description=description)
        options = [SelectOption(option, option) for option in self.votes]
        vnum = min(self.required_votes, len(self.votes))
        components = Components([[Select('add_vote', options, min_values=vnum, max_values=vnum)]])
        return await get_town_channel().send(content=get_player_role().mention, embed=embed, view=components)

    def results_embed(self, end: bool = False) -> discord.Embed:
        """Generates embed with current voting results, with ending note if needed
        """
        summary = ''
        title = '**Głosowanie zakończone!**\n' if end else 'Głosowanie: {} - podgląd\n'.format(self.title[0])
        for option, voters in self.votes.items():
            voters_readable = [voter.display_name for voter in voters]
            summary += '**{}** na **{}**:\n {}\n\n'.format(len(voters), option, ', '.join(voters_readable))
        message = "**Wyniki**:\n\n{}".format(summary)
        embed = discord.Embed(title=title, colour=discord.Colour(0x00ccff))
        not_voted = list(self.participants - self.voted)
        if not end:
            if not len(not_voted):
                message += "**Wszyscy grający oddali głosy**"
            else:
                message += "**Nie zagłosowali tylko:**\n"
                not_voted = [p.display_name for p in not_voted]
                message += '\n'.join(not_voted)
        embed.description = message
        return embed

    def parse_vote(self, vote: str) -> typing.List[str]:
        vote: typing.List[str] = [v.strip().lower() for v in vote.split(',')]
        votes = []
        for v in vote:
            for i, option in enumerate(self.lowered_options):
                if v in option:
                    v_std = self.options[i][-1]
                    if v_std in votes:
                        raise DuplicateVote(v_std)
                    votes.append(v_std)
                    break
            else:
                raise WrongVote(v)
        if len(votes) != self.required_votes:
            raise WrongValidVotesNumber(len(votes), self.required_votes)
        return votes

    async def register_vote(self, author: discord.Member, votes: typing.List[str]) -> str:
        if author not in self.participants:
            raise VotingNotAllowed('Author can\'t vote now.')
        if author in self.voted:
            for option in self.voters[author]:
                self.votes[option].remove(author)
        self.voted.add(author)
        self.voters[author] = votes
        for option in votes:
            self.votes[option].append(author)
        await self.update_message()
        return self.message.format(', '.join(votes))

    async def end(self):
        components = Components.from_message(self.vote_msg)
        components.components_list[0][0].disabled = True
        await self.vote_msg.edit(view=components)
        embed = self.results_embed(end=True)
        await get_town_channel().send(embed=embed)
        if self.resolved:
            summary = dict(zip(self.resolved, self.votes.values()))
        else:
            summary = self.votes
        if self.following is not None:
            await self.day.push_state(self.following, summary=summary, **self.metadata)
        else:
            await self.day.end_custom_voting()

    async def cancel(self):
        await self.vote_msg.delete(delay=0)
        if self.following is not None:
            await self.day.push_state(self.previous, **self.metadata)
        else:
            await self.day.end_custom_voting()

    async def on_die(self, member: discord.Member, reason=None):
        if self.previous is Duel and member in self.metadata.values():
            await self.vote_msg.delete(delay=0)
            await get_town_channel().send('Pojedynek został anulowany z powodu śmierci jednego z uczestników.')
            await self.day.push_state(InitialState)
        await super().on_die(member)


# (previous, following, after_voting)
ORDER: typing.Dict[typing.Type[DayState], tuple] = {
    InitialState: (None, SearchOnlyState, SearchingSummary),
    Duel: (InitialState, InitialState, DuelSummary),
    DuelSummary: (Duel, InitialState, None),
    SearchOnlyState: (InitialState, None, SearchingSummary),
    SearchingSummary: (SearchOnlyState, HangIfable, SearchingSummary),
    SearchingSummaryWithRevote: (SearchOnlyState, HangIfable, SearchingSummary),
    SearchingSummaryWithRandom: (SearchOnlyState, HangIfable, SearchingSummary),
    HangIfable: (None, None, HangIfSummary),
    HangIfSummary: (HangIfable, None, HangingSummary),
    HangingSummary: (HangIfSummary, Evening, HangingSummary),
    HangingSummaryWithRevote: (HangIfSummary, Evening, HangingSummary),
}
