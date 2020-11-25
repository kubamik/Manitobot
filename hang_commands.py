from utility import *
from discord.ext import commands
import discord
#kolejność, kończenie głosowania przy przerwij, swap
from settings import FRAKCJE_CATEGORY_ID
import globals
from starting import if_game



class Wieszanie(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

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