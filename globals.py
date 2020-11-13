from discord.ext import commands
import discord
from random import SystemRandom

command_prefix = '&'


class Help(commands.DefaultHelpCommand):
  def __init__(self):
    super().__init__(no_category='Pozostałe', verify_checks=False)

  def get_ending_note(self):
    return '''Informacje o konkretnej komendzie:\t{0}help <komenda>
Informacje o konkretnej kategorii:\t{0}help <kategoria>
Skrócona pomoc dla Manitou:\t\t   {0}help m
Skrócona pomoc dla graczy\t\t\t {0}help g'''.format(command_prefix)


intents = discord.Intents.default()
intents.members = True


bot = commands.Bot(
  command_prefix = commands.when_mentioned_or(command_prefix), help_command = Help(), owner_id=388764073191538688, case_insensitive=True, self_bot=False,
  intents = intents)
current_game = None


@bot.command(name='HONK', hidden=True)
async def honk(ctx):
  await ctx.send("KWAK")

@bot.command(name='honk', hidden=True)
async def honk(ctx):
  await ctx.send("kwak")

@bot.command(name='kwak', hidden=True)
async def honk(ctx):
  await ctx.send("honk")

@bot.command(name='KWAK', hidden=True)
async def honk(ctx):
  await ctx.send("HONK")

@bot.command(name='gulugulu', hidden=True)
async def honk(ctx):
  await ctx.send("gulugulugulugu")

@bot.command(name='GULUGULU', hidden=True)
async def honk(ctx):
  await ctx.send("GULUGULUGULUGU")

@bot.command(name='ping', hidden=True)
async def honk(ctx):
  await ctx.send("pong")

@bot.command(name='pingu', hidden=True)
async def honk(ctx):
  await ctx.send("NOOT NOOT")


@bot.command(name='ważnawiadomość', hidden=True)
async def honk(ctx, member=None):
  if member is not None:
    try:
      member = await discord.ext.commands.MemberConverter().convert(ctx, member)
      await ctx.send(member.mention)
    except commands.BadArgument:
      await ctx.send("nie ma takiego gracza")
      return
  await ctx.send("ZABIJ SIĘ!")

@bot.command(name='dziobak', hidden=True)
async def honk(ctx):
  await ctx.send("dubidubiduba")

@bot.command(name='DZIOBAK', hidden=True)
async def honk(ctx):
  await ctx.send("DUBIDUBIDUBA")

@bot.command(name='dubidubiduba', hidden=True)
async def honk(ctx):
  await ctx.send("AAAAAGEEEENT PEEEEEEE!!!")

@bot.command(name='DUBIDUBIDUBA', hidden=True)
async def honk(ctx):
  await ctx.send("AAAAAGEEEENT PEEEEEEE!!!")
