import asyncio
from random import randint
from typing import Union

import discord
import typing
from discord.ext import commands

from settings import FAC2CHANN_ID, CONFIG
from . import postacie, daily_commands
from . import utility
from .basic_models import NotAGame, ManiBot
from .daynight import Day, PartialDay
from .errors import MembersNotPlaying
from .my_checks import manitou_cmd, game_check, mafia_check, ktulu_check, day_only, voting_check
from .converters import MyMemberConverter
from .postacie import get_role_details
from .starting import if_game
from .utility import playerhelp, manitouhelp, get_faction_channel, \
    get_admin_role, get_town_channel, get_player_role, \
    get_manitou_role, get_voice_channel, get_member, get_dead_role, \
    get_spectator_role, get_guild, clear_nickname, send_to_manitou, \
    get_duel_winner_role, get_duel_loser_role, \
    get_searched_role, get_hanged_role, get_control_panel


class DlaManitou(commands.Cog, name="Dla Manitou"):

    def __init__(self, bot: ManiBot):
        self.bot = bot

    async def remove_cogs(self):
        rm_cog = self.bot.remove_cog
        rm_cog('Polecenia postaci i frakcji')
        rm_cog('Panel Sterowania')
        rm_cog(daily_commands.DailyCommands.__cog_name__)
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions().all()
        tasks = []
        for faction in FAC2CHANN_ID:  # TODO: Optimize this
            ch = get_faction_channel(faction)
            tasks.append(ch.edit(sync_permissions=True))
        tasks.append(get_admin_role().edit(permissions=p, colour=0xffa9f9))
        tasks.append(get_town_channel().edit(sync_permissions=True))
        tasks.append(self.bot.change_presence(activity=None))
        await asyncio.gather(*tasks)

    @commands.command(aliases=['cvote', 'cv'])
    @manitou_cmd()
    @voting_check()
    async def custom_vote(
            self, _, title,
            votes_count: typing.Optional[int] = 1, *options):
        """ⓂRozpoczyna customowe głosowanie:
        Argumentami są:
          -tytuł głosowania.
          -wymagana liczba głosów.
          -nazwy kandydatów"""
        game = self.bot.game
        if game.day is None:
            msg = game.panel.day_message
            game.day = PartialDay(game, msg)
        await game.day.custom_voting(title, list(options), votes_count)

    @commands.command(name='votesee', aliases=['vs'])
    @manitou_cmd()
    @voting_check(reverse=True)
    async def vote_see(self, _):
        """Ⓜ/&vs/Pisze do wszystkich manitou obecne wyniki głosowania"""
        results = self.bot.game.day.state.results_embed()
        await send_to_manitou(embed=results)

    @commands.command(aliases=['MM'], enabled=False)
    @manitou_cmd()
    async def mass_mute(self, _):
        """ⓂMutuje graczy niebędących Manitou
        """
        tasks = []
        players = get_player_role().members
        for member in get_voice_channel().members:
            if member in players and member not in get_manitou_role().members \
                    and not member.voice.self_mute:
                tasks.append(member.edit(mute=True))
        await asyncio.gather(*tasks)

    @commands.command(aliases=['MU'], enabled=False)
    @manitou_cmd()
    async def mass_unmute(self, _):
        """ⓂUnmutuje graczy niebędących Manitou
        """
        tasks = []
        players = get_player_role().members
        for member in get_voice_channel().members:
            if member in players and member.voice.mute:
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

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def nuke(self, ctx):
        """ⓂOdbiera rolę Gram i Trup wszystkim userom
        """
        player_role = get_player_role()
        dead_role = get_dead_role()
        spec_role = get_spectator_role()
        manit_role = get_manitou_role()
        tasks = [
            utility.remove_roles(dead_role.members + player_role.members + spec_role.members
                                 + manit_role.members, dead_role, player_role, spec_role, manit_role)
        ]
        for member in get_guild().members:
            if member.id != self.bot.user.id:
                tasks.append(clear_nickname(member))
        async with ctx.typing():
            await self.remove_cogs()
            await asyncio.gather(*tasks)
        await ctx.message.add_reaction('☢️')

    @commands.command()
    @manitou_cmd()
    @game_check()
    async def kill(self, _, *, player: MyMemberConverter):
        """ⓂZabija otagowaną osobę
        """
        await self.bot.game.player_map[player].role_class.die()

    @commands.command()
    @manitou_cmd()
    @ktulu_check()
    async def refresh_panel(self, _):
        """ⓂAktualizuje osoby w Panelu Manitou
        """
        await self.bot.game.panel.update_panel()

    @commands.command()
    @manitou_cmd()
    @game_check()
    async def plant(self, _, *, player: MyMemberConverter):
        """ⓂPodkłada posążek wskazanegu graczowi, nie zmieniając frakcji posiadaczy
        """
        await self.bot.game.statue.manitou_plant(player)

    @commands.command(name='give', aliases=['statue'])
    @manitou_cmd()
    @game_check()
    async def give(self, _, *, player: MyMemberConverter):
        """Ⓜ/&statue/Daje posążek w posiadanie wskazanegu graczowi
        """
        await self.bot.game.statue.give(player)

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
    async def swap(self, ctx, player1: MyMemberConverter(player_only=False),
                   player2: MyMemberConverter(player_only=False)):
        """ⓂZamienia role 2 wskazanych osób
        """
        first = player1
        second = player2
        players = get_player_role().members + get_dead_role().members
        if first not in players and second not in players:
            raise MembersNotPlaying
        elif first not in players:
            first, second = second, first
        send = self.bot.game.message is not None
        if second not in players:
            roles = [get_player_role(), get_dead_role(), get_duel_winner_role(), get_duel_loser_role(),
                     get_searched_role(), get_hanged_role()]
            role = self.bot.game.replace_player(first, second)
            await first.send('**Zostałeś(-aś) usunięty(-a) z gry**')
            if send:
                await second.send('Zostałeś(-aś) dodany(-a) do gry zamiast {}. Twoja rola to:\n{}'.format(
                    first.display_name, get_role_details(role, role)))
            else:
                await second.send('Zostałeś(-aś) dodany(-a) do gry zamiast {}.'.format(first.display_name))
            member_roles = [r for r in roles if r in first.roles]
            await first.remove_roles(*member_roles)
            await second.add_roles(*member_roles)
            await ctx.send('**{0.display_name}** gra teraz zamiast **{1.display_name}**'.format(second, first))
            await self.bot.game.panel.replace_player(first, second, role)
        else:
            role1, role2 = self.bot.game.swap(first, second)
            await self.bot.game.panel.swapping(first, second, role1, role2)
            if send:
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
        async with ctx.typing():
            await self.bot.game.end()
            await self.remove_cogs()
            self.bot.game = NotAGame()
            await get_town_channel().send('Gra została zakończona')

    @commands.command(name='end')
    @manitou_cmd()
    @game_check()
    async def end_reset(self, ctx):
        """ⓂResetuje graczy i kończy grę"""
        m = await ctx.send('Czy na pewno chcesz zakończyć grę?')
        await m.add_reaction('✅')
        await m.add_reaction('⛔')

        def check_func(r: discord.Reaction, u: Union[discord.User, discord.Member]):
            return all([get_member(u.id) in get_manitou_role().members, r.emoji in ('✅', '⛔'),
                        r.message.id == m.id])

        try:  # TODO: Put this in some public function
            reaction, _ = await self.bot.wait_for('reaction_add', check=check_func, timeout=60)
            if reaction.emoji == '⛔':
                raise asyncio.TimeoutError
        except asyncio.TimeoutError:
            await ctx.message.delete(delay=0)
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
        to_delete = [dead_role, winner_role, loser_role, searched_role, hanged_role, player_role]
        tasks = []
        async with ctx.typing():
            for member in dead_role.members + player_role.members:
                roles = [r for r in member.roles if r not in to_delete]
                if member in get_voice_channel().members:
                    roles.append(player_role)
                tasks.append(member.edit(roles=roles))
            await self.remove_cogs()
            await asyncio.gather(*tasks)

    @commands.command(name='revive', aliases=['reset'])
    @manitou_cmd()
    @game_check(reverse=True)
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
        for role in self.bot.game.role_map.values():
            if role.alive:
                alive_roles.append(role.name)
        team = postacie.print_list(alive_roles)
        await ctx.send('Liczba żywych graczy: {}\nPozostali:{}'.format(len(alive_roles), team))

    @commands.command(name='rioters_count', aliases=['criot'])
    @manitou_cmd()
    @game_check()
    async def count_rioters(self, ctx):
        """Ⓜ/criot/Zwraca liczbę zbuntowanych graczy
        """
        await ctx.send("Liczba buntowników wynosi {}".format(len(self.bot.game.rioters)))

    @commands.command(aliases=['gd', 'num'])
    @manitou_cmd()
    @ktulu_check()
    async def number(self, _, name: str, n: int):
        """Ⓜ/&num/Zmienia liczby gry (pojedynki, przeszukania, odpływanie, limit zgłoszeń)
        Argumenty: <duels, searches, evening, morning, reports lub pierwsze litery> <liczba>
        """
        name2attr = {
            'd': 'duels',
            's': 'searches',
            'm': 'bandit_morn',
            'e': 'bandit_even',
            'r': 'reports_limit'
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

    @commands.command(name='day')
    @manitou_cmd()
    @game_check()
    @day_only(reverse=True)
    async def night_end(self, _):
        """ⓂRozpoczyna dzień
        """
        await self.bot.game.new_day()

    @commands.command(name='night')
    @manitou_cmd()
    @game_check()
    @day_only()
    async def night_start(self, _):
        """ⓂRozpoczyna noc
        """
        await self.bot.game.new_night()

    @commands.command(aliases=['spnight'])
    @manitou_cmd()
    @game_check()
    @day_only()
    async def special_night(self, _):
        """Rozpoczyna specjalną noc, gdy Manitou coś zepsuje"""
        await self.bot.game.emergency_night()

    @commands.command(name='m', help=manitouhelp(), hidden=True, brief='&help m')
    async def manitou_help(self, ctx):
        await ctx.message.delete(delay=0)
