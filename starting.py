import discord
import postacie
from random import shuffle
import datetime
import os

from basic_models import NotAGame
from utility import *
from settings import *
from game import Game
from globals import bot
import globals
from role import Role
from player import Player
from postacie import get_faction
from mafia import Mafia



async def start_game(ctx, *lista, mafia = False, faction_data = ()):
  roles = open('Postacie.txt', 'w')
  gracze = list(get_player_role().members)
  if if_game():
    await ctx.send("Musisz najpierw zakończyć trwającą grę, użyj `&end`.")
    return
  if len(lista) != len(gracze):
    await ctx.send(
		    "Błędna liczba postaci. Oczekiwano {}, Otrzymano {}".format(
		        len(gracze), len(lista)))
    return
  
  globals.current_game = Game() if not mafia else Mafia()

  lista_shuffled = list(lista)
  shuffle(lista_shuffled)

  c = "\nPostacie:\n"
  roles.write("Postacie:\n")
  globals.current_game.roles = lista
  for member, role in zip(gracze, lista_shuffled):
    try:
      await clear_nickname(member, ctx)
      await member.create_dm()
      await member.dm_channel.send(
			    """{}\nWitaj, jestem cyfrowym przyjacielem Manitou. Możesz wykorzystać mnie aby ułatwić sobie rozgrywkę. Jako gracz masz dostęp m.in. do następujących komend:
`&help` pokazuje wszystkie dostępne komendy
`&help g` pokazuje komendy przydatne dla graczy
`&postać <nazwa postaci>` pokazuje opis danej postaci
`&żywi` przedstawia żywe postaci, które biorą udział w grze
{}
Twoja postać to:\n{}""".format(RULLER, RULLER, postacie.get_role_details(role, role)))
    except discord.errors.Forbidden:
      await ctx.send(
			    "Nie można wysłać wiadomości do {}\nKonieczne będzie ręczne przekazanie roli".format(get_nickname(member.id)))
    globals.current_game.add_pair(member, role)
  globals.current_game.make_factions(lista, faction_data)
  for member in sorted(gracze, key = lambda m: get_nickname(m.id).lower()):
    c += "{};\t{}\n".format(get_nickname(member.id),globals.current_game.player_map[member].role)
    k = lambda m: get_nickname(m.id)
    roles.write("{}\t{}\n".format(get_nickname(member.id),globals.current_game.player_map[member].role))
  try:
    roles.close()
    await send_to_manitou(c)
    time = datetime.datetime.now()
    with open("Postacie.txt",'rb') as fp:
      await send_to_manitou(file=discord.File(fp,'Postacie {}.txt'.format(time.strftime("%Y-%m-%d_%H-%M-%S"))))
    os.remove("Postacie.txt")
  except discord.errors.Forbidden:
    await ctx.send("Nie można wysłać wiadomości do Manitou")
  for member in get_manitou_role().members:
    await member.add_roles(get_other_manitou_role())
  for member in gracze:
    if member in get_newcommer_role().members:
      await member.remove_roles(get_newcommer_role())
  await bot.change_presence(activity = discord.Game("Ktulu"))
  for channel in get_guild().text_channels:
    if channel.category_id == FRAKCJE_CATEGORY_ID  or channel.category_id == NIEPUBLICZNE_CATEGORY_ID:
      await channel.send(RULLER)
  team = globals.current_game.print_list(lista, faction_data)
  globals.current_game.message = await get_town_channel().send("""Rozdałem karty. Liczba graczy: {}
Gramy w składzie:{}""".format(len(lista), team))
  try:
    await globals.current_game.message.pin()
  except (discord.NotFound, discord.Forbidden, discord.HTTPException):
    pass
  await bot.get_cog('Panel Sterowania').prepare_panel(globals.current_game)
  try:
    await get_town_channel().set_permissions(get_player_role(), send_messages = False)
  except (discord.Forbidden, discord.HTTPException):
    pass

    
def if_game():
  return not isinstance(globals.current_game, NotAGame)
