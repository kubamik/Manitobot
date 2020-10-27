from discord.ext import commands
import discord

from utility import *
from settings import FRAKCJE_CATEGORY_ID
import globals
from starting import if_game



class Pojedynki(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def cog_check(self, ctx):
    try:
      return not globals.current_game.night and (not globals.current_game.days[-1].duel or get_member(ctx.author.id) in get_manitou_role().members)
    except:
      return False

  async def cog_command_error(self, ctx, error):
    if type(error) is commands.CheckFailure:
      await ctx.send("Tej komendy można używać tylko w dzień i (prawdopodobnie) nie w trakcie pojedynku", delete_after=5)


  @commands.command(name='wyzywam')
  async def duel_dare(self,ctx,*, gracz):
    '''Wyzywa podaną osobę na pojedynek'''
    try:
      member = await converter(ctx, gracz)
      author = get_member(ctx.author.id)
      playing(member, author=author)
      if member == author:
        await ctx.send("Celujesz sam w siebie, ale przypominasz sobie, że Twój pies będzie smutny")
        return
      globals.current_game.days[-1].add_dare(author, member)
      await globals.current_game.days[-1].if_start(author, member)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='odrzucam', aliases=['spierdalaj'])
  async def decline(self,ctx):
    '''/&od/Służy do odrzucenia pojedynku'''
    try:
      author = get_member(ctx.author.id)
      playing(author=author)
      mess = globals.current_game.days[-1].remove_dare(author)
      await get_town_channel().send(mess)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next()
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='przyjmuję', aliases=['pr'])
  async def accept(self,ctx):
    '''/&pr/Służy do przyjęcia pojedynku'''
    author = get_member(ctx.author.id)
    try:
      c = globals.current_game.days[-1].accept(author)
      await get_town_channel().send(c)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next(True)
    except InvalidRequest as err:
      await ctx.send(err.reason)

  
  @commands.command(name='break', aliases=['br'])
  @manitou_cmd
  async def interrupt(self, ctx):
    '''Ⓜ/&br/Przerywa trwający pojedynek lub usuwa pierwsze wyzwanie z listy'''
    try:
      c = await globals.current_game.days[-1].interrupt()
      await get_town_channel().send(c)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next()
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='wyzwania', aliases=['pend'])
  @manitou_cmd
  async def challenges(self, ctx):
    '''Ⓜ/&pend/Pokazuje aktualne wyzwania'''
    c = globals.current_game.days[-1].dares_print()
    await ctx.send(c)


  @commands.command(name='duelend', aliases=['dnd'])
  @manitou_cmd
  async def duel_end(self, ctx):
    '''Ⓜ/&dnd/Kończy pojedynek z wynikiem ogłoszonym automatycznie'''
    try:
      await globals.current_game.days[-1].end_duel(ctx)
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='search_phase', aliases=['abend'])
  @manitou_cmd
  async def no_duels(self, ctx):
    '''Ⓜ/&abend/Kończy turę pojedynków'''
    globals.current_game.days[-1].duels_today = globals.current_game.duels
    await ctx.message.add_reaction('✅')
    await get_town_channel().send("__Zakończono turę pojedynków__")
    