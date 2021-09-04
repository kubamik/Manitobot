import asyncio
from typing import Dict, Optional

import discord
from discord.ext import commands

from settings import FAC2EMOJI, EMOJI2COMMAND, REMOVABLE
from .basic_models import ManiBot
from .utility import get_control_panel, get_manitou_role, get_member, get_player_role, cleared_nickname


class ControlPanel(commands.Cog, name='Panel Sterowania'):
    """Class which controls Manitou Control Panel
    """

    def __init__(self, bot):  # '🌇' - day, '🌃' - night
        self.bot: ManiBot = bot
        self.state_msg: Optional[discord.Message] = None
        self.statue_msg: Optional[discord.Message] = None
        self.msg2mbr: Optional[Dict[discord.Message, discord.Member]] = None
        self.mbr2msg: Optional[Dict[discord.Member, discord.Message]] = None
        self.daynight_msg: Optional[discord.Message] = None
        self.emoji2fac: Dict[int, str] = dict()

    async def prepare_panel(self):
        channel = get_control_panel()
        await channel.purge()
        base = channel.send
        players = sorted(self.bot.game.player_map.values(), key=lambda pl: pl.member.display_name.lower())
        messages = []
        for player in players:
            messages.append(await base(f'{cleared_nickname(player.member.display_name)} '
                                       f'({player.role_class.qualified_name})'))
        self.daynight_msg = await base('**Noc**')
        self.state_msg = await base('Aktywna frakcja')
        self.statue_msg = await base('Posążek ma frakcja: **{}**'.format(self.bot.game.statue.faction_holder))
        members = sorted(self.bot.game.player_map.keys(), key=lambda mbr: mbr.display_name.lower())
        self.msg2mbr = dict(zip(messages, members))
        self.mbr2msg = dict(zip(members, messages))
        tasks1, tasks2, tasks3 = [], [], []
        for m in messages:
            tasks1.append(m.add_reaction('😴'))
            tasks2.append(m.add_reaction('🗿'))
            tasks3.append(m.add_reaction('☠️'))
        for fac, id_ in FAC2EMOJI.items():
            if fac in self.bot.game.faction_map:
                self.emoji2fac[id_] = fac
        await self.daynight_msg.add_reaction('🌇')
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
                await self.msg2mbr[m].send('Zostałeś(-aś) uśpiony(-a) lub trafiłeś(-aś) do więzienia. '
                                           'Nie budzisz się więcej tej nocy')
            if m and event.emoji.name == '🗿':
                await self.bot.game.statue.give(self.msg2mbr[m])
            if m and event.emoji.name == '☠️':
                await self.confirm_kill(m, get_member(event.user_id))
            return
        if event.message_id == self.state_msg.id:
            fac = self.emoji2fac.get(event.emoji.id)
            if fac and self.bot.game.night_now:
                await self.bot.game.faction_map[fac].wake_up()
            command = EMOJI2COMMAND.get(event.emoji.name)
            day = self.bot.game.day
            if command and day and hasattr(day.state, command):
                await getattr(day.state, command)()
        elif event.message_id == self.daynight_msg.id:
            if event.emoji.name == '🌇' and self.bot.game.night_now:
                await self.bot.game.new_day()
            elif event.emoji.name == '🌃' and not self.bot.game.night_now:
                await self.bot.game.new_night()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent) -> None:
        if event.user_id not in [mbr.id for mbr in get_manitou_role().members]:
            return
        if event.emoji.name == '😴' and self.bot.game.night_now:
            m = discord.utils.get(self.msg2mbr.keys(), id=event.message_id)
            if m:
                self.bot.game.player_map[self.msg2mbr[m]].unsleep()
                await self.msg2mbr[m].send('Jednak nie zostałeś(-aś) uśpiony(-a). Obudź się na następne zawołanie')
                if '\t😴' in m.content:
                    await m.edit(content=m.content.replace('\t😴', ''))
        elif event.message_id == self.state_msg.id:
            fac = self.emoji2fac.get(event.emoji.id)
            if fac:
                await self.bot.game.faction_map[fac].put_to_sleep()
            if event.emoji.name in REMOVABLE:
                command = EMOJI2COMMAND.get(event.emoji.name)
                day = self.bot.game.day
                if command and day and hasattr(day.state, command):
                    await getattr(day.state, command)()

    async def morning_reset(self) -> None:
        tasks = list()
        tasks.append(self.daynight_msg.add_reaction('🌃'))
        manitous = get_manitou_role().members
        tasks.append(self.daynight_msg.clear_reaction('🌇'))
        tasks.append(self.daynight_msg.edit(content='**Dzień**'))
        for m in self.msg2mbr:
            if '\t😴' in m.content:
                tasks.append(m.edit(content=m.content.replace('\t😴', '')))
                for member in manitous:
                    tasks.append(m.remove_reaction('😴', member))
        tasks.append(self.add_state_emojis())
        tasks.append(self.bot.game.day.state.set_message(self.state_msg))
        await asyncio.gather(*tasks)

    async def evening(self):
        tasks = list()
        tasks.append(self.daynight_msg.add_reaction('🌇'))
        tasks.append(self.daynight_msg.clear_reaction('🌃'))
        tasks.append(self.daynight_msg.edit(content='**Noc**'))
        await self.state_msg.clear_reactions()
        tasks.append(self.state_msg.edit(content='Aktywna frakcja', embed=None))
        await asyncio.gather(*tasks)
        for id_ in self.emoji2fac:
            await self.state_msg.add_reaction(self.bot.get_emoji(id_))

    async def add_state_emojis(self):
        await self.state_msg.clear_reactions()
        for emoji, command in EMOJI2COMMAND.items():
            if hasattr(self.bot.game.day.state, command):
                await self.state_msg.add_reaction(emoji)

    async def swapping(self, first: discord.Member, second: discord.Member, first_role: str, second_role: str):
        m_1 = self.mbr2msg[first]
        m_2 = self.mbr2msg[second]
        content_1 = f'{first.display_name} ({first_role.replace("_", " ")})' + '\t' + m_1.content.partition('\t')[2]
        content_2 = f'{second.display_name} ({second_role.replace("_", " ")})' + '\t' + m_2.content.partition('\t')[2]
        await asyncio.gather(m_1.edit(content=content_1), m_2.edit(content=content_2))

    async def replace_player(self, first: discord.Member, second: discord.Member, role: str):
        msg = self.mbr2msg[first]
        self.mbr2msg[second] = msg
        self.msg2mbr[msg] = second
        self.mbr2msg.pop(first)
        await msg.edit(
            content=f'{second.display_name} ({role.replace("_", " ")})' + '\t' + msg.content.partition('\t')[2])

    async def confirm_kill(self, message: discord.Message, manitou: discord.Member):
        await message.add_reaction('💀')
        try:
            await self.bot.wait_for(
                'reaction_add', timeout=10,
                check=lambda rn, usr: usr.id == manitou.id and rn.emoji == '💀' and rn.message.id == message.id,
            )
        except asyncio.TimeoutError:
            return
        else:
            await self.bot.game.player_map[self.msg2mbr[message]].role_class.die()
        finally:
            await message.clear_reaction('💀')
            await message.remove_reaction('☠️', manitou)

    async def statue_change(self, prev_holder: discord.Member, holder: discord.Member,
                            faction: str, planted: bool = False) -> None:
        tasks = []
        if prev_holder != holder:
            if prev_holder:
                m = self.mbr2msg[prev_holder]
                for member in get_manitou_role().members:
                    tasks.append(m.remove_reaction('🗿', member))
                tasks.append(m.edit(content=m.content.replace('\t🗿', '')))
            m = self.mbr2msg[holder]
            tasks.append(m.edit(content=m.content+'\t🗿'))
        tasks.append(self.statue_msg.edit(content='Posążek ma frakcja: **{}**{}'.format(
            faction, ' *(podłożony)*' if planted else '')))
        await asyncio.gather(*tasks)

    async def die(self, member: discord.Member):
        m = self.mbr2msg[member]
        await m.clear_reactions()
        await m.edit(content=f'~~{m.content}~~')

    async def update_panel(self):
        """Edit messages with deads who was back to live and changes swapped roles
        """
        tasks1, tasks2, tasks3 = [], [], []
        for member in get_player_role().members:
            m = self.mbr2msg[member]
            if '~~' in m.content:
                tasks1.append(m.edit(content=m.content.replace('~~', '')))
                tasks1.append(m.add_reaction('😴'))
                tasks2.append(m.add_reaction('🗿'))
                tasks3.append(m.add_reaction('☠️'))
        await asyncio.gather(*tasks1)
        await asyncio.gather(*tasks2)
        await asyncio.gather(*tasks3)
