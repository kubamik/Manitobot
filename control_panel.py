import asyncio
from typing import Dict, Optional

import discord
from discord.ext import commands

from game import Game
from settings import FAC2EMOJI
from utility import get_control_panel, get_manitou_role


class ControlPanel(commands.Cog, name='Panel Sterowania'):
    """Class which controls Manitou Control Panel"""

    def __init__(self, bot):
        self.bot = bot
        self.message: Optional[discord.Message] = None
        self.msg2mbr: Optional[Dict[discord.Message, discord.Member]] = None
        self.mem2mess: Optional[Dict[discord.Member, discord.Message]] = None
        self.game: Game = self.bot.game
        self.emoji2fac: Dict[int, str] = {}

    async def prepare_panel(self):
        await get_control_panel().purge()
        base = get_control_panel().send
        players = sorted(self.game.player_map.keys(), key=lambda mbr: mbr.display_name)
        messages = []
        for player in players:
            messages.append(await base(player.display_name))
        messages.append(await base("Aktywna frakcja"))
        self.message = messages[-1]
        self.msg2mbr = dict(zip(messages[:-1], players))
        self.mem2mess = dict(zip(players, messages[:-1]))
        tasks = []
        for m in messages[:-1]:
            tasks.append(m.add_reaction('😴'))
        for fac, id_ in FAC2EMOJI.items():
            if fac in self.bot.game.faction_map:
                tasks.append(self.message.add_reaction(self.bot.get_emoji(id_)))
                self.emoji2fac[id_] = fac
        await asyncio.gather(*tasks)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        if event.user_id == self.bot.user.id:
            return
        if event.emoji.name == '😴':
            m = discord.utils.get(self.msg2mbr.keys(), id=event.message_id)
            if m:
                self.game.player_map[self.msg2mbr[m]].sleep()
                await m.edit(content=m.content + '\t😴')
            return
        fac = self.emoji2fac.get(event.emoji.id)
        if fac and event.message_id == self.message.id:
            await self.game.faction_map[fac].wake_up()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent) -> None:
        if event.emoji.name == '😴':
            m = discord.utils.get(self.msg2mbr.keys(), id=event.message_id)
            if m:
                self.game.player_map[self.msg2mbr[m]].unsleep()
                if '\t' in m.content:
                    await m.edit(content=m.content.replace('\t😴', ''))
            return
        fac = self.emoji2fac.get(event.emoji.id)
        if fac and event.message_id == self.message.id:
            await self.game.faction_map[fac].put_to_sleep()

    async def morning_reset(self) -> None:
        tasks = []
        for m in self.msg2mbr:
            if m.content.endswith('\t😴'):
                tasks.append(m.edit(content=m.content[:-2]))
                for member in get_manitou_role().members:
                    tasks.append(m.remove_reaction('😴', member))
        await asyncio.gather(*tasks)
