import asyncio
import datetime as dt
from collections import defaultdict

import discord
from discord.ext import commands

from converters import MyMemberConverter
from settings import TOWN_CHANNEL_ID, PING_MESSAGE_ID, PING_GREEN_ID, PING_BLUE_ID, GUILD_ID
from utility import get_newcommer_role, get_ping_reminder_role, get_ping_game_role, get_member, get_admin_role, \
    get_ankietawka_channel, get_guild, get_voice_channel

ankietawka = '''**O której możesz grać {date}?**
Zaznacz __wszystkie__ opcje, które ci odpowiadają.

Zaznacz :eye: jeśli __zobaczyłæś__ (nawet, jeśli nic innego nie zaznaczasz).
:strawberry: 17.00     :basketball: 18.00     :baby_chick: 19.00     :cactus: 20.00     :whale: 21.00\
     :grapes: 22.00     :pig: 23.00     :no_entry_sign: Nie mogę grać tego dnia'''

ankietawka_emoji = ['🍓', '🏀', '🐤', '🌵', '🐳', '🍇', '🐷', '🚫', '👁️']

zbiorka = 'Zaraz gramy, więc zapraszam na <#{}>'.format(TOWN_CHANNEL_ID)


class Management(commands.Cog, name='Dla Adminów'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_member_join')
    async def new_member_guild(self, member):
        if member.guild.id != GUILD_ID:
            return
        await member.add_roles(get_newcommer_role(), get_ping_reminder_role(), get_ping_game_role())

    @commands.Cog.listener('on_member_remove')
    async def member_leaves(self, member):
        if member.guild.id != GUILD_ID:
            return
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
                        avatar_url='https://discord.com/assets/2c21aeda16de354ba5334551a883b481.png')

    @commands.Cog.listener('on_raw_reaction_add')
    async def ping_reaction_add(
            self, event: discord.RawReactionActionEvent) -> None:
        if event.message_id != PING_MESSAGE_ID:
            return
        if event.user_id == self.bot.user.id:
            return
        if event.emoji.id == PING_GREEN_ID:
            member = get_member(event.user_id)
            await member.remove_roles(get_ping_reminder_role())
        if event.emoji.id == PING_BLUE_ID:
            member = get_member(event.user_id)
            await member.remove_roles(get_ping_game_role())

    async def cog_check(self, ctx):
        if ctx.author in get_admin_role().members or await self.bot.is_owner(ctx.author):
            return True
        raise commands.MissingRole(get_admin_role())

    @commands.Cog.listener('on_raw_reaction_remove')
    async def ping_reaction_remove(
            self, event: discord.RawReactionActionEvent):
        if event.message_id != PING_MESSAGE_ID or event.user_id == self.bot.user.id:
            return
        member = get_member(event.user_id)
        if event.emoji.id == PING_GREEN_ID:
            await member.add_roles(get_ping_reminder_role())
        if event.emoji.id == PING_BLUE_ID:
            await member.add_roles(get_ping_game_role())

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
    async def ankietka(self, ctx, *, data):
        """Wysyła na kanał ankietawka ankietę do gry w dzień podany w argumencie.
        Uwaga dzień należy podać w formacie <w/we> <dzień-tygodnia> <data>. Nie zawiera oznaczeń.
        """
        async with ctx.typing():
            m = await get_ankietawka_channel().send(ankietawka.format(date=data))
            for emoji in ankietawka_emoji:
                await m.add_reaction(emoji)

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

        if not len(members):
            members = list(get_guild().members)

        await ctx.channel.purge(after=ctx.message.created_at - dt.timedelta(minutes=time),
                                before=ctx.message.created_at, check=lambda mess: mess.author in members)
        try:
            await ctx.message.add_reaction('✅')
        except discord.errors.NotFound:
            pass

    @commands.command(name='reakcje')
    async def reactions(self, ctx, wiadomosc: discord.Message):
        """Wysyła podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link
        """
        m = wiadomosc
        members = defaultdict(list)
        for reaction in m.reactions:
            async for user in reaction.users():
                members[user].append(str(reaction.emoji))
        msg = ""
        for member, r in members.items():
            if isinstance(member, discord.Member) and member.id != self.bot.user.id:
                msg += f'**{member.display_name}:**\t' + '\t'.join(r) + '\n'
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send('Do tej wiadomości nie dodano reakcji')

    @commands.command(name='gramy', aliases=['zbiórka'])
    async def special_send(self, ctx, wiadomosc: discord.Message, *emoji):
        """Wysyła wiadomości o grze do wszystkich, którzy oznaczyli dane opcje w podanej wiadomości.
        Należy podać link lub id wiadomości.
        """
        m = wiadomosc
        reactions = filter(lambda rn: rn.emoji in emoji, m.reactions)
        members = set()
        tasks = []
        async with ctx.typing():
            for r in reactions:
                async for member in r.users():
                    members.add(member)
            members -= {self.bot.user, get_member(self.bot.user.id)}
            members -= set(get_voice_channel().members)
            for member in members:
                tasks.append(member.send(zbiorka))
            await asyncio.gather(*tasks, return_exceptions=True)
