import discord
from discord.ext import commands
from random import randint
from time import sleep

from settings import DIE415_ID, DIE421_ID, DIE456_ID, DIE462_ID
from .bot_basics import bot
from .utility import get_admin_role


class Election(commands.Cog, name='Wybory'):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author in get_admin_role().members or await self.bot.is_owner(ctx.author):
            return True
        raise commands.MissingRole(get_admin_role())

    @commands.command(name='losuj_kww')
    async def rand_kww(self, ctx, komitet):
        """Przydziela losowy numer kandydatowi zgodnie z standardem RFC 1149.5
        """
        await ctx.send('Losuję numer komitetu...')
        time.sleep(2)
        match random.randint(0, 3):
            case 0:
                await ctx.send(f'<:kostka4:{DIE415_ID}>')
            case 1:
                await ctx.send(f'<:kostka4:{DIE421_ID}>')
            case 2:
                await ctx.send(f'<:kostka4:{DIE456_ID}>')
            case 3:
                await ctx.send(f'<:kostka4:{DIE462_ID}>')
        time.sleep(1)
        await ctx.send(f'Wylosowany numer KWW {komitet} to 4.')
