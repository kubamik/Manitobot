from discord.ext import commands
import datetime as dt
from collections import defaultdict
import asyncio

from settings import PING_GREEN_ID, PING_BLUE_ID, PING_MESSAGE_ID
from utility import *

ankietawka = '**O której możesz grać {date}?**\nZaznacz __wszystkie__ opcje, które ci odpowiadają.\n\nZaznacz :eye: jeśli __zobaczyłæś__ (nawet, jeśli nic innego nie zaznaczasz).\n\n:strawberry: 17.00     :basketball: 18.00     :baby_chick: 19.00     :cactus: 20.00     :whale: 21.00     :grapes: 22.00     :pig: 23.00     :no_entry_sign: Nie mogę grać tego dnia'

ankietawka_emoji = ['🍓', '🏀', '🐤', '🌵', '🐳', '🍇', '🐷', '🚫', '👁️']

zbiorka = 'Zaznaczyłeś, że będziesz grać, więc zapraszam na <#{}>'.format(TOWN_CHANNEL_ID)


class Management(commands.Cog, name='Dla Adminów'):
  def __init__(self, bot):
    self.bot = bot

  def is_admin():
    def predicate(ctx):
      if get_member(ctx.author.id) in get_admin_role().members:
        return True
      raise commands.MissingRole(get_admin_role())
    return commands.check(predicate)

  @bot.listen('on_member_join')
  async def new_member_guild(member):
    await member.add_roles(get_newcommer_role(), get_ping_reminder_role(), get_ping_game_role())

  @bot.listen('on_member_remove')
  async def member_leaves(member):
    ch = get_guild().system_channel
    if ch is None:
      return
    for wb in await ch.webhooks():
      if wb.name == 'System':
        wbhk = wb
        break
    else:
      wbhk = await ch.create_webhook(name='System')
    await wbhk.send("**{}** opuścił(-a) serwer".format(member.display_name), avatar_url='https://wallpaperaccess.com/full/765574.jpg')

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

  @commands.Cog.listener('on_raw_reaction_remove')
  async def ping_reaction_remove(
      self, event: discord.RawReactionActionEvent) -> None:
    if event.message_id != PING_MESSAGE_ID:
      return
    if event.user_id == self.bot.user.id:
      return
    if event.emoji.id == PING_GREEN_ID:
      member = get_member(event.user_id)
      await member.add_roles(get_ping_reminder_role())
    if event.emoji.id == PING_BLUE_ID:
      member = get_member(event.user_id)
      await member.add_roles(get_ping_game_role())

  @commands.command(name='adminuj')
  @is_admin()
  async def adminate(self, ctx, *, member):
    '''Mianuje nowego admina'''
    member = await converter(ctx, member)
    if member is None:
      await ctx.message.delete(delay=5)
      await ctx.send("Nie ma takiej osoby", delete_after=5)
      return
    await member.add_roles(get_admin_role())
    await ctx.message.add_reaction('✅')


  @commands.command(name='nie_adminuj', hidden=True)
  @commands.is_owner()
  async def not_adminate(self, ctx, *, member):
    '''Usuwa admina'''
    member = await converter(ctx, member)
    if member is None:
      await ctx.send("Nie ma takiej osoby")
      return
    await member.remove_roles(get_admin_role())

  @commands.command()
  @is_admin()
  async def ankietka(self, ctx, *, date):
    '''Wysyła na kanał ankietawka ankietę do gry w dzień podany w argumencie. Uwaga dzień należy podać w formacie <w/we> <dzień-tygodnia> <data>. Nie zawiera oznaczeń.'''
    author = get_member(ctx.author.id)
    if author not in get_admin_role().members:
      raise commands.MissingRole(get_admin_role())
    async with ctx.typing():
      m = await get_ankietawka_channel().send(ankietawka.format(date=date))
      tasks = []
      for emoji in ankietawka_emoji:
        tasks.append(m.add_reaction(emoji))
      await asyncio.gather(*tasks)
    await ctx.message.add_reaction('✅')

  
  @commands.command(name='usuń')
  @is_admin()
  async def delete(self, ctx, time: int, *members):
    '''Masowo usuwa wiadomości, używać tylko do spamu!\nSkładnia &usuń <czas w minutach> [członkowie], w przypadku braku podania członków czyszczone są wszystkie wiadomości'''
    if time > 24*60:
      await ctx.send("Maksymalny czas to 24 godziny")
    new_members = []
    if not len(members):
      new_members = list(get_guild().members)
    else:
      for member in members:
        m = member
        member = await converter(ctx, member)
        if member is None:
          await ctx.send(f"Nieznana osoba: {m}")
        else:
          new_members.append(member)
    def proper_members(m):
      return m.author in new_members
    await ctx.channel.purge(after=ctx.message.created_at-dt.timedelta(minutes=time), before=ctx.message.created_at, check=proper_members)
    try:
      await ctx.message.add_reaction('✅')
    except discord.errors.NotFound:
      pass

  @commands.command(name='reakcje', hidden=True)
  @is_admin()
  async def reactions(self, ctx, m : discord.Message):
    '''Wysyła podsumowanie reakcji dodanych do wiadomości przekazanej przez ID lub link'''
    members = defaultdict(list)
    for reaction in m.reactions:
      async for user in reaction.users():
        members[user].append(str(reaction.emoji))
    mess = ""
    for user, r in members.items():
      if user != self.bot.user:
        mess += f'**{get_member(user.id).display_name}:**\t' + '\t'.join(r) + '\n'
    await ctx.send(mess)

  @commands.command(name='gramy', aliases=['zbiórka'])
  @is_admin()
  async def special_send(self, ctx, m : discord.Message, *emojis):
    '''Wysyła wiadomości o grze do wszystkich, którzy oznaczyli dane opcje w podanej wiadomości. Należy podać link lub id wiadomości'''
    reactions = filter(lambda r: r.emoji in emojis, m.reactions)
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
      asyncio.gather(*tasks)
    await ctx.message.add_reaction('✅')



