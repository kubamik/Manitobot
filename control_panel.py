import asyncio
from typing import Dict, Optional

import discord
from discord.ext import commands


from settings import FAC2EMOJI
from utility import get_control_panel, get_manitou_role


class ControlPanel(commands.Cog, name='Panel Sterowania'):
    """Class which controls Manitou Control Panel
    """

    def __init__(self, bot):
        self.bot = bot
        self.active_msg: Optional[discord.Message] = None
        self.statue_msg: Optional[discord.Message] = None
        self.msg2mbr: Optional[Dict[discord.Message, discord.Member]] = None
        self.mbr2msg: Optional[Dict[discord.Member, discord.Message]] = None
        self.emoji2fac: Dict[int, str] = {}

    async def prepare_panel(self):
        await get_control_panel().purge()
        base = get_control_panel().send
        players = sorted(self.bot.game.player_map.keys(), key=lambda mbr: mbr.display_name)
        messages = []
        for player in players:
            messages.append(await base(player.display_name))
        self.active_msg = await base('Aktywna frakcja')
        self.statue_msg = await base('Posążek ma frakcja: **{}**'.format(self.bot.game.statue.faction_holder))
        self.msg2mbr = dict(zip(messages, players))
        self.mbr2msg = dict(zip(players, messages))
        tasks1, tasks2, tasks3 = [], [], []
        for m in messages:
            tasks1.append(m.add_reaction('😴'))
            tasks2.append(m.add_reaction('🗿'))
            tasks3.append(m.add_reaction('☠️'))
        for fac, id_ in FAC2EMOJI.items():
            if fac in self.bot.game.faction_map:
                await self.active_msg.add_reaction(self.bot.get_emoji(id_))
                self.emoji2fac[id_] = fac
        await asyncio.gather(*tasks1)
        await asyncio.gather(*tasks2)
        await asyncio.gather(*tasks3)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        if event.user_id not in [mbr.id for mbr in get_manitou_role().members]:
            return
        if event.emoji.name in ('😴', '🗿', '☠️'):
            m = discord.utils.get(self.msg2mbr.keys(), id=event.message_id)
            if m and event.emoji.name == '😴':
                self.bot.game.player_map[self.msg2mbr[m]].sleep()
                await m.edit(content=m.content + '\t😴')
            if m and event.emoji.name == '🗿':
                await self.bot.game.controller.statue_reaction_add(self.msg2mbr[m])
            if m and event.emoji.name == '☠️':
                await self.bot.game.controller.kill_reaction_add(self.msg2mbr[m])
            return
        fac = self.emoji2fac.get(event.emoji.id)
        if fac and event.message_id == self.active_msg.id:
            await self.bot.game.faction_map[fac].wake_up()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent) -> None:
        if event.emoji.name == '😴':
            m = discord.utils.get(self.msg2mbr.keys(), id=event.message_id)
            if m:
                self.bot.game.player_map[self.msg2mbr[m]].unsleep()
                if '\t😴' in m.content:
                    await m.edit(content=m.content.replace('\t😴', ''))
            return
        fac = self.emoji2fac.get(event.emoji.id)
        if fac and event.message_id == self.active_msg.id:
            await self.bot.game.faction_map[fac].put_to_sleep()

    async def morning_reset(self) -> None:
        tasks = []
        for m in self.msg2mbr:
            if '\t😴' in m.content:
                tasks.append(m.edit(content=m.content.replace('\t😴', '')))
                for member in get_manitou_role().members:
                    tasks.append(m.remove_reaction('😴', member))
        await asyncio.gather(*tasks, return_exceptions=True)
