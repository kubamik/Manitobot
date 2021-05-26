from typing import Optional

import discord
from discord.ext import commands

from .errors import MemberNotPlaying
from .utility import get_player_role, get_dead_role, get_member, get_guild


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

    @classmethod
    def nickname_fit(cls, nick: str) -> Optional[discord.Member]:
        nick = cls.transform_nickname(nick)
        for player in set(get_player_role().members + get_dead_role().members):
            if cls.transform_nickname(player.display_name) == nick:
                return player
        return None

    async def convert(self, ctx: commands.Context, name: str) -> discord.Member:
        member = self.nickname_fit(name)
        if member is None:
            try:
                member = await super().convert(ctx, name)
            except commands.BadArgument:
                raise commands.MemberNotFound(name)
            else:
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
