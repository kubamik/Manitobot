import asyncio
from random import randint
from typing import Union

from discord.ext import commands
import discord

import utility
from basic_models import NotAGame
from converters import MyMemberConverter
from cheks import manitou_cmd, game_check, mafia_check, ktulu_check, day_only
from settings import FAC2CHANN_ID, CONFIG
from utility import playerhelp, manitouhelp, get_faction_channel, get_admin_role, get_town_channel, get_player_role, \
    get_other_manitou_role, get_manitou_role, get_voice_channel, get_manitou_notebook, get_member, get_dead_role, \
    get_spectator_role, get_guild, clear_nickname, send_to_manitou, get_duel_winner_role, get_duel_loser_role, \
    get_searched_role, get_hanged_role
from starting import if_game
from postacie import get_role_details
import postacie


class DlaManitou(commands.Cog, name="Dla Manitou"):

    def __init__(self, bot):
        self.bot = bot

    async def remove_cogs(self):
        rm_cog = self.bot.remove_cog
        rm_cog("Głosowania")
        rm_cog("Polecenia postaci i frakcji")
        rm_cog("Pojedynki")
        rm_cog("Przeszukania")
        rm_cog("Wieszanie")
        rm_cog("Panel Sterowania")
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions().all()
        tasks = []
        for faction in FAC2CHANN_ID:  # TODO: Optimize this
            ch = get_faction_channel(faction)
            tasks.append(ch.edit(sync_permissions=True))
        tasks.append(get_admin_role().edit(permissions=p, colour=0xffa9f9))
        tasks.append(get_town_channel().set_permissions(get_player_role(), send_messages=True))
        tasks.append(utility.remove_roles(get_manitou_role().members, get_other_manitou_role()))
        tasks.append(self.bot.change_presence(activity=None))
        await asyncio.gather(*tasks)

    @commands.command(aliases=['MM'])
    @manitou_cmd()
    async def mass_mute(self, _):
        """ⓂMutuje wszystkich niebędących Manitou
        """
        tasks = []
        for member in get_voice_channel().members:
            if member not in get_manitou_role().members:
                tasks.append(member.edit(mute=True))
        await asyncio.gather(*tasks)

    @commands.command(aliases=['MU'])
    @manitou_cmd()
    async def mass_unmute(self, _):
        """ⓂUnmutuje wszystkich niebędących Manitou
        """
        tasks = []
        for member in get_voice_channel().members:
            if member not in get_manitou_role().members:
                tasks.append(member.edit(mute=False))
        await asyncio.gather(*tasks)

    @commands.command(name='set_manitou_channel', aliases=['m_channel'])
    @manitou_cmd()
    async def set_m_channel(self, ctx):
        """Ⓜ/&m_channel/Użyte na serwerze ustawia kanał Manitou na #notatnik-manitou, użyte na DM ustawia na DM
        """
        if ctx.channel.type == discord.ChannelType.private:
            CONFIG['DM_Manitou'] = True
        else:
            CONFIG['DM_Manitou'] = False

    @commands.command(name='tea', enabled=False, hidden=True)
    @manitou_cmd()
    @game_check()
    @day_only()
    async def tea(self, ctx):
        """ⓂUruchamia śmierć od ziółek
        """
        herb = self.bot.game.nights[-1].herbed
        if herb is None:
            await ctx.send("Nikt nie ma podłożonych ziółek", delete_after=5)  # TODO: Raise some error
            await ctx.message.delete(delay=5)
            return
        await get_town_channel().send("Ktoś robi się zielony(-a) na twarzy :sick: i...")
        await asyncio.sleep(3)
        await herb.die("herbs")

    @commands.command(name='next', aliases=['n'], enabled=False, hidden=True)
    @manitou_cmd()
    @game_check()
    @day_only(rev=True)  # TODO: Do somthing with this command
    async def next_night(self, ctx):
        """Ⓜ/&n/Rozpoczyna rundę następnej postaci w trakcie nocy.
        """
        if ctx.channel.type != discord.ChannelType.private and ctx.channel != get_manitou_notebook():
            await ctx.send("Tej komendy można użyć tylko w DM lub notatniku manitou", delete_after=5)
            await ctx.message.delete(delay=5)
            return
        await self.bot.game.nights[-1].night_next(ctx.channel)

    @commands.Cog.listener('on_reaction_add')
    async def new_reaction(self, emoji, member):
        if not get_member(member.id) in get_manitou_role().members:
            return
        if emoji.emoji != '➡️':
            return
        if not emoji.me:
            return
        await self.bot.game.nights[-1].night_next(emoji.message.channel)

    @commands.command()
    @manitou_cmd()
    @game_check(rev=True)
    async def nuke(self, ctx):
        """ⓂOdbiera rolę Gram i Trup wszystkim userom
        """
        player_role = get_player_role()
        dead_role = get_dead_role()
        spec_role = get_spectator_role()
        tasks = [utility.remove_roles(dead_role.members + player_role.members + spec_role.members,
                                      dead_role, player_role, spec_role)]
        for member in get_guild().members:
            tasks.append(clear_nickname(member))
        async with ctx.typing():
            await self.remove_cogs()
            await asyncio.gather(*tasks)
        await ctx.message.add_reaction('❤️')

    @commands.command(name='kill')
    @manitou_cmd()
    @game_check()
    async def kill(self, _, *, gracz: MyMemberConverter):
        """ⓂZabija otagowaną osobę
        """
        player = gracz
        await self.bot.game.player_map[player].role_class.die()

    @commands.command(name='plant')
    @manitou_cmd()
    @game_check()
    async def plant(self, _, *, gracz: MyMemberConverter):
        """ⓂPodkłada posążek wskazanegu graczowi, nie zmieniając frakcji posiadaczy
        """
        member = gracz
        self.bot.game.statue.manitou_plant(member)  # TODO: Remove raising InvalidRequest

    @commands.command(name='give', aliases=['statue'])
    @manitou_cmd()
    @game_check()
    async def give(self, _, *, gracz: MyMemberConverter):
        """Ⓜ/&statue/Daje posążek w posiadanie wskazanegu graczowi
        """
        member = gracz
        self.bot.game.statue.give(member)  # TODO: Remove InvalidRequest

    @commands.command(name='who_has', aliases=['whos'])
    @manitou_cmd()
    @game_check()
    async def who_has(self, _):
        """Ⓜ/&whos/Wysyła do Manitou kto ma aktualnie posążek
        """
        try:  # TODO: Make some property in game.statue
            c = "Posążek {}jest podłożony i ma go **{}**, frakcja **{}**".format(
                "nie " if not self.bot.game.statue.planted else "",
                self.bot.game.statue.holder.display_name, self.bot.game.statue.faction_holder)
        except AttributeError:
            c = f"Posążek ma frakcja **{self.bot.game.statue.faction_holder}**, posiadacz jest nieustalony."
        await send_to_manitou(c)

    @commands.command(name='swap')
    @manitou_cmd()
    @game_check()
    async def swap(self, ctx, gracz1: MyMemberConverter(), gracz2: MyMemberConverter()):
        """ⓂZamienia role 2 wskazanych osób
        """
        first = gracz1
        second = gracz2
        role1, role2 = self.bot.game.swap(first, second)
        await first.send("Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(get_role_details(role1, role1)))
        await second.send("Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(get_role_details(role2, role2)))
        await ctx.send("**{}** to teraz **{}**\n**{}** to teraz **{}**".format(
            first.display_name, role1, second.display_name, role2))

    @commands.command(name='gra')
    @manitou_cmd()
    async def if_game_started(self, ctx):
        """ⓂSłuży do sprawdzania czy gra została rozpoczęta
        """
        await ctx.send('Gra została rozpoczęta' if if_game() else 'Gra nie została rozpoczęta')

    @commands.command(hidden=True)
    @manitou_cmd()
    @game_check()
    async def end_game(self, ctx):
        """ⓂKończy grę
        """
        tasks = []
        async with ctx.typing():
            tasks.append(self.bot.game.end())
            tasks.append(self.remove_cogs())
            await asyncio.gather(*tasks)
            self.bot.game = NotAGame()
            await get_town_channel().send("Gra została zakończona")

    @commands.command(name='end')
    @manitou_cmd()
    @game_check()
    async def end_reset(self, ctx):
        """ⓂResetuje graczy i kończy grę"""
        m = await ctx.send("Czy na pewno chcesz zakończyć grę?")
        await m.add_reaction('✅')
        await m.add_reaction('⛔')

        def check_func(r: discord.Reaction, u: Union[discord.User, discord.Member]):
            return all([get_member(u.id) in get_manitou_role().members, r.emoji in ('✅', '⛔'),
                       r.message.id == m.id])

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=check_func, timeout=60)
            if reaction.emoji == '⛔':
                raise asyncio.TimeoutError
        except asyncio.TimeoutError:
            await ctx.message.delete(delay=0)  # TODO: Some cancellation error
        else:
            await self.end_game(ctx)
            await self.reset(ctx)
        finally:
            await m.delete(delay=0)

    @commands.command(name='Manitou_help', aliases=['mhelp'])
    @manitou_cmd()
    async def manithelp(self, ctx):
        """Ⓜ/&mhelp/Pokazuje skrótową pomoc dla Manitou"""
        msg = manitouhelp()
        await ctx.send(f'```fix\n{msg}```')

    @commands.command(name='random')
    @manitou_cmd()
    async def random(self, ctx, n: int):
        """ⓂLosuje liczbę naturalną z przedziału [1, n]"""
        r = randint(1, n)
        await ctx.send(r)

    async def reset(self, ctx: commands.Context):
        player_role = get_player_role()
        dead_role = get_dead_role()
        winner_role = get_duel_winner_role()
        loser_role = get_duel_loser_role()
        searched_role = get_searched_role()
        hanged_role = get_hanged_role()
        tasks = []
        async with ctx.typing():
            tasks.append(utility.remove_roles(dead_role.members + player_role.members,
                                              dead_role, winner_role, loser_role, searched_role, hanged_role))
            tasks.append(utility.add_roles(get_voice_channel().members, player_role))
            tasks.append(self.remove_cogs())
            await asyncio.gather(*tasks)

    @commands.command(name='revive', aliases=['resetuj', 'reset'])
    @manitou_cmd()
    @game_check(rev=True)
    async def reset_players(self, ctx):
        """Ⓜ/&reset/Przywraca wszystkim trupom rolę gram"""
        await self.reset(ctx)

    @commands.command()
    @manitou_cmd()
    @game_check()
    async def alives(self, ctx):
        """ⓂŻywi dla Manitou (nie używać publicznie)
        """
        alive_roles = []
        for role in self.bot.game.roles:
            if self.bot.game.role_map[role].player.member in get_player_role().members:
                alive_roles.append(role)
        team = postacie.print_list(alive_roles)
        await ctx.send(
            '''Liczba żywych graczy: {}
      Pozostali:{}'''.format(len(alive_roles), team))

    @commands.command(name='rioters_count', aliases=['criot'])
    @manitou_cmd()
    @game_check()
    async def countrioters(self, ctx):
        """Ⓜ/criot/Zwraca liczbę zbuntowanych graczy
        """
        await ctx.send("Liczba buntowników wynosi {}".format(len(self.bot.game.rioters)))

    @commands.command(aliases=['gd', 'num'])
    @ktulu_check()
    async def number(self, _, nazwa: str, n: int):
        """Ⓜ/&n/Zmienia liczby gry (pojedynki, przeszukania, odpływanie)
        Argumenty: <duels, searches, evening, morning lub pierwsze litery> <liczba>
        """
        name = nazwa
        name2attr = {
            'd': 'duels',
            's': 'searches',
            'm': 'bandit_morn',
            'e': 'bandit_even'
        }
        try:
            setattr(self.bot.game, name2attr[name[0]], n)
        except KeyError:
            raise commands.BadArgument(f'No phrase "{name}" in data') from None

    @commands.command(name='turn_revealing_on', aliases=['rev_on'])
    @manitou_cmd()
    @mafia_check()
    async def revealing_on(self, _):
        """Ⓜ/rev_on/Włącza ujawnianie postaci po śmierci
        """
        self.bot.game.reveal_dead = True

    @commands.command(name='switch_revealing_off', aliases=['rev_off'])
    @manitou_cmd()
    @mafia_check()
    async def revealing_off(self, _):
        """Ⓜ/rev_off/Wyłącza ujawnianie postaci po śmierci
        """
        self.bot.game.reveal_dead = False

    @commands.command(name="day")
    @manitou_cmd()
    @game_check()
    @day_only(rev=True)
    async def night_end(self, _):
        """ⓂRozpoczyna dzień"""
        tasks = []
        await self.bot.game.new_day()
        tasks.append(utility.send_game_channels('=\nDzień {}'.format(self.bot.game.day)))
        tasks.append(get_town_channel().set_permissions(get_player_role(), send_messages=True))
        tasks.append(self.bot.get_cog("Panel Sterowania").morning_reset())
        await asyncio.gather(*tasks)

    @commands.command(name="night")
    @manitou_cmd()
    @game_check()
    @day_only()
    async def night_start(self, _):
        """ⓂRozpoczyna noc
        """
        try:
            await get_town_channel().set_permissions(get_player_role(), send_messages=False)
        except discord.HTTPException:
            pass
        self.bot.game.new_night()

    @commands.command(name='m', help=manitouhelp(), hidden=True)
    async def manitou_help(self, ctx):
        await ctx.message.delete(delay=0)
