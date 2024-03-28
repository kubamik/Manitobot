from discord.ext import commands


class Election(commands.Cog, name='Wybory'):
    def __init__(self, bot):
        self.bot = bot
