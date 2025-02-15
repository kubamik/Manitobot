import asyncio
from contextlib import suppress
from typing import Dict, Optional, List

import discord
from discord.ext import commands

from settings import FAC2EMOJI, EMOJI2COMMAND, REMOVABLE
from .basic_models import ManiBot
from .interactions import ComponentCallback
from discord import ButtonStyle
from .interactions.components import Button, Components
from .utility import get_control_panel, get_player_role, cleared_nickname


class MessageGetter:
    """Class holding message data, used to get message from cache or fetch it to have newest content
    """
    
    def __init__(self, bot: ManiBot, msg: discord.Message):
        self.bot = bot
        self.msg_id = msg.id
        self.msg_channel = msg.channel
        
    async def __call__(self):
        if msg := discord.utils.get(self.bot.cached_messages, id=self.msg_id):
            return msg
        return await self.msg_channel.fetch_message(self.msg_id)
    
    def partial(self):
        return self.msg_channel.get_partial_message(self.msg_id)

# noinspection PyAttributeOutsideInit
class ControlPanel(commands.Cog, name='Panel Sterowania'):
    """Class which is used as Manitou Control Panel
    """

    def __init__(self, bot):  # '🌇' - day, '🌃' - night
        self.bot: ManiBot = bot
        self.faction_message: MessageGetter
        self.day_message: MessageGetter
        self.statue_msg: MessageGetter
        self.msg2mbr: Dict[int, discord.Member]
        self.mbr2msg: Dict[discord.Member, MessageGetter]
        self.daynight_msg: MessageGetter
        self.emoji2fac: Dict[int, str] = dict()
        
    def create_message_getter(self, message: discord.Message) -> MessageGetter:
        return MessageGetter(self.bot, message)

    async def cog_unload(self):
        rm = self.bot.remove_component_callback
        rm('sleep')
        rm('unsleep')
        rm('statue')
        rm('kill')
        rm('confirm_kill')
        rm('cancel_kill')
        rm('day')
        rm('night')
        for _, name in EMOJI2COMMAND.values():
            rm(name)
        for id_ in self.emoji2fac:
            rm(f'{id_}-wake')
            rm(f'{id_}-sleep')

    async def prepare_panel(self):
        channel = get_control_panel()
        with suppress(discord.DiscordException):
            await channel.purge()
        for fac, id_ in FAC2EMOJI.items():
            if fac in self.bot.game.faction_map:
                self.emoji2fac[id_] = fac

        base = channel.send
        getter = self.create_message_getter
        self.register_callbacks()
        players = sorted(self.bot.game.player_map.values(), key=lambda pl: pl.member.display_name.lower())
        player_messages_getters = []
        for player in players:
            comp = self._player_buttons()
            newcomer_sign = '🔰 ' if player.is_newcomer else ''
            msg = await base(f'{newcomer_sign}{cleared_nickname(player.member.display_name)} '
                             f'({player.role_class.qualified_name})',
                             view=comp)
            player_messages_getters.append(self.create_message_getter(msg))

        comp = self._day_night_button(day=False)
        msg = await base('*Trwa:* **Noc**', view=comp)
        self.daynight_msg = getter(msg)

        comp = self._faction_buttons()
        msg = await base('Aktywna frakcja', view=comp)
        self.faction_message = getter(msg)
        
        msg = await base('*Trwa noc*')
        self.day_message = getter(msg)
        
        msg = await base('Posążek ma frakcja: **{}**'.format(self.bot.game.statue.faction_holder))
        self.statue_msg = getter(msg)
        
        members = sorted(self.bot.game.player_map.keys(), key=lambda mbr: mbr.display_name.lower())
        self.msg2mbr = dict(zip((m.msg_id for m in player_messages_getters), members))
        self.mbr2msg = dict(zip(members, player_messages_getters))

    async def _reset_day_message(self):
        await self.day_message.partial().delete(delay=0)
        await self.statue_msg.partial().delete(delay=0)

        send = get_control_panel().send
        day_message = await self.day_message()
        self.day_message = await send(day_message.content, view=Components.from_message(day_message))
        
        statue_msg = await self.statue_msg()
        self.statue_msg = await send(statue_msg.content)

    @staticmethod
    def _day_night_button(day: bool) -> Components:
        if not day:
            name = 'Dzień'
            emoji = '🌇'
            custom_id = 'day'
        else:
            name = 'Noc'
            emoji = '🌃'
            custom_id = 'night'
        return Components([[Button(ButtonStyle.primary, name, emoji, custom_id=custom_id)]])

    @staticmethod
    def _player_buttons(current_components: Components | None = None, sleep: bool | None = None,
                        statue: bool | None = None, dead: bool | None = None, planted: bool | None = None) -> Components:
        if current_components is None:
            components = [[
                Button(ButtonStyle.success, label='Uśpij', emoji='😴', custom_id='sleep'),
                Button(ButtonStyle.primary, label='Posążek', emoji='🗿', custom_id='statue'),
                Button(ButtonStyle.danger, label='Zabij', emoji='☠️', custom_id='kill')
            ]]
        else:
            components = current_components.components_list
        if not components or not components[0]:
            return Components([])
        if planted is not None:
            if planted and len(components[0]) == 3:
                components[0].append(
                    Button(ButtonStyle.secondary, label='Podłożony', emoji='🗿', custom_id='not_usable', disabled=True)
                )
            elif not planted and len(components[0]) % 3 == 1:  # len 1 or 4
                components[0].pop(-1)
        if dead and len(components[0]) > 1:
            has_statue = statue if statue is not None else components[0][1].disabled
            has_planted = not statue and planted is not False and len(components[0]) == 4  # cannot be both has_*
            return Components([[components[0][c]] for c, has in zip([1, -1], [has_statue, has_planted]) if has])
        if sleep is not None:
            style, custom_id, name = (ButtonStyle.success, 'sleep', 'Uśpij') if not sleep else \
                (ButtonStyle.danger, 'unsleep', 'Obudź')
            components[0][0] = Button(style, label=name, emoji='😴', custom_id=custom_id)
        if statue is not None and len(components[0]) > 1:
            components[0][1].disabled = statue
            if len(components[0]) == 4 and not planted:
                components[0].pop(-1)
        elif statue is not None:
            return Components([])
        return Components(components)

    def _confirm_kill_button(self, player: discord.Member) -> List[Button]:
        suffix = ' (w dzień)' if not self.bot.game.night_now else ''
        return [
            Button(ButtonStyle.danger, label=f'Potwierdź zabicie {player.display_name}' + suffix,
                   emoji='☠️', custom_id='confirm_kill'),
            Button(ButtonStyle.success, label='Anuluj', emoji='❌', custom_id='cancel_kill')
        ]

    def _state_buttons(self, current_components: Components | None = None, command=None) -> Components:
        if command is not None:
            components = current_components.components_list
            button = discord.utils.get(components[0], custom_id=command)
            if button is not None:
                button.style = ButtonStyle.danger if button.style is ButtonStyle.success else ButtonStyle.success
                return current_components
        components = [[]]
        state = self.bot.game.day.state
        for emoji, (label, name) in EMOJI2COMMAND.items():
            if hasattr(state, name):
                style = ButtonStyle.primary if name not in REMOVABLE else ButtonStyle.success
                components[0].append(Button(style, label=label, emoji=emoji, custom_id=name))
        if not components[0]:
            return Components([])
        return Components(components)

    def _faction_buttons(self, current_components: Components | None = None, change: str | None = None) -> Components:
        if not current_components:
            components = [[]]
            for id_, name in self.emoji2fac.items():
                emoji = self.bot.get_emoji(id_) or discord.PartialEmoji(name=name, id=id_)
                components[0].append(Button(ButtonStyle.success, name, emoji, custom_id=f'{id_}-wake'))
        else:
            components = current_components.components_list
            button = discord.utils.get(components[0], label=change)
            style = button.style
            style = ButtonStyle.success if style is ButtonStyle.danger else ButtonStyle.danger
            action = 'wake' if style is ButtonStyle.success else 'sleep'
            id_ = button.custom_id.partition('-')[0]
            button.style = style
            button.custom_id = id_ + '-' + action
        return Components(components[0] and components)

    async def edit_day_message(self, **fields):
        try:
            await self.day_message.partial().edit(**fields)
        except discord.HTTPException as e:
            if e.status == 429:
                await self._reset_day_message()
                await self.day_message.partial().edit(**fields)
            else:
                raise

    async def change_removable(self, command):
        components = Components.from_message(await self.day_message())
        new_components = self._state_buttons(components, command)
        await self.edit_day_message(view=new_components)

    def register_callbacks(self):
        async def put_sleep(interaction: discord.Interaction, _: str):
            m_id = interaction.message.id
            player = self.msg2mbr[m_id]
            self.bot.game.player_map[player].sleep()
            components = Components.from_message(interaction.message)
            components = self._player_buttons(components, sleep=True)
            await player.send('Zostałeś(-aś) uśpiony(-a) lub trafiłeś(-aś) do więzienia. '
                              'Nie budzisz się więcej tej nocy')
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.edit_message(view=components)

        self.bot.add_component_callback(ComponentCallback('sleep', put_sleep))

        async def unsleep(interaction: discord.Interaction, _: str):
            m_id = interaction.message.id
            player = self.msg2mbr[m_id]
            self.bot.game.player_map[player].unsleep()
            components = Components.from_message(interaction.message)
            components = self._player_buttons(components, sleep=False)
            await player.send('Jednak nie zostałeś(-aś) uśpiony(-a). Obudź się na następne zawołanie')
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.edit_message(view=components)

        self.bot.add_component_callback(ComponentCallback('unsleep', unsleep))

        async def confirm_kill(interaction: discord.Interaction, _: str):
            m_id = interaction.message.id
            player = self.msg2mbr[m_id]
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.defer(thinking=False)
            await self.bot.game.player_map[player].role_class.die()
        self.bot.add_component_callback(ComponentCallback('confirm_kill', confirm_kill))

        async def cancel_kill(interaction: discord.Interaction, _: str):
            comp = Components.from_message(interaction.message)
            if len(comp.components_list) == 2:
                comp.components_list.pop(-1)
                # noinspection PyTypeChecker
                resp: discord.InteractionResponse = interaction.response
                await resp.edit_message(view=comp)

        self.bot.add_component_callback(ComponentCallback('cancel_kill', cancel_kill))

        async def kill(interaction: discord.Interaction, _: str):
            comp = Components.from_message(interaction.message)
            m_id = interaction.message.id
            player = self.msg2mbr[m_id]
            if len(comp.components_list) == 1:
                comp.components_list.append(self._confirm_kill_button(player))
                # noinspection PyTypeChecker
                resp: discord.InteractionResponse = interaction.response
                await resp.edit_message(view=comp)
                if not self.bot.game.night_now:
                    # noinspection PyTypeChecker
                    followup: discord.Webhook = interaction.followup
                    await followup.send("**Uwaga!**\nTrwa dzień", ephemeral=True)
        self.bot.add_component_callback(ComponentCallback('kill', kill))

        async def statue_give(interaction: discord.Interaction, _: str):
            m_id = interaction.message.id
            player = self.msg2mbr[m_id]
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.defer(thinking=False)
            await self.bot.game.statue.give(player)
        self.bot.add_component_callback(ComponentCallback('statue', statue_give))

        async def day(interaction: discord.Interaction, _: str):
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.defer(thinking=False)
            await self.bot.game.new_day()
        self.bot.add_component_callback(ComponentCallback('day', day))

        async def night(interaction: discord.Interaction, _: str):
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.defer(thinking=False)
            await self.bot.game.new_night()
        self.bot.add_component_callback(ComponentCallback('night', night))

        async def temp(interaction: discord.Interaction, command: str):
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.defer(thinking=False)
            await getattr(self.bot.game.day.state, command)()
            if command in REMOVABLE:
                await self.change_removable(command)

        for _, name in EMOJI2COMMAND.values():
            self.bot.add_component_callback(ComponentCallback(name, temp))

        async def faction_action(interaction: discord.Interaction, custom_id: str):
            emoji_id, _, action = custom_id.partition('-')
            fac = self.emoji2fac.get(int(emoji_id))
            if fac and action == 'wake':
                await self.bot.game.faction_map[fac].wake_up()
            elif fac:
                await self.bot.game.faction_map[fac].put_to_sleep()
            comp = Components.from_message(await self.faction_message())
            # noinspection PyTypeChecker
            resp: discord.InteractionResponse = interaction.response
            await resp.edit_message(view=self._faction_buttons(comp, change=fac))

        for id_ in self.emoji2fac:
            self.bot.add_component_callback(ComponentCallback(f'{id_}-wake', faction_action))
            self.bot.add_component_callback(ComponentCallback(f'{id_}-sleep', faction_action))

    async def morning_reset(self) -> None:
        tasks = list()

        tasks.append(self.daynight_msg.partial().edit(content='*Trwa:* **Dzień**', view=self._day_night_button(day=True)))
        for m in self.mbr2msg.values():
            msg = await m()
            components = Components.from_message(msg)
            comp = components.components_list
            if comp and comp[0] and comp[0][0].style is ButtonStyle.danger:
                tasks.append(msg.edit(view=self._player_buttons(components, sleep=False)))
        tasks.append(self.bot.game.day.state.set_msg_edit_callback(self.edit_day_message))
        tasks.append(self.bot.game.day.state.async_init())
        tasks.append(self.add_state_buttons())
        await asyncio.gather(*tasks)

    async def evening(self):
        tasks = list()
        tasks.append(self.daynight_msg.partial().edit(content='*Trwa:* **Noc**', view=self._day_night_button(day=False)))
        tasks.append(self.edit_day_message(content='*Trwa noc*', view=None))
        await asyncio.gather(*tasks)

    async def add_state_buttons(self):
        await self.edit_day_message(view=self._state_buttons())

    async def swapping(self, first: discord.Member, second: discord.Member, first_role: str, second_role: str):
        m_1 = self.mbr2msg[first].partial()
        m_2 = self.mbr2msg[second].partial()
        content_1 = f'{first.display_name} ({first_role.replace("_", " ")})'
        content_2 = f'{second.display_name} ({second_role.replace("_", " ")})'
        await asyncio.gather(m_1.edit(content=content_1), m_2.edit(content=content_2))

    async def replace_player(self, first: discord.Member, second: discord.Member, role: str):
        msg = self.mbr2msg[first]
        self.mbr2msg[second] = msg
        self.msg2mbr[msg.msg_id] = second
        self.mbr2msg.pop(first)
        await msg.partial().edit(
            content=f'{second.display_name} ({role.replace("_", " ")})' + '\t' + msg.content.partition('\t')[2])

    async def statue_change(self, prev_holder: discord.Member, holder: discord.Member,
                            faction: str, planted: bool = False) -> None:
        tasks = []
        if prev_holder != holder and prev_holder:
            m = await self.mbr2msg[prev_holder]()
            comp = Components.from_message(m)
            tasks.append(m.edit(view=self._player_buttons(comp, statue=False)))
        m = await self.mbr2msg[holder]()
        comp = self._player_buttons(Components.from_message(m), statue=not planted, planted=planted)
        tasks.append(m.edit(view=comp))
        tasks.append(self.statue_msg.partial().edit(content='Posążek ma frakcja: **{}**{}'.format(
            faction, ' *(podłożony)*' if planted else '')))
        await asyncio.gather(*tasks)

    async def die(self, member: discord.Member):
        m = await self.mbr2msg[member]()
        comp = Components.from_message(m)
        await m.edit(content=f'~~{m.content}~~', view=self._player_buttons(comp, dead=True))

    async def update_panel(self):
        """Edit messages with deads who was back to live and changes swapped roles
        """
        tasks = []
        for member in get_player_role().members:
            m = await self.mbr2msg[member]()
            if '~~' in m.content:
                player = self.bot.game.player_map[member]
                comp = Components.from_message(m).components_list
                plt = comp and comp[0][0].style is ButtonStyle.secondary
                tasks.append(m.edit(content=m.content.replace('~~', ''),
                                    view=self._player_buttons(sleep=player.sleeped, statue=bool(comp) and not plt,
                                                                    planted=plt)))
        await asyncio.gather(*tasks)
