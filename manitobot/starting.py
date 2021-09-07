import asyncio
import datetime
import os
from random import shuffle
from typing import List, Tuple, Optional

import discord
from discord.ext import commands

from settings import RULLER
from . import postacie
from . import utility
from .basic_models import NotAGame
from .bot_basics import bot
from .game import Game
from .mafia import Mafia
from .utility import get_player_role, clear_nickname, send_to_manitou, \
    get_newcommer_role, get_town_channel, cleared_nickname

STARTING_INSTRUCTION = '''{0}
Witaj, jestem cyfrowym przyjacielem Manitou. Możesz wykorzystać mnie aby ułatwić sobie rozgrywkę. \
Jako gracz masz dostęp m.in. do następujących komend:
`&help` pokazuje wszystkie dostępne komendy
`&help g` pokazuje komendy przydatne dla graczy
`&żywi` przedstawia żywe postaci, które biorą udział w grze
`&zgłaszam <gracz>` zgłasza gracza do przeszukania
`&wyzywam <gracz>` wyzywa gracza na pojedynek
{0}
Twoja postać to:\n{1}'''

ROLES_FILE = 'Postacie.txt'


async def start_game(ctx: commands.Context, *roles: str, mafia: bool = False,
                     faction_data: Optional[Tuple[List[str], List[str]]] = None):
    players = list(get_player_role().members)
    faction_data = faction_data or ([], [])

    ctx.bot.game = game = Game() if not mafia else Mafia()

    roles_file = open(ROLES_FILE, 'w')
    shuffled_list = list(roles)
    shuffle(shuffled_list)
    shuffle(shuffled_list)
    tasks = []

    msg = "\nPostacie:\n"
    roles_file.write("Postacie:\n")
    game.roles = roles
    for member, role in zip(players, shuffled_list):
        tasks.append(clear_nickname(member))
        tasks.append(member.send(STARTING_INSTRUCTION.format(RULLER, postacie.get_role_details(role, role))))
        game.add_pair(member, role)
    game.make_factions(roles, faction_data)
    await asyncio.gather(*tasks, return_exceptions=True)

    tasks = []
    for member in sorted(players, key=lambda m: m.display_name.lower()):
        msg += "{};\t{}\n".format(cleared_nickname(member.display_name), game.player_map[member].role)
        roles_file.write("{}\t{}\n".format(member.display_name, game.player_map[member].role))
    roles_file.close()
    time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    with open(ROLES_FILE, 'rb') as fp:
        tasks.append(send_to_manitou(msg, file=discord.File(fp, 'Postacie {}.txt'.format(time))))
    try:
        os.remove(ROLES_FILE)
    except PermissionError:
        pass
    tasks.append(
        utility.remove_roles(list(set(players) & set(get_newcommer_role().members)), get_newcommer_role()))
    tasks.append(ctx.bot.change_presence(activity=discord.Game('Ktulu')))
    tasks.append(utility.send_game_channels(RULLER))
    team = game.print_list(list(roles), faction_data)
    game.message = await get_town_channel().send('''Rozdałem karty. Liczba graczy: {}
Gramy w składzie:{}'''.format(len(roles), team))

    tasks.append(game.message.pin())
    tasks.append(game.new_night())
    await game.panel.prepare_panel()
    await asyncio.gather(*tasks)


def if_game():
    return not isinstance(bot.game, NotAGame)
