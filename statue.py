from utility import playing, GameEnd, send_to_manitou, get_town_channel, get_manitou_notebook
from postacie import send_faction, give_faction
import globals


class Statue:
  def __init__(self):
    self.holder = None
    self.faction_holder = "Bandyci"
    self.planted = False
    self.last_change = -1
    self.followed = {}

  def follow(self, author, member):
    self.followed[author] = member

  def luke_win(self):
    if self.has():
      raise GameEnd("Lucky Luke odjeżdża z posążkiem","Lucky_Luke")

  def unfollow(self, author):
    try:
      del self.followed[author]
    except KeyError:
      pass

  async def if_followed(self, member):
    for auth, mem in self.followed.items():
      if mem == member and member != self.holder:
        self.last_change = globals.current_game.day
        self.planted = False
        self.holder = auth
        role = globals.current_game.player_map[auth].role
        faction = give_faction(role)
        self.faction_holder = faction
        c = "{} przejmuje posążek w wyniku śledzenia".format(globals.current_game.player_map[auth].role)
        await send_to_manitou(c)
        await get_manitou_notebook().send(c)
        return c[:-19]
    return False

  async def plant(self, member):
    f = await self.if_followed(member)
    if not f:
      self.planted = True
      self.holder = member
    else:
      globals.current_game.nights[-1].output += f

  async def unplant(self, member):
    f = await self.if_followed(member)
    if not f:
      self.planted = False
      self.holder = member
    else:
      globals.current_game.nights[-1].output += f
  
  def give(self, member):
    playing(member)
    self.holder = member
    self.planted = False
    role = globals.current_game.player_map[member].role
    faction = send_faction(role)[2:-2]
    if faction.endswith(':'):
      faction = faction[:-1]
    self.faction_holder = faction

  def day_search(self, member):
    if self.holder == member:
      raise GameEnd("**{}** ma posążek".format(member.display_name), "Miasto")
    else:
      return "**{}** nie ma posążka".format(member.display_name)

  async def search(self, author, role, member, info = True):
    if self.holder == member:
      f = await self.if_followed(author)
      if not f:
        self.last_change = globals.current_game.day
        c = "{} przejmuje posążek".format(role)
        await send_to_manitou(c)
        await get_manitou_notebook().send(c)
        globals.current_game.nights[-1].output = c
        self.holder = author
        faction = send_faction(role)[2:-2]
        if faction.endswith(':'):
          faction = faction[:-1]
        self.faction_holder = faction
        self.planted = False
        return "Przejmujesz posążek"
      else:
        globals.current_game.nights[-1].output = f
        return "Przejmujesz posążek i go tracisz"
    if info:
      c = "{} nie przejmuje posążka".format(role)
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      if not globals.current_game.nights[-1].output:
        globals.current_game.nights[-1].output += c
    return "Nie przejmujesz posążka"

  async def special_search(self, author, role, member, info = True):
    if self.holder == member:
      f = await self.if_followed(author)
      if not f:
        self.last_change = globals.current_game.day
        c = "{} przejmuje posążek".format(role)
        await send_to_manitou(c)
        await get_manitou_notebook().send(c)
        await get_town_channel().send(c)
        self.holder = author
        faction = send_faction(role)[2:-2]
        if faction.endswith(':'):
          faction = faction[:-1]
        self.faction_holder = faction
        self.planted = False
        return "Przejmujesz posążek"
      else:
        await get_town_channel().send(f)
        return "Przejmujesz posążek i go tracisz"
    if info:
      c = "{} nie przejmuje posążka".format(role)
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      await get_town_channel().send(c)
      return "Nie przejmujesz posążka"

  async def present(self, member, role):
    f = await self.if_followed(member)
    if not f:
      c = "{} przejmuje posążek".format(role)
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      self.holder = member
      self.planted = False
      faction = send_faction(role)[2:-2]
      if faction.endswith(':'):
        faction = faction[:-1]
      self.faction_holder = faction
      globals.current_game.nights[-1].output = "{} przejmuje(-ą) posążek".format(faction)
    else:
      globals.current_game.nights[-1].output = f

  async def faction_search(self, faction, member, info = True):
    if self.holder == member:
      self.last_change = globals.current_game.day
      c = "{} przejmuje(-ą) posążek".format(faction)
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      await get_town_channel().send(c)
      self.planted = False
      self.faction_holder = faction
      self.holder = None
      return "Przejmujecie posążek"
    if info:
      c = "{} nie przejmuje(-ą) posążka".format(faction)
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      await get_town_channel().send(c)
      return "Nie przejmujecie posążka"

  async def change_holder(self, member):
    f = await self.if_followed(member)
    if not f:
      self.holder = member
    else:
      await get_town_channel().send(f)