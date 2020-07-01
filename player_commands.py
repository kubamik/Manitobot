import globals
import permissions
import postacie
from utility import *


class DlaGraczy(commands.Cog, name="Dla Graczy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='postacie', aliases=['lista'])
    async def lista(self, ctx):
        """Pokazuje listę dostępnych postaci, które bot obsługuje"""
        mess = "__Lista dostępnych postaci:__\n:warning:Większość funkcji przedstawionych postaci nie była testowana, więc mogą być bardzo niestabilne:warning:\n"
        mess += ", ".join(permissions.role_activities)
        await ctx.send(mess)

    @commands.command(name='postać')
    async def role_help(self, ctx, *role):
        """Zwraca informacje o postaci podanej jako argument"""
        await postacie.role_details(ctx, role)

    @commands.command(name='czy_gram')
    async def if_registered(command, ctx):
        """Sprawdza czy user ma rolę gram."""
        if czy_gram(ctx):
            await ctx.send("TAK")
        else:
            await ctx.send("NIE")

    @commands.command(name='obserwuję', aliases=['obs'])
    async def spectate(self, ctx):
        """/&obs/Zmienia rolę usera na spectator."""
        member = get_member(ctx.author.id)
        if globals.current_game is not None \
                and member in get_player_role().members + get_dead_role().members:
            await ctx.send("Gra została rozpoczęta, nie możesz nie grać")
            return
        await member.remove_roles(get_player_role(), get_dead_role())
        await member.add_roles(get_spectator_role())
        nickname = member.display_name
        await ctx.message.add_reaction('✅')
        if not nickname.startswith('!'):
            try:
                await get_member(member.id).edit(nick="!" + nickname)
            except discord.errors.Forbidden:
                await ctx.send("Dodaj sobie '!' przed nickiem")

    @commands.command(name='nie_obserwuję', aliases=['nie_obs'])
    async def not_spectate(self, ctx):
        """/&nie_obs/Usuwa userowi rolę spectator."""
        guild = get_guild()
        member = get_member(ctx.author.id)
        await member.remove_roles(get_spectator_role())
        nickname = member.display_name
        if nickname.startswith('!'):
            try:
                await get_member(member.id).edit(nick=nickname[1:])
            except discord.errors.Forbidden:
                pass
        await ctx.message.add_reaction('✅')

    @commands.command(name='bunt', aliases=['riot'])
    async def riot(self, ctx):
        '''/&riot/W przypadku poparcia przez co najmniej 67 % osób biorących udział w grze (także martwych, ale online) kończy grę'''
        if not czy_gram(ctx) and not czy_trup(ctx):
            await ctx.send("Mogą użyć tylko grający")
            return
        try:
            globals.current_game.rioters.add(get_member(ctx.author.id))
        except AttributeError:
            await ctx.send("Gra nie została rozpoczęta")
            return
        count = set()
        for person in get_player_role().members + get_dead_role().members:
            if person.status != discord.Status.offline:
                count.add(person)
            else:
                if person in globals.current_game.rioters:
                    del globals.current_game.rioters[
                        globals.current_game.rioters.index(person)]
        if len(globals.current_game.rioters) == 1:
            await get_town_channel().send(
                "Ktoś rozpoczął bunt. Użyj `&riot` jeśli chcesz dołączyć")
            await send_to_manitou("Ktoś rozpoczął bunt.")
        if len(globals.current_game.rioters) >= len(count) * 0.67:
            for manitou in get_manitou_role().members:
                await manitou.remove_roles(get_manitou_role())
                c = ""
            for member in globals.current_game.player_map.values():
                c += "Rola {} to {}\n".format(get_nickname(member.member.id),
                                              member.role)
            globals.current_game = None
            player_role = get_player_role()
            dead_role = get_dead_role()
            for member in dead_role.members + player_role.members:
                await member.remove_roles(dead_role)
                await member.add_roles(player_role)
                nickname = get_nickname(member.id)
                await clear_nickname(member, ctx)
            await get_town_channel().send(
                "Doszło do buntu gra została zakończona\n{}".format(c))
        await ctx.send("Zarejestrowałem cię jako buntownika")

    @commands.command(name="żywi", aliases=['zywi'])
    async def living(self, ctx):
        """/&zywi/Wypisuje listę żywych graczy"""
        team = ""
        alive_roles = []
        for role in globals.current_game.roles:
            if globals.current_game.role_map[
                role].player.member in get_player_role().members \
                    or (
                    globals.current_game.role_map[
                        role].player.member in get_dead_role().members
                    and not globals.current_game.role_map[role].revealed
            ):
                alive_roles.append(role)
        team = postacie.print_list(alive_roles)
        await ctx.send("""Liczba żywych graczy: {}
Liczba martwych o nieznanych rolach: {}
Pozostali:{}""".format(len(get_player_role().members),
                       len(alive_roles) - len(get_player_role().members), team))
