import discord
import random


from utility import *
from settings import *
from game import Game
import globals

async def glosowanie(ctx, title, required_votes, 
                     options, not_voting = (), vtype = None):
  if globals.current_game.voting_in_progress():
    await ctx.send("Najpierw zakończ bieżące głosowanie")
    return
  globals.current_game.new_voting(required_votes, options, not_voting, vtype)
  options_readable=""
  for option in options:
    options_readable += "**{}**\n\n".format(", ".join(option))
  title = title.split('\n')
  etitle = "Głosowanie: {}".format(title[0])
  description = title[1].format(required_votes) + '\n\n' + options_readable
  embed = discord.Embed(title=etitle, colour=discord.Colour(0x00aaff), description=description)
  embed.set_footer(text="INSTRUKCJA\nAby zagłosować wyślij tu dowolny wariant dowolnej opcji. Wiele głosów należy oddzielić przecinkami. Wielkość znaków nie ma znaczenia.")
  gracze = list(get_player_role().members)
  trupy = list(get_dead_role().members)
  nie_glos = list(globals.current_game.not_voting)
  for gracz in gracze:
    if gracz not in trupy + nie_glos:
      await gracz.send(embed=embed)
  await ctx.message.add_reaction('✅')


async def see_voting(ctx, end_vote):
  if not globals.current_game.voting_allowed:
    await ctx.send("Nie trwa teraz żadne głosowanie")
    return
  voing_summary = globals.current_game.summarize_votes()
  summary_readable = ""
  votes_count = 0
  if end_vote:
    globals.current_game.voting_allowed = False
    title = "**Głosowanie zakończone!**\n"
  else:
    title = "Podgląd głosowania\n"
  
  for option, voters in voing_summary.items():
    voters_readable = [get_nickname(voter_id) for voter_id in voters]
    summary_readable += "**{}** na **{}**:\n {}\n\n".format(len(voters_readable), option, ", ".join(voters_readable))
    votes_count += len(voters_readable)
  
  message = "**Wyniki**:\n\n{}".format(summary_readable)
  embed = discord.Embed(title=title, colour=discord.Colour(0x00ccff), description=message)

  if end_vote:
    await get_town_channel().send(embed=embed)
<<<<<<< HEAD
    for member in get_player_role().members:
      async for m in member.history(limit=1):
        try:
          await m.edit(embed=embed)
        except Exception:
          pass
=======
>>>>>>> 5c45f659f3f7e49bab875dba8fb0e2d934e59d72
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
      message += "**Wszyscy grający oddali głosy**"
    else:
      message += "**Nie zagłosowali tylko:**\n"
      for player in not_voted:
        message += get_nickname(player.id) + "\n"
    embed.description = message
    await send_to_manitou(embed=embed)
  await ctx.message.add_reaction('✅')
