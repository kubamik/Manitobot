from utility import *
from discord.ext import commands
import discord

from settings import FRAKCJE_CATEGORY_ID
import globals
from starting import if_game



class Pojedynki(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  async def cog_check(self, ctx):
    try:
      return not globals.current_game.night and (not globals.current_game.days[-1].duel or get_member(ctx.author.id) in get_manitou_role().members)
    except:
      return False

  async def cog_command_error(self, ctx, error):
    if type(error) is commands.CheckFailure:
      await ctx.send("Tej komendy można używać tylko w dzień i (prawdopodobnie) nie w trakcie pojedynku", delete_after=5)


  @commands.command(name='wyzywam')
  async def duel_dare(self,ctx,*, gracz):
    '''Wyzywa podaną osobę na pojedynek'''
    try:
      member = await converter(ctx, gracz)
      author = get_member(ctx.author.id)
      playing(member, author=author)
      if member == author:
        await ctx.send("Celujesz sam w siebie, ale przypominasz sobie, że Twój pies będzie smutny")
        return
      globals.current_game.days[-1].add_dare(author, member)
      await globals.current_game.days[-1].if_start(author, member)
      await ctx.message.add_reaction('✅')
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='odrzucam', aliases=['od', 'spierdalaj'])
  async def decline(self,ctx):
    '''/&od/Służy do odrzucenia pojedynku'''
    try:
      author = get_member(ctx.author.id)
      playing(author=author)
      mess = globals.current_game.days[-1].remove_dare(author)
      await get_town_channel().send(mess)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next()
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='przyjmuję', aliases=['pr'])
  async def accept(self,ctx):
    '''/&pr/Służy do przyjęcia pojedynku'''
    author = get_member(ctx.author.id)
    try:
      c = globals.current_game.days[-1].accept(author)
      await get_town_channel().send(c)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next(True)
    except InvalidRequest as err:
      await ctx.send(err.reason)

  
  @commands.command(name='break', aliases=['br'])
  @manitou_cmd
  async def interrupt(self,ctx):
    '''Ⓜ/&br/Przerywa trwający pojedynek'''
    try:
      c = await globals.current_game.days[-1].interrupt()
      await get_town_channel().send(c)
      await ctx.message.add_reaction('✅')
      await globals.current_game.days[-1].if_next()
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='wyzwania', aliases=['pend'])
  @manitou_cmd
  async def challenges(self, ctx):
    '''Ⓜ/&pend/Pokazuje aktualne wyzwania'''
    c = globals.current_game.days[-1].dares_print()
    await ctx.send(c)


  @commands.command(name='duelend', aliases=['dnd'])
  @manitou_cmd
  async def duel_end(self, ctx):
    '''Ⓜ/&dnd/Kończy pojedynek z wynikiem ogłoszonym automatycznie'''
    try:
      await globals.current_game.days[-1].end_duel(ctx)
    except InvalidRequest as err:
      await ctx.send(err.reason)


  @commands.command(name='search_phase', aliases=['abend'])
  @manitou_cmd
  async def no_duels(self, ctx):
    '''Ⓜ/&abend/Kończy turę pojedynków'''
    globals.current_game.days[-1].duels_today = globals.current_game.duels
    await ctx.message.add_reaction('✅')
    await get_town_channel().send("__Zakończono turę pojedynków__")


  """@commands.command(name='wyzywam')
  async def duel_dare(self,ctx,*, gracz):
    '''Wyzywa podaną osobę na pojedynek'''
    
    try:
      gracz = await discord.ext.commands.MemberConverter().convert(ctx, gracz)
    except commands.BadArgument:
      gracz = nickname_fit(gracz)
    member = get_member(ctx.author.id)
    if member not in get_player_role().members:
      await ctx.send("Nie grasz teraz")
      return
    if globals.current_game.night:
      await ctx.send("Nie można wyzywać w nocy")
      return
    if globals.current_game.days[-1].duel:
      await ctx.send("Nie można zgłaszać pojedynków w czasie pojedynku")
      return
    if globals.current_game.days[-1].duels_today == globals.current_game.duels:
      await ctx.send("Nie ma już więcej pojedynków tego dnia")
      return
    if gracz is None or gracz not in get_guild().members:
      await ctx.send("Nie ma takiego gracza")
      return
    if gracz in get_dead_role().members:
      await ctx.send("Ten gracz nie żyje")
      return
    if not if_game() or gracz not in get_player_role().members:
      await ctx.send("Ta osoba nie gra")
      return
    if member == gracz:
      await ctx.send("Celujesz sam w siebie, ale przypominasz sobie, że Twój pies będzie smutny")
      return
    if gracz not in globals.current_game.days[-1].dared:
      globals.current_game.days[-1].dared[gracz] = []
    if member not in globals.current_game.days[-1].daring:
      globals.current_game.days[-1].daring[member] = []
    if member not in globals.current_game.days[-1].dared:
      globals.current_game.days[-1].dared[member] = []
    if member in globals.current_game.days[-1].dared[gracz] or gracz in globals.current_game.days[-1].dared[member]:
      await ctx.send("Wyzwałeś już tego gracza lub on wyzwał ciebie")
      return
    globals.current_game.days[-1].dared[gracz].append(member)
    globals.current_game.days[-1].daring[member].append(gracz)
    globals.current_game.days[-1].duels_order.append(gracz)
    print("daring\n",globals.current_game.days[-1].daring.items())
    print("dared\n",globals.current_game.days[-1].dared.items())
    try:
      if globals.current_game.role_map["Szeryf"].alive():
        await get_town_channel().send("**{}** wyzwał **{}** na pojedynek.\n<@{}> czy przyjmujesz? Użyj `&przyjmuję` lub `&odrzucam`".format(get_nickname(member.id), get_nickname(gracz.id), gracz.id))
        return
      else:
        await get_town_channel().send("**{}** wyzwał **{}** na pojedynek.\nSzeryf nie żyje, więc pojedynek rozpoczyna się automatycznie".format(get_nickname(member.id), get_nickname(gracz.id)))
    except:
      await get_town_channel().send("**{}** wyzwał **{}** na pojedynek.\nSzeryf nie gra, więc pojedynek rozpoczyna się automatycznie".format(get_nickname(member.id), get_nickname(gracz.id)))
    t = member
    member = gracz
    gracz = t
    del globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]][globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]].index(member)]
    del globals.current_game.days[-1].dared[member][0]
    del globals.current_game.days[-1].duels_order[globals.current_game.days[-1].duels_order.index(member)]
    await globals.current_game.days[-1].start_duel(gracz, member)
  

  @commands.command(name='odrzucam', aliases=['od'])
  async def decline(self,ctx):
    '''/&od/Służy do odrzucenia pojedynku'''
    member = get_member(ctx.author.id)
    if globals.current_game.night:
      await ctx.send("Nie można wyzywać w nocy")
      return
    if globals.current_game.days[-1].duel:
      await ctx.send("Nie można odrzucać pojedynków w czasie pojedynku")
      return
    if member not in  globals.current_game.days[-1].duels_order:
      await ctx.send("Nie zostałeś wyzwany")
      return
    if member in globals.current_game.days[-1].duels_queue:
      await ctx.send("Masz już oczekujący pojedynek")
      return
    gracz = globals.current_game.days[-1].dared[member][0]
    del globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]][globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]].index(member)]
    del globals.current_game.days[-1].dared[member][0]
    del globals.current_game.days[-1].duels_order[globals.current_game.days[-1].duels_order.index(member)]
    await get_town_channel().send("**{}** odrzucił pojedynek od **{}**".format(get_nickname(member.id), get_nickname(gracz.id)))
    if len(globals.current_game.days[-1].duels_queue) > 0 and globals.current_game.days[-1].duels_order[0] ==  globals.current_game.days[-1].duels_queue[0]:
      member = globals.current_game.days[-1].duels_queue[0]
      gracz = globals.current_game.days[-1].dared[member][0]
      del globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]][globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]].index(member)]
      del globals.current_game.days[-1].dared[member][0]
      del globals.current_game.days[-1].duels_order[globals.current_game.days[-1].duels_order.index(member)]
      await globals.current_game.days[-1].start_duel(gracz, member)


  @commands.command(name='przyjmuję', aliases=['pr'])
  async def accept(self,ctx):
    '''/&pr/Służy do przyjęcia pojedynku'''
    member = get_member(ctx.author.id)
    if globals.current_game.night:
      await ctx.send("Nie można wyzywać w nocy")
      return
    if globals.current_game.days[-1].duel:
      await ctx.send("Nie można przyjmować pojedynków w czasie pojedynku")
      return
    if member not in  globals.current_game.days[-1].duels_order:
      await ctx.send("Nie zostałeś wyzwany")
      return
    if member in globals.current_game.days[-1].duels_queue:
      await ctx.send("Masz już oczekujący pojedynek")
      return
    gracz = globals.current_game.days[-1].dared[member][0]
    await get_town_channel().send("{} przyjął pojedynek od {}".format(get_nickname(member.id), get_nickname(gracz.id)))
    if globals.current_game.days[-1].duels_order[0] != member:
      globals.current_game.days[-1].duels_queue.append(member)
      c = {}
      for key in globals.current_game.days[-1].dared.keys():
        c[key] = globals.current_game.days[-1].dared[key].copy()
      mess = "**Zanim rozpocznie się ten pojedynek muszą zostać rozpatrzone wyzwania:**\n"
      q = globals.current_game.days[-1].duels_queue.copy()
      for player in globals.current_game.days[-1].duels_order:
        if player == member:
          break
        mess += "**{}** vs. **{}**".format(get_nickname(c[player][0].id),get_nickname(player.id))
        if player == q[0]:
          mess += " - *przyjęte*"
          del q[0]
        mess += "\n"
        del c[player][0]
      await ctx.send(mess)
    else:
      del globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]][globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]].index(member)]
      del globals.current_game.days[-1].dared[member][0]
      del globals.current_game.days[-1].duels_order[globals.current_game.days[-1].duels_order.index(member)]
      await globals.current_game.days[-1].start_duel(gracz, member)

  @commands.command(name='przerwij', aliases=['br'])
  @manitou_cmd
  async def interrupt(self,ctx):
    '''Ⓜ/&br/Przerywa trwający pojedynek'''
    if globals.current_game.night or not globals.current_game.days[-1].duel:
      await ctx.send("Nie trwa pojedynek")
      return
    winner_role = get_duel_winner_role()
    loser_role = get_duel_loser_role()
    globals.current_game.days[-1].duel = False
    globals.current_game.days[-1].duelers = ()
    globals.current_game.days[-1].duels_result = False
    globals.current_game.voting_allowed = False
    await get_town_channel().send("Manitou anulował aktualnie trwający pojedynek")
    await get_glosowania_channel().send("Manitou anulował aktualnie trwający pojedynek")
    await globals.current_game.days[-1].agresor.remove_roles(winner_role, loser_role)
    await globals.current_game.days[-1].victim.remove_roles(winner_role, loser_role)
    if len(globals.current_game.days[-1].duels_queue) > 0 and globals.current_game.days[-1].duels_order[0] == globals.current_game.days[-1].duels_queue[0] and globals.current_game.days[-1].duels_today < globals.current_game.duels:
      member = globals.current_game.days[-1].duels_queue[0]
      gracz = globals.current_game.days[-1].dared[member][0]
      del globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]][globals.current_game.days[-1].daring[globals.current_game.days[-1].dared[member][0]].index(member)]
      del globals.current_game.days[-1].dared[member][0]
      del globals.current_game.days[-1].duels_order[globals.current_game.days[-1].duels_order.index(member)]
      del globals.current_game.days[-1].duels_queue[0]
      await globals.current_game.days[-1].start_duel(gracz, member)
    await ctx.message.add_reaction('✅')



  @commands.command(name='wyzwania', aliases=['pend'])
  @manitou_cmd
  async def challenges(self, ctx):
    '''Ⓜ/&pend/Pokazuje aktualne wyzwania'''
    if globals.current_game.night:
      await ctx.send("Nie można wyzywać w nocy")
      return
    c = {}
    for key in globals.current_game.days[-1].dared.keys():
      c[key] = globals.current_game.days[-1].dared[key].copy()
    mess = "**Aktualne wyzwania ({}):**\n".format(len(globals.current_game.days[-1].duels_order))
    q = globals.current_game.days[-1].duels_queue.copy()
    for member in globals.current_game.days[-1].duels_order:
      mess += "**{}** vs. **{}**".format(get_nickname(c[member][0].id),get_nickname(member.id))
      if len(q) > 0 and member == q[0]:
        mess += " - *przyjęte*"
        del q[0]
      mess += "\n"
      del c[member][0]
    mess += "\nPozostało {} pojedynków".format(globals.current_game.duels - globals.current_game.days[-1].duels_today)
    await ctx.send(mess)


  @commands.command(name='duelend', aliases=['dnd'])
  @manitou_cmd
  async def duel_end(self, ctx):
    '''Ⓜ/&dnd/Kończy pojedynek z wynikiem ogłoszonym automatycznie'''
    if globals.current_game.night:
      await ctx.send("Nie trwa pojedynek")
      return
    if not globals.current_game.days[-1].duels_result:
      await ctx.send("Najpierw musisz przeprowadzić głosowanie na zwycięzcę")
      return
    await globals.current_game.days[-1].end_duel(ctx)



  @commands.command(name='wins', aliases=['dwin'])
  @manitou_cmd
  async def winning(self, ctx, *, member):
    '''Ⓜ/&dwin/Zmienia wynik pojedynku argumentem jest pseudonim gracza, który ma wygrać lub 2, gdy nikt ma nie zginąć, 0 - gdy obaj mają zginąć'''
    if globals.current_game.night:
      await ctx.send("Nie trwa pojedynek")
      return
    if member != "0" and member != "2":
      try:
        member = await discord.ext.commands.MemberConverter().convert(ctx, member)
      except commands.BadArgument:
        member = nickname_fit(member)
    globals.current_game.days[-1].change_winner(member)
    if member == "2":
      await get_glosowania_channel().send("Jednak w wyniku pojedynku nikt nie ginie. *(na razie)*")
      await get_town_channel().send("Jednak w wyniku pojedynku nikt nie ginie *(na razie)*")
    elif member == "0":
      await get_glosowania_channel().send("Jednak w wyniku pojedynku mają zginąć obaj pojedynkujący się")
      await get_town_channel().send("Jendak w wyniku pojedynku mają zginąć obaj pojedynkujący się")
    else:
      await get_glosowania_channel().send("Jednak pojedynek ma wygrać **{}**.".format(get_nickname(member.id)))
      await get_town_channel().send("Jednak pojedynek ma wygrać **{}**.".format(get_nickname(member.id)))
    await ctx.message.add_reaction('✅')"""


