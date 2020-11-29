import discord
from collections import defaultdict
from typing import NoReturn

import utility
from daynight import Day, Night
from vote import Vote
from faction import Faction
from role import Role
from player import Player


class Mafia(Vote):
  def __init__(self):
    Vote.__init__(self)
    self.player_map = {}
    self.faction_map = {}
    self.roles = []
    self.night = True
    self.day = 0
    self.rioters = set()
    self.new_night()
    self.reveal_dead = False
    self.stats = {
      "Miasto":0,
      "Mafia":0
    }

  def __getattr__(self, name: str) -> NoReturn:
    raise utility.WrongGameType('Current game type does not support this attribute.')

  async def new_day(self):
    self.day += 1
    self.night = False

  def new_night(self):
    self.night = True


  def make_factions(self, roles, data):
    for player in self.player_map.values():
      if player.role in data[0]:
        player.role_class.faction = 'Miasto'
      else:
        player.role_class.faction = 'Mafia'
      self.stats[player.role_class.faction] += 1
        

  def add_pair(self, member, role):
    self.player_map[member] = Player(member, role)
    self.player_map[member].role_class = Role(role, self.player_map[member])

  async def winning(self, reason, faction):
    c = ":scroll:{}:scroll:\n**WYGRALIŚCIE!**".format(reason)
    for member, player in self.player_map.items():
      if player.role_class.faction == faction:
        await member.send(c)

  def swap(self, first, second):
    frole = self.player_map[first].role
    srole = self.player_map[second].role
    self.player_map[first].role = srole
    self.player_map[second].role = frole
    frole_cls = self.player_map[first].role_class
    srole_cls = self.player_map[second].role_class
    frole_cls.player = self.player_map[second]
    srole_cls.player = self.player_map[second]
    self.player_map[first].role_class = srole_cls
    self.player_map[second].role_class = frole_cls
    return (srole, frole)

  def town_win(self):
    if self.stats["Miasto"] == len(utility.get_player_role().members):
      raise utility.GameEnd("Zostali sami Miastowi", "Miasto")

  def mafia_win(self):
    if self.stats["Mafia"] == len(utility.get_player_role().members):
      raise utility.GameEnd("Zostali tylko Mafiozi", "Mafia")

  def on_die(self, reason, player):
    self.stats[player.role_class.faction] -= 1
    self.mafia_win()
    self.town_win()

  def print_list(self, everyone, data):
    mess = ''
    for roles, faction in zip(data, ('Miasto', 'Mafia')):
      mess += f'\n**{faction}: ({len(roles)})**\n'
      for role in roles:
        if everyone.count(role) > 1:
          mess += f'{role} ({everyone.count(role)})\n'
        else:
          mess += f'{role}\n'
    return mess
