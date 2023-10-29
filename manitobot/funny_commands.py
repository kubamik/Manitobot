from discord.ext import commands

from .converters import MyMemberConverter


class Funny(commands.Cog, name='HONK'):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='_HONK', hidden=True)
    async def honk1(self, ctx):
        await ctx.send("KWAK")

    @commands.command(name='honk', hidden=True)
    async def honk2(self, ctx):
        await ctx.send("kwak")

    @commands.command(name='kwak', hidden=True)
    async def honk3(self, ctx):
        await ctx.send("honk")

    @commands.command(name='_KWAK', hidden=True)
    async def honk4(self, ctx):
        await ctx.send("HONK")

    @commands.command(name='gulugulu', hidden=True)
    async def honk5(self, ctx):
        await ctx.send("gulugulugulugu")

    @commands.command(name='_GULUGULU', hidden=True)
    async def honk6(self, ctx):
        await ctx.send("GULUGULUGULUGU")

    @commands.command(name='pingu', hidden=True)
    async def honk8(self, ctx):
        await ctx.send("NOOT NOOT")

    @commands.command(name='dziobak', hidden=True)
    async def honk10(self, ctx):
        await ctx.send("&dubidubiduba")

    @commands.command(name='_DZIOBAK', hidden=True)
    async def honk11(self, ctx):
        await ctx.send("DUBIDUBIDUBA")

    @commands.command(name='dubidubiduba', hidden=True)
    async def honk12(self, ctx):
        await ctx.send("AAAAAGEEEENT PEEEEEEE!!!")

    @commands.command(name='_DUBIDUBIDUBA', hidden=True)
    async def honk13(self, ctx):
        await ctx.send("AAAAAGEEEENT PEEEEEEE!!!")
