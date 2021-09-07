import inspect
import typing
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

import discord

from manitobot import base_day_states, utility, day_states
from manitobot.daynight import Day
from manitobot.game import Game


class BaseTestCase(unittest.IsolatedAsyncioTestCase):
    def create_patch(self, *args, **kwargs):
        patcher = patch(*args, **kwargs)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def patch_modules_functions(self, curr_module, *modules):
        members = inspect.getmembers(curr_module)
        members_mod = [attr[1] for attr in members]
        members_names = [attr[0] for attr in members]
        for mod in modules:
            name = mod.__name__.rpartition('.')[-1]
            if mod in members_mod and not hasattr(self, name):
                as_name = members_names[members_mod.index(mod)]
                setattr(self, name, self.create_patch(f'{curr_module.__name__}.{as_name}', autospec=True))
            elif mod in members_mod and hasattr(self, name):  # if patching module in more than one current module
                as_name = members_names[members_mod.index(mod)]
                self.create_patch(f'{curr_module.__name__}.{as_name}', new=getattr(self, name))
            elif not hasattr(self, name):
                setattr(self, name, MagicMock(spec=mod))
        for attr in members:
            mod = inspect.getmodule(attr[1])
            if mod in modules:
                name = mod.__name__.rpartition('.')[-1]
                module = getattr(self, name)
                if hasattr(module, attr[0]):
                    mock = self.create_patch(f'{curr_module.__name__}.{attr[0]}', new=getattr(module, attr[0]))
                else:
                    mock = self.create_patch(f'{curr_module.__name__}.{attr[0]}', autospec=attr[1])
                    setattr(module, attr[0], mock)
                hints = typing.get_type_hints(attr[1])
                if 'return' in hints:  # ensure that objects returned will have proper sync and async methods
                    return_type = hints['return']
                    mock.return_value = MagicMock(spec=return_type)


class BaseStateTest(BaseTestCase):
    utility: AsyncMock

    def setUp(self) -> None:
        self.patch_modules_functions(base_day_states, utility)
        self.patch_modules_functions(day_states, utility)
        self.game = game = Game()
        game.panel = AsyncMock()
        self.day = Day(game, AsyncMock())

    @property
    def state(self):
        return self.day.state

    @staticmethod
    def mock_members(number=2):
        members = list()
        for i in range(number):
            members.append(AsyncMock(discord.Member))
            members[-1].display_name = f'M{i + 1}'
        if number != 1:
            return members
        else:
            return members[0]
