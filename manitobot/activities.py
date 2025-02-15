import inspect

from . import permissions
from .errors import GameEnd
from .night_comunicates import webhook_com, meantime_operation_com, \
    new_night_com
from .postacie import get_faction, send_faction, give_faction, get_role_details
from .utility import *


class Activity:
    def __init__(self):
        pass

    def if_not_sleeped(self):
        if self.plyer.sleeped:
            raise InvalidRequest("Nie możesz działać, bo jesteś zamknięty lub upity")

    def if_night(self):
        if not bot.game.night_now:
            raise InvalidRequest()

    def if_worked(self):
        if not self.worked:
            self.member = None
            raise InvalidRequest("Postępuj według kolejności w instrukcji")

    def if_not_worked(self):
        if self.worked:
            self.member = None
            raise InvalidRequest("Postępuj według kolejności w instrukcji")

    def make_it_work(self):
        self.worked = True

    def unwork(self):
        self.worked = False

    async def mark_arrest(self):
        nick = self.member.member.display_name
        try:
            await self.member.member.edit(nick=nick + '#')
        except discord.Forbidden:
            pass

    def angel_alive(self):
        r = permissions.SPEC_ROLES["inqui_change_on_death"]
        try:
            if bot.game.role_map[r].player.member in get_dead_role().members:
                raise InvalidRequest()
        except KeyError:
            raise InvalidRequest()

    async def who_pastored(self):
        try:
            p = bot.game.role_map["Pastor"]
            if p.player.member not in get_dead_role().members:
                o = p.roled_members[-1]
                if o != None:
                    await self.player.member.send(
                        "Pastor sprawdził {}, członka frakcji {}".format(o.member.display_name, get_faction(o.role)))
                else:
                    await self.player.member.send("Pastor nie sprawdzał tej nocy")
                raise InvalidRequest("{} otrzymał informacje o Pastorze".format(self.name))
        except KeyError:
            pass

    async def bishop_back(self):
        await bot.game.nights[-1].bishop_back()
        await self.channel.send("Możecie kontynuować wcześniejszą akcję")

    def inqui_alone_win(self):
        if bot.game.stats["Inkwizycja"] == len(get_player_role().members):
            raise GameEnd("Zostali sami Inkwizytorzy", "Inkiwzycja")

    async def statue_none(self):
        if bot.game.statue.holder is None:
            await bot.game.nights[-1].bishop(self, self.member.member.display_name)
            self.my_activities["burn"] -= 1
            raise InvalidRequest("Zabójstwo zostanie zrealizowane po ustaleniu posiadacza posążka")

    def nonzero(self):
        if bot.game.day_num == 0:
            self.member = None
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
            if night > bot.game.day_num:
                raise InvalidRequest()
            self.output += new_night_com[role]
            c += "Poczekaj aż użyje pożądanych zdolności"
        except InvalidRequest:
            self.output += "Nie możesz teraz użyć żadnej zdolności tej postaci. Idziesz spać."
            self.deactivate()
        except KeyError:
            pass
        self.my_activities["start"] = "uncopy"
        self.my_activities["copy"] = 1
        await send_to_manitou(c)

    async def angelize(self):
        r = permissions.SPEC_ROLES["inqui_change_on_death"]
        angel = bot.game.role_map[r].player.member
        await angel.send("Skorzystałeś ze swojej umiejętności twoja nowa rola to:\n {}".format(
            get_role_details(self.name, self.name)))
        c = "{} jako Anioł przejął rolę {}, czyli {}".format(angel.display_name, self.player.member.display_name,
                                                             self.name)
        bot.game.swap(self.player.member, angel)
        await send_to_manitou(c)
        await get_manitou_notebook().send(c)

    def if_holders(self):
        if give_faction(self.member.role) == bot.game.statue.faction_holder:
            return "Ta osoba należy do frakcji posiadaczy posążka"
        return "Ta osoba nie należy do frakcji posiadaczy posążka"

    async def make_peace(self):
        state = bot.game.day.state
        if hasattr(state, 'peace'):
            await state.peace()
            await self.meantime_send()
            
    async def send_refusal(self):
        await send_to_manitou("{} zdecydował nie działać".format(self.name))
        
    async def del_state_special_msg(self):
        try:
            await bot.game.day.state.special_message.delete(delay=0)
        except AttributeError:
            pass

    def indian_win(self):
        if bot.game.stats["Indianie"] == len(get_player_role().members):
            raise GameEnd("Zostali sami Indianie", "Indianie")

    def inqui_win(self):
        d = bot.game.stats
        if not (d["Indianie"] or d["Ufoki"] or d["Janosik"] or d["Lusterko"] or d["Murzyni"] or d["Bogowie"] or not d[
            "Inkwizycja"]):
            raise GameEnd("Wszyscy heretycy nie żyją", "Inkwizycja")

    def unrefuse(self):
        if "refuse" in self.my_activities:
            del self.my_activities["refuse"]

    def deactivate(self):
        bot.game.nights[-1].active_role = None
        self.member = None

    async def reactivate_luke(self):
        if "look" in self.my_activities.values():
            k = self.my_activities["kill"]
            f = self.my_activities["follow"]
            if ((k or f) and not self.worked) or (k and f):
                bot.game.nights[-1].active_role = self
                c = "Poczekaj na decyzję o dodatkowej zdolności {}".format(self.name.replace('_', ' '))
                ret = None
                await get_town_channel().send(bot.game.nights[-1].output)
                bot.game.nights[-1].output = ""
            else:
                c = "{} dowiedział się kto ma posążek".format(self.name)
                ret = self.who()
            await send_to_manitou(c)
            return ret

    def if_day(self):
        if bot.game.night_now:
            self.member = None
            raise InvalidRequest("Tej zdolności można użyć tylko w dzień")

    def if_not_self(self):
        if self.member == self.player:
            self.member = None
            raise InvalidRequest("Nie możesz działać sam na siebie")

    def if_parameter(self):
        if self.member is None:
            raise InvalidRequest("Brakuje parametru: gracz")

    def set_use(self):
        self.count -= 1

    def signal(self):
        self.data += 1

    def if_not_revealed(self):
        if self.revealed:
            raise InvalidRequest("Nie możesz więcej użyć tej zdolności")

    async def reveal(self, dead=False, verbose=True):
        self.revealed = True
        member = self.player.member
        nickname: str = member.display_name
        if dead and not nickname.startswith('+'):
            nickname = '+' + nickname
        if verbose:
            await get_town_channel().send("**{}** to **{}**".format(nickname.replace('+', ''),
                                                                    self.name.replace('_', ' ')))
        try:
            await member.edit(nick=nickname + "({})".format(self.name.replace('_', ' ')))
        except discord.errors.Forbidden:
            pass
        except discord.HTTPException:
            role = list(self.name.split('_'))
            role[0] = role[0][:3] + '.'
            if len(nickname + '({})'.format(" ".join(role))) < 32:
                await member.edit(nick=nickname + '({})'.format(" ".join(role)))
            else:
                await member.send(f"Wepchnij jakoś swoją rolę ({' '.join(role)}) do nicka")

    def if_duel(self):
        if self.member is not None:
            duel = bot.game.day.state
            if not hasattr(duel, 'change_winner'):
                self.member = None
                raise InvalidRequest(
                    'Nie możesz teraz zmienić wyniku pojedynku, aby tylko się ujawnić użyj samego `&wygr`')
            if self.member.member not in duel.winners + duel.losers:
                self.member = None
                raise InvalidRequest('Ta osoba nie brała udziału w pojedynku')

    def if_active(self):
        if self != bot.game.nights[-1].active_role:
            self.member = None
            raise InvalidRequest("Nie możesz teraz działać")

    async def change_duel(self):
        if self.member and "copied" not in self.my_activities:
            await bot.game.day.state.change_winner(self.member.member)
            await self.meantime_send()

    async def meantime_send(self):
        display_name = None if self.member is None else self.member.member.display_name
        try:
            if not meantime_operation_com[self.operation][1]:
                raise KeyboardInterrupt
            com = webhook_com[self.operation]
            for webhk in await get_town_channel().webhooks():
                if webhk.name == "Manitobot {}".format(self.name.replace('_', ' ')):
                    wbhk = webhk
                    break
            else:
                wbhk = await get_town_channel().create_webhook(name="Manitobot {}".format(self.name.replace('_', ' ')))
            await wbhk.send(com[0].format(role=self.name.replace('_', ' '), member=display_name),
                            username=self.name.replace('_', ' '), avatar_url=com[1])
        except:
            com = meantime_operation_com[self.operation]
            if com[1]:
                await get_town_channel().send(com[0].format(role=self.name.replace('_', ' '), member=display_name))
            if com[2]:
                await send_to_manitou(com[0].format(role=self.name.replace('_', ' '), member=display_name))

    def sleep(self):
        self.member.sleeped = True

    def protect(self):
        self.member.protected = True

    def protect_killing(self):
        self.member.killing_protected = True

    async def search(self):
        found = await bot.game.statue.search(self.player.member, self.name, self.member.member,
                                                         not self.if_has())
        return found

    def refusal(self):
        if "refused" in self.my_activities:
            bot.game.nights[-1].output += self.my_activities["refused"]

    def can_hold(self):
        if self.member.role not in self.roles:
            self.member = None
            raise InvalidRequest("Możesz wręczyć posążek tylko członkowi swojej frakcji")
        if self.member.sleeped:
            self.member = None
            raise InvalidRequest("Ta osoba nie jest aktywna")

    async def change_holder(self):
        await bot.game.statue.change_holder(self.member.member)

    async def if_better(self):
        role = self.member.role
        if role == "Szuler" or send_faction(role)[2:-3] == "Miasto":
            self.deactivate()
            await self.die("shoot")
            raise InvalidRequest("Trafiłeś na lepszego od siebie. Giniesz")

    async def special_search(self):
        found = await bot.game.statue.special_search(self.player.member, self.name, self.member.member,
                                                                 not self.if_has())
        return found

    def f_has(self):
        return bot.game.statue.faction_holder == self.name and not bot.game.statue.planted

    def has(self):
        if bot.game.statue.holder != self.player.member:
            raise InvalidRequest()

    def if_has(self):
        return self.player.member == bot.game.statue.holder and not bot.game.statue.planted

    def if_shooted(self):
        if self.die_reason != "shoot":
            raise InvalidRequest()

    async def present(self):
        await bot.game.statue.present(self.member.member, self.member.role)

    async def kill(self):
        await self.member.role_class.die()

    async def f_search(self):
        return await bot.game.statue.faction_search(self.name, self.member.member, not self.f_has())

    def alone(self):
        if len(get_player_role().members) == 1:
            raise GameEnd("Został tylko {}".format(self.name), "Miasto")

    def if_protected(self):
        if self.member.protected:
            self.member = None
            raise InvalidRequest("Ta osoba jest chroniona")

    async def statue_alone(self):
        if self.awake_number == 1 and self.f_has():
            await bot.game.statue.change_holder(self.leader.member)

    def if_not_prev(self):
        if self.member == self.roled_members[-1]:
            self.member = None
            raise InvalidRequest("Nie możesz użyć swojej zdolności na tej samej osobie dwa razy z rzędu")

    def check_faction(self):
        return "Frakcja {} to {}".format(self.member.member.display_name, get_faction(self.member.role))

    def check_role(self):
        return "**{}** to **{}**".format(self.member.member.display_name, self.member.role.replace('_', ' '))

    async def hang_win(self):
        if self.die_reason == 'hang':
            reason = "Powieszony(-a) został(a) {}, czyli {}".format(self.player.member.display_name, self.name)
            raise GameEnd(reason, self.name)

    def can_unplant(self):
        player = self.roles["Cicha_Stopa"].player
        if player.sleeped or player.member in get_dead_role().members or not bot.game.statue.planted or bot.game.statue.faction_holder != self.name:
            raise InvalidRequest()

    async def unplant(self):
        member = self.roles["Cicha_Stopa"].player.member
        await bot.game.statue.unplant(member)

    def got_today(self):
        try:
            if not (self.faction.f_has() or bot.game.statue.last_change == bot.game.day_num):
                raise InvalidRequest()
        except AttributeError:
            if not (self.has() or bot.game.statue.last_change == bot.game.day_num):
                raise InvalidRequest()

    def lone(self):
        try:
            if self.faction.awake_number > 1:
                raise InvalidRequest()
        except AttributeError:
            pass

    def follow(self):
        bot.game.statue.follow(self.player.member, self.member.member)

    async def mirror_send(self):
        c = "{} zlustrowało {}".format(self.name, self.member.member.display_name)
        await send_to_manitou(c)

    def unfollow(self):
        bot.game.statue.unfollow(self.player.member)

    def luke_win(self):
        if self.if_has():
            raise GameEnd("Lucky Luke odjeżdża z posążkiem", "Lucky_Luke")

    async def plant(self):
        await bot.game.statue.plant(self.member.member)

    def szaman_yes(self):
        bot.game.nights[-1].output += "Szaman sprawdzał tej nocy"

    def herb(self):
        bot.game.nights[-1].herbed = self.member.role_class

    def who(self):
        return "Posążek ma {}".format(bot.game.statue.holder.display_name)

    def detect(self):
        holder = bot.game.statue.holder.display_name.lower()
        member = self.member.member.display_name.lower()
        me = self.player.member.display_name.lower()
        if holder == member:
            return "{} ma posążek".format(holder.display_name)
        if me > holder > member or me < holder < member:
            return "Posążek jest na wewnętrznym łuku między Tobą i {}".format(member)
        return "Posążek jest na zewnętrznym łuku między Tobą i {}".format(member)
