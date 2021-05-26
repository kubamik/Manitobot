import asyncio
from typing import Optional, List

import discord
from discord.ext import commands

from .bot_basics import bot, command_prefix
from .errors import InvalidRequest
from settings import *


def get_guild() -> discord.Guild:
    return bot.get_guild(GUILD_ID)


def get_player_role() -> discord.Role:
    return get_guild().get_role(PLAYER_ROLE_ID)


def get_manitou_role() -> discord.Role:
    return get_guild().get_role(MANITOU_ROLE_ID)


def get_other_manitou_role() -> discord.Role:
    return get_guild().get_role(OTHER_MANITOU_ROLE_ID)


def get_dead_role() -> discord.Role:
    return get_guild().get_role(TRUP_ROLE_ID)


def get_spectator_role() -> discord.Role:
    return get_guild().get_role(SPECTATOR_ROLE_ID)


def get_admin_role() -> discord.Role:
    return get_guild().get_role(ADMIN_ROLE_ID)


def get_duel_winner_role() -> discord.Role:
    return get_guild().get_role(DUEL_WINNER_ID)


def get_duel_loser_role() -> discord.Role:
    return get_guild().get_role(DUEL_LOSER_ID)


def get_searched_role() -> discord.Role:
    return get_guild().get_role(SEARCHED_ID)


def get_hanged_role() -> discord.Role:
    return get_guild().get_role(HANGED_ID)


def get_newcommer_role() -> discord.Role:
    return get_guild().get_role(NEWCOMMER_ID)


def get_ping_reminder_role() -> discord.Role:
    return get_guild().get_role(PING_REMINDER_ID)


def get_ping_game_role() -> discord.Role:
    return get_guild().get_role(PING_GAME_ID)


def get_control_panel() -> discord.TextChannel:
    return get_guild().get_channel(CONTROL_PANEL_ID)


def get_ankietawka_channel() -> discord.TextChannel:
    return get_guild().get_channel(ANKIETAWKA_CHANNEL_ID)


def get_manitou_notebook() -> discord.TextChannel:
    return get_guild().get_channel(NOTATNIK_MANITOU_CHANNEL_ID)


def get_town_channel() -> discord.TextChannel:
    return get_guild().get_channel(TOWN_CHANNEL_ID)


def get_voice_channel() -> discord.VoiceChannel:
    return get_guild().get_channel(VOICE_CHANNEL_ID)


def get_faction_channel(faction: str) -> discord.TextChannel:
    return get_guild().get_channel(FAC2CHANN_ID[faction])


def get_member(member_id: int) -> discord.Member:
    return get_guild().get_member(member_id)


def get_nickname(member_id: int) -> str:
    """Deprecated"""
    print('Using deprecated method: `utility.get_nickname`')
    return get_member(member_id).display_name


def on_voice(ctx: commands.Context) -> bool:
    return ctx.author in get_voice_channel().members


def czy_manitou(ctx: commands.Context) -> bool:
    return ctx.author in get_manitou_role().members


def czy_gram(ctx: commands.Context) -> bool:
    return ctx.author in get_player_role().members


def czy_trup(ctx: commands.Context) -> bool:
    return ctx.author in get_dead_role().members


def help_format(command: str) -> str:
    try:
        c = bot.get_command(command)
        txt = ""
        txt += "**{pref}{name}**\n"
        if len(c.aliases) > 0:
            txt += "*{pref}" + "*\n*{pref}".join(c.aliases) + "*\n"
        txt += c.help.rpartition('Ⓜ')[2].rpartition('/')[2]
        return txt.format(pref=command_prefix, name=c.name) + '\n\n'
    except AttributeError:
        return ''


def playerhelp() -> str:
    comm = ['postać', 'żywi', 'riot', 'pax', 'wyzywam', 'odrzucam', 'przyjmuję', 'zgłaszam', 'cofam']
    msg = ""
    for c in comm:
        msg += help_format(c)
    return msg


def manitouhelp() -> str:
    comm = ['plant', 'give', 'kill', 'day', 'pend', 'br', 'vdl', 'vend', 'dnd', 'abend', 'rpt', 'repblok', 'vsch',
            'revote', 'snd', 'vhif', 'vhg', 'hrnd', 'hnd', 'night', 'num']
    msg = ""
    for c in comm:
        msg += help_format(c)
    return msg


async def add_roles(members: List[discord.Member], *roles: discord.Role) -> None:
    tasks = []
    for member in members:
        tasks.append(member.add_roles(*roles))
    await asyncio.gather(*tasks, return_exceptions=True)


async def remove_roles(members: List[discord.Member], *roles: discord.Role) -> None:
    tasks = []
    for member in members:
        tasks.append(member.remove_roles(*roles))
    await asyncio.gather(*tasks, return_exceptions=True)


async def send_to_manitou(content: Optional[str] = None,
                          embed: Optional[discord.Embed] = None,
                          file: Optional[discord.File] = None) -> None:
    if CONFIG['DM_Manitou']:
        for member in get_manitou_role().members:
            await member.send(content, embed=embed, file=file)
    else:
        await get_manitou_notebook().send(content, embed=embed, file=file)


async def send_game_channels(content: str) -> None:
    tasks = []
    for channel in get_guild().text_channels:
        if channel.category_id == FRAKCJE_CATEGORY_ID or channel.category_id == NIEPUBLICZNE_CATEGORY_ID:
            tasks.append(channel.send(content))
    await asyncio.gather(*tasks, return_exceptions=True)


async def clear_nickname(member: discord.Member) -> None:
    old_nickname = member.display_name
    nick = old_nickname
    if nick.startswith(('+', '!')):
        nick = nick[1:]
    if nick.endswith('#'):
        nick = nick[:-1]
    if all(nick.rpartition('(')):
        nick = nick.rpartition('(')[0]
    if nick != old_nickname:
        try:
            await member.edit(nick=nick)
        except discord.errors.Forbidden:
            pass


def playing(gracz=-1, *, author=-1):
    """Deprecated
    """
    print('Using deprecated function: `utility.playing`')
    if gracz != -1 and (gracz is None or gracz not in get_guild().members):
        raise InvalidRequest("Nie ma takiego gracza")
    if gracz != -1 and (gracz in get_dead_role().members):
        raise InvalidRequest("Ten gracz nie żyje")
    if gracz != -1 and (gracz not in get_player_role().members):
        raise InvalidRequest("Ta osoba nie gra")
    if author != -1 and author in get_dead_role().members:
        raise InvalidRequest("Jesteś martwy")
    if author != -1 and author not in get_player_role().members:
        raise InvalidRequest("Nie grasz")


def plused(before: discord.Member, after: discord.Member) -> bool:
    return before.display_name[0] != after.display_name[0] and after.display_name.startswith('+')
