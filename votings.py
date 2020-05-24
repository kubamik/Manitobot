import discord
import random


from utility import *
from settings import *
from game import Game
import globals

async def glosowanie(ctx, title, required_votes, options, not_voting = (), vtype = None):
  if globals.current_game is None:
    await ctx.send("Najpierw rozpocznij grę ;)")
    return
  if globals.current_game.voting_in_progress():
    await ctx.send("Najpierw zakończ bieżące głosowanie")
    return
  globals.current_game.new_voting(required_votes, options, not_voting, vtype)
  await ctx.message.add_reaction('✅')
  options_readable=""
  for option in options:
    options_readable+="- {}\n".format(",".join(option))

  message = """Rozpoczynamy głosowanie nad: {}
Wymagana liczba głosów to: {}
Opcje:
{}

  Aby zagłosować wyślij mi (botowi) na priv dowolny wariant dowolnej opcji. Wiele głosów należy oddzielić przecinkami. Wielkość znaków nie ma znaczenia.
  """.format(title, required_votes, options_readable)

  await get_glosowania_channel().send(message)
  gracze = list(get_player_role().members)
  trupy = list(get_dead_role().members)
  for gracz in gracze:
    if gracz not in trupy:
      await gracz.create_dm()
      await gracz.dm_channel.send(message)


async def see_voting(ctx, end_vote):
  if not globals.current_game.voting_allowed:
    await ctx.send("Nie trwa teraz żadne głosowanie")
    return
  voing_summary = globals.current_game.summarize_votes()
  summary_readable = ""
  votes_count = 0
  if end_vote:
    globals.current_game.voting_allowed = False
    message = "Głosowanie zakończone!\n"
  else:
    message = "Podgląd głosowania\n"
  for option, voters in voing_summary.items():
    voters_readable = [get_nickname(voter_id) for voter_id in voters]
    summary_readable+= "- {} na {}: {}\n".format(len(voters_readable), option, ", ".join(voters_readable))
    votes_count+=len(voters_readable)
  await ctx.message.add_reaction('✅')
  message += """Wyniki:
{}
Łączna liczba oddanych głosów: {}
Liczba głosujących: {}\n""".format(summary_readable,votes_count,votes_count//globals.current_game.required_votes)

  if end_vote:
    await get_glosowania_channel().send(message)
    for member in get_player_role().members:
      await member.send(message)
    if globals.current_game.vote_type == "duel":
      await globals.current_game.days[-1].result_duel(ctx, voing_summary.items())
    elif globals.current_game.vote_type == "hang":
      await globals.current_game.days[-1].hang_sumarize(ctx, voing_summary.items())
    elif globals.current_game.vote_type == "hangif":
      await globals.current_game.days[-1].if_hang(ctx, voing_summary)
    elif globals.current_game.vote_type == "search":
      await globals.current_game.days[-1].search_summary(ctx, voing_summary.items())
  else:
    not_voted=list(set(get_player_role().members) - set(list(get_dead_role().members)) - globals.current_game.players_voted - set(globals.current_game.not_voting))
    if len(not_voted) == 0:
      message += "Wszyscy grający oddali głosy"
    else:
      message += "Nie zagłosowali tylko:\n"
      for player in not_voted:
        message += get_nickname(player.id) + "\n"
    await send_to_manitou(message)