import asyncio
import datetime as dt
import random
import re
from collections import defaultdict
from contextlib import suppress
from typing import Optional, Union

import discord
from discord import app_commands, AppCommandType
from discord.ext import commands

from settings import PING_MESSAGE_ID, PING_GREEN_ID, \
    PING_BLUE_ID, GUILD_ID, PING_YELLOW_ID, SYSTEM_MESSAGES_CHANNEL_ID, PING_PINK_ID, \
    OTHER_PING_MESSAGE_ID, BOT_TRAP_CHANNEL_ID, VERIFICATION_MESSAGE_ID, VERIFICATION_CHANNEL_ID
from .basic_models import ManiBot
from .converters import MyMemberConverter
from .errors import MissingMembers, MissingAdministrativePermissions
from .interactions import ComponentCallback, Button
from .interactions.components import Components
from .my_checks import admin_cmd
from .utility import get_newcomer_role, get_ping_game_role, get_member, get_admin_role, \
    get_guild, get_ping_poll_role, get_ping_declaration_role, \
    get_ping_other_games_role, get_mod_role, is_trusted_member, get_system_messages_channel, get_verified_role


VERIFICATION_MESSAGE_TEMPLATE = """W ramach weryfikacji kliknij przycisk z **{}**.
**Nie klikaj żadnego innego przycisku!**"""

VERIFICATION_MAX_EMOJI_COUNT = 25
CORRECT_VERIFICATION_ID = 'verification-9'
INCORRECT_VERIFICATION_IDS = [f'verification-{i}' 
                              for i in list(range(0, 9)) + list(range(10, VERIFICATION_MAX_EMOJI_COUNT+1))]


class Management(commands.Cog, name='Dla Adminów'):
    def __init__(self, bot: ManiBot):
        self.bot = bot
        self.bot.tree.add_command(app_commands.ContextMenu(name='reakcje', callback=self.reactions_msg,
                                                           type=AppCommandType.message))

        for i in range(VERIFICATION_MAX_EMOJI_COUNT+1):
            self.bot.add_component_callback(ComponentCallback(f'verification-{i}', self.verification_callback))
            self.bot.add_component_callback(ComponentCallback(f'preview-verification-{i}',
                                                              self.verification_preview_callback))

    @staticmethod
    async def verification_callback(interaction: discord.Interaction, custom_id: str):
        await interaction.response.defer(ephemeral=True , thinking=True)
        if interaction.user in get_verified_role().members:
            await interaction.edit_original_response(content='Jesteś już pomyślnie zweryfikowany(-a).')
            return

        if custom_id != CORRECT_VERIFICATION_ID:
            begin_date = dt.datetime.now(dt.UTC) - dt.timedelta(days=7)
            kicks = [a async for a in get_guild().audit_logs(
                limit=None, after=begin_date, user=get_guild().me, action=discord.AuditLogAction.kick)
                     if a.target.id == interaction.user.id]
            if not kicks:
                # Not kicked in a week - kick as a warning
                await interaction.user.kick(reason='Nieprawidłowa odpowiedź na weryfikację')
                await get_system_messages_channel().send(f'Użytkownik {interaction.user.mention} został wyrzucony'
                                                         f' za nieprawidłową odpowiedź na weryfikację')
            else:
                # Kicked in a week - ban
                await interaction.user.ban(reason='Nieprawidłowa odpowiedź na weryfikację')
                await get_system_messages_channel().send(f'Użytkownik {interaction.user.mention} został zbanowany'
                                                         f' za kolejną nieprawidłową odpowiedź na weryfikację')
        else:
            await interaction.edit_original_response(content='Zostaniesz zweryfikowany(-a) w ciągu 15 sekund. '
                                                             '**Nie wciskaj żadnego przycisku!**')
            await asyncio.sleep(15)
            try:
                member = await get_guild().fetch_member(interaction.user.id)
            except discord.NotFound:
                return
            if member and member not in get_verified_role().members:
                await member.add_roles(get_verified_role())
                await interaction.followup.send('Zostałeś(-aś) zweryfikowany(-a).', ephemeral=True)

    async def verification_preview_callback(self, interaction: discord.Interaction, custom_id: str):
        msg = interaction.message
        msg_ref = msg.reference.resolved or await msg.channel.fetch_message(msg.reference.message_id)
        if interaction.user.id != msg_ref.mentions[0].id:
            await interaction.response.send_message('Nie masz uprawnień do tej akcji', ephemeral=True)
            return
        if custom_id == 'preview-' + CORRECT_VERIFICATION_ID:
            buttons = [
                [Button(style=discord.ButtonStyle.grey, emoji=button.emoji,
                        custom_id=button.custom_id.removeprefix('preview-')) for button in row]
                for row in Components.from_message(msg).components_list
            ]
            await self.bot.get_channel(VERIFICATION_CHANNEL_ID).get_partial_message(VERIFICATION_MESSAGE_ID).edit(
                content=msg.content, view=Components(buttons)
            )
            await interaction.response.send_message('Zaktualizowano wiadomość weryfikacyjną', ephemeral=True)
        else:
            await interaction.response.send_message('Anulowano akcję', ephemeral=True)

        await msg_ref.delete(delay=5)
        await msg.delete(delay=5)


    @commands.Cog.listener('on_member_join')
    async def add_new_member_roles(self, member):
        if member.guild.id != GUILD_ID:
            return
        # TODO: maybe remove auto role adding (or wait for rule acceptance)
        await member.add_roles(get_newcomer_role(), get_ping_poll_role(), get_ping_game_role(),
                               get_ping_declaration_role())

    @commands.Cog.listener('on_member_remove')
    async def member_leaves(self, member):
        if member.guild.id != GUILD_ID:
            return
        if SYSTEM_MESSAGES_CHANNEL_ID is not None:
            ch = self.bot.get_channel(SYSTEM_MESSAGES_CHANNEL_ID)
        else:
            ch = member.guild.system_channel
        if ch is None:
            return
        for wb in await ch.webhooks():
            if wb.name == 'System':
                wbhk = wb
                break
        else:
            wbhk = await ch.create_webhook(name='System')
        await wbhk.send("{} **({})** opuścił(-a) serwer".format(member.mention, member.display_name),
                        avatar_url='https://cdn.discordapp.com/embed/avatars/5.png')

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        if message.channel.id != BOT_TRAP_CHANNEL_ID or message.author.id == self.bot.user.id:
            return

        await message.delete()
        await get_system_messages_channel().send(f'Użytkownik {message.author.mention} wysłał wiadomość '
                                                 f'na zabronionym kanale:\n```\n{message.content}\n```',
                                                 allowed_mentions=discord.AllowedMentions.none()
                                                 )
        if is_trusted_member(message.author):
            with suppress(discord.Forbidden):
                await message.author.timeout(dt.timedelta(minutes=5), reason='Użycie kanału bot_trap')
            await message.author.send('Nie używaj tego kanału. Potraktuj to jako upomnienie.')
        else:
            await message.author.ban(reason='Użycie kanału bot_trap')
            await get_system_messages_channel().send(
                f'Użytkownik {message.author.mention} został zbanowany za użycie kanału bot_trap'
            )

    @commands.Cog.listener('on_raw_reaction_add')
    async def ping_reaction_add(
            self, event: discord.RawReactionActionEvent) -> None:
        if event.user_id == self.bot.user.id:
            return
        member = get_member(event.user_id)
        if event.message_id == PING_MESSAGE_ID:
            if event.emoji.id == PING_YELLOW_ID:
                await member.remove_roles(get_ping_poll_role())
            if event.emoji.id == PING_GREEN_ID:
                await member.remove_roles(get_ping_declaration_role())
            if event.emoji.id == PING_BLUE_ID:
                await member.remove_roles(get_ping_game_role())
        elif event.message_id == OTHER_PING_MESSAGE_ID:
            if event.emoji.id == PING_PINK_ID:
                await member.add_roles(get_ping_other_games_role())

    @commands.Cog.listener('on_raw_reaction_remove')
    async def ping_reaction_remove(
            self, event: discord.RawReactionActionEvent):
        if event.user_id == self.bot.user.id:
            return
        member = get_member(event.user_id)
        if event.message_id == PING_MESSAGE_ID:
            if event.emoji.id == PING_YELLOW_ID:
                await member.add_roles(get_ping_poll_role())
            if event.emoji.id == PING_GREEN_ID:
                await member.add_roles(get_ping_declaration_role())
            if event.emoji.id == PING_BLUE_ID:
                await member.add_roles(get_ping_game_role())
        elif event.message_id == OTHER_PING_MESSAGE_ID:
            if event.emoji.id == PING_PINK_ID:
                await member.remove_roles(get_ping_other_games_role())

    async def cog_check(self, ctx):
        if (ctx.author in get_admin_role().members or ctx.author in get_mod_role().members
                or await self.bot.is_owner(ctx.author)):
            return True
        raise MissingAdministrativePermissions

    @commands.command(name='edytuj_weryfikacje')
    @admin_cmd()
    async def edit_verification(self, ctx: commands.Context, correct: discord.Emoji | str, *, text_and_emojis: str):
        """Edytuje wiadomość weryfikacyjną. Uwaga! Przed użyciem dokładnie zapoznaj się z instrukcją.
        
        Komenda edytuje wiadomość weryfikacyjną z emotkami. 
        Jeżeli pożądana jest edycja treści wiadomości weryfikacyjnej należy wysłać wiadomość o docelowej treści (na dowolny kanał) i w odpowiedzi na nią użyć tej komendy.
        Jeśli chcesz użyć gotowej wiadomości musisz wpisać nazwę właściwej emotki tak jak opisano poniżej.
        
        Po komendzie należy wpisać emoji, które ma być poprawne, następnie spację i nazwę tego emoji w narzędniku (jeśli nie chcesz edytować całej treści wiadomości). 
        W kolejnych liniach wypisz emoji używane przy weryfikacji (w ułożeniu docelowym - maksymalnie 5x5).
        
        Po wysłaniu komendy bot wyśle podgląd wiadomości weryfikacyjnej do zatwierdzenia.
        
        Przykładowe wywołanie:
        &edytuj_weryfikacje 🥕 marchewką
        🍓🍋🍐🦄🍆
        🍇🥦🍌🥕🍒
        """
        if VERIFICATION_MESSAGE_ID is None:
            await ctx.send('Opcja niewspierana, skontaktuj się z deweloperem')
            return

        text, *emoji_rows = text_and_emojis.strip().split('\n')
        if ctx.message.reference is not None:
            message = (await ctx.fetch_message(ctx.message.reference.message_id)).content
        else:
            message = VERIFICATION_MESSAGE_TEMPLATE.format(text)

        if len(emoji_rows) < 1 or not all([e.strip() for e in emoji_rows]):
            await ctx.send('Nie podano żadnych przycisków', delete_after=10)
            ctx.command_failed = True
            return

        ids = INCORRECT_VERIFICATION_IDS.copy()
        random.shuffle(ids)
        incorrect_ids = iter(ids)
        
        buttons = []

        for row in emoji_rows:
            buttons.append(list())
            i = 0
            row = row.strip().replace(' ', '').replace('\ufe0f', '')
            matches = re.finditer(r'<:\w+:\d+>', row)
            while i < len(row):
                if row[i] == '<':
                    match = next(matches)
                    i = match.end()
                    emoji = discord.PartialEmoji.from_str(match.group(0))
                else:
                    emoji = row[i]
                    i += 1
                buttons[-1].append(Button(
                    style=discord.ButtonStyle.grey, emoji=emoji, 
                    custom_id='preview-' + (next(incorrect_ids) if emoji != correct else CORRECT_VERIFICATION_ID)
                ))
        
        if len(buttons) > 5 or any(len(row) > 5 for row in buttons):
            await ctx.send('Maksymalne wymiary tablicy z przyciskami to 5x5', delete_after=10)
            ctx.command_failed = True
            return
        
        msg = await ctx.send(f'{ctx.author.mention}\nPodgląd wiadomości weryfikacyjnej, aby zatwierdzić wciśnij '
                             f'właściwy przycisk, aby odrzucić wciśnij błędny')
        try:
            await msg.reply(message, view=Components(buttons))
        except discord.HTTPException as exc:
            await msg.reply(f'Wystąpił błąd zweryfikuj poprawność wprowadzonych danych\n||{exc.text}||', 
                           delete_after=10)
            ctx.command_failed = True
            await msg.delete(delay=10)


    @commands.command(name='adminuj')
    @admin_cmd()
    async def adminate(self, _, *, osoba: MyMemberConverter(player_only=False)):
        """Mianuje nowego admina
        """
        member = osoba
        await member.add_roles(get_admin_role())

    @commands.command(name='nie_adminuj', hidden=True)
    @admin_cmd()
    async def not_adminate(self, _, *, osoba: MyMemberConverter(player_only=False)):
        """Usuwa admina
        """
        member = osoba
        await member.remove_roles(get_admin_role())

    @commands.command(name='usuń')
    @commands.guild_only()
    async def delete(self, ctx, czas_w_minutach: int, *osoby: MyMemberConverter(player_only=False)):
        """Masowo usuwa wiadomości, używać tylko do spamu!
        W przypadku braku podania członków czyszczone są wszystkie wiadomości.
        """
        time = czas_w_minutach
        members = osoby
        if time > 24 * 60:
            await ctx.send("Maksymalny czas to 24 godziny")
            return

        if not members:
            if ctx.author in get_admin_role().members:
                members = list(get_guild().members)
            else:
                raise MissingMembers

        await ctx.channel.purge(after=ctx.message.created_at - dt.timedelta(minutes=time),
                                before=ctx.message.created_at, check=lambda mess: mess.author in members)

    @commands.command(name='reakcje')
    async def reactions(self, ctx, wiadomosc: discord.Message):
        """Wysyła podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link
        """
        m = wiadomosc
        for msg in await self.reactions_summary(m):
            await ctx.send(msg)

    @commands.command(name='wyślij')
    @admin_cmd()
    async def special_send(self, ctx, channel_id: Optional[int] = None, *, content):
        """Wysyła podaną wiadomośc na podany kanał lub obecny kanał"""
        if not channel_id:
            await ctx.send(content)
        else:
            channel = get_guild().get_channel_or_thread(channel_id)
            if channel is None:
                raise commands.BadArgument('Wrong channel id')
            await channel.send(content)
        await ctx.message.delete()

    @commands.command(name='dodaj_reakcje', aliases=['emojis'])
    async def add_reactions(self, ctx: commands.Context, wiadomosc: Optional[discord.Message] = None,
                            *emoji: Union[discord.Emoji, str]):
        """Dodaje reakcje do wiadomości przekazanej przez ID/link lub do wiadomości, na którą odpowiadasz.
        Reakcje powinny być oddzielone spacją.
        """
        if wiadomosc is None and ctx.message.reference is not None:
            wiadomosc = (ctx.message.reference.resolved or
                         await ctx.fetch_message(ctx.message.reference.message_id))
        for e in emoji:
            try:
                await wiadomosc.add_reaction(e)
            except discord.HTTPException:
                pass

    @commands.command(name='braki', aliases=['missing'])
    async def missing_reactions(self, ctx, emoji: Union[discord.Emoji, str], first: discord.Message,
                                second: discord.Message):
        """Wysyła listę osób, które dodały emoji do pierwszej wiadomości, ale nie zareagowały na drugą
        """
        reaction = discord.utils.get(first.reactions, emoji=emoji)
        first_users = set([user async for user in reaction.users()])
        second_users = set([m for r in second.reactions async for m in r.users()])
        missing = first_users - second_users
        if missing:
            msg = f'**Brakujące osoby na {emoji}:**\n- '
            msg += '\n- '.join([f'{m.display_name}' for m in missing])
        else:
            msg = f'Nie ma brakujących osób na {emoji}'
        await ctx.send(msg)

    @staticmethod
    async def reactions_summary(m: discord.Message) -> list[str]:
        reactions = [user for r in m.reactions async for user in r.users()]
        members = list(set(sum(reactions, start=list())))
        parsed = defaultdict(list)
        for r, users in zip(m.reactions, reactions):
            emoji = str(r.emoji)
            for member in members:
                if member in users:
                    parsed[member].append(emoji)
                else:
                    parsed[member].append('<:e:881860336712560660>')
        members = [member for member in members if isinstance(member, discord.Member)]

        if not members:
            return ['Do tej wiadomości nie dodano reakcji']

        maxlen = len(max(members, key=lambda mem: len(mem.display_name)).display_name)
        msg = ''
        msgs = []
        for member, r in parsed.items():
            if isinstance(member, discord.Member):
                txt = f'`{member.display_name:{maxlen}} `' + ''.join(r) + '\n'
                if len(msg) + len(txt) >= 2000:  # maximum discord message len
                    msgs.append(msg)
                    msg = ''
                msg += txt

        msgs.append(msg)
        return msgs

    async def reactions_msg(self, interaction: discord.Interaction, m: discord.Message):
        """Wysyła na DM podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link
        """
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True)
        for msg in await self.reactions_summary(m):
            await interaction.followup.send(msg, ephemeral=True)

