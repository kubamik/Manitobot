from discord.ext import commands
import random
import typing

from utility import manitou_cmd, get_nickname, InvalidRequest, get_player_role, get_searched_role
import votings
import globals

class Glosowania(commands.Cog, name="Głosowania"):

  def __init__(self, bot):
    self.bot = bot
  
  def not_night():  
    def predicate(ctx):
      return not globals.current_game.night
    return commands.check(predicate)

  async def cog_command_error(self, ctx, error):
    if type(error) is commands.CheckFailure:
      await ctx.send("Tej komendy można używać tylko w dzień", delete_after=5)
  
  @commands.command(name='vote_cancel', aliases=['vclc'])
  @manitou_cmd
  async def cancel_vote(self, ctx):
    '''Ⓜ/&vclc/Anuluje trwające głosowanie'''
    if not globals.current_game.voting_allowed:
      await ctx.send("Nie trwa głosowanie")
      return
    globals.current_game.voting_allowed = False
    await ctx.message.add_reaction('✅')

  @commands.command(name='vote')
  @manitou_cmd
  async def glosowanie_custom(
      self, ctx, title, 
      count : typing.Optional[int] = 1, *options):
    """ⓂRozpoczyna customowe głosowanie:
    Argumentami są:
      -tytuł głosowania.
      -wymagana liczba głosów.
      -nazwy kandydatów"""
    if not '\n' in title:
      title += '\nWymagana liczba głosów: {}'
    options_parsed = []
    for option in options:
      options_parsed.append(option.split(','))
    await votings.glosowanie(ctx, title, int(count), options_parsed)

  @commands.command(name='duel')
  @manitou_cmd
  async def pojedynek(self, ctx, *kandydaci):
    """ⓂRozpoczyna głosowanie: kto ma wygrać pojedynek?
    Argumentami są nazwy kandydatów."""
    if len(kandydaci)<1:
      await ctx.send("Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(len(kandydaci),1))
      return
    await self.glosowanie_custom(ctx, "Pojedynek\nMasz {} głos na osobę, która ma **wygrać** pojedynek", "1", *kandydaci, "3,Wstrzymuję_Się")

  @commands.command(name='duel_vote', aliases=['vdl'])
  @manitou_cmd
  async def duel_vote(self, ctx):
    """Ⓜ/&vdl/Rozpoczyna głosowanie: kto ma wygrać pojedynek na podstawie automatycznie rozpoczętego pojedynku"""
    if not globals.current_game.days[-1].duel:
      await ctx.send("Nie rozpoczęto pojedynku")
      return
    agresor = globals.current_game.days[-1].participants[0]
    victim = globals.current_game.days[-1].participants[1]
    options_parsed = [["1", get_nickname(agresor.id)], ["2",get_nickname(victim.id)], ["3", "Wstrzymuję_Się"]]
    await votings.glosowanie(ctx, "Pojedynek\nMasz {} głos na osobę, która ma **wygrać** pojedynek", 1, options_parsed, (agresor, victim), "duel")

  @commands.command(name='search')
  @manitou_cmd
  async def przeszukania(self, ctx, *kandydaci):
    """ⓂRozpoczyna głosowanie: kogo przeszukać?
    Argumentami są nazwy kandydatów.
    Wymaganych jest tyle głosów ile wynosi zdefiniowana ilość preszukań (domyślnie 2)."""
    if len(kandydaci)<globals.current_game.searches:
      await ctx.send("Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(len(kandydaci),globals.current_game.searches))
      return
    await self.glosowanie_custom(ctx, "Przeszukania\nMasz {} głosy na osoby, które mają **zostać przeszukane**", globals.current_game.searches, *kandydaci)


  @commands.command(name='search_vote', aliases=['vsch'])
  @manitou_cmd
  @not_night()
  async def search_vote(self, ctx):
    '''Ⓜ/&vsch/Rozpoczyna głosowanie kogo przeszukać na podstawie zgłoszonych kandydatur'''
    globals.current_game.days[-1].to_search = []
    if globals.current_game.days[-1].hang_time:
      await ctx.send("Przeszukania już były")
      return
    try:
      if globals.current_game.nights[-1].herbed.alive():
        await ctx.send("Nie zapomniałeś o czymś:herb:?")
        return
    except AttributeError:
      pass
    for member in get_searched_role().members:
      await member.remove_roles(get_searched_role())
    globals.current_game.days[-1].search = True
    kandydaci = list(globals.current_game.days[-1].searched.keys())
    if len(get_player_role().members) < globals.current_game.searches:
      globals.current_game.searches = len(get_player_role().members)
    while len(kandydaci) < globals.current_game.searches:
      kandydaci.append(random.choice(list(set(get_player_role().members) - set(kandydaci))))
    if len(kandydaci) == globals.current_game.searches:
      await globals.current_game.days[-1].search_end(kandydaci)
      return
    options_parsed = [['{}'.format(number+1),get_nickname(member.id)] for number, member in enumerate(kandydaci)]
    await votings.glosowanie(ctx, "Przeszukania\nMasz {} głosy na osoby, które mają **zostać przeszukane**", globals.current_game.searches, options_parsed, vtype="search")

  @commands.command(name='revote', aliases=['vre'])
  @manitou_cmd
  @not_night()
  async def revote(self, ctx):
    '''Ⓜ/&vre/Uruchamia głosowanie uzupełniające'''
    cand_h_revote = globals.current_game.days[-1].to_hang
    cand_s_revote = globals.current_game.days[-1].to_revote
    if len(cand_h_revote) > 0:
      kandydaci = cand_h_revote
      options_parsed = [['{}'.format(number+1),get_nickname(member.id)] for number, member in enumerate(kandydaci)]
      await votings.glosowanie(ctx, "Wieszanie - uzupełniające\nPrzeszukania\nMasz {} głos na osobę, która ma zginąć", 1, options_parsed, vtype="hang")
    elif len(cand_s_revote) > 0:
      kandydaci = cand_s_revote
      options_parsed = [['{}'.format(number+1),get_nickname(member.id)] for number, member in enumerate(kandydaci)]
      await votings.glosowanie(ctx, "Przeszukania - uzupełniające\nMasz {} głos(y) na osobę(-y), która(-e) ma(ją) **zostać przeszukana(-e)**", globals.current_game.searches - len(globals.current_game.days[-1].to_search), options_parsed, vtype="search")
    else:
      await ctx.send("Nie ma kandydatur na takie głosowanie")

  @commands.command(name='hangif', aliases=['vhif', 'hiv'])
  @manitou_cmd
  @not_night()
  async def czy_wieszamy(self, ctx):
    """Ⓜ/&vhif/Rozpoczyna głosowanie: czy powiesić?"""
    if not globals.current_game.days[-1].hang_time:
      await ctx.send("Najpierw przeszukania. Jeżeli chcesz wymusić głosowanie użyj `&fhangif`")
      return
    await votings.glosowanie(ctx, "Czy wieszamy?\nMasz {} głos na wybraną opcję.", 1, [["t", "Tak"], ["n", "Nie"]], vtype="hangif")

  @commands.command(name='force_hangif', aliases=['fhangif'])
  @manitou_cmd
  async def hanging(self, ctx):
    """Ⓜ/&fhangif/Rozpoczyna głosowanie: czy powiesić?"""
    await votings.glosowanie(ctx, "Czy wieszamy?\nMasz {} głos na wybraną opcję.", 1, [["t", "Tak"], ["n", "Nie"]])

  @commands.command(name='hang')
  @manitou_cmd
  async def kogo_wieszamy(self, ctx, *kandydaci):
    """ⓂRozpoczyna głosowanie: kogo powiesić?
    Argumentami są nazwy kandydatów"""
    if len(kandydaci)<1:
      await ctx.send("Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}".format(len(kandydaci),1))
      return
    await self.glosowanie_custom(ctx, "Wieszanie\nGłosujecie Głosujecie na osobę, która **ma być powieszona**", "1", *kandydaci)

  @commands.command(name='hang_vote',aliases=['vhg'])
  @manitou_cmd
  @not_night()
  async def hang_vote(self,ctx):
    '''Ⓜ/&vhg/Rozpoczyna głosowanie kogo powiesić na podstawie przeszukiwanych osób'''
    if not globals.current_game.days[-1].hang_time or globals.current_game.days[-1].hang is None:
      await ctx.send("Najpierw głosowanie `&hangif`")
      return
    globals.current_game.days[-1].hang = True
    kandydaci = globals.current_game.days[-1].candidates
    if len(kandydaci) == 1:
      await globals.current_game.days[-1].hang_sumarize(ctx, [[kandydaci[0].display_name, []]])
    else:
      options_parsed = [['{}'.format(number+1),get_nickname(member.id)] for number, member in enumerate(kandydaci)]
      await votings.glosowanie(ctx, "Wieszanie\nGłosujecie na osobę, która **ma być powieszona**", 1, options_parsed, vtype="hang")

  @commands.command(name='votend',aliases=['vend'])
  @manitou_cmd
  async def glosowanie_koniec(self, ctx):
    """Ⓜ/&vend/Kończy głosowanie, wypisuje podsumowanie głosów, uruchamia akcje powiązane (przeszukania, pojedynki, wieszanie)"""
    await votings.see_voting(ctx, True)

  @commands.command(name='votesee',aliases=['vs'])
  @manitou_cmd
  async def glosowanie_podgląd(self, ctx):
    """Ⓜ/&vs/Pisze do wszystkich manitou obecne wyniki głosowania"""
    await votings.see_voting(ctx, False)