from discord.ext import commands

import globals
from settings import FRAKCJE_CATEGORY_ID
from utility import manitou_cmd, get_guild, get_dead_role, get_nickname


class WywolywaniePostaci(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    '''@commands.command(name='szeryf')
    @manitou_cmd
    async def sheriff(self, ctx):
      """ⓂRozpoczyna czas działania szeryfa, wysyła mu instrukcję"""
      try:
        if globals.current_game.active_player != None:
          await ctx.send("Teraz trwa runda {}. Zakończ ją używając `&cancel` i spróbuj ponownie.".format(globals.current_game.active_player.name))
          return
        me = globals.current_game.role_map["Szeryf"]
        await me.night_start(ctx)
      except InvalidRequest as err:
        await send_to_manitou(err.reason)
        if ctx.channel == get_manitou_notebook():
          await ctx.send(err.reason)
      except:
        await ctx.send("Szeryf teraz nie gra lub gra nie została rozpoczęta")
  
    @commands.command(name="pijemy")
    @manitou_cmd
    async def drinking(self, ctx):
      """ⓂRozpoczyna czas działania opoja/pijanego sędziego, wysyła mu instrukcję"""
      try:
        if globals.current_game.active_player != None:
          await ctx.send("Teraz trwa runda {}. Zakończ ją używając `&cancel` i spróbuj ponownie.".format(globals.current_game.active_player.name))
          return
        me = globals.current_game.role_map["Pijany_Sędzia"]
      except:
        try:
          me = globals.current_game.role_map["Opój"]
        except:
          await ctx.send("W tej grze nie gra nikt kto może upijać lub gra nie została rozpoczęta")
          return
      try:
        await me.night_start(ctx)
      except InvalidRequest as err:
        await send_to_manitou(err.reason)
        if ctx.channel == get_manitou_notebook():
          await ctx.send(err.reason)
  
    @commands.command(name='pastor')
    @manitou_cmd
    async def pastor(self, ctx):
      """ⓂRozpoczyna czas działania pastora, wysyła mu instrukcję"""
      try:
        if globals.current_game.active_player != None:
          await ctx.send("Teraz trwa runda {}. Zakończ ją używając `&cancel` i spróbuj ponownie.".format(globals.current_game.active_player.name))
          return
        me = globals.current_game.role_map["Pastor"]
        await me.night_start(ctx)
      except InvalidRequest as err:
        await send_to_manitou(err.reason)
        if ctx.channel == get_manitou_notebook():
          await ctx.send(err.reason)
      except:
        await ctx.send("Pastor teraz nie gra lub gra nie została rozpoczęta")
  
    @commands.command(name='dziwka')
    @manitou_cmd
    async def dziwka(self, ctx):
      """ⓂRozpoczyna czas działania dziwki, wysyła jej instrukcję"""
      try:
        if globals.current_game.active_player != None:
          await ctx.send("Teraz trwa runda {}. Zakończ ją używając `&cancel` i spróbuj ponownie.".format(globals.current_game.active_player.name))
          return
        me = globals.current_game.role_map["Dziwka"]
        print("kk",globals.current_game.role_map)
        await me.night_start(ctx)
      except InvalidRequest as err:
        await send_to_manitou(err.reason)
        if ctx.channel == get_manitou_notebook():
          await ctx.send(err.reason)
      except:
        await ctx.send("Dziwka teraz nie gra lub gra nie została rozpoczęta")
      
  
  
    @commands.command(name='cancel')
    @manitou_cmd
    async def interrupt(self, ctx):
      """ⓂAnuluje trwającą rundę postaci"""
      try:
        await ctx.send("Anulowano rundę {}".format(globals.current_game.active_player.name))
        globals.current_game.active_player = None
      except:
        await ctx.send("Nie trwa runda żadnej postaci lub gra nie została rozpoczęta")'''

    @commands.command(name="day")
    @manitou_cmd
    async def night_end(self, ctx):
        """ⓂRozpoczyna dzień"""
        if not globals.current_game.night:
            await ctx.send("Dzień można rozpocząć tylko w nocy")
            return
        globals.current_game.used_roles = []
        globals.current_game.new_day()
        for member in globals.current_game.sleeped_players:
            member.sleeped = False
        globals.current_game.sleeped_players = set()
        for member in globals.current_game.protected_players:
            member.protected = False
        globals.current_game.protected_players = set()
        for member in globals.current_game.killing_protected_players:
            member.killing_protected = False
        globals.current_game.killing_protected_players = set()
        globals.current_game.day += 1
        globals.current_game.night = False
        for channel in get_guild().text_channels:
            if channel.category_id == FRAKCJE_CATEGORY_ID:
                await channel.send(
                    "=\nDzień {}".format(globals.current_game.day))
        for member in get_dead_role().members:
            nickname = get_nickname(member.id)
            if not globals.current_game.player_map[member].role_class.revealed:
                await globals.current_game.player_map[
                    member].role_class.reveal()
        await ctx.message.add_reaction('✅')

    @commands.command(name="night")
    @manitou_cmd
    async def night_start(self, ctx):
        '''ⓂRozopoczyna noc'''
        if globals.current_game.night:
            await ctx.send("Noc można rozpocząć tylko w dzień")
            return
        globals.current_game.new_night()
        globals.current_game.night = True
        await ctx.message.add_reaction('✅')
