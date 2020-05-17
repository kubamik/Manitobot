import discord
import asyncio

import postacie
from utility import *
import globals
import permissions
from night_comunicates import night_send, operation_send
from postacie import get_faction, send_faction, give_faction

class Activity:
  def __init__(self):
    pass

  def if_night(self):
    if not globals.current_game.night:
      raise InvalidRequest()

  def if_worked(self):
    if not self.worked:
      raise InvalidRequest("Postępuj według kolejności w instrukcji")
  
  def if_not_worked(self):
    if self.worked:
      raise InvalidRequest("Postępuj według kolejności w instrukcji")

  def make_it_work(self):
    self.worked = True

  def unwork(self):
    self.worked = False

  def angel_alive(self):
    r = permissions.role_abilities["inqui_change_on_death"]
    try:
      if globals.current_game.role_map[r].player.member in get_dead_role().members:
        raise InvalidRequest()
    except KeyError:
      raise InvalidRequest()

  async def who_pastored(self):
    try:
      p = globals.current_game.role_map["Pastor"]
      if p.player.member not in get_dead_role().members:
        o = p.roled_members[-1]
        if o != None:
          await self.player.member.send("Pastor sprawdził {}, członka frakcji {}".format(o.member.display_name, get_faction(o.role)))
        else:
          await self.player.member.send("Pastor nie sprawdzał tej nocy")
        raise InvalidRequest("{} otrzymał informacje o Pastorze".format(self.name))
    except KeyError:
      pass

  async def bishop_back(self):
    await globals.current_game.nights[-1].bishop_back()
    await self.channel.send("Możecie kontynuować wcześniejszą akcję")

  def inqui_alone_win(self):
    if globals.current_game.stats["Inkwizycja"] == len(get_player_role().members):
      raise GameEnd("Zostali sami Inkwizytorzy", "Inkiwzycja")

  async def statue_none(self):
    if globals.current_game.statue.holder is None:
      await globals.current_game.nights[-1].bishop(self, self.member.member.display_name)
      self.my_activities["burn"] -= 1
      raise InvalidRequest("Zabójstwo zostanie zrealizowane po ustaleniu posiadacza posążka")
  
  def nonzero(self):
    if globals.current_game.day == 0:
      raise InvalidRequest("Nie możesz działać zerowej nocy")

  def if_member(self):
    if self.member is None:
      raise InvalidRequest("Musisz działać według kolejności opisanej w instrukcji")

  def check_heresis(self):
    fac = give_faction(self.member.role)
    if fac in ["Indianie", "Ufoki", "Janosik", "Lusterko", "Murzyni", "Bogowie"]:
      return "Ta osoba jest heretykiem"
    return "Ta osoba nie jest heretykiem"

  async def deactivate_cond(self):
    if self.count == -2 and not "copied" in self.my_activities:
      self.deactivate()
      c = "{} wykorzystał(-a) już dodatkową zdolność".format(self.name)
    else:
      c = "Poczekaj na decyzję o dodatkowej zdolności {}".format(self.name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  def deactivate_if(self):
    if self.count != 0 and not "copied" in self.my_activities:
      self.deactivate()

  def unchange(self):
    if self.count == -2:
      self.my_activities = permissions.role_activities[self.name][2].copy()
      self.my_activities["copy"] = 0

  async def search_send(self):
    c = "{} przeszukał(-a) {}".format(self.name, self.member.member.display_name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  async def kill_send(self):
    c = "{} zabił(-a) {}".format(self.name, self.member.member.display_name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  async def follow_send(self):
    c = "{} śledzi {}".format(self.name, self.member.member.display_name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  async def copy(self):
    role = self.member.role
    activities = permissions.role_activities[role]
    self.my_activities = activities[2].copy()
    self.my_activities["copied"] = True
    for k in ("die", "refused"):
      try:
        del self.my_activities[k]
      except KeyError:
        pass
    night = activities[0]
    c = "{} skopiowało {}\n".format(self.name, role)
    try:
      for f in permissions.get_activity(self.my_activities["start"], self):
        if inspect.iscoroutinefunction(f):
          await f()
        else:
          f()
      if night > globals.current_game.day:
        raise InvalidRequest()
      self.output += new_night_com[role]
      c += "Poczekaj aż użyje pożądanych zdolności"
    except InvalidRequest:
      self.output += "Nie możesz teraz użyć żadnej zdolności tej postaci. Idziesz spać."
    except KeyError:
      pass
    self.my_activities["start"] = "uncopy"
    self.my_activities["copy"] = 1
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  async def angelize(self):
    r = permissions.role_abilities["inqui_change_on_death"]
    angel = globals.current_game.role_map[r].player.member
    globals.current_game.swap(self.player.member, angel)
    await angel.send("Skorzystałeś ze swojej umiejętności twoja nowa rola to: {}".format(self.name))
    c = "{} jako Anioł przejął rolę {}, czyli {}".format(angel.display_name, self.player.member.display_name, self.name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  def if_holders(self):
    if give_faction(self.member.role) == globals.current_game.statue.faction_holder:
      return "Ta osoba należy do frakcji posiadaczy posążka"
    return "Ta osoba nie należy do frakcji posiadaczy posążka" 

  async def if_hang_time(self):
    try:
      if globals.current_game.days[-1].hang_final:
        await get_town_channel().send("Burmistrz ułaskawił wieszaną osobę")
        await get_glosowania_channel().send("Burmistrz ułaskawił wieszaną osobę")
    except AttributeError:
      pass

  def indian_win(self):
    if globals.current_game.stats["Indianie"] == len(get_player_role().members):
      raise GameEnd("Zostali sami Indianie", "Indianie")
  
  def inqui_win(self):
    d = globals.current_game.stats
    if not (d["Indianie"] or d["Ufoki"] or d["Janosik"] or d["Lusterko"] or d["Murzyni"] or d["Bogowie"] or not d["Inkwizycja"]):
      raise GameEnd("Wszyscy heretycy nie żyją","Inkwizycja")

  def unrefuse(self):
    if "refuse" in self.my_activities:
      del self.my_activities["refuse"]

  def deactivate(self):
    globals.current_game.nights[-1].active_role = None
    self.member = None

  async def reactivate_luke(self):
    if "look" in self.my_activities.values():
      k = self.my_activities["kill"]
      f = self.my_activities["follow"]
      if ((k or f) and not self.worked) or (k and f):
        globals.current_game.nights[-1].active_role = self
        c = "Poczekaj na decyzję o dodatkowej zdolności {}".format(self.name)
        ret = None
      else:
        c = "{} dowiedział się kto ma posążek".format(self.name)
        ret = self.who()
      await send_to_manitou(c)
      await get_manitou_notebook().send(c)
      return ret
        

  def if_day(self):
    if globals.current_game.night:
      raise InvalidRequest("Tej zdolności można użyć tylko w dzień")

  def if_not_self(self):
    if self.member == self.player:
      raise InvalidRequest("Nie możesz działać sam na siebie")

  def if_parameter(self):
    if self.member is None:
      raise InvalidRequest("Brakuje parametru: gracz")

  def set_use(self):
    self.count -= 1

  def signal(self):
    self.data += 1

  async def reveal(self):
    nickname = get_nickname(self.player.member.id)
    self.revealed = True
    member = self.player.member
    await get_town_channel().send("Rola **{}** to **{}**".format(nickname.replace('+',''),self.name.replace('_',' ')))
    try:
      await member.edit(nick=nickname + "({})".format(self.name.replace('_',' ')))
    except discord.errors.Forbidden:
      await member.send("Zmień swój nick na {}, bo ja nie mam uprawnień.".format(nickname+"({})".format(self.name.replace('_',' '))))

  def if_duel(self):
    if not self.member is None:
      if not globals.current_game.days[-1].duels_result:
        raise InvalidRequest("Nie możesz teraz zmienić wyniku pojedynku, aby tylko się ujawnić użyj samego `&wygr`")
      if not self.member.member in globals.current_game.days[-1].participants:
        raise InvalidRequest("Ta osoba nie brała udziału w pojedynku")

  def if_active(self):
    if self != globals.current_game.nights[-1].active_role:
      raise InvalidRequest("Nie możesz teraz działać")

  async def change_duel(self):
    if not self.member is None and not "copied" in self.my_activities:
      await globals.current_game.days[-1].change_winner(self.member.member)

  def sleep(self):
    self.member.sleeped = True
    
  def protect(self):
    self.member.protected = True
  
  def protect_killing(self):
    self.member.killing_protected = True

  async def search(self):
    found = await globals.current_game.statue.search(self.player.member, self.name, self.member.member, not self.if_has())
    return found

  def refusal(self):
    if "refused" in self.my_activities:
      globals.current_game.nights[-1].output += self.my_activities["refused"]

  def can_hold(self):
    if self.member.role not in self.roles:
      raise InvalidRequest("Możesz wręczyć posążek tylko członkowi swojej frakcji")
    if self.member.sleeped:
      raise InvalidRequest("Ta osoba nie jest aktywna")

  async def change_holder(self):
    await globals.current_game.statue.change_holder(self.member.member)

  async def if_better(self):
    role = self.member.role
    if role == "Szuler" or send_faction(role)[2:-3] == "Miasto":
      self.deactivate()
      await self.die("shoot")
      raise InvalidRequest("Trafiłeś na lepszego od siebie. Giniesz")

  async def special_search(self):
    found = await globals.current_game.statue.special_search(self.player.member, self.name, self.member.member, not self.if_has())
    return found

  def f_has(self):
    return globals.current_game.statue.faction_holder == self.name and not globals.current_game.statue.planted

  def has(self):
    if globals.current_game.statue.holder != self.player.member:
      raise InvalidRequest()

  def if_has(self):
    return self.player.member == globals.current_game.statue.holder and not globals.current_game.statue.planted
    
  def if_shooted(self):
    if self.die_reason != "shoot":
      raise InvalidRequest()

  async def present(self):
    await globals.current_game.statue.present(self.member.member, self.member.role)

  async def kill(self):
    await self.member.role_class.die()

  async def f_search(self):
    return await globals.current_game.statue.faction_search(self.name, self.member.member, not self.f_has())

  def alone(self):
    if len(get_player_role().members) == 1:
      raise GameEnd("Został tylko {}".format(self.name), "Miasto")
  
  def if_protected(self):
    if self.member.protected:
      raise InvalidRequest("Ta osoba jest chroniona")

  async def statue_alone(self):
    if self.awake_number == 1 and self.f_has():
      await globals.current_game.statue.change_holder(self.leader.member)
  
  def if_not_prev(self):
    if self.member == self.roled_members[-1]:
      raise InvalidRequest("Nie możesz użyć swojej zdolności na tej samej osobie dwa razy z rzędu")

  def check_faction(self):
    return "Frakcja {} to {}".format(self.member.member.display_name,get_faction(self.member.role))

  def check_role(self):
    return "Rola **{}** to **{}**".format(self.member.member.display_name, self.member.role.replace('_',' '))
  
  async def hang_win(self):
    if self.die_reason == 'hang':
      reason = "Powieszony został {}, czyli {}".format(self.player.member.display_name, self.name)
      raise GameEnd(reason, self.name)

  async def peace_make(self):
    if not "copied" in self.my_activities:
      await globals.current_game.days[-1].peace()

  def can_unplant(self):
    player = self.roles["Cicha_Stopa"].player
    if player.sleeped or player.member in get_dead_role().members or not globals.current_game.statue.planted or globals.current_game.statue.faction_holder != self.name:
      raise InvalidRequest()

  async def unplant(self):
    member = self.roles["Cicha_Stopa"].player.member
    await globals.current_game.statue.unplant(member)

  def got_today(self):
    try:
      if not (self.faction.f_has() or globals.current_game.statue.last_change == globals.current_game.day):
        raise InvalidRequest()
    except AttributeError:
      if not (self.has() or globals.current_game.statue.last_change == globals.current_game.day):
        raise InvalidRequest()

  def lone(self):
    try:
      if self.faction.awake_number > 1:
        raise InvalidRequest()
    except AttributeError:
      pass
  
  def follow(self):
    globals.current_game.statue.follow(self.player.member, self.member.member)

  async def mirror_send(self):
    c = "{} zlustrowało {}".format(self.name, self.member.member.display_name)
    await send_to_manitou(c)
    await get_manitou_notebook().send(c)

  def unfollow(self):
    globals.current_game.statue.unfollow(self.player.member)

  def luke_win(self):
    if self.f_has():
      raise GameEnd("Lucky Luke odjeżdża z posążkiem","Lucky_Luke")
  
  async def plant(self):
    await globals.current_game.statue.plant(self.member.member)

  def szaman_yes(self):
    globals.current_game.nights[-1].output += "Szaman sprawdzał tej nocy"

  def herb(self):
    globals.current_game.nights[-1].herbed = self.member.role_class

  def who(self):
    return "Posążek ma {}".format(globals.current_game.statue.holder.display_name)

  def detect(self):
    holder = globals.current_game.statue.holder.display_name.lower()
    member = self.member.member.display_name.lower()
    me = self.player.member.display_name.lower()
    if holder == member:
      return "{} ma posążek".format(holder.display_name)
    if me > holder > member or me < holder < member:
      return "Posążek jest na wewnętrznym łuku między Tobą i {}".format(member)
    return "Posążek jest na zewnętrznym łuku między Tobą i {}".format(member)


    