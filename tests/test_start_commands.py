import inspect
import unittest
from unittest.mock import AsyncMock, patch

import manitobot.basic_models
from manitobot import start_commands, utility
from manitobot.errors import GameStartedException
from bases import BaseTestCase


class StartCommands(BaseTestCase):
    utility: AsyncMock

    def setUp(self) -> None:
        bot = manitobot.basic_models.ManiBot(command_prefix='.')
        self.sc = start_commands.Starting(bot)
        bot.add_cog(self.sc)
        self.patch_modules_functions(start_commands, utility)


@patch('manitobot.my_checks.if_game', autospec=True)
class GramTest(StartCommands):
    async def test_gram_before_game(self, if_game):
        if_game.return_value = False
        ctx = AsyncMock()
        await self.sc.register.invoke(ctx)
        self.utility.clear_nickname.assert_called_once_with(ctx.author)

    async def test_gram_during_game(self, if_game):
        if_game.return_value = True
        ctx = AsyncMock()
        with self.assertRaises(GameStartedException):
            await self.sc.register.invoke(ctx)
        self.utility.clear_nickname.assert_not_called()

    async def test_niegram_before_game(self, if_game):
        if_game.return_value = False
        ctx = AsyncMock()
        await self.sc.deregister.invoke(ctx)
        ctx.author.remove_roles.assert_called()

    async def test_niegram_during_game(self, if_game):
        if_game.return_value = True
        ctx = AsyncMock()
        with self.assertRaises(GameStartedException):
            await self.sc.deregister.invoke(ctx)
        ctx.author.remove_roles.assert_not_called()


if __name__ == '__main__':
    unittest.main()
