import asyncio
from collections import defaultdict
from typing import Optional, Dict, List, Set, Tuple, Mapping

import discord

from . import postacie
from .controller import Controller
from .daynight import Day, Night
from .errors import GameEnd
from .faction import Faction
from .player import Player
from .postacie import get_faction, give_faction
from .role import Role
from .statue import Statue
from .utility import get_dead_role, get_player_role
from .vote import Vote


class Game:
    def __init__(self):
        self.message: Optional[discord.Message] = None
        self.statue: Statue = Statue()
        self.player_map: Dict[discord.Member, Player] = {}
        self.role_map: Dict[str, Role] = {}
        self.faction_map: Dict[str, Faction] = {}
        self.roles: List[str] = []
        self.night: bool = True
        self.day: int = 0
        self.days: List[Optional[Day]] = [None]
        self.nights: List[Optional[Night]] = [None]
        self.duels: int = 2
        self.searches: int = 2
        self.bandit_night: int = 3
        self.bandit_morning: bool = True
        self.rioters: Set[discord.Member] = set()
        self.new_night()
        self.reveal_dead: bool = True
        self.voting: Optional[Vote] = None
        self.stats: Mapping[str, int] = defaultdict(int)
        self.controller: Controller = Controller()

    def calculate_stats(self) -> None:
        self.stats = defaultdict(int)
        for role in self.role_map.values():
            if role.alive:
                self.stats[postacie.give_faction(role.name)] += 1

    async def new_day(self) -> None:
        self.days.append(Day())
        self.day += 1
        self.night = False
        tasks = []
        self.town_win()
        for player in self.player_map.values():
            tasks.append(player.new_day())
        for member in get_dead_role().members:
            if not self.player_map[member].role_class.revealed:
                tasks.append(self.player_map[member].role_class.reveal())
        await asyncio.gather(*tasks, return_exceptions=True)
        self.calculate_stats()
        self.inqui_win()
        self.morning_bandits_win()

    def new_night(self) -> None:
        self.nights.append(Night())
        self.night = True
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
        self.player_map[member] = Player(member, role)
        self.role_map[role] = Role(role, self.player_map[member])
        self.player_map[member].role_class = self.role_map[role]

    async def end(self) -> None:
        tasks = []
        for player in self.player_map.values():
            if not player.role_class.revealed:
                tasks.append(player.role_class.reveal())
        tasks.append(self.message.unpin())
        await asyncio.gather(*tasks, return_exceptions=True)

    async def winning(self, reason: str, faction: str):  # TODO: Chamge winning mechanizm
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
        if self.day == self.bandit_night and not self.bandit_morning and self.statue.faction_holder == 'Bandyci' \
                and self.statue.holder:
            raise GameEnd('Bandyci odpływają z posążkiem', 'Bandyci')

    def morning_bandits_win(self) -> None:
        if self.statue.faction_holder == 'Bandyci' and self.statue.holder and (
                self.day > self.bandit_night or (self.bandit_morning and self.day == self.bandit_night)):
            raise GameEnd('Bandyci odpływają z posążkiem', 'Bandyci')

    @property
    def voting_in_progress(self) -> bool:
        return self.voting is not None

    async def on_die(self, reason, player) -> None:
        await self.controller.die(player.member)
        self.calculate_stats()
        if reason == 'herbs':
            self.statue.day_search(player.member)
        self.indian_win()
        if not self.night:
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
