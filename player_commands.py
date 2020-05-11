from discord.ext import commands

from utility import *
from settings import *
from starting import if_game
import globals
import postacie
import permissions


class DlaGraczy(commands.Cog, name = "Dla Graczy"):
  def __init__(self, bot):
        self.bot = bot

  '''@commands.command(name='stop')
  async def stop(self, ctx):
    """Prosi manitou i graczy o przerwanie gry"""
    gracz = get_guild().get_member(ctx.author.id)
    if gracz not in get_player_role().members or gracz in get_dead_role().members:
      await ctx.send("Tylko gracze mogą poprosić o przerwę")
      return
    nickname = get_nickname(ctx.author.id)
    message = "Gracz {} prosi o zatrzymanie gry.".format(nickname)
    for channel in get_guild().text_channels:
      if channel.category_id==FRAKCJE_CATEGORY_ID:
        await channel.send(message)
    await send_to_manitou(message)'''
  
  @commands.command(name='postacie',aliases=['lista'])
  async def lista(self, ctx):
    """Pokazuje listę dostępnych postaci, które bot obsługuje"""
    mess = "__Lista dostępnych postaci:__\n:warning:Większość funkcji przedstawionych postaci nie była testowana, więc mogą być bardzo niestabilne:warning:\n"
    mess += ", ".join(permissions.role_activities)
    await ctx.send(mess)


  '''@commands.command(name="ginę")
  async def kill_yourself(self, ctx):
    """Służy do popełnienia radykalnego bukkake."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if czy_trup(ctx):
      await ctx.send("Już jesteś martwy {}".format(member.name if member.nick==None else member.nick))
      return
    if not if_game() or not czy_gram(ctx):
      await ctx.send("Musisz grać, abyś mógł zginąć")
      return
    await globals.current_game.player_map[member].role_class.die()
    await ctx.message.add_reaction('✅')'''

  @commands.command(name='postać')
  async def role_help(self, ctx,*role):
    """Zwraca informacje o postaci podanej jako argument"""
    await postacie.role_details(ctx, role)

  '''@commands.command(name='gram')
  async def register(self, ctx):
    """Służy do zarejestrowania się do gry."""
    #global globals.current_game
    guild = get_guild()
    member = get_member(ctx.author.id)
    if not globals.current_game==None:
      await ctx.send("Gra została rozpoczęta, nie możesz grać")
      return
    if czy_gram(ctx):
      await ctx.send("Już jesteś zarejestrowany {}".format(get_nickname(ctx.author.id)))
      return
    await clear_nickname(member,ctx)
    await member.remove_roles(get_spectator_role())
    await member.remove_roles(get_dead_role())
    await member.add_roles(get_player_role())
    await ctx.send("Zostałeś zarejestrowany {}".format(get_nickname(ctx.author.id)))


  @commands.command(name='nie_gram')
  async def deregister(self, ctx):
    """Służy do wyrejestrowania się z gry."""
    #global globals.current_game
    guild = get_guild()
    member = get_member(ctx.author.id)
    if not globals.current_game==None:
      await ctx.send("Gra została rozpoczęta, nie możesz nie grać")
      return
    if not czy_gram(ctx) and not czy_trup(ctx):
      await ctx.send("Już jesteś wyrejestrowany {}".format(get_nickname(ctx.author.id)))
      return
    await member.remove_roles(get_player_role())
    await member.remove_roles(get_dead_role())
    await ctx.send("Zostałeś wyrejestrowany {}".format(get_nickname(ctx.author.id)))'''


  @commands.command(name='czy_gram')
  async def if_registered(command, ctx):
    """Sprawdza czy user ma rolę gram."""
    if czy_gram(ctx):
      await ctx.send("TAK")
    else:
      await ctx.send("NIE")

  @commands.command(name='obserwuję',aliases=['obs'])
  async def spectate(self, ctx):
    """/&obs/Zmienia rolę usera na spectator."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    if not globals.current_game==None and member in get_player_role().members + get_dead_role().members:
      await ctx.send("Gra została rozpoczęta, nie możesz nie grać")
      return
    await member.remove_roles(get_player_role())
    await member.remove_roles(get_dead_role())
    await member.add_roles(get_spectator_role())
    nickname = get_nickname(ctx.author.id)
    await ctx.send("Zostałeś obserwatorem {}".format(get_nickname(ctx.author.id)))
    if nickname[0] != '!':
      try:
        await get_member(member.id).edit(nick="!" + nickname)
      except discord.errors.Forbidden:
        await ctx.send("Nie mam uprawnień aby zmienić nick")

  @commands.command(name='nie_obserwuję')
  async def not_spectate(self, ctx):
    """/&nie_obs/Usuwa userowi rolę spectator."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.remove_roles(get_spectator_role())
    await ctx.send("Nie zostałeś obserwatorem {}".format(get_nickname(ctx.author.id)))

  @commands.command(name='bunt',aliases=['riot'])
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
    for person in get_player_role().members+get_dead_role().members:
      if person.status != discord.Status.offline:
        count.add(person)
      else:
        if person in globals.current_game.rioters:
          del globals.current_game.rioters[globals.current_game.rioters.index(person)]
    if len(globals.current_game.rioters) == 1:
      await get_town_channel().send("Ktoś rozpoczął bunt. Użyj `&riot` jeśli chcesz dołączyć")
      await send_to_manitou("Ktoś rozpoczął bunt.")
    if len(globals.current_game.rioters) >= len(count) * 0.67:
      for manitou in get_manitou_role().members:
        await manitou.remove_roles(get_manitou_role())
        c=""
      for member in globals.current_game.player_map.values():
        c += "Rola {} to {}\n".format(get_nickname(member.member.id),member.role)
      globals.current_game = None
      player_role = get_player_role()
      dead_role = get_dead_role()
      for member in dead_role.members + player_role.members:
        await member.remove_roles(dead_role)
        await member.add_roles(player_role)
        nickname = get_nickname(member.id)
        await clear_nickname(member,ctx)
      await get_town_channel().send("Doszło do buntu gra została zakończona\n{}".format(c))
    await ctx.send("Zarejestrowałem cię jako buntownika")
      

  @commands.command(name="żywi",aliases=['zywi'])
  async def living(self, ctx):
    """/&zywi/Wypisuje listę żywych graczy"""
    team = ""
    alive_roles = []
    for role in globals.current_game.roles:
      if globals.current_game.role_map[role].player.member in get_player_role().members or (globals.current_game.role_map[role].player.member in get_dead_role().members and not globals.current_game.role_map[role].revealed):
        alive_roles.append(role)
    team = postacie.print_list(alive_roles)
    await ctx.send("""Liczba żywych graczy: {}
Liczba martwych o nieznanych rolach: {}
Pozostali:{}""".format(len(get_player_role().members),len(alive_roles) - len(get_player_role().members),team))

  
  '''@commands.command(name='reveal')
  async def player_reveal(self, ctx):
    """Dodaje w nicku rolę. Do użycia po śmierci"""
    member = ctx.author
    if globals.current_game is None:
      await ctx.send("Gra nie została rozpoczęta")
      return
    if member not in get_dead_role().members:
      await ctx.send("Tylko martwi mogą się ujawniać")
      return
    if globals.current_game.night:
      await ctx.send("Ujawniać można się tylko w dzień")
      return
    nickname = get_nickname(ctx.author.id)
    globals.current_game.player_map[member].role_class.revealed = True
    if nickname[-1] != ')':
      try:
        await member.edit(nick=nickname + "({})".format(globals.current_game.player_map[member].role.replace('_',' ')))
      except discord.errors.Forbidden:
        await member.create_dm()
        await member.dm_channel.send("Zmień swój nick na {}, bo ja nie mam uprawnień.".format(nickname+"({})".format(globals.current_game.player_map[member].role.replace('_',' '))))
        await ctx.send("Nie mam uprawnień aby zmienić nick")
      await get_town_channel().send("Rola **{}** to **{}**".format(nickname.replace('+',' '),globals.current_game.player_map[member].role.replace('_',' ')))
      await ctx.send("Done!")
    else:
      await ctx.send("Jesteś już ujawniony")'''
      
