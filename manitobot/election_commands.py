import asyncio
from random import randint

from discord.ext import commands

from settings import DIE415_ID, DIE421_ID, DIE456_ID, DIE462_ID
from .my_checks import admin_cmd


class Election(commands.Cog, name='Wybory'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='losuj_kww')
    @admin_cmd()
    async def rand_kww(self, ctx, komitet):
        """Przydziela losowy numer kandydatowi zgodnie z standardem RFC 1149.5
        """
        await ctx.send('Losuję numer komitetu...')
        await asyncio.sleep(2)
        match randint(0, 3):
            case 0:
                await ctx.send(f'<:kostka4:{DIE415_ID}>')
            case 1:
                await ctx.send(f'<:kostka4:{DIE421_ID}>')
            case 2:
                await ctx.send(f'<:kostka4:{DIE456_ID}>')
            case 3:
                await ctx.send(f'<:kostka4:{DIE462_ID}>')
        await asyncio.sleep(1)
        await ctx.send(f'Wylosowany numer KWW {komitet} to 4.')
