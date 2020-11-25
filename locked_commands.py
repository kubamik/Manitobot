from discord.ext import commands

from utility import *
from settings import *
from starting import if_game
import globals
import postacie

# Removed


class FunkcjeBlokowane(commands.Cog):

  def __init__(self,bot):
    self.bot = bot

  @commands.command(name="żywi")
  async def living(self, ctx):
    """Wypisuje listę żywych graczy"""
    team = ""
    alive_roles = []
    for role in globals.current_game.roles:
      if globals.current_game.role_map[role].player.member in get_player_role().members or (globals.current_game.role_map[role].player.member in get_dead_role().members and not globals.current_game.role_map[role].revealed):
        alive_roles.append(role)
    team = postacie.print_list(alive_roles)
    await ctx.send("""Liczba żywych graczy: {}
Liczba martwych o nieznanych rolach: {}
Pozostali:{}""".format(len(get_player_role().members),len(alive_roles) - len(get_player_role().members),team))

  
  @commands.command(name='reveal')
  async def player_reveal(self, ctx):
    """Dodaje w nicku rolę. Do użycia po śmierci"""
    member = ctx.author
    if globals.current_game is None:
      await ctx.send("Gra nie została rozpoczęta")
      return
    if member not in get_dead_role().members:
      await ctx.send("Tylko martwi mogą się ujawniać")
      return
    if globals.current_game.night:
      await ctx.send("Ujawniać można się tylko w dzień")
      return
    nickname = get_nickname(ctx.author.id)
    globals.current_game.player_map[member].role_class.revealed = True
    if nickname[-1] != ')':
      try:
        await member.edit(nick=nickname + "({})".format(globals.current_game.player_map[member].role.replace('_',' ')))
      except discord.errors.Forbidden:
        await member.create_dm()
        await member.dm_channel.send("Zmień swój nick na {}, bo ja nie mam uprawnień.".format(nickname+"({})".format(globals.current_game.player_map[member].role.replace('_',' '))))
        await ctx.send("Nie mam uprawnień aby zmienić nick")
      await get_town_channel().send("Rola **{}** to **{}**".format(nickname.replace('+',' '),globals.current_game.player_map[member].role.replace('_',' ')))
      await ctx.send("Done!")
    else:
      await ctx.send("Jesteś już ujawniony")