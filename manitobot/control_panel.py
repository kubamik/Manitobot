import asyncio
from typing import Dict, Optional, List

import discord
from discord.ext import commands

from settings import FAC2EMOJI, EMOJI2COMMAND, REMOVABLE
from .basic_models import ManiBot
from .interactions import ComponentCallback
from .interactions.components import ButtonStyle, Button, ComponentMessage
from .interactions.interaction import ComponentInteraction
from .utility import get_control_panel, get_manitou_role, get_member, get_player_role, cleared_nickname


class ControlPanel(commands.Cog, name='Panel Sterowania'):
    """Class which is used as Manitou Control Panel
    """

    def __init__(self, bot):  # '🌇' - day, '🌃' - night
        self.bot: ManiBot = bot
        self.state_msg: Optional[ComponentMessage] = None
        self.statue_msg: Optional[discord.Message] = None
        self.msg2mbr: Optional[Dict[int, discord.Member]] = None
        self.mbr2msg: Optional[Dict[discord.Member, ComponentMessage]] = None
        self.daynight_msg: Optional[ComponentMessage] = None
        self.emoji2fac: Dict[int, str] = dict()

    def cog_unload(self):
        self.bot.remove_component_callback('sleep')
        self.bot.remove_component_callback('unsleep')
        self.bot.remove_component_callback('statue')
        self.bot.remove_component_callback('kill')
        self.bot.remove_component_callback('day')
        self.bot.remove_component_callback('night')
        for _, name in EMOJI2COMMAND.values():
            self.bot.remove_component_callback(name)
        for id_ in self.emoji2fac:
            self.bot.remove_component_callback(f'{id_}-wake')
            self.bot.remove_component_callback(f'{id_}-sleep')

    async def prepare_panel(self):
        channel = get_control_panel()
        await channel.purge()
        for fac, id_ in FAC2EMOJI.items():
            if fac in self.bot.game.faction_map:
                self.emoji2fac[id_] = fac

        base = channel.send
        self.register_callbacks()
        players = sorted(self.bot.game.player_map.values(), key=lambda pl: pl.member.display_name.lower())
        messages = []
        for player in players:
            comp = self._player_buttons()
            msg = await base(f'{cleared_nickname(player.member.display_name)} ({player.role_class.qualified_name})',
                             components=comp)
            msg = ComponentMessage.from_message(msg, components=comp)
            messages.append(msg)

        comp = self._day_night_button(day=False)
        daynight_msg = await base('**Noc**', components=comp)
        self.daynight_msg = ComponentMessage.from_message(daynight_msg, components=comp)

        comp = self._faction_buttons()
        state_msg = await base('Aktywna frakcja', components=comp)
        self.state_msg = ComponentMessage.from_message(state_msg, components=comp)

        self.statue_msg = await base('Posążek ma frakcja: **{}**'.format(self.bot.game.statue.faction_holder))
        members = sorted(self.bot.game.player_map.keys(), key=lambda mbr: mbr.display_name.lower())
        self.msg2mbr = dict(zip((m.id for m in messages), members))
        self.mbr2msg = dict(zip(members, messages))

    @staticmethod
    def _day_night_button(day):
        if not day:
            name = 'Dzień'
            emoji = '🌇'
            custom_id = 'day'
        else:
            name = 'Noc'
            emoji = '🌃'
            custom_id = 'night'
        return [[Button(ButtonStyle.Primary, name, emoji, custom_id=custom_id)]]

    @staticmethod
    def _player_buttons(components=None, sleep=None, statue=None, dead=None) -> List[List[Button]]:
        if components is None:
            components = [[
                Button(ButtonStyle.Success, label='Uśpij', emoji='😴', custom_id='sleep'),
                Button(ButtonStyle.Primary, label='Posążek', emoji='🗿', custom_id='statue'),
                Button(ButtonStyle.Destructive, label='Zabij', emoji='☠️', custom_id='kill')
            ]]
        if not components or not components[0]:
            return components
        if dead and len(components[0]) > 1:
            has_statue = statue if statue is not None else components[0][1].disabled
            return [[components[0][1]]] if has_statue else []
        if sleep is not None:
            style, custom_id, name = (ButtonStyle.Success, 'sleep', 'Uśpij') if not sleep else \
                (ButtonStyle.Destructive, 'unsleep', 'Obudź')
            components[0][0] = Button(style, label=name, emoji='😴', custom_id=custom_id)
        if statue is not None and len(components[0]) > 1:
            components[0][1].disabled = statue
        elif statue is not None:
            return []
        return components

    def _state_buttons(self, components=None, command=None) -> List[List[Button]]:
        if command is not None:
            button = discord.utils.get(components[0], custom_id=command)
            if button is not None:
                button.style = ButtonStyle.Destructive if button.style is ButtonStyle.Success else ButtonStyle.Success
                return components
        components = [[]]
        state = self.bot.game.day.state
        for emoji, (label, name) in EMOJI2COMMAND.items():
            if hasattr(state, name):
                style = ButtonStyle.Primary if name not in REMOVABLE else ButtonStyle.Success
                components[0].append(Button(style, label=label, emoji=emoji, custom_id=name))
        if not components[0]:
            return []
        return components

    def _faction_buttons(self, components=None, change: str = None):
        if not components:
            components = [[]]
            for id_, name in self.emoji2fac.items():
                emoji = self.bot.get_emoji(id_) or discord.PartialEmoji(name=name, id=id_)
                components[0].append(Button(ButtonStyle.Success, name, emoji, custom_id=f'{id_}-wake'))
        else:
            button = discord.utils.get(components[0], label=change)
            style = button.style
            style = ButtonStyle.Success if style is ButtonStyle.Destructive else ButtonStyle.Destructive
            action = 'wake' if style is ButtonStyle.Success else 'sleep'
            id_ = button.custom_id.partition('-')[0]
            button.style = style
            button.custom_id = id_ + '-' + action
        return components[0] and components

    async def change_removable(self, command):
        components = self.state_msg.components
        new_components = self._state_buttons(components, command)
        await self.state_msg.edit(components=new_components)

    def register_callbacks(self):
        async def put_sleep(ctx: ComponentInteraction):
            m_id = ctx.message.id
            player = self.msg2mbr[m_id]
            self.bot.game.player_map[player].sleep()
            components = ctx.message.components
            components = self._player_buttons(components, sleep=True)
            await player.send('Zostałeś(-aś) uśpiony(-a) lub trafiłeś(-aś) do więzienia. '
                              'Nie budzisz się więcej tej nocy')
            await ctx.edit_message(components=components)
            self.mbr2msg[player] = ctx.message

        self.bot.add_component_callback(ComponentCallback('sleep', put_sleep))

        async def unsleep(ctx: ComponentInteraction):
            m_id = ctx.message.id
            player = self.msg2mbr[m_id]
            self.bot.game.player_map[player].unsleep()
            components = ctx.message.components
            components = self._player_buttons(components, sleep=False)
            await player.send('Jednak nie zostałeś(-aś) uśpiony(-a). Obudź się na następne zawołanie')
            await ctx.edit_message(components=components)
            self.mbr2msg[player] = ctx.message

        self.bot.add_component_callback(ComponentCallback('unsleep', unsleep))

        async def kill(ctx: ComponentInteraction):
            m_id = ctx.message.id
            player = self.msg2mbr[m_id]
            await ctx.ack_for_update()
            await self.bot.game.player_map[player].role_class.die()
        self.bot.add_component_callback(ComponentCallback('kill', kill))

        async def statue_give(ctx: ComponentInteraction):
            m_id = ctx.message.id
            player = self.msg2mbr[m_id]
            await ctx.ack_for_update()
            await self.bot.game.statue.give(player)
        self.bot.add_component_callback(ComponentCallback('statue', statue_give))

        async def day(ctx: ComponentInteraction):
            await ctx.ack_for_update()
            await self.bot.game.new_day()
        self.bot.add_component_callback(ComponentCallback('day', day))

        async def night(ctx: ComponentInteraction):
            await ctx.ack_for_update()
            await self.bot.game.new_night()
        self.bot.add_component_callback(ComponentCallback('night', night))

        async def temp(ctx: ComponentInteraction):
            command = ctx.custom_id
            await ctx.ack_for_update()
            await getattr(self.bot.game.day.state, command)()
            if command in REMOVABLE:
                await self.change_removable(command)

        for _, name in EMOJI2COMMAND.values():
            self.bot.add_component_callback(ComponentCallback(name, temp))

        async def faction_action(ctx: ComponentInteraction):
            emoji_id, _, action = ctx.custom_id.partition('-')
            fac = self.emoji2fac.get(int(emoji_id))
            if fac and action == 'wake':
                await self.bot.game.faction_map[fac].wake_up()
            elif fac:
                await self.bot.game.faction_map[fac].put_to_sleep()
            comp = self.state_msg.components
            await ctx.edit_message(components=self._faction_buttons(components=comp, change=fac))
            self.state_msg = ctx.message

        for id_ in self.emoji2fac:
            self.bot.add_component_callback(ComponentCallback(f'{id_}-wake', faction_action))
            self.bot.add_component_callback(ComponentCallback(f'{id_}-sleep', faction_action))

    async def morning_reset(self) -> None:
        tasks = list()

        tasks.append(self.daynight_msg.edit(content='**Dzień**', components=self._day_night_button(day=True)))
        for m in self.mbr2msg.values():
            comp = m.components
            if comp and comp[0] and comp[0][0].style is ButtonStyle.Destructive:
                tasks.append(m.edit(components=self._player_buttons(comp, sleep=False)))
        tasks.append(self.bot.game.day.state.set_message(self.state_msg))
        tasks.append(self.add_state_emojis())
        await asyncio.gather(*tasks)

    async def evening(self):
        tasks = list()
        tasks.append(self.daynight_msg.edit(content='**Noc**', components=self._day_night_button(day=False)))
        tasks.append(self.state_msg.edit(content='Aktywna frakcja', embed=None, components=self._faction_buttons()))
        await asyncio.gather(*tasks)

    async def add_state_emojis(self):
        await self.state_msg.edit(components=self._state_buttons())

    async def swapping(self, first: discord.Member, second: discord.Member, first_role: str, second_role: str):
        m_1 = self.mbr2msg[first]
        m_2 = self.mbr2msg[second]
        content_1 = f'{first.display_name} ({first_role.replace("_", " ")})'
        content_2 = f'{second.display_name} ({second_role.replace("_", " ")})'
        await asyncio.gather(m_1.edit(content=content_1), m_2.edit(content=content_2))

    async def replace_player(self, first: discord.Member, second: discord.Member, role: str):
        msg = self.mbr2msg[first]
        self.mbr2msg[second] = msg
        self.msg2mbr[msg] = second
        self.mbr2msg.pop(first)
        await msg.edit(
            content=f'{second.display_name} ({role.replace("_", " ")})' + '\t' + msg.content.partition('\t')[2])

    async def statue_change(self, prev_holder: discord.Member, holder: discord.Member,
                            faction: str, planted: bool = False) -> None:
        tasks = []
        if prev_holder != holder:
            if prev_holder:
                m = self.mbr2msg[prev_holder]
                comp = m.components
                tasks.append(m.edit(components=self._player_buttons(comp, statue=False)))
            m = self.mbr2msg[holder]
            comp = m.components
            tasks.append(m.edit(components=self._player_buttons(comp, statue=True)))
        tasks.append(self.statue_msg.edit(content='Posążek ma frakcja: **{}**{}'.format(
            faction, ' *(podłożony)*' if planted else '')))
        await asyncio.gather(*tasks)

    async def die(self, member: discord.Member):
        m = self.mbr2msg[member]
        comp = m.components
        await m.edit(content=f'~~{m.content}~~', components=self._player_buttons(comp, dead=True))

    async def update_panel(self):
        """Edit messages with deads who was back to live and changes swapped roles
        """
        tasks = []
        for member in get_player_role().members:
            m = self.mbr2msg[member]
            if '~~' in m.content:
                player = self.bot.game.player_map[member]
                comp = m.components
                tasks.append(m.edit(content=m.content.replace('~~', ''),
                                    components=self._player_buttons(sleep=player.sleeped, statue=bool(comp))))
        await asyncio.gather(*tasks)
