import asyncio
from contextlib import suppress

import discord
from discord.ext import commands

from . import postacie
from .basic_models import NotAGame
from .errors import VotingNotAllowed
from .my_checks import game_check, playing_cmd, on_voice_check, player_cmd, voting_check, trusted_cmd
from .starting import if_game
from .utility import get_player_role, get_dead_role, get_spectator_role, \
    get_town_channel, send_to_manitou, \
    get_voice_channel, get_manitou_role, playerhelp, is_dead, nickname_without_prefix, cleared_nickname


class PlayerCommands(commands.Cog, name="Dla Graczy"):
    def __init__(self,  bot):
        self.bot = bot

    @commands.Cog.listener(name='on_voice_state_update')
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel != after.channel and after.channel == get_voice_channel() and if_game():
            if (member not in get_dead_role().members and member not in get_player_role().members 
                    and member not in get_manitou_role().members):
                if not member.display_name.startswith('!') or not after.mute:
                    with suppress(discord.errors.Forbidden):
                        await member.edit(nick='!' + member.display_name.removeprefix('!'), mute=True)
            if (member in get_dead_role().members or member in get_player_role().members and self.bot.game.night_now) \
                    and not after.mute:
                with suppress(discord.errors.Forbidden):
                    await member.edit(mute=True)

    @commands.command(name='postać')
    async def role_help(self, ctx, rola: str):
        """Zwraca informacje o postaci podanej jako argument
        """
        await ctx.send(postacie.get_role_details(rola))

    @commands.command(name='obserwuję', aliases=['obs', 'obserwuje'])
    @playing_cmd(reverse=True)
    @trusted_cmd()
    async def spectate(self, ctx):
        """/&obs/Zmienia rolę usera na obserwator - tylko dla Weteranów Ktulu
        """
        member = ctx.author
        nickname = member.display_name
        if not nickname.startswith('!') and (not if_game() or not is_dead(ctx)):
            nickname = '!' + nickname_without_prefix(nickname)
        await ctx.bot.workers.edit_member(
            member, nick=nickname, roles_to_add=[get_spectator_role()],
            roles_to_remove=[get_dead_role(), get_player_role(), get_manitou_role()] if not if_game() else []
        )


    @commands.command(name='nie_obserwuję', aliases=['nie_obserwuje', 'nieobserwuje', 'nie_obs', 'nieobs'])
    async def not_spectate(self, ctx):
        """/&nie_obs/Usuwa userowi rolę obserwator.
        """
        member = ctx.author
        nickname = member.display_name
        if nickname.startswith('!'):
            nickname = cleared_nickname(member.display_name)
        await ctx.bot.workers.edit_member(member, nick=nickname, roles_to_remove=[get_spectator_role()])


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
            await get_town_channel().send('**Doszło do buntu\nKończenie gry...**')
            for manitou in get_manitou_role().members:
                tasks.append(manitou.remove_roles(get_manitou_role()))
            manit = self.bot.cogs['Dla Manitou']
            tasks.append(manit.end_and_reset(ctx))
        if tasks:
            await asyncio.gather(*tasks)
        await ctx.message.add_reaction('👊')

    @commands.command(name="żywi", aliases=['zywi'])
    @game_check()
    async def living(self, ctx):
        """Wypisuje listę żywych graczy"""
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
