import discord
from discord.ext import commands

help = commands.DefaultHelpCommand(
    no_category='Pozostałe',
    verify_checks=False,
)

bot = commands.Bot(command_prefix='&', help_command=help,
                   owner_id=388764073191538688)
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
