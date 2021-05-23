import unittest
from unittest.mock import patch, AsyncMock

from discord.ext.commands import Context, MissingRole

import manitobot.basic_models
import manitobot.management_commands


class ManagmentCommands(unittest.IsolatedAsyncioTestCase):
    def create_patch(self, *args, **kwargs):
        patcher = patch(*args, **kwargs)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def setUp(self) -> None:
        self.ctx = Context(prefix="&", message=AsyncMock(), bot=AsyncMock())
        self.converter = self.create_patch('manitobot.management_commands.MyMemberConverter', autospec=True)
        self.get_admin_role = self.create_patch('manitobot.management_commands.get_admin_role')
        self.admin_members = AsyncMock()
        self.admin_members.members = []
        self.get_admin_role.return_value = self.admin_members
        self.is_owner = self.create_patch('manitobot.basic_models.ManiBot.is_owner')
        self.is_owner.return_value = False
        bot = manitobot.basic_models.ManiBot(command_prefix='.')
        self.mg = manitobot.management_commands.Management(bot)
        bot.add_cog(self.mg)


class GramTest(ManagmentCommands):
    async def test_adminuj(self):
        self.converter.convert.return_value = osoba = AsyncMock()
        self.admin_members.members = [self.ctx.author]
        #FIXME to na dole z jakiegos powodu nie uruchmia checku na admina
        await self.ctx.invoke(self.mg.adminate, osoba=osoba)
        osoba.add_roles.assert_called()

    async def test_adminuj_by_not_admin(self):
        self.converter.convert.return_value = osoba = AsyncMock()
        with self.assertRaises(MissingRole):
            await self.mg.adminate.invoke(self.ctx)
        osoba.add_roles.assert_not_called()

if __name__ == '__main__':
    unittest.main()
