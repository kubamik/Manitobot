from random import randint
from discord.ext import commands
import discord
import asyncio

from utility import manitou_cmd, GameEnd
from utility import *
from settings import *
import globals
from votings import glosowanie, see_voting
from starting import start_game,if_game
import sklady
import locked_commands
from postacie import get_role_details
import postacie
from game import Game


class DlaManitou(commands.Cog, name="Dla Manitou"):

  def __init__(self, bot):
    self.bot = bot

  async def remove_cogs(self):
    bot.remove_cog("Głosowania")
    bot.remove_cog("Polecenia postaci i frakcji")
    bot.remove_cog("Pojedynki")
    bot.remove_cog("Przeszukania")
    bot.remove_cog("Wieszanie")
    bot.get_command('g').help = playerhelp()
    bot.get_command('m').help = manitouhelp()
    p = discord.Permissions().all()
    try:
      await get_admin_role().edit(permissions = p)
    except (NameError, discord.errors.Forbidden):
      pass
    
  @commands.command(name='set_manitou_channel', aliases=['m_channel'])
  @manitou_cmd
  async def set_m_channel(self, ctx):
    '''Ⓜ/&m_channel/Użyte na serwerze ustawia kanał Manitou na #notatnik-manitou, użyte na DM ustawia na DM'''
    if (ctx.channel.type == discord.ChannelType.private):
      CONFIG['DM_Manitou'] = True
    else:
      CONFIG['DM_Manitou'] = False
    await ctx.message.add_reaction('✅')


  @commands.command(name='tea', enabled=False, hidden=True)
  @manitou_cmd
  async def tea(self, ctx):
    '''ⓂUruchamia śmierć od ziółek'''
    if globals.current_game.night:
      await ctx.send("Nie możesz tego użyć podczas nocy", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    herb = globals.current_game.nights[-1].herbed
    if herb is None:
      await ctx.send("Nikt nie ma podłożonych ziółek", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    await get_town_channel().send("Ktoś robi się zielony(-a) na twarzy :sick: i...")
    await asyncio.sleep(3)
    await herb.die("herbs")
    await ctx.message.add_reaction('✅')

  @commands.command(name='next', aliases=['n'], enabled=False, hidden=True)
  @manitou_cmd
  async def next_night(self,ctx):
    """Ⓜ/&n/Rozpoczyna rundę następnej postaci w trakcie nocy."""
    if not globals.current_game.night:
      await ctx.send("Tej komendy można użyć tylko w nocy", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    if ctx.channel.type != discord.ChannelType.private and ctx.channel != get_manitou_notebook():
      await ctx.send("Tej komendy można użyć tylko w DM lub notatniku manitou", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    await globals.current_game.nights[-1].night_next(ctx.channel)


  @bot.listen('on_reaction_add')
  async def new_reaction(emoji, member):
    if not get_member(member.id) in get_manitou_role().members:
      return
    if emoji.emoji != '➡️':
      return
    if not emoji.me:
      return
    await globals.current_game.nights[-1].night_next(emoji.message.channel)


  @commands.command(name='nuke')
  @manitou_cmd
  async def nuke(self, ctx):
    """ⓂOdbiera rolę Gram i Trup wszystkim userom"""
    if if_game():
      await ctx.send("Najpierw zakończ grę!", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    player_role = get_player_role()
    dead_role = get_dead_role()
    spec_role = get_spectator_role()
    async with ctx.typing():
      await self.remove_cogs()
      for member in dead_role.members:
        await member.remove_roles(dead_role)
        await clear_nickname(member, ctx)
      for member in player_role.members:
        await member.remove_roles(player_role)
        await clear_nickname(member, ctx)
      for member in spec_role.members:
        await member.remove_roles(spec_role)
        await clear_nickname(member, ctx) 
    await ctx.message.add_reaction('❤️')


  @commands.command(name='kill')
  @manitou_cmd
  async def kill(self, ctx,*, gracz):
    """ⓂZabija otagowaną osobę"""
    gracz = await converter(ctx, gracz)
    if gracz is None or gracz not in get_guild().members:
      await ctx.send("Nie ma takiego gracza")
      return
    if gracz in get_dead_role().members:
      await ctx.send("Ten gracz już nie żyje")
      return
    if not if_game() or gracz not in get_player_role().members:
      await ctx.send("Ten gracz musi grać, aby mógł zginąć")
      return
    await globals.current_game.player_map[gracz].role_class.die()
    await ctx.message.add_reaction('✅')

  @commands.command(name='plant', aliases=[])
  @manitou_cmd
  async def plant(self, ctx, *, member):
    '''ⓂPodkłada posążek wskazanegu graczowi, nie zmieniając frakcji posiadaczy'''
    member = await converter(ctx, member)
    try:
      playing(member)
      globals.current_game.statue.manitou_plant(member)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='give',aliases=['statue'])
  @manitou_cmd
  async def give(self, ctx, *, member):
    '''Ⓜ/&statue/&statuette/Daje posążek w posiadanie wskazanegu graczowi'''
    member = await converter(ctx, member)
    try:
      playing(member)
      globals.current_game.statue.give(member)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)

  @commands.command(name='who_has',aliases=['whos','whohas'])
  @manitou_cmd
  async def who_has(self, ctx):
    '''Ⓜ/&whos/&who_has/Wysyła do Manitou kto ma aktualnie posążek'''
    try:
      c = "Posążek {}jest podłożony i ma go **{}**, frakcja **{}**".format("nie " if not globals.current_game.statue.planted else "", globals.current_game.statue.holder.display_name, globals.current_game.statue.faction_holder)
    except AttributeError:
      c = f"Posążek ma frakcja **{globals.current_game.statue.faction_holder}**, posiadacz jest nieustalony."
    await send_to_manitou(c)
    await ctx.message.add_reaction('✅')

  @commands.command(name='swap')
  @manitou_cmd
  async def swap(self, ctx, first, second):
    '''ⓂZamienia role 2 wskazanych osób'''
    first = await converter(ctx, first)
    second = await converter(ctx, second)
    try:
      role1,role2 = globals.current_game.swap(first, second)
      await first.send("Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(get_role_details(role1, role1)))
      await second.send("Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(get_role_details(role2, role2)))
      await send_to_manitou("**{}** to teraz **{}**\n**{}** to teraz **{}**".format(first.display_name, role1, second.display_name, role2))
      await ctx.message.add_reaction('✅')
    except KeyError:
      await ctx.send("Ta osoba nie gra lub nie ma takiej osoby")


  @commands.command(name='revealdead',aliases=['red'])
  @manitou_cmd
  async def dead_reveal(self,ctx):
    """Ⓜ/&red/Dodaje w nicku rolę wszystkim martwym graczom"""
    for member in get_dead_role().members:
      if not globals.current_game.player_map[member].role_class.revealed:
        await globals.current_game.player_map[member].role_class.reveal()
    await ctx.message.add_reaction('✅')


  @commands.command(name='gra')
  async def if_game_started(self, ctx):
    """Służy do sprawdzania czy gra została rozpoczęta"""
    if if_game():
      await ctx.send("Gra została rozpoczęta")
    else:
      await ctx.send("Gra nie została rozpoczęta")


  @commands.command(name='end_game')
  @manitou_cmd
  async def end_game(self, ctx):
    """ⓂKończy grę"""
    async with ctx.typing():
      for role in globals.current_game.role_map.values():
        if not role.revealed:
          await role.reveal()
      try:
        await globals.current_game.message.unpin()
      except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError):
        pass
      try:
        await get_town_channel().set_permissions(get_player_role(), send_messages = True)
      except (discord.Forbidden, discord.HTTPException):
        pass
      globals.current_game = None
      await self.remove_cogs()
      await bot.change_presence(activity = None)
      await get_town_channel().send("Gra została zakończona")

  

  @commands.command(name='end')
  @manitou_cmd
  async def end_reset(self, ctx):
    """ⓂResetuje graczy i kończy grę"""
    if globals.current_game is None:
      raise AttributeError('Game not started')
    m = await ctx.send("Czy na pewno chcesz zakończyć grę?")
    await m.add_reaction('✅')
    await m.add_reaction('⛔')
    def check_func(r, u):
      if get_member(u.id) not in get_manitou_role().members or r.emoji not in ('✅', '⛔') or r.message.id != m.id:
        return False
      return True
    try:
      reaction, _ = await bot.wait_for('reaction_add', check=check_func, timeout=60)
      if reaction.emoji == '✅':
        raise asyncio.TimeoutError
      await ctx.message.delete(delay=0)
    except asyncio.TimeoutError:
      await self.end_game(ctx)
      await self.resetuj_grajacych(ctx)
      await ctx.message.add_reaction('✅')
    await m.delete()
    

  @commands.command(name='Manitou_help', aliases=['mhelp'])
  @manitou_cmd
  async def manithelp(self, ctx):
    '''Ⓜ/&mhelp/Pokazuje skrótową pomoc dla Manitou'''
    comm = ['give', 'kill', 'day', 'pend', 'br', 'vdl', 'vend', 'dnd', 'abend', 'rpt', 'repblok', 'vsch', 'snd', 'vhif', 'vhg', 'hnd',  'night']
    mess = ""
    for c in comm:
      mess += help_format(c)
    await ctx.send(f'```fix\n{mess}```')

  @commands.command(name='random')
  @manitou_cmd
  async def losuj(self, ctx, n):
    """ⓂLosuje liczbę naturalną z przedziału [1, n]"""
    try:
      n = int(n)
      if (n < 1):
        await ctx.send("Należy podać liczbę naturalną dodatnią")
        return
      r = randint(1, n)
      await ctx.send(r)
    except ValueError:
        await ctx.send("Należy podać liczbę naturalną dodatnią")


  @commands.command(name='revive', aliases=['resetuj','reset'])
  @manitou_cmd
  async def resetuj_grajacych(self, ctx):
    """Ⓜ/&resetuj/Przywraca wszystkim trupom rolę gram"""
    if if_game():
      await ctx.send("Najpierw zakończ grę!", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    player_role = get_player_role()
    dead_role = get_dead_role()
    winner_role = get_duel_winner_role()
    loser_role = get_duel_loser_role()
    searched_role = get_searched_role()
    hanged_role = get_hanged_role()
    p = discord.Permissions().all()
    try:
      await get_admin_role().edit(permissions = p)
    except (NameError, discord.errors.Forbidden):
      pass
    async with ctx.typing():
      for member in dead_role.members + player_role.members:
        await member.remove_roles(dead_role, winner_role, loser_role, searched_role, hanged_role)
        if member in get_voice_channel().members:
          await member.add_roles(player_role)
      await self.remove_cogs()
    await get_town_channel().send("Wszystkim z rolą 'Trup' na kanale głosowym nadano rolę 'Gram!'")


  @commands.command(name="alives")
  @manitou_cmd
  async def alives(self, ctx):
    """Ⓜ&żywi dla Manitou (nie używać publicznie)"""
    team = ""
    try:
      alive_roles = []
      for role in globals.current_game.roles:
        if globals.current_game.role_map[role].player.member in get_player_role().members and not globals.current_game.role_map[role].player.member in get_dead_role().members:
          alive_roles.append(role)
      team = postacie.print_list(alive_roles)
      await ctx.send(
      """Liczba żywych graczy: {}
Pozostali:{}""".format(len(alive_roles),team))
    except AttributeError:
      await ctx.send("Najpierw rozpocznij grę")


  @commands.command(name='rioters_count', aliases=['criot'])
  @manitou_cmd
  async def countrioters(self, ctx):
    '''ⓂZwraca liczbę zbuntowanych graczy'''
    await ctx.send("Liczba buntowników wynosi {}".format(len(globals.current_game.rioters)))

  @commands.command(name='searches')
  @manitou_cmd
  async def searches(self, ctx, n: int):
    '''ⓂZmienia ilość przeszukań dziennie'''
    globals.current_game.searches = n
    await ctx.message.add_reaction('✅')

  @commands.command(name='duels')
  @manitou_cmd
  async def duels(self, ctx, n: int):
    '''ⓂZmienia ilość pojedynków dziennie'''
    globals.current_game.duels = n
    await ctx.message.add_reaction('✅')

  @commands.command(name='evening', aliases=['even'])
  @manitou_cmd
  async def evening(self, ctx, n: int):
    '''Ⓜ/&even/Ustawia czas odjazdu bandytów na podany wieczór'''
    globals.current_game.bandit_night = n
    globals.current_game.bandit_morning = False
    await ctx.message.add_reaction('✅')
  
  @commands.command(name='morning', aliases=['morn'])
  @manitou_cmd
  async def morning(self, ctx, n: int):
    '''Ⓜ/&morn/Ustawia czas odjazdu bandytów na podany poranek'''
    globals.current_game.bandit_night = n
    globals.current_game.bandit_morning = True
    await ctx.message.add_reaction('✅')

  @commands.command(name="day")
  @manitou_cmd
  async def night_end(self, ctx):
    """ⓂRozpoczyna dzień"""
    if not globals.current_game.night:
      await ctx.send("Dzień można rozpocząć tylko w nocy", delete_after=5)
      await ctx.message.delete(delay=5)
      return
    await globals.current_game.new_day()
    for channel in get_guild().text_channels:
      if channel.category_id==FRAKCJE_CATEGORY_ID:
        await channel.send("=\nDzień {}".format(globals.current_game.day))
    try:
      await get_town_channel().set_permissions(get_player_role(), send_messages = True)
    except (discord.Forbidden, discord.HTTPException):
      pass
    for member in get_dead_role().members:
      if not globals.current_game.player_map[member].role_class.revealed:
        await globals.current_game.player_map[member].role_class.reveal()
    await ctx.message.add_reaction('✅')

  @commands.command(name="night")
  @manitou_cmd
  async def night_start(self, ctx):
    '''ⓂRozpoczyna noc'''
    if globals.current_game.night:
      await ctx.send("Noc można rozpocząć tylko w dzień", delete_after=5)
      await ctx.message.delete(delay=5)
    try:
      await get_town_channel().set_permissions(get_player_role(), send_messages = False)
    except (discord.Forbidden, discord.HTTPException):
      pass
    globals.current_game.new_night()
    globals.current_game.night = True
    await ctx.message.add_reaction('✅')

  @commands.command(name='m', help=manitouhelp(), hidden=True)
  async def manitou_help(self, ctx):
    await ctx.message.delete(delay=0)