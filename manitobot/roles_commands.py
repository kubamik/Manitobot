import discord
from discord.ext import commands

from . import bot_basics
from . import utility
from .errors import AuthorNotPlaying
from .interactions import ComponentCallback
from .interactions.interaction import ComponentInteraction
from .utility import get_member, InvalidRequest


# TODO: IDEA: change commands to message reactions or buttons


def proper_channel():  # TODO: move to checks
    async def predicate(ctx):
        faction = bot_basics.bot.game.nights[-1].active_faction
        if faction is not None and ctx.channel != faction.channel:
            raise commands.NoPrivateMessage
        if faction is None and ctx.channel.type != discord.ChannelType.private:
            raise commands.PrivateMessageOnly
        return True

    return commands.check(predicate)


class PoleceniaPostaci(commands.Cog, name="Polecenia postaci i frakcji",
                       command_attrs=dict(enabled=False, hidden=True)):

    def __init__(self, bot):
        self.bot = bot
        self.lock = False
        add = bot.add_component_callback
        add(ComponentCallback('reveal', self.reveal_role))
        add(ComponentCallback('role_action_cancel', self.role_action_cancel))
        add(ComponentCallback('role_wins_first', self.role_wins_first))
        add(ComponentCallback('role_wins_second', self.role_wins_second))
        add(ComponentCallback('role_veto', self.role_veto))
        
    def cog_unload(self):
        rm = self.bot.remove_component_callback
        rm('reveal')
        rm('role_action_cancel')
        rm('role_wins_first')
        rm('role_wins_second')
        rm('role_veto')

    async def cog_check(self, ctx):
        return not self.lock

    async def cog_before_invoke(self, ctx):
        self.lock = True

    async def cog_after_invoke(self, ctx):
        self.lock = False

    def _get_role(self, member):
        try:
            return self.bot.game.player_map[member].role_class
        except KeyError:
            raise AuthorNotPlaying from None

    async def reveal_role(self, ctx: ComponentInteraction):
        """For usage of reveal button"""
        member = get_member(ctx.author.id)  # ctx.author will probably be of type discord.User
        role = self._get_role(member)
        ability = role.usable_ability('wins', 'reveal')
        await role.new_activity(ctx, ability)
        await ctx.edit_message(components=[])

    async def role_action_cancel(self, ctx: ComponentInteraction):
        """"For usage of canceling day changing (duel, hang) actions button"""
        member = get_member(ctx.author.id)  # ctx.author will probably be of type discord.User
        role = self._get_role(member)
        await role.new_activity(ctx, 'day_refuse')

    async def role_wins_first(self, ctx: ComponentInteraction):
        """For usage of Judge's button for change duel result"""
        member = get_member(ctx.author.id)
        role = self._get_role(member)
        try:
            target = self.bot.game.day.state.author
        except AttributeError:
            pass
        else:
            await role.new_activity(ctx, 'wins', target)

    async def role_wins_second(self, ctx: ComponentInteraction):
        """For usage of Judge's button for change duel result"""
        member = get_member(ctx.author.id)
        role = self._get_role(member)
        try:
            target = self.bot.game.day.state.subject
        except AttributeError:
            pass
        else:
            await role.new_activity(ctx, 'wins', target)
            
    async def role_veto(self, ctx: ComponentInteraction):
        member = get_member(ctx.author.id)
        role = self._get_role(member)
        await role.new_activity(ctx, "peace")

    async def command_template(self, ctx, member, operation):
        author = get_member(ctx.author.id)
        try:
            faction = self.bot.game.nights[-1].active_faction
            if faction is not None and faction == self.bot.game.nights[-1].active_role:
                await faction.new_activity(ctx, operation, member)
            else:
                await self.bot.game.player_map[author].role_class.new_activity(ctx, operation, member)
        except InvalidRequest as err:
            await ctx.send(err.msg)
        except KeyError as err:
            await ctx.message.delete(delay=11)
            await ctx.send("Nie grasz w tej grze", delete_after=10)

    @commands.command(name='śledź')
    @commands.dm_only()
    async def follow(self, ctx, *, member):
        '''Służy do śledzenia'''
        await self.command_template(ctx, member, "follow")

    @commands.command(name='lustruj')
    @commands.dm_only()
    async def mirror(self, ctx, *, member):
        '''Służy do zlustrowania'''
        await self.command_template(ctx, member, "mirror")

    @commands.command(name='kopiuj')
    @commands.dm_only()
    async def copy_it(self, ctx):
        '''Służy do skopiowania zdolności'''
        await self.command_template(ctx, None, "copy")

    @commands.command(name='heretyk')
    @proper_channel()
    async def heretic(self, ctx, *, member):
        '''Służy do sprawdzenia czy osoba jest heretykiem'''
        await self.command_template(ctx, member, "heretic")

    @commands.command(name='przeszukaj', aliases=['przesz'])
    @proper_channel()
    async def research(self, ctx):
        '''/&przesz/Służy do przeszukania sprawdzanej osoby'''
        await self.command_template(ctx, None, "research")

    @commands.command(name='daj')
    @proper_channel()
    async def special_hold(self, ctx, *, member):
        '''Awaryjne oddawanie posążka w razie przerwania gry'''
        await self.command_template(ctx, member, "sphold")

    @commands.command(name='dobij')
    @proper_channel()
    async def finoff(self, ctx):
        '''Służy do zabicia sprawdzanej osoby'''
        await self.command_template(ctx, None, "finoff")

    @commands.command(name='posiadacze', aliases=['posiad'])
    @proper_channel()
    async def holders(self, ctx, *, member):
        '''/&posiad/Służy do sprawdzenia, czy osoba jest z frakcji posiadaczy posążka'''
        await self.command_template(ctx, member, "holders")

    @commands.command(name='spal')
    @commands.dm_only()
    async def burn(self, ctx, *, member):
        '''Służy biskupowi do zabicia i ujawnienia się'''
        self.bot.game.nights[-1].bishop_base = ctx
        author = get_member(ctx.author.id)
        utility.lock = True
        try:
            await self.bot.game.player_map[author].role_class.new_activity(ctx, "burn", member)
        except InvalidRequest as err:
            await ctx.send(err.msg)
        except KeyError:
            await ctx.send("Nie grasz w tej grze")
            raise
        utility.lock = False

    @commands.command(name='podłóż', aliases=['podł'])
    @proper_channel()
    async def plant(self, ctx, *, member):
        '''/&podł/Służy do podłożenia posążka przez Cichą Stopę'''
        await self.command_template(ctx, member, "plant")

    @commands.command(name='ograj')
    @proper_channel()
    async def cheat(self, ctx, *, member):
        '''Służy do ogrania osoby przez Szulera'''
        await self.command_template(ctx, member, "cheat")

    @commands.command(name='ziółka', aliases=['zioł'])
    @proper_channel()
    async def herbs(self, ctx, *, member):
        '''/&zioł/Służy do podłożenia ziółek przez Szamankę'''
        await self.command_template(ctx, member, "herb")

    @commands.command(name='kto')
    @proper_channel()
    async def who(self, ctx):
        '''Służy do sprawdzenia kto ma posążek'''
        await self.command_template(ctx, None, "who")

    @commands.command(name='detektuj', aliases=['detekt'])
    @proper_channel()
    async def detect(self, ctx, *, member):
        '''/&detekt/Służy do użycia Detektora'''
        await self.command_template(ctx, member, "detect")

    @commands.command(name='karta')
    @proper_channel()
    async def card(self, ctx, *, member):
        '''Służy do prawdzenia karty'''
        await self.command_template(ctx, member, "check")

    @commands.command(name='rola')
    @proper_channel()
    async def role(self, ctx, *, member):
        '''Służy do sprawdzenia roli'''
        await self.command_template(ctx, member, "eat")

    @commands.command(name='szam')
    @proper_channel()
    async def szam(self, ctx, *, member):
        '''Służy do oszamanienia osoby'''
        await self.command_template(ctx, member, "szam")

    @commands.command(name='zabij')
    @proper_channel()
    async def zabij(self, ctx, *, member):
        '''Służy do zabicia osoby'''
        await self.command_template(ctx, member, "kill")

    @commands.command(name='posążek', aliases=['pos'])
    @proper_channel()
    async def posag(self, ctx, *, member):
        '''Służy do przekazania posążka'''
        await self.command_template(ctx, member, "hold")

    @commands.command(name='szukaj')
    @proper_channel()
    async def szukaj(self, ctx, *, member):
        '''Służy do przeszukania osoby'''
        await self.command_template(ctx, member, "search")

    @commands.command(name='graj')
    @commands.dm_only()
    async def play(self, ctx, *, member):
        '''Służy do zabicia osoby przez Hazardzistę'''
        await self.command_template(ctx, member, "play")

    @commands.command(name='upij', aliases=['pij'])
    @commands.dm_only()
    async def drink(self, ctx, *, member):
        '''/&pij/Służy do upijania przez Opoja lub Pijanego Sędziego'''
        await self.command_template(ctx, member, "drink")

    @commands.command(name='dziw', aliases=['zadziw'])
    @commands.dm_only()
    async def hmmm(self, ctx, *, member):
        '''/&zadziw/Służy do sprawdzenia osoby przez Dziwkę'''
        await self.command_template(ctx, member, "dziw")

    @commands.command(name='zamknij', aliases=['zamk'])
    @commands.dm_only()
    async def arrest(self, ctx, *, member):
        '''/&zamk/Służy do zamknięcia osoby przez Szeryfa'''
        await self.command_template(ctx, member, "arrest")

    @commands.command(name='spowiedź', aliases=['spowiadaj', 'spow'])
    @commands.dm_only()
    async def pasteur(self, ctx, *, member):
        '''/&spow/Służy do wyspowiadania osoby przez pastora'''
        await self.command_template(ctx, member, "pasteur")

    @commands.command(name='wygrywa', aliases=['wygr'], enabled=True, hidden=False)
    @commands.dm_only()
    async def wins(self, ctx, *, member=None):
        '''/&wygr/Służy do ujawnienia się przez Sędziego, użyte z nazwą gracza powoduje, że wygrywa on pojedynek, użyte samo ujawnia Sędziego powodując utratę zdolności'''
        await self.command_template(ctx, member, "wins")

    @commands.command(name='veto', aliases=['łaska'], enabled=True, hidden=False)
    @commands.dm_only()
    async def veto(self, ctx):
        '''/&łaska/Służy do ujawnienia się przez Burmistrza, użyte w trakcie wieszania ułaskawia, użyte poza ujawnia Burmistrza powodując utratę zdolności'''
        await self.command_template(ctx, None, "peace")

    @commands.command(name='nie')
    async def nein(self, ctx):
        '''Służy do odmowy skorzystania ze zdolności'''
        await self.command_template(ctx, None, "refuse")
