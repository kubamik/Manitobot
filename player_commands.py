from discord.ext import commands
import datetime as dt

from basic_models import NotAGame
from utility import *
from settings import *
from starting import if_game
import globals
import postacie
import permissions


class DlaGraczy(commands.Cog, name = "Dla Graczy"):
  def __init__(self, bot):
        self.bot = bot

  @commands.command(name='postać')
  async def role_help(self, ctx,*role):
    '''Zwraca informacje o postaci podanej jako argument'''
    await postacie.role_details(ctx, role)
    
  @commands.command(name='czy_gram')
  async def if_registered(command, ctx):
    """Sprawdza czy user ma rolę gram."""
    if czy_gram(ctx):
      await ctx.send("TAK")
    else:
      await ctx.send("NIE")

  @commands.command(name='obserwuję', aliases=['obs'])
  async def spectate(self, ctx):
    """/&obs/Zmienia rolę usera na spectator."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if if_game() and member in get_player_role().members + get_dead_role().members:
      await ctx.send("Gra została rozpoczęta, nie możesz nie grać")
      return
    await member.remove_roles(get_player_role(), get_dead_role())
    await member.add_roles(get_spectator_role())
    nickname = member.display_name
    await ctx.message.add_reaction('✅')
    if not nickname.startswith('!'):
      try:
        await get_member(member.id).edit(nick = "!" + nickname)
      except discord.errors.Forbidden:
        await ctx.send("Dodaj sobie '!' przed nickiem")

  @commands.command(name='nie_obserwuję', aliases=['nie_obs', 'nieobs'])
  async def not_spectate(self, ctx):
    """/&nie_obs/Usuwa userowi rolę spectator."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.remove_roles(get_spectator_role())
    nickname = member.display_name
    if nickname.startswith('!'):
      try:
        await get_member(member.id).edit(nick=nickname[1:])
      except discord.errors.Forbidden:
        pass
    await ctx.message.add_reaction('✅')

  @commands.command(name='pax')
  @game_check()
  async def pax(self, ctx):
    '''Wyrejestrowuje gracza ze zbioru buntowników'''
    try:
      globals.current_game.rioters.remove(get_member(ctx.author.id))
      await ctx.message.add_reaction('🕊️')
    except KeyError:
      await ctx.send("Nie jesteś buntownikiem")
    

  @commands.command(name='bunt', aliases=['riot'])
  @game_check()
  async def riot(self, ctx):
    '''/&riot/W przypadku poparcia przez co najmniej 67 % osób biorących udział w grze kończy grę'''
    if not ((czy_gram(ctx) or czy_trup(ctx)) and on_voice(ctx)):
      await ctx.send("Mogą użyć tylko grający na kanale głosowym")
      return
    globals.current_game.rioters.add(get_member(ctx.author.id))
    count = set()
    for person in globals.current_game.player_map:
      if person in get_voice_channel().members:
        count.add(person)
      else:
        if person in globals.current_game.rioters:
          globals.current_game.rioters.remove(person)
    if len(globals.current_game.rioters) == 1:
      await get_town_channel().send("Ktoś rozpoczął bunt. Użyj `&riot` jeśli chcesz dołączyć")
      await send_to_manitou("Ktoś rozpoczął bunt.")
    if len(globals.current_game.rioters) >= len(count) * 0.67:
      await get_town_channel().send("**Doszło do buntu\nGra została zakończona**")
      for manitou in get_manitou_role().members:
        await manitou.remove_roles(get_manitou_role())
      try:
        for role in globals.current_game.role_map.values():
          if not role.revealed:
            await role.reveal()
        await globals.current_game.message.unpin()
      except AttributeError:
        pass
      manit = bot.cogs['Dla Manitou']
      await bot.change_presence(activity = None)
      player_role = get_player_role()
      dead_role = get_dead_role()
      winner_role = get_duel_winner_role()
      loser_role = get_duel_loser_role()
      searched_role = get_searched_role()
      hanged_role = get_hanged_role()
      for member in dead_role.members + player_role.members:
        await member.remove_roles(dead_role, winner_role, loser_role, searched_role, hanged_role)
        if member in get_voice_channel().members:
          await member.add_roles(player_role)
      globals.current_game = NotAGame()
      await manit.remove_cogs()
    await ctx.message.add_reaction("👊")
      

  @commands.command(name="żywi",aliases=['zywi'])
  @game_check()
  async def living(self, ctx):
    """/&zywi/Wypisuje listę żywych graczy"""
    team = ""
    alive_roles = []
    for role in globals.current_game.roles:
      if globals.current_game.role_map[role].player.member in get_player_role().members or (globals.current_game.role_map[role].player.member in get_dead_role().members and not globals.current_game.role_map[role].revealed):
        alive_roles.append(role)
    team = postacie.print_list(alive_roles)
    await ctx.send("""Liczba żywych graczy: {}
Liczba martwych o nieznanych rolach: {}
Pozostali:{}""".format(len(get_player_role().members),len(alive_roles) - len(get_player_role().members),team))

  

  @commands.command(name='g', help=playerhelp(), hidden=True)
  async def player_help(self, ctx):
    await ctx.message.delete(delay=0)

      
