import collections
import functools
import unittest
from unittest.mock import AsyncMock, MagicMock

import discord

from manitobot.base_day_states import AcceptedChallenge, Challenge, HangSummary
from manitobot.day_states import InitialState, SearchOnlyState, Voting, Duel, DuelSummary, SearchingSummary, \
    SearchingSummaryWithRevote, SearchingSummaryWithRandom, HangIfable, HangIfSummary, HangingSummary, \
    HangingSummaryWithRevote, Evening
from bases import BaseStateTest
from manitobot.errors import SelfChallengeError, DuplicateChallenge, ChallengeNotFound, DuelAlreadyAccepted, \
    AuthorIsSubjectChallengeError, ReportingLocked, DuelDoublePerson, NotDuelParticipant, MoreSearchedThanSearches, \
    IllegalSearch, TooMuchHang, IllegalHang
from manitobot.permissions import SPEC_ROLES
from settings import GUN_ID


class TestInitialState(BaseStateTest):
    def test_new_method(self):
        self.assertIsInstance(self.state, InitialState)

    def test_new_method_class_change(self):
        self.day.duels = self.game.duels
        state = InitialState(self.game, self.day)
        self.assertIsInstance(state, SearchOnlyState)

    async def test_end(self):
        await self.state.end()
        self.utility.get_town_channel.return_value.send.assert_awaited()
        self.assertIsInstance(self.state, SearchOnlyState)


class TestReporting(BaseStateTest):
    async def test_add_report(self):
        author = AsyncMock(discord.Member)
        subject = AsyncMock(discord.Member)
        await self.state.add_report(author, subject)
        reports = self.day.reports
        self.assertIn(subject, reports)
        self.assertIn(author, reports[subject])
        await self.state.add_report(author, subject)
        self.assertEqual(reports[subject], [author])

    async def test_remove_report(self):
        author = AsyncMock(discord.Member)
        subject = AsyncMock(discord.Member)
        await self.state.remove_report(author, subject)  # check if not raising
        await self.state.add_report(author, subject)
        await self.state.remove_report(author, subject)
        reports = self.day.reports
        self.assertIn(subject, reports)
        self.assertNotIn(author, reports[subject])

    async def test_pen_reports(self):
        member1, member2, member3 = self.mock_members(3)
        await self.state.add_report(member1, member2)
        await self.state.add_report(member2, member2)
        await self.state.add_report(member3, member1)
        await self.state.add_report(member1, member3)
        await self.state.remove_report(member1, member3)  # test removing empty keys in pen_reports method
        channel = AsyncMock()
        await self.state.pen_reports(channel)
        msg = channel.send.call_args[0][0]
        self.assertEqual(msg, '__Zgłoszenia (2):__\n**M2** *przez* M1, M2\n**M1** *przez* M3\n\nLiczba przeszukań: 2')

    async def test_voting(self):
        member1, member2, member3 = self.mock_members(3)
        await self.state.add_report(member1, member2)
        await self.state.add_report(member2, member2)
        await self.state.add_report(member3, member1)
        await self.state.add_report(member1, member3)  # being removed later
        await self.state.remove_report(member1, member3)  # test removing empty keys in voting method
        self.game.searches = 1
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.title[0], 'Przeszukania')
        self.assertEqual(self.state.options, [['1', 'M2'], ['2', 'M1']])
        self.assertEqual(self.state.required_votes, self.game.searches)
        await self.state.end()
        self.assertIsInstance(self.state, SearchingSummary)

    async def test_voting_with_draw(self):
        member1, member2, member3 = self.mock_members(3)
        self.utility.get_player_role().members = self.mock_members(5) + [member1, member2, member3]
        await self.state.add_report(member1, member2)
        await self.state.add_report(member2, member2)
        await self.state.add_report(member3, member1)
        await self.state.add_report(member1, member3)
        await self.state.remove_report(member1, member3)

        await self.state.voting()  # voting shouldn't be created
        self.assertIsInstance(self.state, SearchingSummary)

    async def test_voting_too_less_reports(self):
        self.utility.get_player_role().members = self.mock_members(5)
        await self.state.voting()
        self.assertIsInstance(self.state, SearchingSummaryWithRandom)


class TestChallenging(BaseStateTest):
    def mock_decline_role(self, present=True, alive=True):
        role = SPEC_ROLES['decline_duels']
        self.game.role_map = roles = dict()
        if present:
            roles[role] = mock = MagicMock()
            mock.alive = alive

    async def test_adding_challenge_1(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role(present=False)
        await self.state.add_challenge(member1, member2)
        self.assertNotIn((member1, member2), self.day.challenges)
        channel = self.utility.get_town_channel()
        role = SPEC_ROLES['decline_duels']
        channel.send.assert_any_await(f'**M1** wyzywa **M2** na pojedynek.\n{role} nie żyje, '
                                      f'więc pojedynek jest automatycznie przyjęty')
        self.assertIsInstance(self.state, Duel)

    async def test_adding_challenge_2(self):
        member1, member2 = self.mock_members()
        member2.id = '123456'
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        self.assertIn((member1, member2), self.day.challenges)
        self.assertIsInstance(self.day.challenges[0], Challenge)
        channel = self.utility.get_town_channel()
        channel.send.assert_awaited_once_with('**M1** wyzywa **M2** na pojedynek.\n<@123456> '
                                              'czy chcesz przyjąć pojedynek? Użyj `&przyjmuję` lub `&odrzucam`')
        self.assertNotIsInstance(self.state, Duel)

    async def test_adding_challenge_3(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role(alive=False)
        await self.state.add_challenge(member1, member2)
        self.assertIsInstance(self.state, Duel)

    async def test_adding_challenge_4_self_challenge(self):
        member1 = AsyncMock()
        with self.assertRaises(SelfChallengeError):
            await self.state.add_challenge(member1, member1)

    async def test_adding_challenge_5_duplicating(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        with self.assertRaises(DuplicateChallenge):
            await self.state.add_challenge(member1, member2)
        with self.assertRaises(DuplicateChallenge):
            await self.state.add_challenge(member2, member1)

    async def test_adding_challenge_6_multiple(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        self.mock_decline_role(alive=False)
        await self.state.add_challenge(member1, member3)
        self.assertIn(Challenge(member1, member2), self.day.challenges)
        self.assertIn(AcceptedChallenge(member1, member3), self.day.challenges)
        channel = self.utility.get_town_channel()
        channel.send.assert_awaited_with('Ten pojedynek nie może się teraz rozpocząć\n__Aktualne wyzwania:__\n'
                                         '**M1** vs. **M2**\n**M1** vs. **M3** - *przyjęte*\n'
                                         '\nPozostało pojedynków: {}'.format(self.game.duels - self.day.duels))
        self.assertNotIsInstance(self.state, Duel)

    async def test_accepting_1(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.accept(member2)
        self.assertIsInstance(self.state, Duel)
        channel = self.utility.get_town_channel()
        channel.send.assert_any_await('**M2** przyjmuje pojedynek od **M1**')
        channel.send.assert_awaited_with(f'Rozpoczynamy pojedynek:\n<:legacy_gun:{GUN_ID}> **M1** vs.:shield: **M2**')

    async def test_accepting_2(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member1, member3)
        channel = self.utility.get_town_channel()
        channel.send.reset_mock()
        await self.state.accept(member3)
        self.assertNotIsInstance(self.state, Duel)
        self.assertEqual(channel.send.await_count, 2)  # acceptance info + pen_challenges
        self.assertIn(AcceptedChallenge(member1, member3), self.day.challenges)
        self.assertEqual(len(self.day.challenges), 2)

    async def test_accepting_3_not_challenged(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role()
        with self.assertRaises(ChallengeNotFound):
            await self.state.accept(member1)
        await self.state.add_challenge(member1, member2)
        with self.assertRaises(ChallengeNotFound):
            await self.state.accept(member1)  # prevent accepting by author

    async def test_accepting_4_already_accepted(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member1, member3)
        await self.state.accept(member3)
        with self.assertRaises(DuelAlreadyAccepted):
            await self.state.accept(member3)

    async def test_declining_1(self):
        member1, member2 = self.mock_members()
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.decline(member2)
        self.assertNotIsInstance(self.state, Duel)
        channel = self.utility.get_town_channel()
        channel.send.assert_any_await('**M2** odrzuca pojedynek od **M1**')
        self.assertNotIn((member1, member2), self.day.challenges)

    async def test_declining_2(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member1, member3)
        await self.state.accept(member3)
        channel = self.utility.get_town_channel()
        channel.send.reset_mock()
        await self.state.decline(member2)
        self.assertIsInstance(self.state, Duel)
        self.assertEqual(channel.send.await_count, 2)  # decline info + duel starting
        self.assertFalse(self.day.challenges)

    async def test_declining_3(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member2, member3)
        await self.state.add_challenge(member3, member1)
        await self.state.accept(member1)
        channel = self.utility.get_town_channel()
        channel.send.reset_mock()
        await self.state.decline(member2)
        self.assertNotIsInstance(self.state, Duel)
        self.assertEqual(channel.send.await_count, 1)  # only decline info
        self.assertEqual(len(self.day.challenges), 2)

    async def test_declining_4_not_challenged(self):
        member1 = AsyncMock()
        with self.assertRaises(ChallengeNotFound):
            await self.state.decline(member1)

    async def test_pen_challenges_1(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member2, member3)
        await self.state.add_challenge(member3, member1)
        channel = AsyncMock()
        await self.state.pen_challenges(channel)
        channel.send.assert_awaited_with('__Wyzwania:__\n**M1** vs. **M2**\n**M2** vs. **M3**\n**M3** vs. **M1**\n\n'
                                         'Pozostało pojedynków: 2')

    async def test_pen_challenges_2_no_challenges(self):
        channel = AsyncMock()
        await self.state.pen_challenges(channel)
        channel.send.assert_awaited_with('Nie ma wyzwań\n\nPozostało pojedynków: 2')
        channel.send.reset_mock()
        self.day.duels += 1
        await self.state.pen_challenges(channel)
        channel.send.assert_awaited_with('Nie ma wyzwań\n\nPozostało pojedynków: 1')
        channel.send.reset_mock()
        self.day.duels += 1
        await self.state.pen_challenges(channel)
        channel.send.assert_awaited_with('Nie ma wyzwań\n\nPozostało pojedynków: 0')

    async def test_pen_challenges_3_accepted(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member2, member3)
        await self.state.add_challenge(member3, member1)
        await self.state.accept(member1)
        channel = AsyncMock()
        await self.state.pen_challenges(channel)
        channel.send.assert_awaited_with('__Wyzwania:__\n**M1** vs. **M2**\n**M2** vs. **M3**\n'
                                         '**M3** vs. **M1** - *przyjęte*\n\nPozostało pojedynków: 2')

    async def test_start_duel_1(self):
        with self.assertRaises(IndexError):
            await self.state.start_duel()

    async def test_start_duel_2(self):
        member1, member2 = self.mock_members()
        self.game.duels = 0
        await self.state.start_duel(member1, member2)
        town = self.utility.get_town_channel.return_value
        town.send.assert_awaited_with('Limit pojedynków został wyczerpany')
        self.assertIsInstance(self.state, SearchOnlyState)

    async def test_start_duel_3(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member3, member2)
        await self.state.start_duel(member2, member3)
        self.assertIn((member1, member2), self.day.challenges)
        self.assertEqual(len(self.day.challenges), 1)
        self.assertIsInstance(self.state, Duel)

    async def test_start_duel_4(self):
        member1, member2, member3 = self.mock_members(3)
        self.mock_decline_role()
        await self.state.add_challenge(member1, member2)
        await self.state.add_challenge(member3, member2)
        await self.state.start_duel(member3, member2)  # reverse member order
        self.assertIn((member1, member2), self.day.challenges)
        self.assertEqual(len(self.day.challenges), 1)
        self.assertIsInstance(self.state, Duel)

    async def test_start_duel_5(self):
        member = self.mock_members(1)
        with self.assertRaises(AuthorIsSubjectChallengeError):
            await self.state.start_duel(member, member)


class TestSearchOnlyState(TestReporting):
    async def asyncSetUp(self) -> None:
        await self.state.end()

    async def test_lock(self):
        member1, member2 = self.mock_members()
        await self.state.lock()
        self.assertTrue(self.state.locked)
        with self.assertRaises(ReportingLocked):
            await self.state.add_report(member1, member2)
        await self.state.lock()
        self.assertFalse(self.state.locked)
        await self.state.add_report(member1, member2)


class TestUndoable(BaseStateTest):
    async def test_undo(self):
        await self.state.end()
        await self.state.undo()
        self.assertIsInstance(self.state, InitialState)


def duel_decorator(coro):

    @functools.wraps(coro)
    async def predicate(self):
        member1, member2 = self.mock_members()
        await self.state.start_duel(member1, member2)
        await coro(self, member1, member2)
    return predicate


def transform_methods(decorator):  # cannot use this in __new__, because of tests construction
    def predicate(cls):
        for name, meth in vars(cls).items():
            if callable(meth) and name.startswith('test'):
                setattr(cls, name, decorator(meth))
        return cls
    return predicate


@transform_methods(duel_decorator)
class TestDuel(BaseStateTest):
    async def test_fields(self, member1, member2):
        self.assertEqual(self.state.author, member1)
        self.assertEqual(self.state.subject, member2)

    async def test_cancel(self, *_):
        await self.state.cancel()
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Manitou anulował trwający pojedynek')
        self.assertIsInstance(self.state, InitialState)

    async def test_on_die_1(self, member1, _):
        member3 = self.mock_members(1)
        await self.state.on_die(member3)
        self.assertIsInstance(self.state, Duel)
        await self.state.on_die(member1)
        self.assertIsInstance(self.state, InitialState)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Pojedynek został anulowany z powodu śmierci jednego z uczestników.')

    async def test_on_die_2(self, _, member2):
        await self.state.on_die(member2)
        self.assertIsInstance(self.state, InitialState)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Pojedynek został anulowany z powodu śmierci jednego z uczestników.')

    async def test_set_message(self, *_):
        msg = AsyncMock(discord.Message)
        await self.state.set_msg_edit_callback(msg)
        msg.edit.assert_awaited_with(content='**Pojedynek:**\n**M1** vs. **M2**', embed=None)

    async def test_start_duel_1(self, *_):
        member1, member2 = self.mock_members()
        await self.state.start_duel(member1, member2)
        self.assertIn(AcceptedChallenge(member1, member2), self.day.challenges)

    async def test_start_duel_2(self, *_):
        member1, member2, member3 = self.mock_members(3)
        self.day.challenges = collections.deque([AcceptedChallenge(member1, member2), Challenge(member3, member2)])
        await self.state.start_duel(member2, member3)
        self.assertEqual(self.day.challenges,
                         collections.deque([AcceptedChallenge(member2, member3), AcceptedChallenge(member1, member2)]))

    async def test_start_duel_3(self, *_):
        member = self.mock_members(1)
        with self.assertRaises(AuthorIsSubjectChallengeError):
            await self.state.start_duel(member, member)

    async def test_voting(self, member1, member2):
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.title[0], 'Pojedynek')
        self.assertEqual(self.state.options, [['1', 'M1'], ['2', 'M2'], ['3', 'Wstrzymuję_Się']])
        self.assertEqual(self.state.required_votes, 1)
        self.assertEqual(self.state.metadata, {'author': member1, 'subject': member2})

    async def test_voting_cancel(self, member1, member2):
        await self.state.voting()
        await self.state.cancel()
        self.assertIsInstance(self.state, Duel)
        self.assertEqual(self.state.author, member1)
        self.assertEqual(self.state.subject, member2)


class TestDuelSummary(BaseStateTest):
    def mock_revoling(self, member1, member2, rev1=False, rev2=False):
        p1, p2 = MagicMock(), MagicMock()
        self.game.player_map.update({member1: p1, member2: p2})
        p1.role_class = r1 = MagicMock()
        p2.role_class = r2 = MagicMock()
        r1.can_use.return_value = rev1
        r2.can_use.return_value = rev2
        r1.die = AsyncMock()
        r2.die = AsyncMock()

    async def change_state(self, summary=None, rev1=False, rev2=False):
        member1, member2 = self.mock_members()
        if summary is None:
            summary = {member1.display_name: [], member2.display_name: [], 'Wstrzymuję_Się': []}
        self.mock_revoling(member1, member2, rev1, rev2)
        await self.day.push_state(DuelSummary, author=member1, subject=member2, summary=summary)
        return member1, member2

    async def test_undo(self):
        member1, member2 = await self.change_state()
        self.assertEqual(self.state.metadata, {'author': member1, 'subject': member2})
        await self.state.undo()
        self.assertIsInstance(self.state, Duel)
        self.assertEqual(self.state.author, member1)
        self.assertEqual(self.state.subject, member2)

    async def test_set_message(self):
        await self.change_state()
        msg = AsyncMock(discord.Message)
        await self.state.set_msg_edit_callback(msg)
        msg.edit.assert_awaited_with(content='**Pojedynek - podsumowanie**\n**M1** vs. **M2**', embed=None)

    async def test_on_die(self):
        member1, member2 = await self.change_state()
        await self.state.on_die(member1)
        self.assertIsInstance(self.state, InitialState)

    async def test_start_duel(self):
        await self.change_state()
        member1, member2 = self.mock_members()
        await self.state.start_duel(member1, member2)
        self.assertIn(AcceptedChallenge(member1, member2), self.day.challenges)

    async def test_init_1_first_rev(self):
        summary = {'M1': [], 'M2': range(10), 'Wstrzymuję_Się': []}
        member1, member2 = await self.change_state(summary=summary, rev1=True)
        self.assertEqual(self.state.winners, [member1])
        self.assertEqual(self.state.losers, [member2])

    async def test_init_2_second_rev(self):
        summary = {'M1': range(20), 'M2': range(10), 'Wstrzymuję_Się': []}
        member1, member2 = await self.change_state(summary=summary, rev2=True)
        self.assertEqual(self.state.winners, [member2])
        self.assertEqual(self.state.losers, [member1])

    async def test_init_3_no_rev(self):
        summary = {'M1': [], 'M2': range(10), 'Wstrzymuję_Się': []}
        member1, member2 = await self.change_state(summary=summary)
        self.assertEqual(self.state.winners, [member2])
        self.assertEqual(self.state.losers, [member1])

    async def test_init_4_no_rev(self):
        summary = {'M1': range(20), 'M2': range(10), 'Wstrzymuję_Się': []}
        member1, member2 = await self.change_state(summary=summary)
        self.assertEqual(self.state.winners, [member1])
        self.assertEqual(self.state.losers, [member2])

    async def test_init_5_no_rev(self):
        summary = {'M1': range(20), 'M2': range(10), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary)
        self.assertEqual(self.state.winners, [member1])
        self.assertEqual(self.state.losers, [member2])

    async def test_init_6_two_revs(self):
        summary = {'M1': range(5), 'M2': range(10), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary, rev1=True, rev2=True)
        self.assertEqual(self.state.winners, [member2])
        self.assertEqual(self.state.losers, [member1])

    async def test_init_7_nonzero_draw(self):
        summary = {'M1': range(10), 'M2': range(10), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary)
        self.assertEqual(self.state.winners, [])
        self.assertEqual(self.state.losers, [member1, member2])

    async def test_init_8_nonzero_draw_revs(self):
        summary = {'M1': range(10), 'M2': range(10), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary, rev1=True, rev2=True)
        self.assertEqual(self.state.winners, [])
        self.assertEqual(self.state.losers, [member1, member2])

    async def test_init_9_zero_draw(self):
        summary = {'M1': list(), 'M2': list(), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary)
        self.assertEqual(self.state.winners, [member1, member2])
        self.assertEqual(self.state.losers, [])

    async def test_init_10_zero_draw_revs(self):
        summary = {'M1': list(), 'M2': list(), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary=summary, rev1=True, rev2=True)
        self.assertEqual(self.state.winners, [member1, member2])
        self.assertEqual(self.state.losers, [])

    async def test_async_init_1(self):
        summary = {'M1': range(10), 'M2': list(), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary)
        self.utility.add_roles.assert_any_await([member1], self.utility.get_duel_winner_role())
        self.utility.add_roles.assert_any_await([member2], self.utility.get_duel_loser_role())
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Pojedynek ma wygrać **M1**. Zginąć ma **M2**')

    async def test_async_init_2_nonzero_draw(self):
        summary = {'M1': range(10), 'M2': range(10), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary)
        self.utility.add_roles.assert_any_await([], self.utility.get_duel_winner_role())
        self.utility.add_roles.assert_any_await([member1, member2], self.utility.get_duel_loser_role())
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('W wyniku pojedynku mają zginąć obaj pojedynkujący się')

    async def test_async_init_3_zero_draw(self):
        summary = {'M1': list(), 'M2': list(), 'Wstrzymuję_Się': range(30)}
        member1, member2 = await self.change_state(summary)
        self.utility.add_roles.assert_any_await([member1, member2], self.utility.get_duel_winner_role())
        self.utility.add_roles.assert_any_await([], self.utility.get_duel_loser_role())
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('W wyniku pojedynku nikt nie ginie *(na razie)*')

    async def test_cleanup(self):
        member1, member2 = await self.change_state()
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.members = [member1, member2]
        loser_role.members = []
        await self.state.cleanup()
        self.utility.remove_roles.assert_awaited_with([member1, member2], winner_role, loser_role)

    async def test_change_winner(self):
        member1, member2 = await self.change_state()
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        await self.state.change_winner(member1)
        member1.add_roles.assert_awaited_with(winner_role)
        member1.remove_roles.assert_awaited_with(loser_role)
        member2.add_roles.assert_awaited_with(loser_role)
        member2.remove_roles.assert_awaited_with(winner_role)

    async def test_end_1(self):
        member1, member2 = await self.change_state()
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.members = [member1]
        loser_role.members = [member2]
        town = self.utility.get_town_channel()
        await self.state.end()
        town.send.assert_awaited_with('Pojedynek wygrywa **M1**')
        self.assertEqual(self.day.duels, 1)
        self.game.player_map[member2].role_class.die.assert_awaited_with('duel')
        self.game.player_map[member1].role_class.die.assert_not_awaited()
        self.assertIsInstance(self.state, InitialState)

    async def test_end_2_duel_limit(self):
        await self.change_state()
        self.day.duels = 1
        await self.state.end()
        self.assertIsInstance(self.state, SearchOnlyState)

    async def test_end_3_two_winners(self):
        summary = {'M1': range(10), 'M2': list(), 'Wstrzymuję_Się': range(15)}
        member1, member2 = await self.change_state(summary)
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.members = [member2, member1]
        loser_role.members = []
        town = self.utility.get_town_channel()
        await self.state.end()
        town.send.assert_awaited_with('W wyniku pojedynku nikt nie ginie')
        self.game.player_map[member2].role_class.die.assert_not_awaited()
        self.game.player_map[member1].role_class.die.assert_not_awaited()

    async def test_end_4_no_winners(self):
        member1, member2 = await self.change_state()
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.members = []
        loser_role.members = [member2, member1]
        town = self.utility.get_town_channel()
        await self.state.end()
        awaits = town.send.await_args_list
        self.assertEqual(len(awaits), 1)
        town.send.assert_awaited_with('W wyniku pojedynku nikt nie ginie *(na razie)*')
        self.game.player_map[member2].role_class.die.assert_awaited_with('duel')
        self.game.player_map[member1].role_class.die.assert_awaited_with('duel')

    async def test_end_5_starting_duel(self):
        await self.change_state()
        member1, member2 = self.mock_members()
        await self.state.start_duel(member1, member2)
        await self.state.end()
        self.assertIsInstance(self.state, Duel)
        self.assertEqual(self.state.author, member1)
        self.assertEqual(self.state.subject, member2)

    async def test_end_6_not_starting_duel(self):
        await self.change_state()
        member1, member2 = self.mock_members()
        challenges = self.day.challenges
        challenges.append(Challenge(member1, member2))
        await self.state.end()
        self.assertIsInstance(self.state, InitialState)

    async def test_end_7_double_role(self):
        member1, member2 = await self.change_state()
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.members = [member2]
        loser_role.members = [member2, member1]
        with self.assertRaises(DuelDoublePerson) as cm:
            await self.state.end()
        self.assertEqual(cm.exception.msg, 'M2 jest zwycięzcą i przegranym jednocześnie')

    async def test_end_8_no_participating(self):
        await self.change_state()
        member = self.mock_members(1)
        winner_role = self.utility.get_duel_winner_role()
        loser_role = self.utility.get_duel_loser_role()
        winner_role.mention = '<WYGRANY>'
        winner_role.members = [member]
        loser_role.members = []
        with self.assertRaises(NotDuelParticipant) as cm:
            await self.state.end()
        self.assertEqual(cm.exception.msg, 'M1 ma rolę <WYGRANY>, a nie pojedynkuje się')

    @duel_decorator
    async def test_voting(self, member1, member2):
        await self.state.voting()
        self.mock_revoling(member1, member2)
        await self.state.end()
        self.assertIsInstance(self.state, DuelSummary)
        self.assertEqual(self.state.author, member1)
        self.assertEqual(self.state.subject, member2)
        self.assertEqual(self.state.winners, [member1, member2])
        self.assertEqual(self.state.losers, [])


class TestSearchingSummary(BaseStateTest):
    async def change_state(self, summary=None, searches=0, other=True, reports=0, alive=0, dead=None):
        if summary is None:
            summary = list()
        m = len(summary)
        n = m + searches + reports + alive
        members = self.mock_members(n)
        votes = summary
        summary = {}
        for mem, v in zip(members[:m], votes):
            summary[mem] = range(v)
        other = members[:m] if other else None
        self.day.reports = dict(zip(members[:m+reports+searches], range(1, n-alive+1)))
        self.game.player_map = dict(zip(members, range(n)))
        searches = members[m: m+searches]
        if dead is not None:
            players = [mem for i, mem in enumerate(members) if i not in dead]
        else:
            players = members
        self.utility.get_player_role().members = players
        await self.day.push_state(SearchingSummary, summary=summary, searches=searches, other=other)
        return members

    async def test_init_1(self):
        members = await self.change_state([1, 3, 1, 6, 2, 0], other=False)
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertSetEqual(set(self.state.searches), {members[1], members[3]})
        self.assertEqual(set(self.state.other), {members[0], members[2], members[4], members[5]})

    async def test_init_2(self):
        members = await self.change_state([1, 3, 1, 6, 2, 3], other=False)
        self.assertIsInstance(self.state, SearchingSummaryWithRevote)
        self.assertEqual(self.state.searches, [members[3]])
        self.assertSetEqual(set(self.state.other), {members[1], members[5]})

    async def test_init_3(self):
        members = await self.change_state(reports=1, alive=2)
        self.assertIsInstance(self.state, SearchingSummaryWithRandom)
        self.assertEqual(self.state.searches, [members[0]])
        self.assertSetEqual(set(self.state.other), {members[1], members[2]})

    async def test_init_4(self):
        members = await self.change_state([1, 2, 3], 1, reports=1, alive=1)
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertSetEqual(set(self.state.searches), {members[3], members[2]})
        self.assertSetEqual(set(self.state.other), {members[0], members[1]})

    async def test_init_5(self):
        members = await self.change_state(summary=[1, 2], searches=1, reports=3, dead=[0, 1, 4])
        self.assertIsInstance(self.state, SearchingSummaryWithRandom)
        self.assertEqual(self.state.searches, [members[2]])
        self.assertSetEqual(set(self.state.other), {members[5], members[3]})

    async def test_init_6(self):
        members = await self.change_state(summary=[7, 5], searches=1, dead=[2], alive=10)
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertSetEqual(set(self.state.searches), {members[2], members[0]})
        self.assertSetEqual(set(self.state.other), {members[1]})

    async def test_init_7(self):
        members = await self.change_state(summary=[4, 8], searches=1, reports=3, dead=[2], alive=10)
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertSetEqual(set(self.state.searches), {members[2], members[1]})
        self.assertSetEqual(set(self.state.other), {members[0]})

    async def test_init_8(self):
        members = await self.change_state(summary=[1, 2], searches=1, reports=1, dead=[0, 1, 3], alive=2)
        self.assertIsInstance(self.state, SearchingSummaryWithRandom)
        self.assertEqual(self.state.searches, [members[2]])
        self.assertSetEqual(set(self.state.other), {members[5], members[4]})

    async def test_init_9(self):
        members = await self.change_state(reports=2, alive=3, other=False)
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertSetEqual(set(self.state.searches), {members[0], members[1]})

    async def test_voting_1(self):
        members = await self.change_state(summary=[1, 5, 4, 3, 4], other=False, alive=15)
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.options, [['1', 'M3'], ['2', 'M5']])
        await self.state.cancel()
        self.assertIsInstance(self.state, SearchingSummaryWithRevote)
        self.assertEqual(self.state.searches, [members[1]])
        self.assertSetEqual(set(self.state.other), {members[2], members[4]})

    async def test_voting_2(self):
        members = await self.change_state(summary=[1, 5, 4, 3, 4], other=False, alive=15)
        await self.state.voting()
        await self.state.end()
        self.assertIsInstance(self.state, SearchingSummaryWithRevote)
        self.assertEqual(self.state.searches, [members[1]])
        self.assertSetEqual(set(self.state.other), {members[2], members[4]})

    async def test_async_init_1(self):
        await self.change_state(summary=[1, 2, 3, 4, 5], other=False, alive=3)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Przeszukani zostaną:\n**M5**\n**M4**\n')

    async def test_async_init_2(self):
        await self.change_state(summary=[3, 6, 3, 1], other=False, alive=2)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with(
            'Przeszukani zostaną:\n**M2**\n\nPotrzebne jest dodatkowe głosowanie dla:\n**M1**\n**M3**\n')

    async def test_async_init_3(self):
        await self.change_state(summary=[3, 2, 3, 3], other=False, alive=4)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Na razie nikt nie ma zostać przeszukany\n\n'
                                      'Potrzebne jest dodatkowe głosowanie dla:\n**M1**\n**M3**\n**M4**\n')

    async def test_async_init_4(self):
        await self.change_state(reports=1, alive=3)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Przeszukani zostaną:\n**M1**\n')

    async def test_async_init_5(self):
        await self.change_state(alive=3)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Na razie nikt nie ma zostać przeszukany\n')

    async def test_end_1(self):
        await self.change_state(summary=[1, 3, 5, 4])
        self.utility.get_searched_role().members = searches = self.state.searches
        await self.state.end()
        town = self.utility.get_town_channel()
        town.send.assert_any_await('Przeszukani zostają:\n**M3**\n**M4**\n')
        self.assertIsInstance(self.state, HangIfable)
        self.assertEqual(self.state.searched, searches)

    async def test_end_2(self):
        await self.change_state(summary=[1, 3, 5, 4, 5, 5])
        self.utility.get_searched_role().members = self.state.searches
        await self.state.end()
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Nikt nie zostaje przeszukany')

    async def test_end_3(self):
        members = await self.change_state(summary=[1, 3, 4, 5])
        self.utility.get_searched_role().members = members
        with self.assertRaises(MoreSearchedThanSearches):
            await self.state.end()

    async def test_end_4(self):
        await self.change_state(summary=[1, 3, 4, 5])
        self.utility.get_searched_role().members = self.mock_members(2)
        with self.assertRaises(IllegalSearch) as cm:
            await self.state.end()
        self.assertEqual(cm.exception.msg, 'M1 ma zostać przeszukany(-a) a nie gra')

    async def test_undo(self):
        await self.change_state(reports=2, alive=3)
        await self.state.undo()
        self.assertIsInstance(self.state, SearchOnlyState)

    async def test_random_1(self):
        members = await self.change_state(reports=1, alive=4, other=False)
        await self.state.random()
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertEqual(len(self.state.searches), 2)
        self.assertIn(members[0], self.state.searches)
        self.assertIn(self.state.searches[1], members[1:])

    async def test_random_2(self):
        members = await self.change_state(summary=[3, 5, 7, 0, 5], alive=3, other=False)
        await self.state.random()
        self.assertIsInstance(self.state, SearchingSummary)
        self.assertEqual(len(self.state.searches), 2)
        self.assertIn(members[2], self.state.searches)
        self.assertIn(self.state.searches[1], [members[1], members[4]])


class TestHangIfable(BaseStateTest):
    async def change_state(self):
        members = self.mock_members()
        await self.day.push_state(HangIfable, searched=members)
        return members

    async def test_voting_1(self):
        members = await self.change_state()
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.title[0], 'Czy wieszamy?')
        self.assertEqual(self.state.options, [['t', 'Tak'], ['n', 'Nie']])
        await self.state.cancel()
        self.assertIsInstance(self.state, HangIfable)
        self.assertEqual(self.state.searched, members)

    async def test_voting_2(self):
        members = await self.change_state()
        await self.state.voting()
        await self.state.end()
        self.assertIsInstance(self.state, HangIfSummary)
        self.assertEqual(self.state.searched, members)


class TestHangIfSummary(BaseStateTest):
    async def change_state(self, summary=None):
        members = self.mock_members()
        if summary:
            await self.day.push_state(HangIfSummary, summary=dict(zip(['Tak', 'Nie'], (range(i) for i in summary))),
                                      searched=members)
        else:
            await self.day.push_state(HangIfSummary, searched=members)
        return members

    async def test_init_1(self):
        members = await self.change_state([10, 9])
        self.assertEqual(self.state.searched, members)
        self.assertTrue(self.state.hang)

    async def test_init_2(self):
        await self.change_state([9, 9])
        self.assertFalse(self.state.hang)

    async def test_init_3(self):
        await self.change_state([0, 5])
        self.assertFalse(self.state.hang)
        self.assertIsNotNone(self.state.hang)

    async def test_init_4(self):
        await self.change_state()
        self.assertIsNone(self.state.hang)

    async def test_set_message_1(self):
        await self.change_state()
        msg = AsyncMock()
        await self.state.set_msg_edit_callback(msg)
        msg.edit.assert_awaited_with(content='**Przed wieszaniem** - wieszamy', embed=None)

    async def test_set_message_2(self):
        await self.change_state([1, 5])
        msg = AsyncMock()
        await self.state.set_msg_edit_callback(msg)
        msg.edit.assert_awaited_with(content='**Przed wieszaniem** - nie wieszamy', embed=None)

    async def test_set_message_3(self):
        await self.change_state([10, 1])
        msg = AsyncMock()
        await self.state.set_msg_edit_callback(msg)
        msg.edit.assert_awaited_with(content='**Przed wieszaniem** - wieszamy', embed=None)

    async def test_async_init_1(self):
        await self.change_state([1, 2])
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Miasto idzie spać.')

    async def test_async_init_2(self):
        await self.change_state([3, 2])
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Decyzją miasta wieszamy.')

    async def test_async_init_3(self):
        await self.change_state()
        town = self.utility.get_town_channel()
        town.send.assert_not_awaited()

    async def test_undo(self):
        members = await self.change_state([12, 5])
        await self.state.undo()
        self.assertIsInstance(self.state, HangIfable)
        self.assertEqual(self.state.searched, members)

    async def test_voting_1(self):
        members = await self.change_state([12, 5])
        self.utility.get_player_role().members = members
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.title[0], 'Wieszanie')
        self.assertEqual(self.state.options, [['1', 'M1'], ['2', 'M2']])
        await self.state.end()
        self.assertIsInstance(self.state, HangSummary)  # no matter if properly classified with draw

    async def test_voting_2(self):
        members = await self.change_state([12, 5])
        self.utility.get_player_role().members = members[:1]
        await self.state.voting()
        self.assertIsInstance(self.state, HangingSummary)


class TestHangingSummary(BaseStateTest):
    async def change_state(self, summary=None, searched=0, other=True, dead=None):
        if summary is None:
            summary = list()
        m = len(summary)
        n = m + searched
        members = self.mock_members(n)
        votes = summary
        summary = {}
        for mem, v in zip(members[:m], votes):
            summary[mem] = range(v)
        other = members[:m] if other else None
        searched = members
        self.game.player_map = dict(zip(members, [AsyncMock() for _ in range(n)]))
        if dead is not None:
            players = [mem for i, mem in enumerate(members) if i not in dead]
        else:
            players = members
        self.utility.get_player_role().members = players
        await self.day.push_state(HangingSummary, summary=summary, searched=searched, other=other)
        return members

    async def test_init_1(self):
        members = await self.change_state([1, 3, 5], other=False)
        self.assertIsInstance(self.state, HangingSummary)
        self.assertEqual(self.state.hanged, members[2])

    async def test_init_2(self):
        members = await self.change_state([4, 4, 3], other=False)
        self.assertIsInstance(self.state, HangingSummaryWithRevote)
        self.assertIsNone(self.state.hanged)
        self.assertEqual(self.state.other, [members[0], members[1]])

    async def test_init_3(self):
        members = await self.change_state([3, 4], searched=1)
        self.assertIsInstance(self.state, HangingSummary)
        self.assertEqual(self.state.hanged, members[1])

    async def test_init_4(self):
        members = await self.change_state([2, 4], dead=[1])
        self.assertIsInstance(self.state, HangingSummary)
        self.assertEqual(self.state.hanged, members[0])

    async def test_init_5(self):
        members = await self.change_state([3, 5, 3], dead=[1])
        self.assertIsInstance(self.state, HangingSummaryWithRevote)
        self.assertEqual(self.state.other, [members[0], members[2]])

    async def test_init_6(self):
        members = await self.change_state(searched=2, dead=[0])
        self.assertIsInstance(self.state, HangingSummary)
        self.assertEqual(self.state.hanged, members[1])

    async def test_init_7(self):
        await self.change_state([2, 3], other=False, dead=[0, 1])
        self.assertIsInstance(self.state, HangingSummary)
        self.assertIsNone(self.state.hanged)

    async def test_async_init_1(self):
        await self.change_state([2, 3], other=False, dead=[0, 1])
        town = self.utility.get_town_channel()
        town.send.assert_not_awaited()

    async def test_async_init_2(self):
        members = await self.change_state([2, 3], other=False)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Powieszony(-a) ma zostać **M2**')
        members[1].add_roles.assert_awaited()

    async def test_async_init_3(self):
        await self.change_state([3, 3], other=False)
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Potrzebne jest głosowanie uzupełniające dla:\n**M1**\n**M2**\n')

    async def test_undo(self):
        members = await self.change_state([1, 2])
        await self.state.undo()
        self.assertIsInstance(self.state, HangIfSummary)
        self.assertEqual(self.state.searched, members)
        self.assertIsNone(self.state.hang)

    async def test_end_1(self):
        members = await self.change_state([3, 5])
        self.utility.get_hanged_role().members = [members[1]]
        await self.state.end()
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Powieszony(-a) zostaje **M2**')
        self.assertIsInstance(self.state, Evening)
        self.game.player_map[members[1]].role_class.die.assert_awaited_with('hang')

    async def test_end_2(self):
        await self.change_state([2, 5])
        self.utility.get_hanged_role().members = []
        await self.state.end()
        town = self.utility.get_town_channel()
        town.send.assert_awaited_with('Nikt nie zostaje powieszony')

    async def test_end_3(self):
        members = await self.change_state([2, 5])
        self.utility.get_hanged_role().members = members
        with self.assertRaises(TooMuchHang):
            await self.state.end()

    async def test_end_4(self):
        await self.change_state([2, 5])
        self.utility.get_hanged_role().members = [self.mock_members(1)]
        with self.assertRaises(IllegalHang) as cm:
            await self.state.end()
        self.assertEqual(cm.exception.msg, 'M1 ma zostać powieszony(-a) a nie gra lub nie żyje')

    async def test_random(self):
        members = await self.change_state([5, 5, 5], other=False)
        await self.state.random()
        self.assertIsInstance(self.state, HangingSummary)
        self.assertIn(self.state.hanged, members)

    async def test_voting_1(self):
        members = await self.change_state([5, 5, 5], other=False)
        await self.state.voting()
        self.assertIsInstance(self.state, Voting)
        self.assertEqual(self.state.title[0], 'Wieszanie - uzupełniające')
        self.assertEqual(self.state.options, [['1', 'M1'], ['2', 'M2'], ['3', 'M3']])
        await self.state.cancel()
        self.assertIsInstance(self.state, HangingSummaryWithRevote)
        self.assertSetEqual(set(self.state.other), set(members))

    async def test_voting_2(self):
        members = await self.change_state([5, 5, 5], other=False)
        await self.state.voting()
        await self.state.end()
        self.assertIsInstance(self.state, HangingSummaryWithRevote)
        self.assertSetEqual(set(self.state.other), set(members))


if __name__ == '__main__':
    unittest.main()
