import asyncio
from collections import defaultdict
from typing import Optional, Dict, List, Set, Tuple, Mapping

import discord

from . import postacie
from .bot_basics import bot
from .control_panel import ControlPanel
from .daynight import Day, Night
from .errors import GameEnd
from .faction import Faction
from .player import Player
from .postacie import get_faction, give_faction
from .role import Role
from .statue import Statue
from .utility import get_dead_role, get_player_role, get_town_channel


class Game:
    def __init__(self):
        self.message: Optional[discord.Message] = None
        self.statue: Statue = Statue()
        self.player_map: Dict[discord.Member, Player] = {}
        self.role_map: Dict[str, Role] = {}
        self.faction_map: Dict[str, Faction] = {}
        self.roles: List[str] = []
        self.day_num: int = 0
        self.nights: List[Optional[Night]] = [None]
        self.day = None
        self.night = None
        self.duels: int = 2
        self.searches: int = 2
        self.bandit_night: int = 3
        self.bandit_morning: bool = True
        self.rioters: Set[discord.Member] = set()
        self.reveal_dead: bool = True
        self.stats: Mapping[str, int] = defaultdict(int)
        self.panel: ControlPanel = bot.get_cog('Panel Sterowania')

    def calculate_stats(self) -> None:
        self.stats = defaultdict(int)
        for role in self.role_map.values():
            if role.alive:
                self.stats[postacie.give_faction(role.name)] += 1

    async def new_day(self) -> None:
        day = Day(self, self.panel.state_msg)
        self.day = day
        self.night = None
        self.day_num += 1
        tasks = []
        for player in self.player_map.values():
            tasks.append(player.new_day())
        try:
            self.town_win()
        except GameEnd:
            for member in get_dead_role().members:
                if not self.player_map[member].role_class.revealed:
                    tasks.append(self.player_map[member].role_class.reveal(verbose=False))
            raise
        else:
            for member in get_dead_role().members:
                if not self.player_map[member].role_class.revealed:
                    tasks.append(self.player_map[member].role_class.reveal())
        finally:
            tasks.append(self.panel.morning_reset())
            await asyncio.gather(*tasks)
            await get_town_channel().send(f'=\nDzień {self.day_num}')
            await get_town_channel().edit(sync_permissions=True)
        self.calculate_stats()
        self.inqui_win()
        self.morning_bandits_win()

    async def new_night(self) -> None:
        self.night = Night()
        if self.day:
            await self.day.state.cleanup()
        self.day = None
        self.nights.append(self.night)
        await self.panel.evening()
        await get_town_channel().set_permissions(get_player_role(), send_messages=False)
        self.evening_bandits_win()

    def make_factions(self, roles, _) -> None:
        for role in roles:
            faction = get_faction(role)
            if faction != 'Miasto' and faction not in self.faction_map:
                try:
                    self.faction_map[faction] = Faction(faction)
                except KeyError:
                    pass

    def add_pair(self, member: discord.Member, role: str) -> None:
        role = '_'.join((r.capitalize() for r in role.split('_')))
        self.player_map[member] = Player(member, role)
        self.role_map[role] = Role(role, self.player_map[member])
        self.player_map[member].role_class = self.role_map[role]

    async def end(self) -> None:
        tasks = []
        for player in self.player_map.values():
            if not player.role_class.revealed:
                tasks.append(player.role_class.reveal())
        tasks.append(self.message.unpin())
        await asyncio.gather(*tasks)

    async def winning(self, reason: str, faction: str):  # TODO: Change winning mechanism
        c = ':scroll:{}:scroll:\n**WYGRALIŚCIE!**'.format(reason)
        for member, player in self.player_map.items():
            if give_faction(player.role) == faction:
                await member.send(c)

    def swap(self, first: discord.Member, second: discord.Member) -> Tuple[str, str]:
        frole = self.player_map[first].role
        srole = self.player_map[second].role
        self.player_map[first].role = srole
        self.player_map[second].role = frole
        self.role_map[srole].player = self.player_map[first]
        self.role_map[frole].player = self.player_map[second]
        self.player_map[second].role_class = self.role_map[frole]
        self.player_map[first].role_class = self.role_map[srole]
        return srole, frole

    def replace_player(self, first, second):
        player = self.player_map[first]
        self.player_map[second] = player
        self.player_map.pop(first)
        player.member = second
        return player.role

    def inqui_win(self) -> None:
        g = self.stats.get
        if not any([g('Indianie'), g('Ufoki'), g('Janosik'), g('Lusterko'), g('Murzyni'), g('Bogowie'),
                    not g('Inkwizycja')]):
            raise GameEnd('Wszyscy heretycy nie żyją', 'Inkwizycja')

    def inqui_alone_win(self) -> None:
        if self.stats['Inkwizycja'] and self.stats['Inkwizycja'] == len(get_player_role().members):
            raise GameEnd('Zostali sami Inkwizytorzy', 'Inkiwzycja')

    def indian_win(self) -> None:
        if self.stats['Indianie'] == len(get_player_role().members):
            raise GameEnd('Zostali sami Indianie', 'Indianie')

    def town_win(self) -> None:
        if self.statue.faction_holder == 'Miasto' and not self.statue.planted:
            role = self.player_map[self.statue.holder].role
            raise GameEnd('{} posiada posążek o poranku'.format(role.replace('_', ' ')), 'Miasto')

    def evening_bandits_win(self) -> None:
        if self.day_num == self.bandit_night and not self.bandit_morning and self.statue.faction_holder == 'Bandyci' \
                and self.statue.holder:
            raise GameEnd('Bandyci odpływają z posążkiem', 'Bandyci')

    def morning_bandits_win(self) -> None:
        if self.statue.faction_holder == 'Bandyci' and self.statue.holder and (
                self.day_num > self.bandit_night or (self.bandit_morning and self.day_num == self.bandit_night)):
            raise GameEnd('Bandyci odpływają z posążkiem', 'Bandyci')

    @property
    def voting_in_progress(self) -> bool:
        return self.day is not None and hasattr(self.day.state, 'register_vote')

    @property
    def night_now(self) -> bool:
        return self.night is not None

    async def on_die(self, reason, player) -> None:
        await self.panel.die(player.member)
        self.calculate_stats()
        if self.day:
            await self.day.state.on_die(player.member, reason)
        if reason == 'herbs':  # TODO: Discuss if only herbs
            self.statue.day_search(player.member)
        self.indian_win()
        if not self.night_now:
            self.inqui_win()
            if reason != 'herbs':
                self.statue.day_search(player.member)
        else:
            self.inqui_alone_win()

    @property
    def bandit_morn(self) -> Optional[int]:
        return self.bandit_night if self.bandit_morning else None

    @bandit_morn.setter
    def bandit_morn(self, n: int) -> None:
        self.bandit_night = n
        self.bandit_morning = True

    @property
    def bandit_even(self) -> Optional[int]:
        return self.bandit_night if not self.bandit_morning else None

    @bandit_even.setter
    def bandit_even(self, n: int) -> None:
        self.bandit_night = n
        self.bandit_morning = False

    @staticmethod
    def print_list(roles, _):
        return postacie.print_list(roles)
