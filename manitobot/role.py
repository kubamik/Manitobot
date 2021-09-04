import inspect

import typing

from . import permissions
from .activities import Activity
from .bot_basics import bot
from .converters import converter
from .night_comunicates import operation_send, new_night_com
from .player import Player
from .utility import *


class Role(Activity):
    def __init__(self, name, player):
        self.roled_members = [None]
        self.name = name
        self.player: Player = player
        self.revealed = False
        self.die_reason = None
        self.faction = None
        self.worked = True
        self.member: typing.Optional[Player] = None
        try:
            self.ability_start = permissions.role_activities[name][0]
            self.count = permissions.role_activities[name][1]
            self.my_activities = permissions.role_activities[name][2].copy()
        except KeyError:
            self.ability_start = None
            self.count = None
            self.my_activities = {}

    def can_use(self, ability: str):
        return ability in self.my_activities and self.my_activities[ability] != 0

    async def new_night_start(self):
        output = ""
        if "start" in self.my_activities:
            for f in permissions.get_activity(self.my_activities["start"], self):
                if inspect.iscoroutinefunction(f):
                    await f()
                else:
                    f()
        if self.player.member in get_dead_role().members and not self.revealed:
            self.refusal()
            raise InvalidRequest("{} nie żyje i nie jest ujawniony".format(self.name))
        if self.player.member in get_dead_role().members:
            raise InvalidRequest()
        if bot.game.day_num < self.ability_start:
            raise InvalidRequest()
        if bot.game.day_num != 0 and self.ability_start == -1:
            raise InvalidRequest()
        if self.player.sleeped:
            self.roled_members.append(None)
            self.refusal()
            raise InvalidRequest(
                "{} nie budzi się tej nocy, bo jest zamknięty(-a) lub upity(-a)".format(self.name.replace('_', ' ')))
        if self.count == 0:
            self.refusal()
            raise InvalidRequest("{} wykorzystał(-a) już swoje zdolności".format(self.name.replace('_', ' ')))
        bot.game.nights[-1].active_role = self
        # self.player.active = True
        com = new_night_com[self.name]
        for c, f in com:
            output += c.format(self.my_activities[f])
        return output

    async def new_activity(self, ctx, operation, member=None):
        # works in progress
        if operation not in self.my_activities:
            raise InvalidRequest("Nie możesz użyć tego polecenia", 1)
        if self.my_activities[operation] == 0:
            raise InvalidRequest("Nie możesz więcej użyć tej zdolności", 0)
        if not member is None:
            member = await converter(ctx, member)
            if member not in get_guild().members:
                raise InvalidRequest("Nie ma takiej osoby")
            if member not in get_player_role().members or member in get_dead_role().members:
                raise InvalidRequest("Ta osoba nie gra lub nie żyje")
            self.member = bot.game.player_map[member]
        self.operation = operation
        output = ""
        try:
            for f in permissions.get_activity(operation, self):
                if inspect.iscoroutinefunction(f):
                    ret = await f()
                else:
                    ret = f()
                if ret is not None:
                    output += ret
        except InvalidRequest as err:
            raise InvalidRequest(err.msg)
        self.my_activities[operation] -= 1
        # if self.my_activities[operation]>-1:
        # self.count -= 1
        if output:
            await ctx.send(output)
        await operation_send(operation, self.player.member, self.name, member)
        self.roled_members.append(self.member)
        await ctx.message.add_reaction('✅')

    async def die(self, reason=None):
        member = self.player.member

        # reset player
        await member.remove_roles(get_player_role(), get_searched_role(), get_hanged_role(), get_duel_loser_role(),
                                  get_duel_winner_role())
        await member.add_roles(get_dead_role())
        nickname = member.display_name
        await get_town_channel().send('Ginie **{}**'.format(nickname))

        # actions in abilities
        self.die_reason = reason
        try:
            actions = self.my_activities['die']
            for f in permissions.get_activity(actions, self):
                if inspect.iscoroutinefunction(f):
                    await f()
                else:
                    f()
        except (KeyError, InvalidRequest):
            pass

        # reset player
        if not any([bot.game.night_now, self.revealed, not bot.game.reveal_dead]):
            await self.reveal(dead=True)
        elif not nickname.startswith('+'):
            try:
                await member.edit(nick='+' + nickname)
            except discord.Forbidden:
                pass

        await bot.game.on_die(reason, self.player)

    @property
    def alive(self) -> bool:
        return self.player.member not in get_dead_role().members

    @property
    def qualified_name(self) -> str:
        return self.name.replace('_', ' ')

    def work(self):
        if bot.game.day_num < self.ability_start:
            return False
        if bot.game.day_num != 0 and self.ability_start == -1:
            return False
        if self.player.member in get_dead_role().members and self.revealed:
            return False
        return True

    def can_use(self, *abilities):
        for a in abilities:
            if a in self.my_activities:
                return a
        return abilities[0]
