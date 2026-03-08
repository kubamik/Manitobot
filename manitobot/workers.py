import asyncio
import itertools
from typing import Any, Optional

import discord


class Workers:

    async def edit_member(self, member: discord.Member,
                          nick: Optional[str] = None,
                          mute: Optional[bool] = None,
                          roles_to_add: Optional[list[discord.Role]] = None,
                          roles_to_remove: Optional[list[discord.Role]] = None,
                          ):
        payload: dict[str, Any] = {}
        roles_to_add = roles_to_add or []
        roles_to_remove = roles_to_remove or []

        if nick is not None and member.display_name != nick:
            payload['nick'] = nick
        if roles_to_add or roles_to_remove:
            to_add = set(roles_to_add)
            to_remove = set(roles_to_remove)
            current = set(member.roles)
            if not to_add.issubset(current) or not to_remove.isdisjoint(current):
                payload['roles'] = [role.id for role in (current - to_remove) | to_add]
        if mute is not None and member.voice and member.voice.mute != mute:
            payload['mute'] = mute

        if payload:
            worker = next(self.workers_queue)
            try:
                await worker.http.edit_member(member.guild.id, member.id, **payload)
            except discord.Forbidden:
                await self._handle_forbidden(member, payload)
            except discord.HTTPException as e:
                if e.status == 400 and e.code == 40032:  # Member not connected to voice channel
                    await self._handle_member_not_connected(member, payload)
                else:
                    raise
    def __init__(self, manitobot_bot: discord.Client, tokens: Optional[list[str]] = None):
        self.tokens = tokens or []
        self.bots = [discord.Client(intents=discord.Intents.default()) for _ in self.tokens]
        if self.bots:
            self.workers_queue = itertools.cycle(self.bots)
        else:
            self.workers_queue = itertools.repeat(manitobot_bot)

    async def login_bots(self):
        for bot, token in zip(self.bots, self.tokens):
            await bot.login(token)

    async def mute_members(self, members: list[discord.Member]):
        await asyncio.gather(*self._prepare_muting_tasks(members, True), return_exceptions=True)

    async def unmute_members(self, members: list[discord.Member]):
        await asyncio.gather(*self._prepare_muting_tasks(members, False), return_exceptions=True)

    async def _handle_forbidden(self, member: discord.Member, payload: dict[str, Any]):
        # Assuming that the most likely reason for Forbidden is that the bot is below the target member
        # in the role hierarchy, so we omit the nickname change
        if 'nick' in payload:
            await member.send('Zmień swój nick na `{}`'.format(payload['nick']))
            payload.pop('nick', None)
            if payload:
                worker = next(self.workers_queue)
                await worker.http.edit_member(member.guild.id, member.id, **payload)

    async def _handle_member_not_connected(self, member: discord.Member, payload: dict[str, Any]):
        if 'mute' in payload:
            payload.pop('mute')
            if payload:
                worker = next(self.workers_queue)
                await worker.http.edit_member(member.guild.id, member.id, **payload)

    def _prepare_muting_tasks(self, members: list[discord.Member], mute: bool):
        tasks = []
        for member, bot in zip(members, self.workers_queue):
            if member.voice is not None and member.voice.mute != mute:
                tasks.append(bot.http.edit_member(member.guild.id, member.id, mute=mute))
        return tasks
    