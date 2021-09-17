import asyncio

import discord
from discord.ext import commands

from . import postacie
from .basic_models import NotAGame
from .errors import VotingNotAllowed
from .my_checks import game_check, playing_cmd, on_voice_check, player_cmd, voting_check
from .utility import get_player_role, get_dead_role, get_spectator_role, \
    get_town_channel, send_to_manitou, \
    get_voice_channel, get_manitou_role, playerhelp


class DlaGraczy(commands.Cog, name="Dla Graczy"):
    def __init__(self,  bot):
        self.bot = bot

    @commands.command(name='postać')
    async def role_help(self, ctx, rola: str):
        """Zwraca informacje o postaci podanej jako argument
        """
        await ctx.send(postacie.get_role_details(rola))

    @commands.command(name='obserwuję', aliases=['obs'])
    @playing_cmd(reverse=True)
    async def spectate(self, ctx):
        """/&obs/Zmienia rolę usera na spectator.
        """
        member = ctx.author
        await member.remove_roles(get_player_role(), get_dead_role())
        await member.add_roles(get_spectator_role())
        nickname = member.display_name
        if not nickname.startswith('!'):
            try:
                await member.edit(nick='!' + nickname)
            except discord.errors.Forbidden:
                pass

    @commands.command(name='nie_obserwuję', aliases=['nie_obs', 'nieobs'])
    async def not_spectate(self, ctx):
        """/&nie_obs/Usuwa userowi rolę spectator.
        """
        member = ctx.author
        await member.remove_roles(get_spectator_role())
        nickname = member.display_name
        if nickname.startswith('!'):
            try:
                await member.edit(nick=nickname[1:])
            except discord.errors.Forbidden:
                pass

    @commands.command(name='pax')
    @game_check()
    @playing_cmd()
    async def pax(self, ctx):
        """Wyrejestrowuje gracza ze zbioru buntowników
        """
        try:
            self.bot.game.rioters.remove(ctx.author)
        except KeyError:
            pass
        await ctx.message.add_reaction('🕊️')

    @commands.command(name='bunt', aliases=['riot'])
    @game_check()
    @playing_cmd()
    @on_voice_check()
    async def riot(self, ctx):
        """/&riot/W przypadku poparcia przez co najmniej 67 % osób biorących udział w grze kończy grę
        """
        tasks = []
        self.bot.game.rioters.add(ctx.author)
        count = set()
        for person in self.bot.game.player_map:
            if person in get_voice_channel().members:
                count.add(person)
            else:
                if person in self.bot.game.rioters:
                    self.bot.game.rioters.remove(person)
        if len(self.bot.game.rioters) == 1:
            await get_town_channel().send('{}\nKtoś rozpoczął bunt. Użyj `&bunt` jeśli chcesz dołączyć'.format(
                get_player_role().mention))
            await send_to_manitou('Ktoś rozpoczął bunt.')

        if len(self.bot.game.rioters) >= len(count) * 0.67:
            tasks.append(get_town_channel().send('**Doszło do buntu\nGra została zakończona**'))
            for manitou in get_manitou_role().members:
                tasks.append(manitou.remove_roles(get_manitou_role()))
            tasks.append(self.bot.game.end())
            manit = self.bot.cogs['Dla Manitou']
            tasks.append(manit.reset(ctx))
            self.bot.game = NotAGame()
        if tasks:
            await asyncio.gather(*tasks)
        await ctx.message.add_reaction('👊')

    @commands.command(name="żywi", aliases=['zywi'])
    @game_check()
    async def living(self, ctx):
        """/&zywi/Wypisuje listę żywych graczy"""
        alive_roles = []
        for role in self.bot.game.role_map.values():
            if role.alive or not role.revealed:
                alive_roles.append(role.name)
        team = postacie.print_list(alive_roles)
        await ctx.send(
            'Liczba żywych graczy: {}\nLiczba martwych o nieznanych rolach: {}\n'
            'Pozostali:{}'.format(len(get_player_role().members),
                                  len(alive_roles) - len(get_player_role().members), team)
        )

    @commands.command(aliases=['vpriv'])
    @player_cmd()
    @game_check()
    @voting_check(reverse=True)
    async def priv_voting(self, ctx):
        """Wysyła opcje do głosowania w wiadomości prywatnej
        umożliwiając głosowanie inaczej niż przez menu z opcjami
        """
        voting = self.bot.game.day.state
        if ctx.author in voting.participants:
            await ctx.author.send(embed=voting.options_embed())
        else:
            raise VotingNotAllowed

    @commands.command(name='g', help=playerhelp(), hidden=True, brief='&help g')
    async def player_help(self, ctx):
        await ctx.message.delete(delay=0)
