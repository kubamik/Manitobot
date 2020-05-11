import os
import discord
import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import asyncio
import inspect

import duels_commands
import hang_commands
import player_commands
import voting_commands
import manitou_commands
import roles_commands
import roles_calling_commands
import start_commands
import search_hang_commands
#from keep_alive import keep_alive
from utility import *
import utility
import settings
from settings import *
from globals import bot
import globals
from f_database import factions_roles

PRZEGRALEM_COOLDOWN = datetime.timedelta(minutes=30)
ostatnio_przegralem = datetime.datetime.now() - PRZEGRALEM_COOLDOWN
#TODO argument ctx w funkcjach get_guild, get_manitou, get_player jest trochę niepotrzebny przez to jak to robimy, a fajnie by było mieć dostępną funkcję do wysyłania wszystkim manitou wiadomości bez potrzeby ctx (bo ) - gotowe ~Kuba
#TODO kontrola głosowania dla Manitou, kontrola ilości głosów, kończenie, gdy wszyscy zagłosowali,
#TODO sprawdzenie czy głosowanie jest rozpoczęte, aby je zakończyć
#TODO szeryf, pastor, upicie
#usunięcie alivów, resume - rozpoczyna pustą grę, zmiana nicków

#HONK!

#wyniki głosowania na priv


@bot.event
async def on_ready():
  print("Hello world!")
  try:
    bot.add_cog(player_commands.DlaGraczy(bot))
    #bot.add_cog(voting_commands.Glosowania(bot))
    bot.add_cog(manitou_commands.DlaManitou(bot))
    #bot.add_cog(roles_commands.PoleceniaPostaci(bot))
    #bot.add_cog(roles_calling_commands.WywolywaniePostaci(bot))
    #bot.add_cog(duels_commands.Pojedynki(bot))
    #bot.add_cog(search_hang_commands.Przeszukania(bot))
    #bot.add_cog(search_hang_commands.Wieszanie(bot))
    bot.add_cog(start_commands.Starting(bot))
  except discord.errors.ClientException:
    pass
  c = '''Teraz jest dobrze?\n'''
  for key,value in factions_roles.items():
    c += "**{}**: {}\n".format(key,", ".join(value))
  #await bot.get_guild(691953007461662741).get_channel(691953007461662745).send(r"=tex \sin(\frac{\pi}{2} + \alpha) = - \cos(\alpha)")
  #await get_guild().get_channel(694111942729662477).send(c)
  #await bot.get_guild(691953007461662741).get_channel(691953007461662745).send("")
  #print(bot.cogs)
  '''for role,sth in get_guild().by_category()[2][0].overwrites.items():
    print(role)
    for a in sth:
      print(a)'''
  #print(get_guild().by_category()[2][0].overwrites)
  #688087497988898823
  #for item in bot.get_guild(GUILD_ID).get_channel(688089712094740542).overwrites[get_manitou_role()]:
    #print(item)
  #for pair in get_town_channel().overwrites:
    #print(pair)
  #await get_town_channel().set_permissions(bot.get_guild(GUILD_ID).get_role(693506243402268742),manage_channels=True,manage_roles=True)



'''@bot.command(name='play',hidden=True)
async def play(ctx):
  opus._load_default()
  vc = await get_voice_channel().connect()
  audio = discord.FFmpegPCMAudio('*plik*')
  vc.play(source=audio)'''

@bot.command(name='pomoc')
async def help1(ctx):
  """Wzywa bota do pomocy"""
  print(isinstance(ctx.channel, discord.DMChannel))
  await ctx.send("nie mogę ci pomóc, jestem botem")
  await ctx.message.add_reaction('✅')
  await ctx.message.add_reaction('✅')


@bot.command(name='przeproś')
async def przeproś(ctx, *, powod = ''):
	"""Przepraszam"""
	await ctx.send("Przepraszam {}".format(powod))


@bot.command(name='przegrywam')
async def lose(ctx):
	"""Dodaje usera do zbioru przegrywów."""
	guild = get_guild()
	member = get_member(ctx.author.id)
	await member.add_roles(
	    discord.utils.get(guild.roles, id=PRZEGRALEM_ROLE_ID))
	await ctx.send("Zostałeś przegranym {}".format(
	    get_nickname(ctx.author.id)))


@bot.command(name='wygrywam')
async def not_lose(ctx):
	"""Usuwa usera ze zbioru przegrywów."""
	guild = get_guild()
	member = get_member(ctx.author.id)
	await member.remove_roles(
	    discord.utils.get(guild.roles, id=PRZEGRALEM_ROLE_ID))
	await ctx.send("Już nie jesteś przegranym {}".format(
	    get_nickname(ctx.author.id)))


@bot.command(name='przegrałem')
async def przegrałeś(ctx):
	"""Przypomina przegrywom o grze."""
	global ostatnio_przegralem
	delta = datetime.datetime.now() - ostatnio_przegralem
	ostatnio_przegralem = datetime.datetime.now()
	if PRZEGRALEM_COOLDOWN > delta:
		await ctx.send("Mam okres ochronny")
		return
	guild = get_guild()
	gracz = discord.utils.get(guild.roles, id=PRZEGRALEM_ROLE_ID)
	gracze = list(gracz.members)
	await ctx.send("Przegrałem!")
	for i in gracze:
		try:
			await i.create_dm()
			await i.dm_channel.send("Przegrałem!")
		except:
			await ctx.send("Nie można wysłać wiadomości do {}".format(
			    get_nickname(i.id)))

'''@bot.listen('on_message')
async def mess(m):
  print(m.content)'''


@bot.listen('on_message')
@commands.dm_only()
async def my_message(m):
	#global globals.current_game
	try:
		if m.type != discord.MessageType.default or m.author.id == BOT_ID or m.content.strip()[0] == '&':
			return
	except:
		pass
	if m.channel.type != discord.ChannelType.private:
		return

	if globals.current_game is None or not globals.current_game.voting_in_progress():
		await m.channel.send("Nie rozumiem. Nie trwa teraz żadne głosowanie")
		return

	try:
		votes = [vote.strip() for vote in m.content.split(',')]
		(res, not_voted) = globals.current_game.register_vote(
		    get_member(m.author.id), votes)
		await m.channel.send("Zarejestrowałem twój głos/-y na {}".format(
		    ", ".join(res)))
		if len(not_voted) == 0:
			await send_to_manitou("Wszyscy grający oddali głosy")
	except InvalidRequest as e:
		await m.channel.send(e.reason)


@bot.event
async def on_command_error(ctx, error):
  utility.lock = False
  if not (isinstance(error, discord.ext.commands.errors.CommandInvokeError) and isinstance(error.original, utility.GameEnd)):
    await ctx.message.delete(delay=5)
  if isinstance(error, CommandNotFound):
    await ctx.send("HONK?", delete_after=5)
  elif isinstance(error, commands.MissingRole):
    await ctx.send("You have no power here!", delete_after=5)
  elif isinstance(error, commands.errors.MissingRequiredArgument):
    await ctx.send("Brakuje parametru: " + str(error.param), delete_after=5)
    await ctx.send_help(ctx.command, delete_after=5)
  elif isinstance(error, ValueError):
    await ctx.send(str(error), delete_after=5)
  elif isinstance(error, commands.errors.BadArgument):
    await ctx.send("Błędny parametr", delete_after=5)
    await ctx.send_help(ctx.command)
  elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, AttributeError):
    await ctx.send("Gra nie została rozpoczęta", delete_after=5)
    raise error
  elif isinstance(error, commands.CheckFailure):
    pass
  elif isinstance(error, commands.PrivateMessageOnly):
    pass
  elif isinstance(error, discord.ext.commands.errors.CommandInvokeError) and isinstance(error.original, utility.GameEnd):
    error = error.original
    c = ":scroll:{}:scroll:".format(error.reason) + '\n' + '**__Grę wygrywa frakcja {}__**'.format(error.winner)
    await globals.current_game.winning(error.reason, error.winner)
    await send_to_manitou(c)
    for channel in get_guild().text_channels:
      if channel.category_id == FRAKCJE_CATEGORY_ID:
        await channel.send(c)
  else:
    print(type(error.original))
    await ctx.send(":robot:Bot did an uppsie :'( :robot:", delete_after=5)
    print(ctx.command, type(error))
    raise error


#@bot.listen('on_member_update')
#async def role_change(before, after):


#keep_alive()
token = os.environ.get("TOKEN")
bot.run(token)
