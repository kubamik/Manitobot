from random import randint
from discord.ext import commands
import discord
from collections import Counter

import control_panel
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
import duels_commands
import hang_commands
import voting_commands
import manitou_commands
import roles_commands
import search_hang_commands

class Starting(commands.Cog, name='Początkowe'):

  def __init__(self, bot):
    self.bot = bot

  async def add_cogs(self):
    try:
      bot.add_cog(voting_commands.Glosowania(bot))
      bot.add_cog(roles_commands.PoleceniaPostaci(bot))
      bot.add_cog(duels_commands.Pojedynki(bot))
      bot.add_cog(search_hang_commands.Przeszukania(bot))
      bot.add_cog(search_hang_commands.Wieszanie(bot))
      bot.add_cog(control_panel.ControlPanel(bot))
    except discord.errors.ClientException:
      pass
    bot.get_command('g').help = playerhelp()
    bot.get_command('m').help = manitouhelp()
    p = discord.Permissions().all()
    p.administrator = False
    try:
      await get_admin_role().edit(permissions = p, colour = 0)
    except (NameError, discord.errors.Forbidden):
      pass

  async def add_cogs_lite(self):
    try:
      bot.add_cog(voting_commands.Glosowania(bot))
    except discord.errors.ClientException:
      pass
    bot.get_command('g').help = playerhelp()
    bot.get_command('m').help = manitouhelp()
    p = discord.Permissions().all()
    p.administrator = False
    try:
      await get_admin_role().edit(permissions = p)
    except (NameError, discord.errors.Forbidden):
      pass

  @commands.command(name="start_mafia")
  @manitou_cmd()
  async def mafia_start(self, ctx, *roles : str):
    '''Rozpoczyna mafię.\nW argumencie należy podać listę postaci (oddzielonych spacją) z liczebnościami w nawiasie (jeśli są różne od 1) np. Miastowy(5).\nWażne jest zachowanie kolejności - rola mafijna jako ostatnia lub w przypadku większej ilości ról mafii oddzielenie ich '|'.\nnp. &start_mafia Miastowy(7) Detektyw Lekarz | Boss Mafiozo(2) lub\n&start_mafia Miastowy(3) Mafiozo'''
    roles = list(roles)
    stop = -1 if '|' not in roles else roles.index('|')
    roles_list = Counter()
    for role in roles:
      if role == '|':
        i = roles.index(role)
        roles.remove(role)
        role = roles[i]
      count = 1
      if role.endswith(')'):
        count = int(role[:-1].rpartition('(')[2])
        role = role[:-3]
      roles_list[role] = count
    await self.add_cogs_lite()
    await start_game(ctx, *roles_list.elements(), mafia=True,\
    faction_data=(list(roles_list)[ : stop], list(roles_list)[stop : ]))

  @commands.command(name='setlist',aliases=['składy'])
  async def składy(self, ctx):
    """/&składy/Wypisuje listę predefiniowanych składów."""
    await ctx.send(sklady.list_sets())


  @commands.command(name='set',aliases=['skład'])
  async def skład(self, ctx, nazwa_składu):
    """/&skład/Wypisuje listę postaci w składzie podanym jako argument."""
    await ctx.send(sklady.print_set(nazwa_składu.upper().replace("_", "")))

  @commands.command(name='start')
  @manitou_cmd()
  async def rozdawanie(self, ctx,*lista):
    """ⓂRozpoczyna grę z składem podanym jako argumenty funkcji."""
    #await resetuj_grajacych(ctx) #dopisałem resetowanie nicku w pętli wysyłaniu graczom roli na PM
    async with ctx.typing():
      await self.add_cogs()
      await start_game(ctx, *lista)
    
      

  @commands.command(name='startset',aliases=['start_skład'])
  @manitou_cmd()
  async def start_skład(self, ctx, nazwa_składu, *dodatkowe):
    """Ⓜ/&start_skład/Rozpoczyna grę jednym z predefiniowanych składów
    Argumentami są:
        -Nazwa predefiniowanego składu (patrz komenda składy)
        -opcjonalnie dodatkowe postacie oddzielone białymi znakami"""
    if not sklady.set_exists(nazwa_składu):
      await ctx.send("Nie ma takiego składu")
      return
    async with ctx.typing():
      await self.add_cogs()
      await start_game(ctx, *(sklady.get_set(nazwa_składu) + list(dodatkowe)))

  @commands.command(name='resume')
  @manitou_cmd()
  async def come_back(self, ctx):
    """ⓂRozpoczyna grę, używać gdy bot się wykrzaczy a potrzeba zrobić głosowanie"""
    if if_game():
      await ctx.message.delete(delay=5)
      await ctx.send("Gra już trwa", delete_after=5)
      return
    globals.current_game = Game()
    await self.add_cogs()
    await ctx.message.add_reaction('✅')

  @commands.command(name='gram')
  async def register(self, ctx):
    """Służy do zarejestrowania się do gry."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if if_game():
      await ctx.message.delete(delay=5)
      await ctx.send("Gra została rozpoczęta, nie możesz grać", delete_after=5)
      return
    await clear_nickname(member, ctx)
    await member.remove_roles(get_spectator_role())
    await member.remove_roles(get_dead_role())
    await member.add_roles(get_player_role())
    await ctx.message.add_reaction('✅')


  @commands.command(name='nie_gram',aliases=['niegram'])
  async def deregister(self, ctx):
    """Służy do wyrejestrowania się z gry."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if if_game():
      await ctx.message.delete(delay=5)
      await ctx.send("Gra została rozpoczęta, nie możesz nie grać", delete_after=5)
      return
    await member.remove_roles(get_player_role())
    await member.remove_roles(get_dead_role())
    await ctx.message.add_reaction('✅')