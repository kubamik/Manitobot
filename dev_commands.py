import datetime as dt
import os

import discord
from discord.ext import commands

from converters import MyMemberConverter
from settings import LOG_FILE


started_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DevCommands(commands.Cog, name='Development'):
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

    @commands.command(name='log')
    async def log(self, ctx):
        """ⒹWysyła logi błędów"""
        try:
            with open(LOG_FILE) as fp:
                time = dt.datetime.now()
                logs = discord.File(fp, filename='Manitobot {}.log'.format(time.strftime("%Y-%m-%d_%H-%M-%S")))
                await ctx.send(file=logs)
        except FileNotFoundError:
            await ctx.send("Logs aren't available now.", delete_after=5)
            await ctx.message.delete(delay=5)

    @commands.command(name='started_at')
    async def start_time(self, ctx):
        """ⒹPokazuje czas rozpoczęcia sesji bota"""
        await ctx.send(f"Current bot session started at {started_at}")

    @commands.command(name='clear_logs', aliases=['logcls'])
    async def log_clear(self, _):
        """ⒹCzyści logi błędów"""
        try:
            os.remove(LOG_FILE)
        except FileNotFoundError:
            pass

    @commands.command(name='invoke')
    async def invoke(
            self, ctx, member: MyMemberConverter(player_only=False), *, txt):
        """🤔"""
        msg = ctx.message
        msg.author = member
        msg.content = '&' + txt if not txt.startswith('&') else txt
        await self.bot.process_commands(msg)
