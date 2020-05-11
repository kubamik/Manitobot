from discord.ext import commands
from functools import wraps
import discord

from settings import *
from globals import bot
# nie mam pojęcia czemu from globals import * nie działa, from globals import bot działą

lock = False

def manitou_cmd(func):
  @wraps(func)
  async def wrapper(self, ctx, *args, **kwargs):
    if not czy_manitou(ctx):
      raise commands.MissingRole(get_manitou_role())
    await func(self, ctx, *args, **kwargs)
  return wrapper


def get_guild():
  """guild = ctx.guild
  if guild is not None:
    return guild"""
  return discord.utils.get(bot.guilds, id=GUILD_ID)

def get_player_role():
  guild=get_guild()
  return discord.utils.get(guild.roles,id=PLAYER_ROLE_ID)

def get_manitou_role():
  guild=get_guild()
  return discord.utils.get(guild.roles,id=MANITOU_ROLE_ID)

def get_dead_role():
  guild=get_guild()
  return discord.utils.get(guild.roles,id=TRUP_ROLE_ID)

def get_spectator_role():
  guild=get_guild()
  return discord.utils.get(guild.roles,id=SPECTATOR_ROLE_ID)

def get_duel_winner_role():
  return bot.get_guild(GUILD_ID).get_role(DUEL_WINNER_ID)

def get_duel_loser_role():
  return bot.get_guild(GUILD_ID).get_role(DUEL_LOSER_ID)

def get_searched_role():
  return bot.get_guild(GUILD_ID).get_role(SEARCHED_ID)

def get_hanged_role():
  return bot.get_guild(GUILD_ID).get_role(HANGED_ID)

def get_glosowania_channel():
  guild=get_guild()
  return discord.utils.get(guild.text_channels, id=GLOSOWANIA_CHANNEL_ID)

def get_manitou_notebook():
  guild = get_guild()
  return discord.utils.get(guild.text_channels, id=NOTATNIK_MANITOU_CHANNEL_ID)

def get_town_channel():
  guild=get_guild()
  return discord.utils.get(guild.text_channels, id=TOWN_CHANNEL_ID)

def get_voice_channel():
  guild = get_guild()
  return discord.utils.get(guild.voice_channels, id=VOICE_CHANNEL_ID)


def get_faction_channel(faction):
  guild = bot.get_guild(GUILD_ID)
  return guild.get_channel(FAC2CHANN_ID[faction])

def get_member(member_id):
  guild = get_guild()
  return discord.utils.get(guild.members, id=member_id)

def get_nickname(member_id):
  member = get_member(member_id)
  return member.nick if member.nick is not None else member.name

def czy_manitou(ctx):
  guild = get_guild()
  member = get_member(ctx.author.id)
  manitou=list(get_manitou_role().members)
  return member in manitou

def czy_gram(ctx):
  guild = get_guild()
  member = discord.utils.get(guild.members, id=ctx.author.id)
  players=list(get_player_role().members)
  return member in players

def czy_trup(ctx):
  guild = get_guild()
  member = discord.utils.get(guild.members, id=ctx.author.id)
  deads=list(get_dead_role().members)
  return member in deads

def nickname_fit(nick):
  nick = nick.lower()
  for player in get_player_role().members:
    if get_nickname(player.id).lower().rpartition('(')[0] == nick:
      return player
  return None

async def send_to_manitou(c):
  manitou=list(get_manitou_role().members)
  for member in manitou:
    await member.create_dm()
    await member.dm_channel.send(c)

async def send_file_to_manitou(c: discord.File):
  manitou=list(get_manitou_role().members)
  for member in manitou:
    await member.create_dm()
    await member.dm_channel.send(file=c)

async def clear_nickname(member, ctx):
  old_nickname = get_nickname(member.id)
  new_nickname = old_nickname
  if new_nickname[0] == '+' or new_nickname[0] == '!':
    new_nickname = new_nickname[1:]
  if new_nickname[-1] == ')':
    new_nickname = new_nickname.rpartition('(')[0]
  if new_nickname != old_nickname:
    try:
      await get_member(member.id).edit(nick=new_nickname)
    except discord.errors.Forbidden:
      await ctx.send("Nie mam uprawnień aby zresetować nick użytkownika {}".format(new_nickname))

async def converter(ctx, member):
  try:
    member = await commands.MemberConverter().convert(ctx, member)
  except commands.BadArgument:
    member = nickname_fit(member)
  return member

def playing(gracz = -1, *, author = -1):
  if gracz != -1 and (gracz is None or gracz not in get_guild().members):
    raise InvalidRequest("Nie ma takiego gracza")
  if gracz != -1 and (gracz in get_dead_role().members):
    raise InvalidRequest("Ten gracz nie żyje")
  if gracz != -1 and (gracz not in get_player_role().members):
    raise InvalidRequest("Ta osoba nie gra")
  if author != -1 and author in get_dead_role().members:
    raise InvalidRequest("Jesteś martwy")
  if author != -1 and author not in get_player_role().members:
    raise InvalidRequest("Nie grasz")

class InvalidRequest(Exception):
  def __init__(self, reason = None):
    self.reason = reason

class NoEffect(Exception):
  def __init__(self, reason = "No reason"):
    self.reason = reason

class GameEnd(Exception):
  def __init__(self, reason, winner):
    self.winner = winner
    self.reason = reason