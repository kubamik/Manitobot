from collections import OrderedDict
import inspect

from converters import converter
from f_database import *
from utility import *
from activities import Activity


class Faction(Activity):
    def __init__(self, name):
        self.name = name
        self.roles = OrderedDict()
        self.leader = None
        self.channel: discord.TextChannel = get_faction_channel(name)
        self.actions = f_actions[name]
        self.operation = None
        self.act_number = -1
        self.data = 0
        self.awake_number = 0
        for role in factions_roles[name]:
            try:
                obj = bot.game.role_map[role]
            except KeyError:
                pass
            else:
                self.roles[role] = obj
                bot.game.role_map[role].faction = self

    async def wake_up(self):
        overwrites = self.channel.overwrites
        for role in self.roles.values():
            if not role.player.sleeped and role.alive():
                overwrites[role.player.member] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True)
        await self.channel.edit(overwrites=overwrites)

    async def put_to_sleep(self):
        await self.channel.edit(sync_permissions=True)

    def what_next(self):
        try:
            for i in self.actions[self.act_number + 1:]:
                if len(i) > 1:
                    raise IndexError
                if i[0] in self.roles and self.roles[i[0]].work():
                    return ' ➡️{}'.format(i[0])
            return ' ➡️{}'.format(self.name + " - koniec")
        except IndexError:
            return ''

    async def night_start(self):
        self.leader = None
        self.act_number = 0
        self.awake_number = 0
        awake = True
        counter = 0
        for role in self.roles.values():
            if not role.player.sleeped and role.player.member not in get_dead_role().members:
                counter += 1
                if self.leader is None:
                    self.leader = role.player
                try:
                    await self.channel.set_permissions(role.player.member, read_messages=True, send_messages=True,
                                                       add_reactions=True)
                except discord.errors.Forbidden:
                    pass
                await role.player.member.send(
                    "Rozpoczynamy rundę twojej frakcji. Wejdź na <#{}>".format(self.channel.id))
            elif role.player.sleeped or (role.player.member in get_dead_role().members and not role.revealed):
                awake = False
        if not counter and not awake:
            if not self.f_has():
                bot.game.nights[-1].output += f_coms[self.name]
            bot.game.nights[-1].active_faction = self
            bot.game.nights[-1].active_role = None
            raise InvalidRequest(
                "{} nie budzą się, bo nie mogą lub są martwi, ale nikt o tym nie wie".format(self.name))
        elif not counter:
            raise InvalidRequest()
        self.awake_number = counter
        try:
            for f in get_activity(self, self.name + " start"):
                if inspect.iscoroutinefunction(f):
                    await f()
                else:
                    f()
        except (InvalidRequest, KeyError):
            pass
        await self.channel.send(
            "Rozpoczynamy rundę frakcji. Liderem dzisiejszej nocy jest {}.\n{}".format(self.leader.role,
                                                                                       "Macie posążek" if self.f_has() else "Nie macie posążka"))
        bot.game.nights[-1].active_faction = self
        bot.game.nights[-1].active_role = self

    async def faction_next(self):
        if self.operation == "hold" and bot.game.statue.holder == None:
            raise InvalidRequest("Najpierw potrzebne jest ustalenie posiadacza posążka (dla Manitou `&give NICK`)")
        try:
            self.operation = self.actions[self.act_number][0]
        except IndexError:
            await self.channel.send("Idziecie spać")
            bot.game.nights[-1].active_faction = None
            bot.game.nights[-1].active_role = None
            for role in self.roles.values():
                try:
                    await self.channel.set_permissions(role.player.member, overwrite=None)
                except discord.errors.Forbidden:
                    pass
            raise InvalidRequest("{} idą spać".format(self.name))
        self.act_number += 1
        try:
            statue = self.actions[self.act_number - 1][1]
            if not self.awake_number:
                await bot.game.nights[-1].night_next()
                return
            if statue is None:
                statue = self.f_has()
            if (self.operation == "hold" or bot.game.day > 0) and statue == self.f_has():
                com = f_coms[self.operation]
                await self.channel.send(com)
                return f_coms_manit[self.operation].format(self.name)
            else:
                await bot.game.nights[-1].night_next()
                return
        except IndexError:
            try:
                mess = await self.roles[self.operation].new_night_start()
                await self.channel.send("**{}:**".format(self.operation))
                await self.channel.send(mess)
                return self.operation + " otrzymał(-a) instrukcje"
            except KeyError:
                raise InvalidRequest()

    async def new_activity(self, ctx, operation, member=None):  # working in progress
        if ctx.author != self.leader.member:
            raise InvalidRequest("Tego polecenia może użyć tylko lider frakcji")
        if operation != self.operation:
            raise InvalidRequest("Nie możesz teraz użyć tego polecenia")
        self.member = member
        if not member is None:
            member = await converter(ctx, member)
            if member not in get_guild().members:
                raise InvalidRequest("Nie ma takiej osoby")
            if member not in get_player_role().members or member in get_dead_role().members:
                raise InvalidRequest("Ta osoba nie gra lub nie żyje")
            self.member = bot.game.player_map[member]
        output = ""
        try:
            for f in get_activity(self, operation):
                if inspect.iscoroutinefunction(f):
                    ret = await f()
                else:
                    ret = f()
                if not ret is None:
                    output += ret
        except InvalidRequest as err:
            raise InvalidRequest(err.reason)
        self.operation = None
        if output:
            await ctx.send(output)
        await ctx.active_msg.add_reaction('✅')
        c = f_coms_manit_end[operation].format(self.name, self.member.member.display_name)
        await send_to_manitou(c)
        await get_manitou_notebook().send(c)
        try:
            self.actions[self.act_number][1]
            await bot.game.nights[-1].night_next()
        except IndexError:
            pass

    async def on_die(self, role):
        try:
            if bot.game.nights[-1].active_faction == self.faction:
                if self.faction.leader == self.player:
                    for role in self.faction.roles.values():
                        if role.player.member not in get_dead_role() and not role.player.sleeped:
                            self.faction.leader = role.player
                            await self.faction.channel.send(
                                "Ginie {}\nNowym liderem zostaje {}".format(self.player.member.display_name,
                                                                            self.faction.leader.role))
                            break
                    else:
                        pass  # Uśpienie frakcji
                await self.faction.channel.set_permissions(self.player.member, overwrite=None)
        except (KeyError, AttributeError, discord.errors.Forbidden):
            pass

    async def make_leader(self, overwrite):
        leader = None
        for role in self.faction.roles.values():
            if role.player.member not in get_dead_role() and not role.player.sleeped:
                leader = role.player
