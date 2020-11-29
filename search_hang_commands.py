from discord.ext import commands
import discord

from utility import *
#kolejność, kończenie głosowania przy przerwij, swap
from settings import FRAKCJE_CATEGORY_ID
import globals
from starting import if_game

class Przeszukania(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def cog_check(self, ctx):
    try:
      return not globals.current_game.night and not globals.current_game.days[-1].duel
    except:
      return False

  async def cog_command_error(self, ctx, error):
    if type(error) is commands.CheckFailure:
      await ctx.send("Tej komendy można używać tylko w dzień i nie w trakcie pojedynku", delete_after=5)

  @commands.command(name='zgłaszam')
  async def duel_dare(self, ctx, *, gracz):
    """Zgłasza podaną osobę do przeszukania"""
    gracz = await converter(ctx, gracz)
    member = get_member(ctx.author.id)
    try:
      playing(gracz, author = member)
      globals.current_game.days[-1].add_report(member, gracz)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)
      return
    

  @commands.command(name='cofam')
  async def undo(self, ctx, *, gracz):
    """Cofa zgłoszenie podanej osoby do przeszukania"""
    gracz = await converter(ctx, gracz)
    member = get_member(ctx.author.id)
    try:
      playing(gracz, author = member)
      globals.current_game.days[-1].remove_report(member, gracz)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)
      return

  
  @commands.command(name='end_reports', aliases=['repblok'])
  @manitou_cmd()
  async def end_reports(self, ctx):
    '''ⓂBlokuje zgłaszanie nowych osób do przeszukania'''
    globals.current_game.days[-1].search_lock = True
    await ctx.message.add_reaction('✅')


  @commands.command(name='reported', aliases=['rpt'])
  @manitou_cmd()
  async def reported(self, ctx):
    """ⓂPokazuje aktualne zgłoszenia"""
    await ctx.send(globals.current_game.days[-1].report_print())


  @commands.command(name='searchend', aliases=['snd'])
  @manitou_cmd()
  async def search_end(self, ctx):
    '''Ⓜ/&snd/Kończy przeszukania'''
    if not globals.current_game.days[-1].search_final:
      await ctx.send("Najpierw musisz przeprowadzić głosowanie")
      return
    if globals.current_game.days[-1].hang_time:
      await ctx.send("Przeszukania już były")
      return
    try:
      await globals.current_game.days[-1].search_finalize(ctx)
    except InvalidRequest:
      pass
    else:
      await ctx.message.add_reaction('✅')


  @commands.command(name='search_random', aliases=['srnd'])
  @manitou_cmd()
  async def searchrand(self, ctx):
    '''Ⓜ/&hrnd/Wyłania drogą losową przeszukiwanych osobę'''
    if globals.current_game.night:
      await ctx.send("Trwa noc!")
      return
    c = await globals.current_game.days[-1].search_random()
    if c:
      await ctx.send(c)



class Wieszanie(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def cog_check(self, ctx):
    try:
      return not globals.current_game.night
    except:
      return False

  async def cog_command_error(self, ctx, error):
    if type(error) is commands.CheckFailure:
      await ctx.send("Tej komendy można używać tylko w dzień", delete_after=5)

  @commands.command(name='hangend',aliases=['hnd'])
  @manitou_cmd()
  async def hangend(self, ctx):
    '''Ⓜ/&hnd/Finalizuje wieszanie'''
    if globals.current_game.night:
      await ctx.send("Trwa noc!")
      return
    try:
      await globals.current_game.days[-1].hang_finalize(ctx)
      await ctx.message.add_reaction('✅')
    except InvalidRequest:
      pass

  @commands.command(name='hang_random', aliases=['hrnd'])
  @manitou_cmd()
  async def hangrand(self, ctx):
    '''Ⓜ/&hrnd/Wyłania drogą losową wieszaną osobę'''
    if globals.current_game.night:
      await ctx.send("Trwa noc!")
      return
    c = await globals.current_game.days[-1].hang_random()
    if c:
      await ctx.send(c)