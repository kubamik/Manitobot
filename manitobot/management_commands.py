import asyncio
import datetime as dt
from collections import defaultdict
from typing import Optional, Union, Any

import discord
from discord.ext import commands

from settings import TOWN_CHANNEL_ID, PING_MESSAGE_ID, PING_GREEN_ID, \
    PING_BLUE_ID, GUILD_ID, PING_YELLOW_ID, PING_POLL_ID, LEAVE_CHANNEL_ID
from .bot_basics import bot
from .converters import MyMemberConverter, MyDateConverter
from .interactions import CommandsTypes
from .utility import get_newcommer_role, get_ping_game_role, get_member, get_admin_role, \
    get_ankietawka_channel, get_guild, get_voice_channel, get_ping_poll_role, get_ping_declaration_role


WEEKDAYS = dict(zip(range(7), ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']))

# Enquiries
ENQUIRY = '''**Ankietka** na {period}
<:ping_yellow:{ping_id}> <:ping_yellow:{ping_id}> <:ping_yellow:{ping_id}>

**Kiedy chcesz grać w ktulu?**

Zaznacz wszystkie opcje, które ci pasują. Możesz zmienić swój wybór w dowolnym momencie.

{data}
🚫 W te dni nie gram.

🔕 Nie chcę dostawać <:ping_green:{ping_green_id}> w dni, których nie zaznaczyłæm.
'''
ENQUIRY_OPTION = '{emoji} {weekday} {date}\n'
ENQUIRY_PERIOD = '{} - {}'
ENQUIRY_EMOJI = ['🚫', '🔕']
MAX_DAYS = dt.timedelta(days=6)

# Declarations
DECLARATION = '''**Deklaracje** ({weekday} {date:dd.mm})
<:ping_green:{ping_id}> <:ping_green:{ping_id}> <:ping_green:{ping_id}>

**Kiedy chcesz grać w ktulu?**

Zaznacz wszystkie opcje, które ci pasują. Postaraj się o dostępność w wybranych terminach.

{data}
🚫 Dzisiaj nie gram.

⚜️ Mogę prowadzić grę.
'''
DECLARATION_OPTION = '{emoji} <t:{timestamp}:t>\n'
DECLARATION_EMOJI = ['🚫', '⚜']
STARTING_HOUR = 17  # hour to start declarations
ENDING_HOUR = 21  # hour to end declarations
INTERVAL = dt.timedelta(hours=1)

OPTIONS_EMOJI = ['🍓', '🏀', '🐤', '🌵', '🐳', '🍇', '🐷']


class Management(commands.Cog, name='Dla Adminów'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_member_join')
    async def new_member_guild(self, member):
        if member.guild.id != GUILD_ID:
            return
        await member.add_roles(get_newcommer_role(), get_ping_poll_role(), get_ping_game_role(),
                               get_ping_declaration_role())

    @commands.Cog.listener('on_member_remove')
    async def member_leaves(self, member):
        if member.guild.id != GUILD_ID:
            return
        if LEAVE_CHANNEL_ID is not None:
            ch = self.bot.get_channel(LEAVE_CHANNEL_ID)
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
        await wbhk.send("**{}** opuścił(-a) serwer".format(member.display_name),
                        avatar_url='https://cdn.discordapp.com/embed/avatars/5.png')

    @commands.Cog.listener('on_raw_reaction_add')
    async def ping_reaction_add(
            self, event: discord.RawReactionActionEvent) -> None:
        if event.message_id != PING_MESSAGE_ID:
            return
        if event.user_id == self.bot.user.id:
            return
        member = get_member(event.user_id)
        if event.emoji.id == PING_YELLOW_ID:
            await member.remove_roles(get_ping_poll_role())
        if event.emoji.id == PING_GREEN_ID:
            await member.remove_roles(get_ping_declaration_role())
        if event.emoji.id == PING_BLUE_ID:
            await member.remove_roles(get_ping_game_role())

    @commands.Cog.listener('on_raw_reaction_remove')
    async def ping_reaction_remove(
            self, event: discord.RawReactionActionEvent):
        if event.message_id != PING_MESSAGE_ID or event.user_id == self.bot.user.id:
            return
        member = get_member(event.user_id)
        if event.emoji.id == PING_YELLOW_ID:
            await member.add_roles(get_ping_poll_role())
        if event.emoji.id == PING_GREEN_ID:
            await member.add_roles(get_ping_declaration_role())
        if event.emoji.id == PING_BLUE_ID:
            await member.add_roles(get_ping_game_role())

    async def cog_check(self, ctx):
        if ctx.author in get_admin_role().members or await self.bot.is_owner(ctx.author):
            return True
        raise commands.MissingRole(get_admin_role())

    @commands.command(name='adminuj')
    async def adminate(self, ctx, *, osoba: MyMemberConverter(player_only=False)):
        """Mianuje nowego admina
        """
        member = osoba
        await member.add_roles(get_admin_role())

    @commands.command(name='nie_adminuj', hidden=True)
    @commands.is_owner()
    async def not_adminate(self, _, *, osoba: MyMemberConverter(player_only=False)):
        """Usuwa admina
        """
        member = osoba
        await member.remove_roles(get_admin_role())

    @commands.command()
    async def ankietka(self, ctx, start: MyDateConverter, end: MyDateConverter, *, period: str = None):  # type: ignore
        """Wysyła na kanał ankietawka ankietę do gry w dzień podany w argumencie.
        Uwaga dzień należy podać w formacie <w/we> <dzień-tygodnia> <data>. Nie zawiera oznaczeń.
        """
        start: dt.date
        end: dt.date
        days = end - start
        if dt.timedelta(0) < days > MAX_DAYS:
            raise commands.BadArgument('Too long or too short day interval')

        data = ''
        date = start
        one_day = dt.timedelta(days=1)
        days = days.days + 1
        for emoji in OPTIONS_EMOJI[:days]:
            weekday = WEEKDAYS[date.weekday()]
            data += ENQUIRY_OPTION.format(emoji=emoji, weekday=weekday, date=date.strftime('%d.%m'))
            date += one_day

        period = period or ENQUIRY_PERIOD.format(start.strftime('%d.%m'), end.strftime('%d.%m'))
        content = ENQUIRY.format(period=period, data=data.strip(), ping_id=PING_YELLOW_ID, ping_green_id=PING_GREEN_ID)

        async with ctx.typing():
            channel = get_ankietawka_channel()
            m = await channel.send(content)
            for emoji in OPTIONS_EMOJI[:days] + ENQUIRY_EMOJI:
                await m.add_reaction(emoji)
            await channel.send(f'<:ping_yellow:{PING_YELLOW_ID}> <@&{PING_POLL_ID}>', reference=m)

            for p in await channel.pins():
                await p.unpin()
            await m.pin()

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
            members = list(get_guild().members)

        await ctx.channel.purge(after=ctx.message.created_at - dt.timedelta(minutes=time),
                                before=ctx.message.created_at, check=lambda mess: mess.author in members)

    @commands.command(name='reakcje')
    async def reactions(self, ctx, wiadomosc: discord.Message):
        """Wysyła podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link
        """
        m = wiadomosc
        reactions = [await r.users().flatten() for r in m.reactions]
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
        maxlen = len(max(members, key=lambda mem: len(mem.display_name)).display_name)
        msg = ''
        for member, r in parsed.items():
            if isinstance(member, discord.Member):
                txt = f'`{member.display_name:{maxlen}} `' + ''.join(r) + '\n'
                if len(msg) + len(txt) >= 2000:  # maximum discord message len
                    await ctx.send(msg)
                    msg = ''
                msg += txt
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send('Do tej wiadomości nie dodano reakcji')

    @commands.command(name='wyślij')
    @commands.dm_only()
    async def special_send(self, ctx, channel_id: Optional[int] = None, *, content):
        """Wysyła podaną wiadomośc na podany kanał lub obecny kanał"""
        if not channel_id:
            await ctx.send(content)
        else:
            try:
                await ctx._state.http.send_message(channel_id, content)
            except discord.HTTPException:
                raise commands.BadArgument('Wrong channel id')

    @commands.command(name='dodaj_reakcje', aliases=['emojis'])
    async def add_reactions(self, _, wiadomosc: discord.Message, *emoji: Union[discord.Emoji, str]):
        for e in emoji:
            try:
                await wiadomosc.add_reaction(e)
            except discord.HTTPException:
                pass


@bot.bot_app_command('reakcje', type_=CommandsTypes.MessageCommand)
async def reactions_msg(ctx, m):
    """Wysyła na DM podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link
    """
    await ctx.ack(ephemeral=True)
    reactions = []
    reactions = [await r.users().flatten() for r in m.reactions]
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
    maxlen = len(max(members, key=lambda mem: len(mem.display_name)).display_name)
    msg = ''
    for member, r in parsed.items():
        if isinstance(member, discord.Member):
            txt = f'`{member.display_name:{maxlen}} `' + ''.join(r) + '\n'
            if len(msg) + len(txt) >= 2000:  # maximum discord message len
                await ctx.send(msg, ephemeral=True)
                msg = ''
            msg += txt
    if msg:
        await ctx.send(msg, ephemeral=True)
    else:
        await ctx.send('Do tej wiadomości nie dodano reakcji', ephemeral=True)
