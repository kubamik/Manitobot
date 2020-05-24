import discord

from permissions import can_refuse

class Player:

  def __init__(self, member, role):
    self.member = member
    self.role = role
    self.active = False
    self.sleeped = False
    self.protected = False
    self.killing_protected = False
    self.role_class = None
  
  def can_refuse(self):
    return self.role in can_refuse

  async def new_day(self):
    self.sleeped = False
    self.protected = False
    self.killing_protected = False
    nickname = self.member.display_name
    if nickname.endswith('#'):
      try:
        await self.member.display_name.edit(nick=nickname[:-1])
      except discord.errors.Forbidden:
        pass