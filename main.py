import os
import discord
import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import asyncio
import inspect
import traceback

import duels_commands
import hang_commands
import player_commands
import voting_commands
import manitou_commands
import roles_commands
import roles_calling_commands
import start_commands
import search_hang_commands
from keep_alive import keep_alive
from utility import *
import utility
import settings
from settings import *
from globals import bot
import globals
from f_database import factions_roles

PRZEGRALEM_COOLDOWN = datetime.timedelta(minutes=30)
ostatnio_przegralem = datetime.datetime.now() - PRZEGRALEM_COOLDOWN


@bot.event
async def on_ready():
  print("Hello world!")
  try:
    bot.add_cog(player_commands.DlaGraczy(bot))
    bot.add_cog(manitou_commands.DlaManitou(bot))
    bot.add_cog(start_commands.Starting(bot))
  except discord.errors.ClientException:
    pass
  await get_member(MY_ID).create_dm()
  await get_member(MY_ID).dm_channel.send('')
 
@bot.command(name='pomoc')
async def help1(ctx):
  """Wzywa bota do pomocy"""
  await ctx.send("nie mogę ci pomóc, jestem botem")
  await ctx.message.add_reaction('✅')


@bot.command(name='przeproś')
async def przeproś(ctx):
	"""Przepraszam"""
	await ctx.send("Przepraszam".format(powod))


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
	try:
		if m.type != discord.MessageType.default or m.author == bot.user or m.content.strip()[0] == '&':
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

@bot.command(name='log')
async def log(ctx):
  '''ⒹWysyła logi błędów'''
  try:
    with open("error.log") as fp:
      logs = discord.File(fp)
      await ctx.send(file=logs)
  except FileNotFoundError:
    await ctx.send("Aktualnie nie ma logów")

@bot.command(name='clear_logs', aliases=['logcls'])
@commands.is_owner()
async def log_clear(ctx):
  '''ⒹCzyści logi błędów'''
  os.remove('error.log')
  await ctx.message.add_reaction('✅')
  

@bot.event
async def on_command_error(ctx, error):
  if not (isinstance(error, discord.ext.commands.errors.CommandInvokeError) and isinstance(error.original, utility.GameEnd)):
    await ctx.message.delete(delay=5)
  if isinstance(error, CommandNotFound):
    await ctx.send("HONK?", delete_after=5)
  elif isinstance(error, commands.MissingRole):
    await ctx.send("You have no power here!", delete_after=5)
  elif isinstance(error, commands.CheckAnyFailure):
    await ctx.send("You have no power here!", delete_after=5)
  elif isinstance(error, commands.NotOwner):
    await ctx.send("You have no power here!", delete_after=5)
  elif isinstance(error, commands.errors.MissingRequiredArgument):
    await ctx.send("Brakuje parametru: " + str(error.param), delete_after=5)
    await ctx.send_help(ctx.command)
  elif isinstance(error, ValueError):
    await ctx.send(str(error), delete_after=5)
  elif isinstance(error, commands.errors.BadArgument):
    await ctx.send("Błędny parametr", delete_after=5)
    await ctx.send_help(ctx.command)
  elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, AttributeError):
    utility.lock = False
    await ctx.send("Gra nie została rozpoczęta", delete_after=5)
    try:
      raise error
    except:
      with open('error.log', 'a') as logs:
        traceback.print_exc(file=logs)
        logs.write(f'\n\n\n\n{RULLER}\n\n\n\n')
      raise error
  elif isinstance(error, commands.DisabledCommand):
    await ctx.send("Prace nad tą komendą trwają. Nie należy jej używać.", delete_after=5)
  elif isinstance(error, commands.CheckFailure):
    pass
  elif isinstance(error, commands.PrivateMessageOnly):
    pass
  elif isinstance(error, commands.NoPrivateMessage):
    pass
  elif isinstance(error, discord.ext.commands.errors.CommandInvokeError) and isinstance(error.original, utility.GameEnd):
    utility.lock = False
    error = error.original
    c = ":scroll:{}:scroll:".format(error.reason) + '\n' + '**__Grę wygrywa frakcja {}__**'.format(error.winner)
    await globals.current_game.winning(error.reason, error.winner)
    await send_to_manitou(c)
    for channel in get_guild().text_channels:
      if channel.category_id == FRAKCJE_CATEGORY_ID:
        await channel.send(c)
  else:
    utility.lock = False
    print(error.original)
    await ctx.send(":robot:Bot did an uppsie :'( :robot:", delete_after=5)
    print(ctx.command, type(error))
    try:
      raise error
    except:
      with open('error.log', 'a') as logs:
        traceback.print_exc(file=logs)
        logs.write(f'\n\n\n\n\n{RULLER}\n\n\n\n')
      raise error
    
    


#@bot.listen('on_member_update')
#async def role_change(before, after):


keep_alive()
token = os.environ.get("TOKEN")
bot.run(token)
