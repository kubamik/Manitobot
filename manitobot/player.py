import discord


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

    async def new_day(self):
        self.sleeped = False
        self.protected = False
        self.killing_protected = False

    async def new_night(self):
        nickname = self.member.display_name
        if '#' in nickname:
            try:
                await self.member.edit(nick=nickname.replace('#', ''))
            except discord.errors.Forbidden:
                pass

    def sleep(self):
        self.sleeped = True

    def unsleep(self):
        self.sleeped = False
