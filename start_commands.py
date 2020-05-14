from random import randint
from discord.ext import commands
import discord

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

  @commands.command(name='setlist',aliases=['składy'])
  async def składy(self, ctx):
    """/&składy/Wypisuje listę predefiniowanych składów."""
    await ctx.send(sklady.list_sets())


  @commands.command(name='set',aliases=['skład'])
  async def skład(self, ctx, nazwa_składu):
    """/&skład/Wypisuje listę postaci w składzie podanym jako argument."""
    await ctx.send(sklady.print_set(nazwa_składu.upper().replace("_", "")))

  @commands.command(name='start')
  @manitou_cmd
  async def rozdawanie(self, ctx,*lista):
    """ⓂRozpoczyna grę z składem podanym jako argumenty funkcji."""
    #await resetuj_grajacych(ctx) #dopisałem resetowanie nicku w pętli wysyłaniu graczom roli na PM
    async with ctx.typing():
      await start_game(ctx,*lista)
      

  @commands.command(name='startset',aliases=['start_skład'])
  @manitou_cmd
  async def start_skład(self, ctx, nazwa_składu, *dodatkowe):
    """Ⓜ/&start_skład/Rozpoczyna grę jednym z predefiniowanych składów
    Argumentami są:
        -Nazwa predefiniowanego składu (patrz komenda składy)
        -opcjonalnie dodatkowe postacie oddzielone białymi znakami"""
    if not sklady.set_exists(nazwa_składu):
      await ctx.send("Nie ma takiego składu")
      return
    await start_game(ctx, *(sklady.get_set(nazwa_składu) + list(dodatkowe)))

  @commands.command(name='resume')
  @manitou_cmd
  async def come_back(self, ctx):
    """ⓂRozpoczyna grę, używać gdy bot się wykrzaczy a potrzeba zrobić głosowanie"""
    globals.current_game = Game()
    await ctx.message.add_reaction('✅')

  @commands.command(name='gram')
  async def register(self, ctx):
    """Służy do zarejestrowania się do gry."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if not globals.current_game==None:
      await ctx.send("Gra została rozpoczęta, nie możesz grać")
      return
    await clear_nickname(member,ctx)
    await member.remove_roles(get_spectator_role())
    await member.remove_roles(get_dead_role())
    await member.add_roles(get_player_role())
    await ctx.message.add_reaction('✅')


  @commands.command(name='nie_gram',aliases=['niegram'])
  async def deregister(self, ctx):
    """Służy do wyrejestrowania się z gry."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if not globals.current_game==None:
      await ctx.send("Gra została rozpoczęta, nie możesz nie grać")
      return
    await member.remove_roles(get_player_role())
    await member.remove_roles(get_dead_role())
    await ctx.message.add_reaction('✅')