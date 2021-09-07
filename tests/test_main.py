import unittest
import main
from unittest.mock import AsyncMock


class BeSorry(unittest.IsolatedAsyncioTestCase):
    async def test_be_sorry(self):
        ctx = AsyncMock()
        await main.be_sory(ctx)
        ctx.send.assert_called_once_with("Przepraszam")


class Lose(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        pass

    async def test_lose(self):
        pass


if __name__ == '__main__':
    unittest.main()


