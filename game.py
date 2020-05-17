import utility
from daynight import Day,Night
from vote import Vote
from statue import Statue
from faction import Faction
from role import Role
from player import Player
from postacie import get_faction, give_faction

class Game(Vote):
  def __init__(self):
    Vote.__init__(self)
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
    self.stats = {
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
    }

  def new_day(self):
    self.days.append(Day())
    self.day += 1
    self.night = False
    for player in self.player_map.values():
      player.new_day()
    self.town_win()
    self.inqui_win()
    self.morning_bandits_win()
    
    

  def new_night(self):
    self.nights.append(Night())
    self.night = True
    self.evening_bandits_win()
    

  def make_factions(self, roles):
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
    d = self.stats
    if not (d["Indianie"] or d["Ufoki"] or d["Janosik"] or d["Lusterko"] or d["Murzyni"] or d["Bogowie"] or not d["Inkwizycja"]):
      raise utility.GameEnd("Wszyscy heretycy nie żyją","Inkwizycja")
    
  def town_win(self):
    if self.statue.faction_holder == "Miasto":
      role = self.player_map[self.statue.holder].role
      raise utility.GameEnd("{} posiada posążek o poranku".format(role.replace("_"," ")),"Miasto")

  def evening_bandits_win(self):
    if self.day == self.bandit_night and not self.bandit_morning and self.statue.faction_holder == "Bandyci":
      raise utility.GameEnd("Bandyci odpływają z posążkiem","Bandyci")

  def morning_bandits_win(self):
    if self.statue.faction_holder == "Bandyci" and (self.day > self.bandit_night or (self.bandit_morning and self.day == self.bandit_night)):
      raise utility.GameEnd("Bandyci odpływają z posążkiem", "Bandyci")

    
