import discord

from manitobot.utility import get_newcomer_role


class Player:

    def __init__(self, member, role):
        self.member = member
        self.role = role
        self.active = False
        self.sleeped = False
        self.protected = False
        self.killing_protected = False
        self.role_class = None
        self.follower = None

    @property
    def is_newcomer(self):
        return self.member in get_newcomer_role().members

    async def new_day(self):
        self.sleeped = False
        self.protected = False
        self.killing_protected = False

        if self.role_class.alive and self.member.voice and self.member.voice.mute:
            try:
                await self.member.edit(mute=False)
            except discord.errors.Forbidden:
                pass

    async def new_night(self):
        nickname = self.member.display_name
        if '#' in nickname:
            try:
                await self.member.edit(nick=nickname.replace('#', ''))
            except discord.errors.Forbidden:
                pass
        if self.member.voice and not self.member.voice.mute:
            try:
                await self.member.edit(mute=True)
            except discord.errors.Forbidden:
                pass

    def sleep(self):
        self.sleeped = True

    def unsleep(self):
        self.sleeped = False
