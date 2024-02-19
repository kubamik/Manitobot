import asyncio
import itertools
import re
from collections import Counter
from typing import Dict, List, Union

import discord
from discord.ext import commands

from settings import RULLER
from .basic_models import ManiBot
from .f_database import factions_roles
from .interactions import ComponentCallback, Select, SelectOption, Button
from .interactions.components import ButtonStyle
from .interactions.interaction import ComponentInteraction
from .my_checks import manitou_cmd, game_check, ktulu_check, qualified_manitou_cmd, sets_channel_only
from .errors import NoSuchSet, WrongRolesNumber, WrongSetNameError, SetExists, NotAuthor, TooLongText
from .game import Game
from .postacie import print_list
from .starting import start_game, STARTING_INSTRUCTION, send_role_list
from .utility import clear_nickname, playerhelp, manitouhelp, get_admin_role, get_spectator_role, get_dead_role, \
    get_player_role, get_town_channel, get_voice_channel, get_manitou_role
from . import control_panel, roles_commands, sklady, daily_commands, postacie as post


class Starting(commands.Cog, name='Początkowe'):
    set_create_ops: Dict[
        int, List[Union[str, List[str], discord.Message]]]
    # Dict[user_id, List[set_name, set_description, Town_players, Bandits_Indians_players, Inqui_Ufo_players,
    # Other_players, set_creation_message]

    def __init__(self, bot_: ManiBot):
        self.bot = bot_
        self.sets_names = sklady.setup_sets_db()
        self.set_create_ops = {}
        self.sets_under_creation = []
        self.bot.add_component_callback(ComponentCallback('modify_set_town', self.modify_set))
        self.bot.add_component_callback(ComponentCallback('modify_set_bandians', self.modify_set))
        self.bot.add_component_callback(ComponentCallback('modify_set_inqufo', self.modify_set))
        self.bot.add_component_callback(ComponentCallback('modify_set_other', self.modify_set))
        self.bot.add_component_callback(ComponentCallback('set_create_confirm', self.confirm_set_creation))
        self.bot.add_component_callback(ComponentCallback('set_create_cancel', self.cancel_set_creation))

    async def add_cogs(self):
        try:
            self.bot.add_cog(roles_commands.PoleceniaPostaci(self.bot))
            self.bot.add_cog(daily_commands.DailyCommands(self.bot))
            self.bot.add_cog(control_panel.ControlPanel(self.bot))
        except discord.errors.ClientException:
            pass
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions.all()
        p.administrator = False
        try:
            await get_admin_role().edit(permissions=p, colour=0)
        except (NameError, discord.errors.Forbidden):
            pass

    async def add_cogs_lite(self):
        try:
            self.bot.add_cog(daily_commands.DailyCommands(self.bot))
        except discord.errors.ClientException:
            pass
        self.bot.get_command('g').help = playerhelp()
        self.bot.get_command('m').help = manitouhelp()
        p = discord.Permissions().all()
        p.administrator = False
        try:
            await get_admin_role().edit(permissions=p)
        except (NameError, discord.errors.Forbidden):
            pass

    def _insert_set(self, set_name: str, set_len: int) -> None:
        # Sorting by roles count first, then alphabetically
        if set_len < 10:
            last_set_q = '0'
            for i, name in enumerate(self.sets_names):
                if name > set_name or last_set_q > name[0]:  # find first bigger occurrence or first double-sign number
                    self.sets_names.insert(i, set_name)
                    break
                last_set_q = name[0]
            else:
                # this shouldn't happen
                self.sets_names.append(set_name)
        else:
            last_set_q = '9'
            n = len(self.sets_names)  # cannot use negative indexing, possible last element inserting
            for i, name in enumerate(self.sets_names[::-1]):
                if name < set_name or last_set_q < name[0]:  # find last lower occurrence or first single-sign number
                    self.sets_names.insert(n-i, set_name)
                    break
                last_set_q = name[0]
            else:
                # this shouldn't happen
                self.sets_names.insert(0, set_name)

    @staticmethod
    def _set_creating_components(ops):
        town = factions_roles['Miasto']
        bandians = factions_roles['Bandyci'] + factions_roles['Indianie']
        inqufo = factions_roles['Ufoki'] + factions_roles['Inkwizycja']
        other = factions_roles['Murzyni'] + factions_roles['Bogowie'] + factions_roles['Inni']
        return [
            [Select('modify_set_town', [SelectOption(r, r, default=r in ops[2]) for r in town], 'Miasto', 0, len(town))],
            [Select('modify_set_bandians', [SelectOption(r, r, default=r in ops[3]) for r in bandians], 'Bandyci/Indianie', 0, len(bandians))
             ],
            [Select('modify_set_inqufo', [SelectOption(r, r, default=r in ops[4]) for r in inqufo], 'Inkwizycja/Ufoki', 0, len(inqufo))],
            [Select('modify_set_other', [SelectOption(r, r, default=r in ops[5]) for r in other], 'Inni', 0, len(other))],
            [Button(ButtonStyle.Success, label='Zatwierdź', emoji='✅', custom_id='set_create_confirm'),
             Button(ButtonStyle.Destructive, label='Anuluj', emoji='❌', custom_id='set_create_cancel')]
        ]

    async def modify_set(self, ctx: ComponentInteraction):
        user_id = ctx.author.id
        author_id = int(re.findall('Autor: <@!?([0-9]+)>', ctx.message.content)[-1])
        if user_id != author_id:
            raise NotAuthor
        op_data = self.set_create_ops[user_id]
        c_id = ctx.custom_id
        idx = 2
        for i, fac in enumerate(['town', 'bandians', 'inqufo', 'other']):
            if c_id.endswith(fac):
                idx += i
                break
        else:
            raise KeyError('Wrong id')
        op_data[idx] = ctx.values
        new_content = ctx.message.content.partition('\n\n')[0]
        roles = []
        for i in range(2, 6):
            roles += op_data[i]
        new_content += '\n\n' + print_list(roles)
        await ctx.edit_message(content=new_content, components=self._set_creating_components(op_data))

    async def confirm_set_creation(self, ctx: ComponentInteraction):
        user_id = ctx.author.id
        author_id = int(re.findall('Autor: <@!?([0-9]+)>', ctx.message.content)[-1])
        if user_id != author_id:
            raise NotAuthor
        name, description, town, bandians, inqufo, other, handle, _ = self.set_create_ops.get(user_id)
        set_roles = town + bandians + inqufo + other
        set_len = str(len(set_roles))
        if set_len == '0':
            await ctx.respond('Skład nie może być pusty', ephemeral=True)
            return
        self.set_create_ops.pop(user_id)
        handle.cancel()
        old_name = name
        if not name.startswith(set_len):
            name = (set_len + name) if not name[0].isdigit() else (set_len + '_' + name)
            if name in self.sets_names:
                for i in itertools.count():
                    if name + f'.{i}' not in self.sets_names:
                        name += f'.{i}'
                        break
        sklady.add_set(user_id, name, description, set_roles)
        self._insert_set(name, len(set_roles))
        self.sets_under_creation.remove(old_name)
        new_content = f'{RULLER}\nNazwa: **{name}**\nOpis: `{description}`\nAutor: <@!{user_id}>\n' \
                      + print_list(set_roles) + '\n' + RULLER
        await ctx.edit_message(content=new_content, components=[])

    async def cancel_set_creation(self, ctx: ComponentInteraction):
        user_id = ctx.author.id
        author_id = int(re.findall('Autor: <@!?([0-9]+)>', ctx.message.content)[-1])
        if user_id != author_id:
            raise NotAuthor
        await self.clean_set_creating(user_id)

    async def clean_set_creating(self, member_id):
        try:
            lst = self.set_create_ops.pop(member_id)
        except KeyError:
            pass
        else:
            await lst[-1].delete()
            lst[-2].cancel()
            self.sets_under_creation.remove(lst[0])

    @commands.command()
    @sets_channel_only()
    @qualified_manitou_cmd()
    async def add_set(self, ctx, name, *, description):
        """Rozpoczyna proces tworzenia setu.
        Nazwa musi składać się ze znaków alfanumerycznych, '-' i '_' i być długości co najmniej 3 znaków,
        jeżeli nazwa nie zaczyna się liczbą postaci to zostanie ona dodana na początku.
        W jednej chwili możliwe jest tworzenie tylko jedego setu na osobę"""
        if not re.match(sklady.SET_NAME, name):
            raise WrongSetNameError
        if name in self.sets_names or name in self.sets_under_creation:
            raise SetExists
        user_id = ctx.author.id
        if user_id in self.set_create_ops:
            raise commands.MaxConcurrencyReached(1, commands.BucketType.user)
        if len(description) > 1000 or len(name) > 100:
            raise TooLongText
        await ctx.message.delete(delay=0)
        self.sets_under_creation.append(name)
        loop = self.bot.loop

        ops = [name, description, [], [], [], []]
        msg = await ctx.send(f'**Dodawanie składu**\nNazwa: **{name}**\nOpis: `{description}`\nAutor: <@!{user_id}>',
                             components=self._set_creating_components(ops))
        handle = loop.call_later(60 * 15, loop.create_task, self.clean_set_creating(user_id))
        self.set_create_ops[user_id] = ops + [handle, msg]

    async def _update_set(self, ctx, set_name, **kwargs):
        if set_name not in self.sets_names:
            raise NoSuchSet
        author_id, r_count = sklady.get_set_author_and_count(set_name)
        name = kwargs.get('name', set_name)
        if not name.startswith(str(r_count)):
            raise WrongSetNameError
        owner = await self.bot.is_owner(ctx.author)
        if not owner and author_id != ctx.author.id:
            raise NotAuthor
        sklady.update_set(set_name, **kwargs)
        if name != set_name:
            self._insert_set(name, r_count)

    @commands.command()
    @sets_channel_only()
    @qualified_manitou_cmd()
    async def rename_set(self, ctx, name, new_name):
        """Zmienia nazwę podanego setu, można używać tylko na swoich setach
        """
        if new_name in self.sets_names or new_name in self.sets_under_creation:
            raise SetExists
        if not re.match(sklady.SET_NAME, new_name):
            raise WrongSetNameError
        await self._update_set(ctx, name, name=new_name)
        self.sets_names.remove(name)

    @commands.command(aliases=['set_description'])
    @sets_channel_only()
    @qualified_manitou_cmd()
    async def redescript_set(self, ctx, name, *, new_description):
        """Zmienia opis podanego setu, można używać tylko na swoich setach
        """
        await self._update_set(ctx, name, description=new_description)

    @commands.command(aliases=['remove_set'])
    @sets_channel_only()
    @qualified_manitou_cmd()
    async def delete_set(self, ctx, name):
        """Usuwa podany set, można używać tylko na swoich setach"""
        if name not in self.sets_names:
            raise NoSuchSet
        author_id, _ = sklady.get_set_author_and_count(name)
        owner = await self.bot.is_owner(ctx.author)
        if not owner and author_id != ctx.author.id:
            raise NotAuthor
        sklady.delete_set(name)
        self.sets_names.remove(name)

    @commands.command(aliases=['składy', 'sets'])
    async def setlist(self, ctx, count: int = None):
        """/&składy/Wypisuje listę predefiniowanych składów, jeśli podana zostanie liczba graczy to wypisuje składy
        dla danej liczby graczy wraz z autorami i opisami
        """
        if count is None:
            await ctx.send(sklady.list_sets([name for name in self.sets_names if name not in self.sets_under_creation]))
            return
        sets = sklady.get_sets(count)
        msg = ''
        for s in sets:
            name, author_id, desc = s
            if author_id:
                content = f'**{name}**\nOpis: `{desc}`\nAutor: <@!{author_id}>\n'
            else:
                content = f'**{name}**\n*wbudowany*\n'
            if len(msg) + len(content) >= 1950:
                await ctx.send(msg + RULLER, allowed_mentions=discord.AllowedMentions(users=False))
                msg = content
            else:
                msg += '\n' + content + RULLER
        if msg:
            await ctx.send(msg, allowed_mentions=discord.AllowedMentions(users=False))
        else:
            await ctx.send('Nie ma składów na podaną liczbę graczy')

    @commands.command(name='set', aliases=['skład'])
    async def set_(self, ctx, nazwa_skladu):
        """/&skład/Wypisuje listę postaci w składzie podanym jako argument.
        """
        set_name = nazwa_skladu
        if set_name not in self.sets_names:
            raise NoSuchSet
        author_id, desc, roles = sklady.get_set(nazwa_skladu)
        if author_id:
            msg = f'**{set_name}**\nOpis: `{desc}`\nAutor: <@!{author_id}>\n'
            msg += print_list(roles)
        else:
            msg = f'**{set_name}**\n{print_list(roles)}'
        await ctx.send(msg, allowed_mentions=discord.AllowedMentions(users=False))

    @staticmethod
    def check_quantity(roles, mafia=False):
        players = get_player_role().members
        if mafia and len(roles) != len(players):
            raise WrongRolesNumber(len(players), len(roles))
        elif not mafia and len(set(roles)) != len(players):
            raise WrongRolesNumber(len(players), len(set(roles)))

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def start_mafia(self, ctx, *postacie: str):
        """Rozpoczyna mafię.
        W argumencie należy podać listę postaci (oddzielonych spacją) z liczebnościami w nawiasie (jeśli są różne od 1)
        np. Miastowy(5).
        Ważne jest zachowanie kolejności - rola mafijna jako ostatnia lub w przypadku większej ilości ról mafii
        oddzielenie ich '|'.
        np. &start_mafia Miastowy(7) Detektyw Lekarz | Boss Mafiozo(2) lub
        &start_mafia Miastowy(3) Mafiozo
        """
        roles = list(postacie)
        stop = -1 if '|' not in roles else roles.index('|')
        roles_list = Counter()
        for role in roles:
            if role == '|':
                i = roles.index(role)
                roles.remove(role)
                role = roles[i]
            count = 1
            if role.endswith(')'):
                role, _, count = role[:-1].rpartition('(')
                count = int(count)
            roles_list[role] = count
        self.check_quantity(list(roles_list.elements()), True)
        await self.add_cogs_lite()
        await start_game(ctx, *roles_list.elements(), mafia=True,
                         faction_data=(list(roles_list)[: stop], list(roles_list)[stop:]))

    @commands.command(name='start')
    @manitou_cmd()
    @game_check(reverse=True)
    async def start_game(self, ctx, *postacie):
        """ⓂRozpoczyna grę ze składem podanym jako argumenty funkcji.
        """
        roles = postacie
        self.check_quantity(roles)
        async with ctx.typing():
            await self.add_cogs()
            await start_game(ctx, *roles)

    @commands.command(aliases=['start_set'])
    @manitou_cmd()
    @game_check(reverse=True)
    async def startset(self, ctx, nazwa_skladu, *dodatkowe):
        """Ⓜ/&start_set/Rozpoczyna grę jednym z predefiniowanych składów
        Argumentami są:
            -Nazwa predefiniowanego składu (patrz komenda składy)
            -opcjonalnie dodatkowe postacie oddzielone białymi znakami
        """
        set_name = nazwa_skladu
        if set_name not in self.sets_names:
            raise NoSuchSet
        await self.start_game(ctx, *(sklady.get_set(set_name)[-1] + list(dodatkowe)))

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def startsetup(self, ctx, nazwa_skladu, *dodatkowe):
        """ⓂRozpoczyna grę jak komenda startset, ale nie wysyła postaci do graczy"""
        set_name = nazwa_skladu
        if set_name not in self.sets_names:
            raise NoSuchSet
        roles = sklady.get_set(set_name)[-1] + list(dodatkowe)
        self.check_quantity(roles)
        async with ctx.typing():
            await self.add_cogs()
            await start_game(ctx, *roles, retard=True)

    @commands.command()
    @manitou_cmd()
    async def verify(self, ctx):
        """ⓂSprawdza integralność osób z rolą gram z osobami na kanale głosowym
        """
        voice_members = set(get_voice_channel().members)
        player_members = set(get_player_role().members)
        observer_members = set(get_spectator_role().members)
        manitou_members = set(get_manitou_role().members)

        msg = ""
        absent = player_members - voice_members
        if absent:
            msg = "**Nieobecni:**\n"
        for m in absent:
            msg += "*{}* ma rolę *Gram* a nie jest na kanale głosowym\n".format(m.display_name)

        present = voice_members - player_members - observer_members - manitou_members
        if present:
            msg += "\n**Obecni:**"
        for m in present:
            msg += "*{}* jest na kanale głosowym a nie ma roli *Gram*, *Obserwator*, *Manitou*\n".format(m.display_name)

        if msg:
            msg += '\n'
        for m in observer_members:
            if not m.display_name.startswith('!') and m not in player_members:
                msg += "*{}* ma rolę *Obserwator* a nie jest oznaczony poprzez `!`\n".format(m.display_name)

        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Wszyscy grający są na kanale głosowym")

    @commands.command()
    @manitou_cmd()
    @game_check(reverse=True)
    async def resume(self, _):
        """ⓂUdaje rozpoczęcie gry, używać gdy bot się wykrzaczy a potrzeba zrobić głosowanie
        """
        await self.add_cogs()
        self.bot.game = Game()

    @commands.command(aliases=['ready'])
    @manitou_cmd()
    @ktulu_check()
    async def deal(self, ctx):
        """ⓂWysyła do wszystkich graczy ich role
        """
        tasks = []
        game = self.bot.game
        for member, player in game.player_map.items():
            role = player.role
            button = player.role_class.button()
            tasks.append(member.send(STARTING_INSTRUCTION.format(RULLER, post.get_role_details(role, role)),
                                     components=button))
        await asyncio.gather(*tasks)
        await send_role_list(game)
        if not game.message:
            team = game.print_list(list(game.roles))
            game.message = msg = await get_town_channel().send(
                'Rozdałem karty. Liczba graczy: {}\nGramy w składzie:{}'.format(
                    len(game.roles), team))
            await msg.pin()

    @commands.command(name='gram')
    @game_check(reverse=True)
    async def register(self, ctx):
        """Służy do zarejestrowania się do gry.
        """
        member = ctx.author
        await clear_nickname(member)
        await member.remove_roles(get_spectator_role(), get_dead_role())
        await member.add_roles(get_player_role())

    @commands.command(name='nie_gram', aliases=['niegram'])
    @game_check(reverse=True)
    async def deregister(self, ctx):
        """Służy do wyrejestrowania się z gry.
        """
        await ctx.author.remove_roles(get_player_role(), get_dead_role())

    @commands.command(aliases=['manit'])
    @game_check(reverse=True)
    @qualified_manitou_cmd()
    async def manitou(self, ctx):
        """ⓂPrzyznaje rolę manitou
        """
        await ctx.author.add_roles(get_manitou_role())

    @commands.command(aliases=['nmanit', 'notmanitou'])
    @game_check(reverse=True)
    @manitou_cmd()
    async def not_manitou(self, ctx):
        """ⓂUsuwa rolę manitou
        """
        await ctx.author.remove_roles(get_manitou_role())
