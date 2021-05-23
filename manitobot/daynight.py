import utility
from basic_models import NotAGame
from duel import Duel
from errors import NoEffect
from hang_search import Search
from utility import *

night_order = ["Lucky_Luke", "Dziwka", "Szeryf", "Pastor", "Opój", "Pijany_Sędzia", "Hazardzista", "Lusterko",
               "Bandyci", "Mściciel", "Złodziej", "Szuler", "Szaman", "Indianie", "Lornecie_Oko", "Ufoki", "Inkwizycja"]


class Night:
    def __init__(self):
        self.active_faction = None
        self.active_number = 0
        self.active_role = None
        self.used_roles = []
        self.active_number = 0
        self.output = ""
        self.last_mess = None
        self.herbed = None
        self.bishop_base = None
        self.statue_owners = [
            None if isinstance(bot.game, NotAGame)
            else bot.game.statue.faction_holder]

    def what_next(self):
        try:
            for i in night_order[self.active_number:]:
                if (i in bot.game.role_map and bot.game.role_map[
                    i].work()) or i in bot.game.faction_map:
                    return ' ➡️{}'.format(i)
            return ' ➡️koniec nocy'
        except IndexError:
            return ''

    async def night_next(self, channel=None):
        if channel is None:
            channel = self.last_mess.channel
        try:
            # print(self.last_mess)
            await self.last_mess.remove_reaction('➡️', bot.user)
        except AttributeError:
            pass
        except discord.errors.NotFound:
            pass
        if self.output:
            await get_town_channel().send(self.output)
        self.output = ""
        if self.active_faction is None:
            try:
                next = night_order[self.active_number]
                self.active_number += 1
            except IndexError:
                await channel.send("Nie ma więcej postaci. Zakończ noc komendą `&day`")
                self.active_faction = None
                self.active_role = None
                return
        if not self.active_faction is None:
            c = self.active_faction.what_next()
            try:
                mess = await self.active_faction.faction_next()
                if mess:
                    self.last_mess = await channel.send(mess + c)
                    await self.last_mess.add_reaction('➡️')
            except InvalidRequest as err:
                if err.msg is None:
                    await self.night_next()
                    return
                self.last_mess = await channel.send(err.msg + c)
                if c:
                    await self.last_mess.add_reaction('➡️')
            except NoEffect as err:
                self.last_mess = await channel.send(err.reason)
                await self.night_next(channel)
                return
        elif next in bot.game.faction_map:
            c = bot.game.faction_map[next].what_next()
            try:
                await bot.game.faction_map[next].night_start()
                self.last_mess = await channel.send("Rozpoczynamy turę {}.".format(next.replace('_', ' ')) + c)
                await self.last_mess.add_reaction('➡️')
            except InvalidRequest as err:
                if err.msg is None:
                    await channel.send("{} nie budzą się.".format(next))
                    await self.night_next(channel)
                    return
                self.last_mess = await channel.send(err.msg + c)
                await self.last_mess.add_reaction('➡️')
        elif next in bot.game.role_map:
            c = self.what_next()
            try:
                ret = await bot.game.role_map[next].new_night_start()
                await bot.game.role_map[next].player.member.send(ret)
                self.last_mess = await channel.send("Wysłano instrukcje do {}".format(next.replace('_', ' ') + c))
                await self.last_mess.add_reaction('➡️')
            except InvalidRequest as err:
                if err.msg is None:
                    await self.night_next(channel)
                    return
                self.last_mess = await channel.send(err.msg + c)
                await self.last_mess.add_reaction('➡️')
        else:
            await self.night_next(channel)

    async def bishop(self, role_class, member):
        c = "Biskup przerwał grę, aby zabić {}, konieczne jest ustalenie posiadacza posążka".format(member)
        await get_manitou_notebook().send(c)
        await send_to_manitou(c)
        ctx = self.bishop_base
        f = self.active_faction
        operation = f.operation
        role = self.active_role
        self.active_role = f
        f.operation = "sphold"
        await f.channel.send(
            "Nastąpiło zatrzymanie gry, konieczne jest ustalenie posiadacza posążka przez lidera komendą `&daj NICK`")
        self.bishop_base = (role_class, ctx, member, operation, role)

    async def bishop_back(self):
        role_class, ctx, member, operation, role = self.bishop_base
        utility.lock = True
        role_class.my_activities["burn"] = 1
        self.active_faction.act_number -= 1
        await role_class.new_activity(ctx, "burn", member)
        utility.lock = False
        # self.active_role = role
        # self.active_faction.operation = operation


class Day(Duel, Search):
    def __init__(self):
        Search.__init__(self)
        Duel.__init__(self)

    def not_night_duel(self):
        if bot.game.night:
            raise InvalidRequest("Nie można robić tego w nocy")
        if self.duel:
            raise InvalidRequest("W czasie pojedynku nie można tego zrobić")
