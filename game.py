from collections import defaultdict
from typing import NoReturn

import discord

import utility
from daynight import Day,Night
from vote import Vote
from statue import Statue
from faction import Faction
from role import Role
from player import Player
from postacie import get_faction, give_faction, print_list
from utility import get_town_channel, WrongGameType

class Game(Vote):
  def __init__(self):
    Vote.__init__(self)
    self.message = None
    self.statue = Statue()
    self.player_map = {}
    self.role_map = {}
    self.faction_map = {}
    self.roles = []
    self.night = True
    self.day = 0
    self.days = [None]
    self.nights = [None]
    self.duels = 2
    self.searches = 2
    self.bandit_night = 3
    self.bandit_morning = True
    self.rioters = set()
    self.new_night()
    self.reveal_dead = True
    '''self.stats = {
      "Miasto":0,
      "Bandyci":0,
      "Janosik":0,
      "Lucky_Luke":0,
      "Lusterko":0,
      "Ufoki":0,
      "Indianie":0,
      "Inkwizycja":0,
      "Bogowie":0,
      "Murzyni":0
    }'''
    self.stats = defaultdict(int)

  def __getattr__(self, name:str) -> NoReturn:
    raise WrongGameType('Current game type does not support this attribute.')

  async def new_day(self):
    self.days.append(Day())
    self.day += 1
    self.night = False
    for player in self.player_map.values():
      await player.new_day()
    self.town_win()
    self.inqui_win()
    self.morning_bandits_win()
    
  def new_night(self):
    self.nights.append(Night())
    self.night = True
    self.evening_bandits_win()

  def make_factions(self, roles, data):
    for role in roles:
      faction = get_faction(role)
      if faction != 'Miasto' and not faction in self.faction_map:
        try:
          self.faction_map[faction] = Faction(faction)
        except KeyError:
          pass
        
  def add_pair(self, member, role):
    try:
      self.stats[give_faction(role)] += 1
    except KeyError:
      pass
    self.player_map[member] = Player(member, role)
    self.role_map[role] = Role(role, self.player_map[member])
    self.player_map[member].role_class = self.role_map[role]

  async def winning(self, reason, faction):
    c = ":scroll:{}:scroll:\n**WYGRALIŚCIE!**".format(reason)
    for member, player in self.player_map.items():
      if give_faction(player.role) == faction:
        await member.send(c)

  def swap(self, first, second):
    frole = self.player_map[first].role
    srole = self.player_map[second].role
    self.player_map[first].role = srole
    self.player_map[second].role = frole
    self.role_map[srole].player = self.player_map[first]
    self.role_map[frole].player = self.player_map[second]
    self.player_map[second].role_class = self.role_map[frole]
    self.player_map[first].role_class = self.role_map[srole]
    return (srole, frole)
  
  def inqui_win(self):
    g = self.stats.get
    if not any([g("Indianie"), g("Ufoki"), g("Janosik"), g("Lusterko"),g("Murzyni"), g("Bogowie"), not g("Inkwizycja")]):
      raise utility.GameEnd("Wszyscy heretycy nie żyją","Inkwizycja")

  def inqui_alone_win(self):
    if self.stats["Inkwizycja"] == len(utility.get_player_role().members):
      raise utility.GameEnd("Zostali sami Inkwizytorzy", "Inkiwzycja")

  def indian_win(self):
    if self.stats["Indianie"] == len(utility.get_player_role().members):
      raise utility.GameEnd("Zostali sami Indianie", "Indianie")
    
  def town_win(self):
    if self.statue.faction_holder == "Miasto" and not self.statue.planted:
      role = self.player_map[self.statue.holder].role
      raise utility.GameEnd("{} posiada posążek o poranku".format(role.replace("_"," ")),"Miasto")

  def evening_bandits_win(self):
    if self.day == self.bandit_night and not self.bandit_morning and self.statue.faction_holder == "Bandyci" and self.statue.holder:
      raise utility.GameEnd("Bandyci odpływają z posążkiem","Bandyci")

  def morning_bandits_win(self):
    if self.statue.faction_holder == "Bandyci" and self.statue.holder and (self.day > self.bandit_night or (self.bandit_morning and self.day == self.bandit_night)):
      raise utility.GameEnd("Bandyci odpływają z posążkiem", "Bandyci")

  def on_die(self, reason, player):
    self.stats[give_faction(player.role)] -= 1
    if reason == "herbs":
      self.statue.day_search(player.member)
    self.indian_win()
    if not self.night:
      self.inqui_win()
      if reason != "herbs":
        self.statue.day_search(player.member)
    else:
      self.inqui_alone_win()
    
  @property
  def bandit_morn(self):
    return self.bandit_night if self.bandit_morning else None

  @bandit_morn.setter
  def bandit_morn(self, n):
    self.bandit_night = n
    self.bandit_morning = True

  @property
  def bandit_even(self):
    return self.bandit_night if not self.bandit_morning else None

  @bandit_even.setter
  def bandit_even(self, n):
    self.bandit_night = n
    self.bandit_morning = False
  
  def print_list(self, roles, data):
    return print_list(roles)
