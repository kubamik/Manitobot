import datetime
import io
import sqlite3

import discord
from discord.ext import commands
import aiosqlite

from manitobot import utility

DB_FILE = 'data/reactions.sqlite3'


class ReactionAnalysis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_db()

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def setup_db():
        with sqlite3.connect(DB_FILE) as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS reactions (
                    channel_id INTEGER,
                    message_id INTEGER,
                    user_id INTEGER,
                    user_name TEXT,
                    emoji NVARCHAR(50),
                    datetime TEXT,
                    PRIMARY KEY (message_id, user_id, emoji, datetime))
                    ''')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event):
        user = utility.get_member(event.user_id)
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                '''INSERT INTO reactions (
                        channel_id, message_id, user_id, user_name, emoji, datetime)
                   VALUES (?, ?, ?, ?, ?, ?) ''',
                (event.channel_id, event.message_id,
                 event.user_id, user.display_name, str(event.emoji),
                 datetime.datetime.now().isoformat()))
            await db.commit()

    @commands.command()
    async def all_reactions(self, ctx):
        msg = ''
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute('SELECT * FROM reactions') as cursor:
                async for row in cursor:
                    msg += f'{",".join(map(str, row))}\n'
        if msg:
            msg = 'channel_id, message_id, user_id, user_name, emoji, datetime\n' + msg
            file = discord.File(filename='reactions.csv', fp=io.StringIO(msg))
            await ctx.send(file=file)
        else:
            await ctx.send('No reactions found')
