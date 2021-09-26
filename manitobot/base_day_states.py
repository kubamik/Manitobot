import random
import typing
from abc import ABC
from collections import namedtuple
from enum import IntEnum
from typing import Awaitable

import discord

from . import errors
from .errors import MoreSearchedThanSearches, IllegalSearch, TooMuchHang, IllegalHang, DuplicateChallenge, \
    ChallengeNotFound, DuelAlreadyAccepted, ReportingLocked, AuthorIsSubjectChallengeError
from .interactions import Button
from .interactions.components import ButtonStyle
from .permissions import SPEC_ROLES
from .utility import get_town_channel, GUN_ID, get_searched_role, remove_roles, get_player_role, add_roles, \
    get_hanged_role


class States(IntEnum):
    """Indexes from .day_states.ORDER meaning special behaviors
    """
    prev = 0  # previous state
    next = 1  # following state
    voted = 2  # state after voting


_args = ['author', 'subject']
Challenge = namedtuple('Challenge', _args)
AcceptedChallenge = namedtuple('AcceptedChallenge', _args)


class DayState(ABC):
    """Base class for all day states
    """
    title = NotImplemented

    def __init__(self, game, day, /):
        self.day = day
        self.game = game

    def set_message(self, msg: discord.Message) -> Awaitable:
        """Edit state message to show actual information
        """
        return msg.edit(content=self.title, embed=None)

    async def async_init(self):
        """Function which is invoked on state change, use when need to to do some async initial work.
        On default this does nothing.
         """
        pass

    async def cleanup(self):
        """Function which is invoked on state change, use when need to do some work while deleting state.
        On default does nothing."""
        pass

    async def on_die(self, member: discord.Member, reason=None):
        reports = self.day.reports
        challenges = self.day.challenges
        if member in reports:
            reports.pop(member)
        for val in reports.values():
            try:
                val.remove(member)
            except ValueError:
                pass
        for chl in challenges.copy():
            if member in chl:
                challenges.remove(chl)


class Challenging(DayState, ABC):
    """Abstract class for states, which implements challenges for duels
    """

    async def async_init(self):
        await self._start_check()

    async def on_die(self, member: discord.Member, reason=None):
        await super(Challenging, self).on_die(member)
        await self._start_check()

    async def add_challenge(self, author: discord.Member, subject: discord.Member):
        challenges = self.day.challenges
        if (author, subject) in challenges or (subject, author) in challenges:
            raise DuplicateChallenge
        if author == subject:
            raise errors.SelfChallengeError
        msg = '**{0.display_name}** wyzywa **{1.display_name}** na pojedynek.\n'.format(author, subject)
        decl_role = SPEC_ROLES['decline_duels']
        if decl_role in self.game.role_map and self.game.role_map[decl_role].alive:
            msg += '<@{0.id}> czy chcesz przyjąć pojedynek? Użyj `&przyjmuję` lub `&odrzucam`'.format(subject)
            challenges.append(Challenge(author, subject))
            await get_town_channel().send(msg)
        else:
            msg += f'{decl_role} nie żyje, więc pojedynek jest automatycznie przyjęty'
            challenges.append(AcceptedChallenge(author, subject))
            await get_town_channel().send(msg)
            await self._start_check(verbose=True)

    def _find(self, subject: discord.Member) -> typing.Union[Challenge, AcceptedChallenge]:
        challenge = discord.utils.get(self.day.challenges, subject=subject)
        if not challenge:
            raise ChallengeNotFound
        if isinstance(challenge, AcceptedChallenge):
            raise DuelAlreadyAccepted
        return challenge

    async def decline(self, subject: discord.Member):
        challenge = self._find(subject)
        self.day.challenges.remove(challenge)
        await get_town_channel().send(
            '**{0[1].display_name}** odrzuca pojedynek od **{0[0].display_name}**'.format(challenge)
        )
        await self._start_check()

    async def accept(self, subject: discord.Member):
        challenges = self.day.challenges
        challenge = self._find(subject)
        idx = challenges.index(challenge)
        challenges[idx] = AcceptedChallenge._make(challenge)
        await get_town_channel().send(
            '**{0[1].display_name}** przyjmuje pojedynek od **{0[0].display_name}**'.format(challenge)
        )
        await self._start_check(verbose=True)

    async def pen_challenges(self, channel: discord.abc.Messageable, *, prefix: str = '__Wyzwania:__'):
        msg = prefix + '\n'
        for chl in self.day.challenges:
            acc = ' - *przyjęte*' if isinstance(chl, AcceptedChallenge) else ''
            msg += f'**{chl[0].display_name}** vs. **{chl[1].display_name}**{acc}\n'
        if not self.day.challenges:
            msg = 'Nie ma wyzwań\n'
        msg += '\nPozostało pojedynków: {}'.format(self.game.duels - self.day.duels)
        await channel.send(msg)

    async def _start_check(self, *, verbose: bool = False):
        if self.day.challenges and isinstance(self.day.challenges[0], AcceptedChallenge):
            await self.start_duel()
        elif verbose:
            await self.pen_challenges(
                get_town_channel(), prefix='Ten pojedynek nie może się teraz rozpocząć\n__Aktualne wyzwania:__'
            )

    async def start_duel(self, *participants: discord.Member):
        author, subject = participants or self.day.challenges.popleft()
        challenges = self.day.challenges
        if (author, subject) in challenges:
            challenges.remove((author, subject))
        elif (subject, author) in challenges:
            challenges.remove((subject, author))
        if author == subject:
            raise AuthorIsSubjectChallengeError
        if self.game.duels - self.day.duels <= 0:
            await self.day.push_state(States.next)
            await get_town_channel().send('Limit pojedynków został wyczerpany')
            return
        await self.day.push_state('duel', author=author, subject=subject)
        await get_town_channel().send(
            'Rozpoczynamy pojedynek:\n<:legacy_gun:{2}> **{0.display_name}** vs.:shield: **{1.display_name}**'.format(
                author, subject, GUN_ID
            )
        )


class Reporting(ABC):
    """Abstract class for states, which implements reporting for searches
    """
    day = NotImplemented
    game = NotImplemented
    locked = False

    async def add_report(self, author: discord.Member, subject: discord.Member):
        if self.locked:
            raise ReportingLocked
        reports = self.day.reports[subject]
        if author not in reports:
            reports.append(author)

    async def remove_report(self, author: discord.Member, subject: discord.Member):
        reports = self.day.reports[subject]
        if author in reports:
            reports.remove(author)

    async def pen_reports(self, channel: discord.abc.Messageable):
        msg = '__Zgłoszenia ({}):__\n'  # count added on the end because of empty keys possibility
        reports = self.day.reports
        for subject, authors in reports.copy().items():
            if not authors:
                reports.pop(subject)
            else:
                msg += '**{}** *przez* '.format(subject.display_name) \
                    + ', '.join([a.display_name for a in authors]) + '\n'
        msg += '\nLiczba przeszukań: {}'.format(self.game.searches)
        await channel.send(msg.format(len(reports)))

    async def voting(self):
        reports = self.day.reports
        for subject, authors in reports.copy().items():
            if not authors:
                reports.pop(subject)
        if len(reports) <= self.game.searches:
            await self.day.push_state(States.voted)
        else:
            await self.day.push_state(
                'vote', title='Przeszukania\nMasz {} głos(y) na osoby, które mają **zostać przeszukane**',
                options=[mbr.display_name for mbr in reports], required_votes=self.game.searches,
                msg='Głosujesz, aby **przeszukać** {}', resolved=list(reports)
            )  # options put into day_states.Voting.__init__


class DuelInterface(DayState, ABC):
    author = NotImplemented
    subject = NotImplemented

    async def on_die(self, member: discord.Member, reason=None):
        if member in (self.author, self.subject) and reason != 'duel':
            await get_town_channel().send('Pojedynek został anulowany z powodu śmierci jednego z uczestników.')
            await self.day.push_state(States.next)  # States.next is InitialState for states subclassing this
        await super().on_die(member)

    async def start_duel(self, author: discord.Member, subject: discord.Member):
        challenges = self.day.challenges
        if (author, subject) in challenges:
            challenges.remove((author, subject))
        elif (subject, author) in challenges:
            challenges.remove((subject, author))
        if author == subject:
            raise AuthorIsSubjectChallengeError
        self.day.challenges.appendleft(AcceptedChallenge(author, subject))


class Undoable(ABC):
    day = NotImplemented
    metadata = dict()

    async def undo(self):
        await self.day.push_state(States.prev, **self.metadata)


class SearchSummary(DayState, Undoable, ABC):
    title = '**Przeszukania - podsumowanie**'

    def __init__(self, game, day, /, *, summary: dict = None, searches: list = None, other: list = None):
        super().__init__(game, day)
        reports = self.day.reports
        players = get_player_role().members
        voted_members = other or list(reports)  # members options in voting
        for member in voted_members.copy():
            if member not in players:
                voted_members.remove(member)
        if searches is None:
            searches = []
        if summary:  # there was a voting (or revoting)
            results = [(len(v), member) for (v, member) in zip(summary.values(), voted_members)]
            results.sort(reverse=True, key=lambda t: t[0])
            accepted_num = len(searches)
            votes = iter(results + [(-1, None)])
            v, member = next(votes)
            last_num = v
            to_revote = []
            to_search = []
            # find n maximum voted people in case of draw use to_revote
            while v != -1 and (accepted_num < self.game.searches or last_num == v):
                if v != last_num:
                    to_search.extend(to_revote)
                    to_revote = [member]
                else:
                    to_revote.append(member)
                accepted_num += 1
                last_num = v
                v, member = next(votes)
            if accepted_num == self.game.searches:
                to_search.extend(to_revote)
                to_revote = []
            searches.extend(to_search)
            other = to_revote or list(set(voted_members) - set(searches)) or list(set(get_player_role().members)
                                                                                  - set(searches))
        elif len(voted_members) <= self.game.searches - len(searches):
            # reported members count is less or equal searches number
            searches.extend(voted_members)
            other = list(set(get_player_role().members) - set(searches))
        else:
            other = voted_members

        self.other = other  # members who are likely to be added to searches
        self.searches = searches  # members to be searched

    async def async_init(self):
        if self.searches:
            msg = 'Przeszukani zostaną:\n'
            for member in self.searches:
                msg += '**{}**\n'.format(member.display_name)
        else:
            msg = 'Na razie nikt nie ma zostać przeszukany\n'
        if self.other and hasattr(self, 'voting'):
            msg += '\nPotrzebne jest dodatkowe głosowanie dla:\n'
            for member in self.other:
                msg += '**{}**\n'.format(member.display_name)
        await get_town_channel().send(msg)
        await add_roles(self.searches, get_searched_role())

    async def cleanup(self):
        searched_role = get_searched_role()
        await remove_roles(searched_role.members, searched_role)

    async def end(self):
        to_search = get_searched_role().members
        if len(to_search) > self.game.searches:
            raise MoreSearchedThanSearches
        msg = "Przeszukani zostają:\n"
        for member in to_search:
            msg += "**{}**\n".format(member.display_name)
            if member not in self.game.player_map:
                raise IllegalSearch(member.display_name)
        if to_search:
            await get_town_channel().send(msg)
        else:
            await get_town_channel().send('Nikt nie zostaje przeszukany')
        try:
            for member in to_search:
                await get_town_channel().send(self.game.statue.day_search(member))  # could raise GameEnd
        finally:
            await self.day.push_state(States.next, searched=to_search)


class RandomizeSearch(SearchSummary, ABC):
    async def random(self):
        num = min(self.game.searches - len(self.searches), len(self.other))
        members = random.sample(self.other, num)
        self.searches.extend(members)
        await self.day.push_state(States.voted, searches=self.searches)


class HangSummary(DayState, Undoable, ABC):
    title = '**Wieszanie**'
    special_message = None

    def __init__(self, game, day, /, *, searched: list, summary: dict = None, other: list = None):
        super().__init__(game, day)
        other = other or searched.copy()  # members options in voting
        players = get_player_role().members
        for member in other.copy():
            if member not in players:
                other.remove(member)
        if summary:  # there was a voting (or revoting)
            results = [(len(v), member) for v, member in zip(summary.values(), other)]
            results.sort(reverse=True, key=lambda t: t[0])
            votes = iter(results + [(-1, None)])
            v, member = next(votes)
            num = v
            to_revote = []
            # find maximum voted people, in case of draw use to_revote
            while num == v:
                to_revote.append(member)
                v, member = next(votes)
            if len(to_revote) == 1:
                hanged = to_revote[0]
            else:
                hanged = None
                other = to_revote
        elif other:  # reported members count is less or equal searches number or all candidates died
            hanged = other[0]
        else:
            hanged = None
        self.metadata = {'searched': searched}
        self.hanged = hanged  # member to be hanged
        self.other = other  # members who are likely to be hanged

    async def async_init(self):
        if self.hanged:
            msg = 'Powieszony(-a) ma zostać **{}**'.format(self.hanged.display_name)
            await self.hanged.add_roles(get_hanged_role())
            await get_town_channel().send(msg)
            for role in SPEC_ROLES['hang_change']:
                try:
                    use = self.game.role_map[role].can_use
                    can = use('reveal') and use('peace')
                except KeyError:
                    pass
                else:
                    if not can:
                        continue
                    self.special_message = await get_town_channel().send(
                        'Czy Burmistrz chce ułaskawić wieszaną osobę?', components=[[
                            Button(ButtonStyle.Primary, label='Ułaskaw', custom_id='role_veto'),
                            Button(ButtonStyle.Destructive, label='Nie', custom_id='role_action_cancel')
                        ]])
                    break
        elif self.other:
            msg = "Potrzebne jest głosowanie uzupełniające dla:\n"
            for member in self.other:
                msg += "**{}**\n".format(member.display_name)
            await get_town_channel().send(msg)

    async def cleanup(self):
        hanged_role = get_hanged_role()
        await remove_roles(hanged_role.members, hanged_role)
        try:
            await self.special_message.delete(delay=0)
        except AttributeError:
            pass

    async def peace(self):
        await self.cleanup()

    async def end(self):
        members = get_hanged_role().members
        if len(members) > 1:
            raise TooMuchHang
        hanged = (members and members[0]) or None
        if hanged and hanged not in get_player_role().members:
            raise IllegalHang(hanged.display_name)
        if not hanged:
            await get_town_channel().send('Nikt nie zostaje powieszony')
        else:
            await get_town_channel().send('Powieszony(-a) zostaje **{}**'.format(self.hanged.display_name))
            role = self.game.player_map[hanged].role_class
            await role.die('hang')  # could raise GameEnd
            # but this state is the last one so nothing happens when next are not pushed
        await self.day.push_state(States.next)
