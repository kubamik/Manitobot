from contextlib import suppress
from typing import TYPE_CHECKING, Optional

import discord

from manitobot.bot_basics import bot
from manitobot.utility import get_newcomer_role

if TYPE_CHECKING:
    from .role import Role

class Player:

    def __init__(self, member, role):
        self.member = member
        self.role = role
        self.active = False
        self.sleeped = False
        self.protected = False
        self.killing_protected = False
        self.role_class: Optional[Role] = None
        self.follower = None

    @property
    def is_newcomer(self):
        return self.member in get_newcomer_role().members

    def new_day(self):
        self.sleeped = False
        self.protected = False
        self.killing_protected = False

    async def new_night(self):
        nickname = self.member.display_name
        if '#' in nickname:
            with suppress(discord.Forbidden):
                await self.member.edit(nick=nickname.replace('#', ''))


    def sleep(self):
        self.sleeped = True

    def unsleep(self):
        self.sleeped = False
