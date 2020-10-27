import asyncio
from typing import Dict

import discord
from discord.ext import commands

from game import Game
from settings import FAC2EMOJI
from utility import get_control_panel, get_manitou_role


class ControlPanel(commands.Cog, name='Panel Sterowania'):
  """Class which controls Manitou Control Panel"""
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    self.message: discord.message
    self.mess2mem: Dict[discord.Message, discord.Member]
    self.mem2mess: Dict[discord.Member, discord.Message]
    self.game: Game
    self.emoji2fac: Dict[int, str] = {}

  async def prepare_panel(self, game: Game) -> None:
    await get_control_panel().purge()
    self.game = game
    base = get_control_panel().send
    tasks = []
    players = sorted(game.player_map.keys(), key=lambda m: m.display_name)
    for player in players:
      tasks.append(base(player.display_name))
    tasks.append(base("Aktywna frakcja"))
    messages = await asyncio.gather(*tasks)
    self.message = messages[-1]
    self.mess2mem = dict(zip(messages[:-1], players))
    self.mem2mess = dict(zip(players, messages[:-1]))
    tasks = []
    for m in messages[:-1]:
      tasks.append(m.add_reaction('😴'))
    for fac, id in FAC2EMOJI.items():
      if fac in game.faction_map:
        tasks.append(self.message.add_reaction(self.bot.get_emoji(id)))
        self.emoji2fac[id] = fac
    await asyncio.gather(*tasks)

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent) -> None:
    if event.user_id == self.bot.user.id:
      return
    if event.emoji.name == '😴':
      m = discord.utils.get(self.mess2mem.keys(), id=event.message_id)
      if m:
        self.game.player_map[self.mess2mem[m]].sleep()
        await m.edit(content=m.content+'\t😴')
      return
    fac = self.emoji2fac.get(event.emoji.id)
    if fac:
      await self.game.faction_map[fac].wake_up()

  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent) -> None:
    if event.emoji.name == '😴':
      m = discord.utils.get(self.mess2mem.keys(), id=event.message_id)
      if m:
        self.game.player_map[self.mess2mem[m]].unsleep()
        if m.content.endswith('\t😴'):
          await m.edit(content=m.content[:-2])
      return
    fac = self.emoji2fac.get(event.emoji.id)
    if fac:
      await self.game.faction_map[fac].put_to_sleep()

  async def morning_reset(self) -> None:
    tasks = []
    for m in self.mess2mem:
      if m.content.endswith('\t😴'):
        tasks.append(m.edit(content=m.content[:-2]))
        for member in get_manitou_role().members:
          tasks.append(m.remove_reaction('😴', member))
    await asyncio.gather(*tasks)

