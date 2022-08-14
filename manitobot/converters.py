from datetime import date
from typing import Optional, List

import discord
from discord.ext import commands

from .errors import MemberNotPlaying
from .utility import get_player_role, get_member, get_guild


class MyFlagConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        if arg.startswith('-'):
            return arg[2:] if arg.startswith('--') else arg[1:]
        raise commands.BadArgument('Invalid flag')


class MyMemberConverter(commands.MemberConverter):
    """Converter from string with name or mention to discord.Member
    """
    def __init__(self, *, player_only: bool = True):
        self.player_only = player_only
        super().__init__()

    @staticmethod
    def transform_nickname(nick: str) -> str:
        if nick.startswith(('+', '!')):
            nick = nick[1:]
        if nick.endswith('#'):
            nick = nick[:-1]
        if all(nick.rpartition('(')):
            nick = nick.rpartition('(')[0]
        return nick.lower()

    def nickname_fit(self, nick: str) -> Optional[discord.Member]:
        nick = self.transform_nickname(nick)
        members = get_guild().members if not self.player_only else get_player_role().members
        member = None
        for player in members:
            player_nick = self.transform_nickname(player.display_name)
            if player_nick == nick:
                return player
            elif nick in player_nick:
                if len(nick) * 3 < len(player_nick) * 2 or member:
                    member = ...
                else:
                    member = player
        if member is Ellipsis or member is None:
            return None
        return member

    async def convert(self, ctx: commands.Context, name: str) -> discord.Member:
        member = self.nickname_fit(name)
        if member is None:
            try:
                member = await super().convert(ctx, name)
            except commands.BadArgument:
                raise commands.MemberNotFound(name)
            if member not in get_guild().members:
                member = get_member(member.id)
            if member is None:
                raise commands.MemberNotFound(name)
        if self.player_only and member not in get_player_role().members:
            raise MemberNotPlaying('This person is not playing.')
        return member


async def converter(ctx: commands.Context, name: str) -> Optional[discord.Member]:
    """Deprecated"""
    try:
        return await MyMemberConverter(player_only=False).convert(ctx, name)
    except commands.MemberNotFound:
        return None


class MyDateConverter(commands.Converter):
    delimiters: List[str] = ['-', '_', '/', '.']

    async def convert(self, ctx: commands.Context, argument: str) -> date:
        parsed = ['']
        for char in argument:
            if char not in self.delimiters:
                parsed[-1] += char
            elif parsed[-1]:
                parsed.append('')  # add new empty element if not present

        if len(parsed) == 3:
            if len(parsed[0]) == 4:  # full year on first position
                p = parsed[::-1]
            elif len(parsed[2]) == 4:  # full year on last position
                p = parsed
            else:  # two digit year on last position
                p = parsed
                p[-1] = '20' + p[-1]
        elif len(parsed) == 2:
            p = parsed + [date.today().year]  # later we convert all to int, so we can add int (year)
        else:
            raise commands.BadArgument('Wrong date format')

        try:
            d, m, y = map(int, p)
        except ValueError as e:
            raise commands.BadArgument from e
        return date(y, m, d)


