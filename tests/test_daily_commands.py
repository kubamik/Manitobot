import unittest
from unittest.mock import AsyncMock

from discord.ext import commands

from bases import BaseStateTest
from manitobot import utility, my_checks
from manitobot.basic_models import ManiBot
from manitobot.daily_commands import DailyCommands
from manitobot.day_states import Evening, SearchingSummaryWithRandom


class TestCommands(BaseStateTest):
    """Test if every command can run without errors
    """

    def setUp(self) -> None:
        bot = ManiBot(command_prefix='&')
        self.bot = bot
        self.cog = DailyCommands(bot)
        bot.add_cog(self.cog)
        super().setUp()
        self.game.day = self.day
        bot.game = self.game
        self.patch_modules_functions(my_checks, utility)

    async def test_undo_1(self):
        await self.state.end()
        ctx = AsyncMock()
        await self.cog.undo.invoke(ctx)

    async def test_undo_2(self):
        ctx = AsyncMock()
        with self.assertRaises(commands.CheckFailure) as cm:
            await self.cog.undo.invoke(ctx)
        self.assertIs(type(cm.exception), commands.CheckFailure)

    async def test_cancel_1(self):
        await self.state.start_duel(*self.mock_members())
        ctx = AsyncMock()
        await self.cog.cancel.invoke(ctx)

    async def test_cancel_2(self):
        ctx = AsyncMock()
        with self.assertRaises(commands.CheckFailure) as cm:
            await self.cog.cancel.invoke(ctx)
        self.assertIs(type(cm.exception), commands.CheckFailure)

    async def test_voting_1(self):
        ctx = AsyncMock()
        await self.cog.voting.invoke(ctx)

    async def test_voting_2(self):
        await self.day.push_state(Evening)
        ctx = AsyncMock()
        with self.assertRaises(commands.CheckFailure) as cm:
            await self.cog.voting.invoke(ctx)
        self.assertIs(type(cm.exception), commands.CheckFailure)

    async def test_random_1(self):
        await self.day.push_state(SearchingSummaryWithRandom)
        ctx = AsyncMock()
        await self.cog.random.invoke(ctx)

    async def test_random_2(self):
        ctx = AsyncMock()
        with self.assertRaises(commands.CheckFailure) as cm:
            await self.cog.random.invoke(ctx)
        self.assertIs(type(cm.exception), commands.CheckFailure)

    async def test_end_1(self):
        ctx = AsyncMock()
        await self.cog.end.invoke(ctx)

    async def test_end_2(self):
        await self.state.end()
        ctx = AsyncMock()
        with self.assertRaises(commands.CheckFailure) as cm:
            await self.cog.end.invoke(ctx)
        self.assertIs(type(cm.exception), commands.CheckFailure)


if __name__ == '__main__':
    unittest.main()
