import asyncio
import datetime
import os
from random import shuffle
from typing import List, Tuple, Optional

import discord

import postacie
import utility
from basic_models import NotAGame
from bot_basics import bot
from errors import WrongRolesNumber
from game import Game
from mafia import Mafia
from settings import RULLER
from utility import get_player_role, clear_nickname, send_to_manitou, get_manitou_role, get_other_manitou_role, \
    get_newcommer_role, get_town_channel

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


async def start_game(*roles: str, mafia: bool = False, faction_data: Optional[Tuple[List[str], List[str]]] = None):
    players = list(get_player_role().members)
    faction_data = faction_data or ([], [])
    if mafia and len(roles) != len(players):
        raise WrongRolesNumber(len(players), len(roles))
    elif not mafia and len(set(roles)) != len(players):
        raise WrongRolesNumber(len(players), len(set(roles)))

    bot.game = Game() if not mafia else Mafia()

    roles_file = open(ROLES_FILE, 'w')
    lista_shuffled = list(roles)
    shuffle(lista_shuffled)
    shuffle(lista_shuffled)
    tasks = []

    msg = "\nPostacie:\n"
    roles_file.write("Postacie:\n")
    bot.game.roles = roles
    for member, role in zip(players, lista_shuffled):
        tasks.append(clear_nickname(member))
        tasks.append(member.send(STARTING_INSTRUCTION.format(RULLER, postacie.get_role_details(role, role))))
        bot.game.add_pair(member, role)
    bot.game.make_factions(roles, faction_data)
    await asyncio.gather(*tasks, return_exceptions=True)

    tasks = []
    for member in sorted(players, key=lambda m: m.display_name.lower()):
        msg += "{};\t{}\n".format(member.display_name, bot.game.player_map[member].role)
        roles_file.write("{}\t{}\n".format(member.display_name, bot.game.player_map[member].role))
    roles_file.close()
    time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    with open(ROLES_FILE, 'rb') as fp:
        tasks.append(send_to_manitou(msg, file=discord.File(fp, 'Postacie {}.txt'.format(time))))
    try:
        os.remove(ROLES_FILE)
    except PermissionError:
        pass
    tasks.append(
        utility.add_roles(get_manitou_role().members, get_other_manitou_role()))
    tasks.append(
        utility.remove_roles(list(set(players) & set(get_newcommer_role().members)), get_newcommer_role()))
    tasks.append(bot.change_presence(activity=discord.Game('Ktulu')))
    tasks.append(utility.send_game_channels(RULLER))
    team = bot.game.print_list(list(roles), faction_data)
    bot.game.message = await get_town_channel().send('''Rozdałem karty. Liczba graczy: {}
Gramy w składzie:{}'''.format(len(roles), team))

    tasks.append(bot.game.message.pin())
    tasks.append(get_town_channel().set_permissions(get_player_role(), send_messages=False))
    tasks.append(bot.get_cog('Panel Sterowania').prepare_panel())
    await asyncio.gather(*tasks, return_exceptions=True)


def if_game():
    return not isinstance(bot.game, NotAGame)
