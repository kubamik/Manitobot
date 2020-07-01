import asyncio
from random import randint

from discord.ext import commands

import globals
import postacie
from postacie import get_role_details
from settings import *
from starting import if_game
from utility import *


class DlaManitou(commands.Cog, name="Dla Manitou"):

    def __init__(self, bot):
        self.bot = bot

    async def remove_cogs(self):
        bot.remove_cog("Głosowania")
        bot.remove_cog("Polecenia postaci i frakcji")
        bot.remove_cog("Pojedynki")
        bot.remove_cog("Przeszukania")
        bot.remove_cog("Wieszanie")
        p = discord.Permissions().all()
        try:
            await get_admin_role().edit(permissions=p)
        except (NameError, discord.errors.Forbidden):
            pass

    @commands.command(name='tea')
    @manitou_cmd
    async def tea(self, ctx):
        '''ⓂUruchamia śmierć od ziółek'''
        if globals.current_game.night:
            await ctx.send("Nie możesz tego użyć podczas nocy")
            return
        herb = globals.current_game.nights[-1].herbed
        if herb is None:
            await ctx.send("Nikt nie ma podłożonych ziółek")
            return
        await get_town_channel().send(
            "Ktoś robi się zielony(-a) na twarzy :sick: i...")
        await asyncio.sleep(3)
        await herb.die("herbs")
        await ctx.message.add_reaction('✅')

    @commands.command(name='next', aliases=['n'])
    @manitou_cmd
    async def next_night(self, ctx):
        """Ⓜ/&n/Rozpoczyna rundę następnej postaci w trakcie nocy."""
        if not globals.current_game.night:
            await ctx.send("Tej komendy można użyć tylko w nocy")
            return
        if ctx.channel.type != discord.ChannelType.private and ctx.channel != get_manitou_notebook():
            await ctx.send(
                "Tej komendy można użyć tylko w DM lub notatniku manitou")
            return
        await globals.current_game.nights[-1].night_next(ctx.channel)

    @bot.listen('on_reaction_add')
    async def new_reaction(emoji, member):
        if not get_member(member.id) in get_manitou_role().members:
            return
        if emoji.emoji != '➡️':
            return
        if bot.user not in await emoji.users().flatten():
            return
        await globals.current_game.nights[-1].night_next(emoji.message.channel)

    @commands.command(name='nuke')
    @manitou_cmd
    async def nuke(self, ctx):
        """ⓂOdbiera rolę Gram i Trup wszystkim userom"""
        if if_game():
            await ctx.send("Najpierw zakończ grę!")
            return
        player_role = get_player_role()
        dead_role = get_dead_role()
        spec_role = get_spectator_role()
        async with ctx.typing():
            await self.remove_cogs()
            for member in dead_role.members:
                await member.remove_roles(dead_role)
                await clear_nickname(member, ctx)
            for member in player_role.members:
                await member.remove_roles(player_role)
                await clear_nickname(member, ctx)
            for member in spec_role.members:
                await member.remove_roles(spec_role)
                await clear_nickname(member, ctx)
        await ctx.send("Usunięto wszystkim role Gram, Trup i Obserwator")

    @commands.command(name='kill')
    @manitou_cmd
    async def kill(self, ctx, *, gracz):
        """ⓂZabija otagowaną osobę."""
        try:
            gracz = await discord.ext.commands.MemberConverter().convert(ctx, gracz)
        except commands.BadArgument:
            gracz = nickname_fit(gracz)
        if gracz is None or gracz not in get_guild().members:
            await ctx.send("Nie ma takiego gracza")
            return
        if gracz in get_dead_role().members:
            await ctx.send("Ten gracz już nie żyje")
            return
        if not if_game() or gracz not in get_player_role().members:
            await ctx.send("Ten gracz musi grać, aby mógł zginąć")
            return
        await globals.current_game.player_map[gracz].role_class.die()
        await ctx.message.add_reaction('✅')

    @commands.command(name='give', aliases=['statue', 'statuette'])
    @manitou_cmd
    async def give(self, ctx, *, member):
        '''Ⓜ/&statue/&statuette/Daje posążek w posiadanie wskazanegu graczowi'''
        member = await converter(ctx, member)
        try:
            globals.current_game.statue.give(member)
            await ctx.message.add_reaction('✅')
        except InvalidRequest as err:
            await ctx.send(err.reason)

    @commands.command(name='whohas', aliases=['whos', 'who_has'])
    @manitou_cmd
    async def who_has(self, ctx):
        '''Ⓜ/&whos/&who_has/Wysyła do Manitou kto ma aktualnie posążek'''
        try:
            c = "Posążek ma {}".format(
                globals.current_game.statue.holder.display_name)
        except AttributeError:
            c = "Na razie nikt nie ma posążka"
        if ctx.channel == get_manitou_notebook():
            await ctx.send(c)
        else:
            await send_to_manitou(c)
        await ctx.message.add_reaction('✅')

    @commands.command(name='swap')
    @manitou_cmd
    async def swap(self, ctx, first, second):
        '''ⓂZamienia role 2 wskazanych osób'''
        first = await converter(ctx, first)
        second = await converter(ctx, second)
        try:
            role1, role2 = globals.current_game.swap(first, second)
            await first.send(
                "Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(
                    get_role_details(role1, role1)))
            await second.send(
                "Zmieniono ci rolę. Twoja nowa rola to:\n{}".format(
                    get_role_details(role2, role2)))
            await send_to_manitou(
                "**{}** to teraz **{}**\n**{}** to teraz **{}**".format(
                    first.display_name, role1, second.display_name, role2))
            await ctx.message.add_reaction('✅')
        except KeyError:
            await ctx.send("Ta osoba nie gra lub nie ma takiej osoby")

    @commands.command(name='revealdead', aliases=['red'])
    @manitou_cmd
    async def dead_reveal(self, ctx):
        """Ⓜ/&red/Dodaje w nicku rolę wszystkim martwym graczom"""
        if globals.current_game is None:
            await ctx.send("Gra nie została rozpoczęta")
            return
        for member in get_dead_role().members:
            nickname = get_nickname(member.id)
            globals.current_game.role_map[
                globals.current_game.player_map[member].role].revealed = True
            if nickname[-1] != ')':
                try:
                    await get_town_channel().send(
                        "Rola **{}** to **{}**".format(
                            nickname.replace('+', ' '),
                            globals.current_game.player_map[
                                member].role.replace('_', ' ')))
                    await member.edit(nick=nickname + "({})".format(
                        globals.current_game.player_map[member].role.replace(
                            '_', ' ')))
                except discord.errors.Forbidden:
                    await member.send(
                        "Zmień swój nick na {}, bo ja nie mam uprawnień.".format(
                            nickname + "({})".format(
                                globals.current_game.player_map[
                                    member].role.replace('_', ' '))))
                    await ctx.send(
                        "Nie mam uprawnień aby zmienić nick użytkownika {}".format(
                            nickname))
        await ctx.message.add_reaction('✅')

    @commands.command(name='gra')
    async def if_game_started(self, ctx):
        """Służy do sprawdzania czy gra została rozpoczęta"""
        if if_game():
            await ctx.send("Gra została rozpoczęta")
        else:
            await ctx.send("Gra nie została rozpoczęta")

    @commands.command(name='end_game')
    @manitou_cmd
    async def end_game(self, ctx):
        """ⓂKończy grę"""
        if globals.current_game == None:
            await ctx.send("Gra musi być rozpoczęta, aby ją zakończyć")
            return
        async with ctx.typing():
            for role in globals.current_game.role_map.values():
                if not role.revealed:
                    await role.reveal()
            globals.current_game = None
            await self.remove_cogs()
            await bot.change_presence(activity=None)
            await ctx.send("Gra została zakończona")

    @commands.command(name='end')
    @manitou_cmd
    async def end_reset(self, ctx):
        """ⓂResetuje graczy i kończy grę"""
        await self.end_game(ctx)
        await self.resetuj_grajacych(ctx)
        await ctx.message.add_reaction('✅')

    @commands.command(name='random')
    @manitou_cmd
    async def losuj(self, ctx, n):
        """ⓂLosuje liczbę naturalną z przedziału [1, n]"""
        try:
            n = int(n)
            if (n < 1):
                await ctx.send("Należy podać liczbę naturalną dodatnią")
                return
            r = randint(1, n)
            await ctx.send(r)
        except ValueError:
            await ctx.send("Należy podać liczbę naturalną dodatnią")

    @commands.command(name='revive', aliases=['resetuj', 'reset'])
    @manitou_cmd
    async def resetuj_grajacych(self, ctx):
        """Ⓜ/&resetuj/Przywraca wszystkim trupom rolę gram"""
        if if_game():
            await ctx.send("Najpierw zakończ grę!")
            return
        player_role = get_player_role()
        dead_role = get_dead_role()
        async with ctx.typing():
            for member in dead_role.members + player_role.members:
                await member.remove_roles(dead_role)
                await member.add_roles(player_role)
            await self.remove_cogs()
        await ctx.send(
            "Wszystkim z rolą 'preparat anatomiczny' nadano rolę 'gram'")

    @commands.command(name="alives")
    @manitou_cmd
    async def alives(self, ctx):
        """Ⓜ&żywi dla Manitou"""
        try:
            alive_roles = []
            for role in globals.current_game.roles:
                if globals.current_game.role_map[role].player.member in get_player_role().members \
                        and not globals.current_game.role_map[role].player.member in get_dead_role().members:
                    alive_roles.append(role)
            team = postacie.print_list(alive_roles)
            await ctx.send(
                """Liczba żywych graczy: {}
          Pozostali:{}""".format(len(alive_roles), team))
        except AttributeError:
            await ctx.send("Najpierw rozpocznij grę")

    @commands.command(name='searches')
    @manitou_cmd
    async def searches(self, ctx, n: int):
        '''ⓂZmienia ilość przeszukań dziennie'''
        globals.current_game.searches = n
        await ctx.message.add_reaction('✅')

    @commands.command(name='duels')
    @manitou_cmd
    async def duels(self, ctx, n: int):
        '''ⓂZmienia ilość pojedynków dziennie'''
        globals.current_game.duels = n
        await ctx.message.add_reaction('✅')

    @commands.command(name='evening', aliases=['even'])
    @manitou_cmd
    async def evening(self, ctx, n: int):
        '''Ⓜ/&even/Ustawia czas odjazdu bandytów na podany wieczór'''
        globals.current_game.bandit_night = n
        globals.current_game.bandit_morning = False
        await ctx.message.add_reaction('✅')

    @commands.command(name='morning', aliases=['morn'])
    @manitou_cmd
    async def evening(self, ctx, n: int):
        '''Ⓜ/&even/Ustawia czas odjazdu bandytów na podany poranek'''
        globals.current_game.bandit_night = n
        globals.current_game.bandit_morning = True
        await ctx.message.add_reaction('✅')

    @commands.command(name="day")
    @manitou_cmd
    async def night_end(self, ctx):
        """ⓂRozpoczyna dzień"""
        if not globals.current_game.night:
            await ctx.send("Dzień można rozpocząć tylko w nocy")
            return
        globals.current_game.new_day()
        for channel in get_guild().text_channels:
            if channel.category_id == get_game_channels_category_id():
                await channel.send("=\nDzień {}".format(globals.current_game.day))
        for member in get_dead_role().members:
            if not globals.current_game.player_map[member].role_class.revealed:
                await globals.current_game.player_map[member].role_class.reveal()
        await ctx.message.add_reaction('✅')

    @commands.command(name="night")
    @manitou_cmd
    async def night_start(self, ctx):
        '''ⓂRozpoczyna noc'''
        if globals.current_game.night:
            await ctx.send("Noc można rozpocząć tylko w dzień")
            return
        globals.current_game.new_night()
        globals.current_game.night = True
        await ctx.message.add_reaction('✅')
