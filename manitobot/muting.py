import asyncio
import itertools

import discord


class Muting:
    tokens: list[str]
    bots: list[discord.Client]
    
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.bots = [discord.Client(intents=discord.Intents.default()) for _ in tokens]
        
    async def login_bots(self):
        for bot, token in zip(self.bots, self.tokens):
            await bot.login(token)
    
    async def mute_members(self, members: list[discord.Member]):
        await asyncio.gather(*self._prepare_muting_tasks(members, True), return_exceptions=True)
        
    async def unmute_members(self, members: list[discord.Member]):
        await asyncio.gather(*self._prepare_muting_tasks(members, False), return_exceptions=True)
            
    def _prepare_muting_tasks(self, members: list[discord.Member], mute: bool):
        tasks = []
        for member, bot in zip(members, itertools.cycle(self.bots)):
            if member.voice is not None and member.voice.mute != mute:
                tasks.append(bot.http.edit_member(member.guild.id, member.id, mute=mute))
        return tasks
    