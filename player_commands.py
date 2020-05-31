from discord.ext import commands

from utility import *
from settings import *
from starting import if_game
import globals
import postacie
import permissions

ankietawka = '@everyone\n**O której możesz grać {date}?**\nZaznacz __wszystkie__ opcje, które ci odpowiadają.\n\nZaznacz :eye: jeśli __zobaczyłæś__ (nawet, jeśli nic innego nie zaznaczasz).\n\n:strawberry: 17.00     :basketball: 18.00     :baby_chick: 19.00     :cactus: 20.00     :whale: 21.00     :grapes: 22.00     :pig: 23.00     :no_entry_sign: Nie mogę grać tego dnia'

ankietawka_emoji = ['🍓', '🏀', '🐤', '🌵', '🐳', '🍇', '🐷', '🚫', '👁️']


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

  @commands.command(name='adminuj')
  async def adminate(self, ctx, member):
    '''Mianuje nowego admina'''
    author = get_member(ctx.author.id)
    member = await converter(ctx, member)
    if author not in get_admin_role().members:
      raise commands.MissingRole(get_admin_role())
    if member is None:
      await ctx.message.delete(delay=5)
      await ctx.send("Nie ma takiej osoby", delete_after=5)
      return
    await member.add_roles(get_admin_role())
    await ctx.message.add_reaction('✅')

  @commands.command(name='nie_adminuj', hidden=True)
  @commands.is_owner()
  async def not_adminate(self, ctx, member):
    '''Usuwa admina'''
    member = await converter(ctx, member)
    if member is None:
      await ctx.send("Nie ma takiej osoby")
      return
    await member.remove_roles(get_admin_role())


  @commands.command()
  async def ankietka(self, ctx, *, date):
    '''Wysyła na kanał ankietawka ankietę do gry w dzień podany w argumencie. Uwaga dzień należy podać w formacie <w/we> <dzień-tygodnia> <data>. Oznaczenia we własnym zakresie'''
    author = get_member(ctx.author.id)
    if author not in get_admin_role().members:
      raise commands.MissingRole(get_admin_role())
    async with ctx.typing():
      m = await get_ankietawka_channel().send(ankietawka.format(date=date))
      for emoji in ankietawka_emoji:
        await m.add_reaction(emoji)
    await ctx.message.add_reaction('✅')

  @commands.command(name='help_gracza', aliases=[])
  async def playerhelp(self, ctx):
    '''Pokazuje skrótową pomoc dla graczy'''
    comm = ['postać', 'żywi', 'riot', 'pax', 'wyzywam', 'odrzucam', 'przyjmuję', 'zgłaszam', 'cofam']
    mess = ""
    for c in comm:
      mess += help_format(c)
    await ctx.send(f'```yaml\n{mess}```')


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
    await member.remove_roles(get_player_role(), get_dead_role())
    await member.add_roles(get_spectator_role())
    nickname = member.display_name
    await ctx.message.add_reaction('✅')
    if not nickname.startswith('!'):
      try:
        await get_member(member.id).edit(nick = "!" + nickname)
      except discord.errors.Forbidden:
        await ctx.send("Dodaj sobie '!' przed nickiem")

  @commands.command(name='nie_obserwuję', aliases=['nie_obs'])
  async def not_spectate(self, ctx):
    """/&nie_obs/Usuwa userowi rolę spectator."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.remove_roles(get_spectator_role())
    nickname = member.display_name
    if nickname.startswith('!'):
      try:
        await get_member(member.id).edit(nick=nickname[1:])
      except discord.errors.Forbidden:
        pass
    await ctx.message.add_reaction('✅')

  @commands.command(name='pax')
  async def pax(self, ctx):
    try:
      globals.current_game.rioters.remove(get_member(ctx.author.id))
      await ctx.message.add_reaction('🕊️')
    except KeyError:
      await ctx.send("Nie jesteś buntownikiem")
    

  @commands.command(name='bunt',aliases=['riot'])
  async def riot(self, ctx):
    '''/&riot/W przypadku poparcia przez co najmniej 67 % osób biorących udział w grze (także martwych, ale online) kończy grę'''
    if not czy_gram(ctx) and not czy_trup(ctx):
      await ctx.send("Mogą użyć tylko grający")
      return
    globals.current_game.rioters.add(get_member(ctx.author.id))
    count = set()
    for person in get_player_role().members + get_dead_role().members:
      if person.status != discord.Status.offline:
        count.add(person)
      else:
        if person in globals.current_game.rioters:
          del globals.current_game.rioters[globals.current_game.rioters.index(person)]
    if len(globals.current_game.rioters) == 1:
      await get_town_channel().send("Ktoś rozpoczął bunt. Użyj `&riot` jeśli chcesz dołączyć")
      await send_to_manitou("Ktoś rozpoczął bunt.")
    if len(globals.current_game.rioters) >= len(count) * 0.67:
      await get_town_channel().send("**Doszło do buntu\nGra została zakończona**")
      for manitou in get_manitou_role().members:
        await manitou.remove_roles(get_manitou_role())
      for role in globals.current_game.role_map.values():
        if not role.revealed:
          await role.reveal()
      globals.current_game = None
      manit = bot.cogs['Dla Manitou']
      await manit.remove_cogs()
      await bot.change_presence(activity = None)
      player_role = get_player_role()
      dead_role = get_dead_role()
      winner_role = get_duel_winner_role()
      loser_role = get_duel_loser_role()
      searched_role = get_searched_role()
      hanged_role = get_hanged_role()
      p = discord.Permissions().all()
      try:
        await get_admin_role().edit(permissions = p)
      except (NameError, discord.errors.Forbidden):
        pass
      for member in dead_role.members + player_role.members:
        await member.remove_roles(dead_role, winner_role, loser_role, searched_role, hanged_role)
        await member.add_roles(player_role)
      await manit.remove_cogs()
    await ctx.message.add_reaction("👊")
      

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
      
