import datetime as dt
import os

import discord
from discord.ext import commands

from settings import LOG_FILE, FULL_LOG_FILE
from .converters import MyMemberConverter

started_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DevCommands(commands.Cog, name='Development'):
    """v1.5.3"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner('Only bot owner can use this commands')
        return True

    @commands.command(name='exec', hidden=True)
    async def execute(self, _, *, string):
        """ⒹUruchamia podany kod"""
        exec(string)

    @staticmethod
    async def send_logs(ctx, full=False):
        if full:
            file = FULL_LOG_FILE
            name = 'Manitobot {}_full.log'
        else:
            file = LOG_FILE
            name = 'Manitobot {}.log'
        time = dt.datetime.now()
        logs = discord.File(file, filename=name.format(time.strftime("%Y-%m-%d_%H-%M-%S")))            
        try:
            await ctx.send(file=logs)
        except discord.HTTPException:
            await ctx.send('Wystąpił błąd')

    @commands.command(name='log')
    async def log(self, ctx):
        """ⒹWysyła logi błędów"""
        await self.send_logs(ctx)

    @commands.command()
    async def full_log(self, ctx):
        """ⒹWysyła pełne logi"""
        await self.send_logs(ctx, full=True)

    @commands.command()
    async def clear_full_log(self, _):
        """ⒹCzyści pełne logi"""
        with open(FULL_LOG_FILE, 'w'):
            pass

    @commands.command(name='started_at')
    async def start_time(self, ctx):
        """ⒹPokazuje czas rozpoczęcia sesji bota"""
        await ctx.send(f"Current bot session started at {started_at}")

    @commands.command(name='clear_logs', aliases=['logcls'])
    async def log_clear(self, _):
        """ⒹCzyści logi błędów"""
        with open(LOG_FILE, 'w'):
            pass

    @commands.command(name='invoke', hidden=True)
    async def invoke(
            self, ctx, member: MyMemberConverter(player_only=False), *, txt):
        """🤔"""
        msg = ctx.message
        _author = ctx.author
        _content = msg.content
        msg.author = member
        msg.content = '&' + txt if not txt.startswith('&') else txt
        await self.bot.process_commands(msg)
        # fixing message to be correct in cache
        msg.author = _author
        msg.content = _content
