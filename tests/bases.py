import inspect
import unittest
from unittest.mock import patch, AsyncMock


class BaseCommandTestCase(unittest.IsolatedAsyncioTestCase):
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
            if mod in members_mod:
                as_name = members_names[members_mod.index(mod)]
                setattr(self, name, self.create_patch(f'{curr_module.__name__}.{as_name}', autospec=True))
            else:
                setattr(self, name, AsyncMock())
        for attr in members:
            mod = inspect.getmodule(attr[1])
            if mod in modules:
                name = mod.__name__.rpartition('.')[-1]
                setattr(getattr(self, name), attr[0],
                        self.create_patch(f'{curr_module.__name__}.{attr[0]}', autospec=True))
