import asyncio

import discord

from bot_basics import bot
from control_panel import ControlPanel
from utility import get_manitou_role, get_player_role


class Controller:
    def __init__(self):
        self.panel: ControlPanel = bot.get_cog('Panel Sterowania')

    @staticmethod
    async def statue_reaction_add(member: discord.Member) -> None:
        await bot.game.statue.give(member)

    @staticmethod
    async def kill_reaction_add(member: discord.Member) -> None:
        await bot.game.player_map[member].role_class.die()

    async def statue_change(self, prev_holder: discord.Member, holder: discord.Member,
                            faction: str, planted: bool) -> None:
        tasks = []
        if prev_holder != holder:
            if prev_holder:
                m = self.panel.mbr2msg[prev_holder]
                for member in get_manitou_role().members:
                    tasks.append(m.remove_reaction('🗿', member))
                tasks.append(m.edit(content=m.content.replace('\t🗿', '')))
            m = self.panel.mbr2msg[holder]
            tasks.append(m.edit(content=m.content+'\t🗿'))
        tasks.append(self.panel.statue_msg.edit(content='Posążek ma frakcja: **{}**{}'.format(
            faction, ' *(podłożony)*' if planted else '')))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def die(self, member: discord.Member):
        m = self.panel.mbr2msg[member]
        await m.clear_reactions()
        await m.edit(content=f'~~{m.content}~~')

    async def update_panel(self):
        """Edit messages with deads who was back to live and changes swaped roles
        """
        tasks1, tasks2, tasks3 = [], [], []
        for member in get_player_role().members:
            m = self.panel.mbr2msg[member]
            if '~~' in m.content:
                tasks1.append(m.edit(content=m.content.replace('~~', '')))
                tasks1.append(m.add_reaction('😴'))
                tasks2.append(m.add_reaction('🗿'))
                tasks3.append(m.add_reaction('☠️'))
        # TODO: Change swaped roles
        await asyncio.gather(*tasks1)
        await asyncio.gather(*tasks2)
        await asyncio.gather(*tasks3)
