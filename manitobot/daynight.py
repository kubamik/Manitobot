import inspect
import typing
from collections import deque, defaultdict

from . import utility
from .base_day_states import DayState, States
from .basic_models import NotAGame
from .day_states import InitialState, Voting, ORDER, Duel
from .errors import NoEffect
from .utility import *

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
                if (i in bot.game.role_map and bot.game.role_map[i].work()) or i in bot.game.faction_map:
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


class Day:
    def __init__(self, game: 'game.Game', callback: typing.Callable):
        self.challenges = deque()
        self.duels = 0
        self.reports = defaultdict(list)
        self.game = game
        self.message_edit_callback = callback
        self.state = InitialState(game, self)
        self._prev = None

    async def push_state(self, state: typing.Union[str, States, typing.Type[DayState]], *args, **kwargs):
        curr = self.state.__class__
        curr_order = ORDER.get(curr)  # None only if state is DayState subclass
        if inspect.isclass(state):
            await self._change_state(state, *args, **kwargs)
        elif state == 'vote':
            flw = curr_order[States.VOTED]
            await self._change_state(Voting, *args, previous=curr, following=flw, **kwargs)
        elif state == 'duel':
            await self._change_state(Duel, *args, **kwargs)
        elif isinstance(state, States):
            state = curr_order[state]
            await self._change_state(state, *args, **kwargs)

    async def _change_state(self, state, *args, **kwargs):
        prev = self.state
        self.state = state(self.game, self, *args, **kwargs)
        await prev.cleanup()
        await self.state.async_init()
        await self.state.set_msg_edit_callback(self.message_edit_callback)
        await self.game.panel.add_state_buttons()

    async def custom_voting(self, *args):
        self._prev = self.state
        if self.state:
            await self._change_state(Voting, *args)
        else:
            self.state = Voting(self.game, self, *args)
            await self.state.async_init()
            await self.state.set_msg_edit_callback(self.message_edit_callback)
            await self.game.panel.add_state_buttons()

    async def end_custom_voting(self):
        if self._prev:
            self.state = self._prev
            await self.state.async_init()
            await self.state.set_msg_edit_callback(self.message_edit_callback)
            await self.game.panel.add_state_buttons()
        else:
            await self.message_edit_callback(content='*Trwa noc*', embed=None, view=None)
            self.game.day = None


# noinspection PyMissingConstructor
class PartialDay(Day):
    """Like day, but to use in emergency cases during night (custom voting)"""

    def __init__(self, game, msg):
        self.challenges = deque()
        self.duels = 0
        self.reports = defaultdict(list)
        self.game = game
        self.msg = msg
        self.state = None
        self._prev = None
