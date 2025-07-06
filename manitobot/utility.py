import asyncio
from typing import Optional, List

import discord
from discord.ext import commands
from discord.utils import MISSING

from .bot_basics import bot, command_prefix
from .errors import InvalidRequest
from settings import *
from .interactions.components import Components


def get_guild() -> discord.Guild:
    return bot.get_guild(GUILD_ID)


def get_player_role() -> discord.Role:
    return get_guild().get_role(PLAYER_ROLE_ID)


def get_manitou_role() -> discord.Role:
    return get_guild().get_role(MANITOU_ROLE_ID)


def get_dead_role() -> discord.Role:
    return get_guild().get_role(TRUP_ROLE_ID)


def get_spectator_role() -> discord.Role:
    return get_guild().get_role(SPECTATOR_ROLE_ID)


def get_duel_winner_role() -> discord.Role:
    return get_guild().get_role(DUEL_WINNER_ID)


def get_duel_loser_role() -> discord.Role:
    return get_guild().get_role(DUEL_LOSER_ID)


def get_searched_role() -> discord.Role:
    return get_guild().get_role(SEARCHED_ID)


def get_hanged_role() -> discord.Role:
    return get_guild().get_role(HANGED_ID)


def get_verified_role() -> discord.Role:
    return get_guild().get_role(VERIFIED_ROLE_ID)


def get_newcomer_role() -> discord.Role:
    return get_guild().get_role(NEWCOMER_ROLE_ID)


def get_qualified_manitou_role() -> discord.Role:
    return get_guild().get_role(QUALIFIED_MANITOU_ROLE_ID)


def get_ping_poll_role() -> discord.Role:
    return get_guild().get_role(PING_POLL_ROLE_ID)


def get_ping_game_role() -> discord.Role:
    return get_guild().get_role(PING_GAME_ROLE_ID)


def get_ping_declaration_role() -> discord.Role:
    return get_guild().get_role(PING_DECLARATION_ROLE_ID)


def get_ping_other_games_role() -> discord.Role:
    return get_guild().get_role(PING_OTHER_GAMES_ROLE_ID)


def get_trusted_role() -> discord.Role:
    return get_guild().get_role(TRUSTED_ROLE_ID)


def get_ex_admin_role() -> discord.Role:
    return get_guild().get_role(EX_ADMIN_ROLE_ID)


def get_mod_role() -> discord.Role:
    return get_guild().get_role(MOD_ROLE_ID)


def get_admin_role() -> discord.Role:
    return get_guild().get_role(ADMIN_ROLE_ID)


def get_control_panel() -> discord.TextChannel:
    return get_guild().get_channel(CONTROL_PANEL_ID)


def get_announcements_channel() -> discord.TextChannel:
    return get_guild().get_channel(ANNOUNCEMENTS_CHANNEL_ID)


def get_manitou_notebook() -> discord.TextChannel:
    return get_guild().get_channel(NOTATNIK_MANITOU_CHANNEL_ID)


def get_town_channel() -> discord.TextChannel:
    return get_guild().get_channel(TOWN_CHANNEL_ID)


def get_voice_channel() -> discord.VoiceChannel:
    return get_guild().get_channel(VOICE_CHANNEL_ID)


def get_faction_channel(faction: str) -> discord.TextChannel:
    return get_guild().get_channel(FAC2CHANN_ID[faction])


def get_sets_channel() -> discord.TextChannel:
    return get_guild().get_channel(SET_CHANNEL_ID)


def get_system_messages_channel() -> discord.TextChannel:
    return get_guild().get_channel(SYSTEM_MESSAGES_CHANNEL_ID)


def get_election_backup_channel() -> discord.TextChannel:
    return bot.get_channel(ELECTION_BACKUP_CHANNEL_ID)


def get_member(member_id: int) -> discord.Member:
    return get_guild().get_member(member_id)


def get_nickname(member_id: int) -> str:
    """Deprecated"""
    print('Using deprecated method: `utility.get_nickname`')
    return get_member(member_id).display_name


def on_voice(ctx: commands.Context) -> bool:
    return ctx.author in get_voice_channel().members


def is_trusted_member(member: discord.Member) -> bool:
    return (member in get_trusted_role().members
            or member in get_ex_admin_role().members
            or member in get_mod_role().members
            or member in get_admin_role().members)


def is_manitou(ctx: commands.Context) -> bool:
    return ctx.author in get_manitou_role().members


def is_player(ctx: commands.Context) -> bool:
    return ctx.author in get_player_role().members


def is_qualified_manitou(ctx: commands.Context) -> bool:
    return ctx.author in get_qualified_manitou_role().members


def is_dead(ctx: commands.Context) -> bool:
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
    comm = ['postać', 'żywi', 'bunt', 'pax', 'wyzywam', 'odrzucam', 'przyjmuję', 'zgłaszam', 'cofam', 'vpriv']
    msg = ""
    for c in comm:
        msg += help_format(c)
    return msg


def manitouhelp() -> str:
    comm = ['plant', 'give', 'kill', 'day', 'pend', 'duel', 'cancel', 'vote', 'undo', 'next', 'pens', 'repblok', 'rand',
            'night', 'num']
    msg = ""
    for c in comm:
        msg += help_format(c)
    return msg


async def add_roles(members: List[discord.Member], *roles: discord.Role) -> None:
    tasks = []
    for member in members:
        tasks.append(member.add_roles(*roles, atomic=False))
    await asyncio.gather(*tasks)


async def remove_roles(members: List[discord.Member], *roles: discord.Role) -> None:
    tasks = []
    for member in members:
        tasks.append(member.remove_roles(*roles, atomic=False))
    await asyncio.gather(*tasks)


async def send_to_manitou(content: str = MISSING,
                          embed: discord.Embed = MISSING,
                          file: discord.File = MISSING,
                          view: Components = MISSING) -> None:
    if CONFIG['DM_Manitou']:
        for member in get_manitou_role().members:
            await member.send(content, embed=embed, file=file, view=view)
    else:
        await get_manitou_notebook().send(content, embed=embed, file=file, view=view)


async def send_game_channels(content: str) -> None:
    tasks = []
    for channel in get_guild().text_channels:
        if channel.category_id == FRAKCJE_CATEGORY_ID or channel.category_id == NIEPUBLICZNE_CATEGORY_ID:
            tasks.append(channel.send(content))
    await asyncio.gather(*tasks)


def cleared_nickname(nick: str) -> str:
    """Perform nickname clearing on given nickname"""
    if nick.startswith(('+', '!', '*')):
        nick = nick[1:]
    if '#' in nick:
        nick = nick.replace('#', '')
    if all(nick.rpartition('(')):
        nick = nick.rpartition('(')[0]
    return nick


async def clear_nickname(member: discord.Member) -> None:
    old_nickname = member.display_name
    nick = cleared_nickname(old_nickname)
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