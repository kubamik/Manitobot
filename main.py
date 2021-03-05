import logging
import os


import discord
from discord.ext import commands

import dev_commands
import funny_commands
import management_commands
import manitou_commands
import player_commands
import start_commands
from bot_basics import bot
from errors import MyBaseException
from keep_alive import keep_alive
from settings import PRZEGRALEM_ROLE_ID, LOG_FILE, RULLER
from starting import if_game
from utility import get_member, get_guild, get_nickname, playerhelp, manitouhelp, send_to_manitou, get_town_channel


@bot.event
async def on_ready():
    print("Hello world!")
    try:
        bot.add_cog(dev_commands.DevCommands(bot))
        bot.add_cog(funny_commands.Funny(bot))
        bot.add_cog(manitou_commands.DlaManitou(bot))
        bot.add_cog(start_commands.Starting(bot))
        bot.add_cog(player_commands.DlaGraczy(bot))
        bot.add_cog(management_commands.Management(bot))
        bot.load_extension('error_handler')
        bot.get_command('g').help = playerhelp()
        bot.get_command('m').help = manitouhelp()
    except (discord.ClientException, AttributeError, commands.ExtensionError):
        pass


@bot.command(name='przeproś')
async def be_sory(ctx):
    """Przepraszam"""
    await ctx.send("Przepraszam")


@bot.command(name='przegrywam')
async def lose(ctx):
    """Dodaje usera do zbioru przegrywów."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.add_roles(
        discord.utils.get(guild.roles, id=PRZEGRALEM_ROLE_ID))
    await ctx.send("Zostałeś przegranym {}".format(
        get_nickname(ctx.author.id)))


@bot.command(name='wygrywam')
async def not_lose(ctx):
    """Usuwa usera ze zbioru przegrywów."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.remove_roles(
        discord.utils.get(guild.roles, id=PRZEGRALEM_ROLE_ID))
    await ctx.send("Już nie jesteś przegranym {}".format(
        get_nickname(ctx.author.id)))


@bot.command(name='przegrałem')
@commands.cooldown(rate=1, per=30 * 60)
async def you_lost(ctx):
    """Przypomina przegrywom o grze."""
    loser = get_guild().get_role(PRZEGRALEM_ROLE_ID)
    await get_member(ctx.author.id).add_roles(loser)
    await ctx.send("Przegrałem!")
    for i in loser.members:
        try:
            await i.send("Przegrałem!")
        except (AttributeError, discord.DiscordException):
            pass


@bot.listen('on_message')
async def my_message(m):
    try:
        if m.type != discord.MessageType.default or m.author == bot.user or m.content.strip()[0] == '&':
            return
    except IndexError:
        pass

    if m.channel.type != discord.ChannelType.private:
        return

    if not if_game() or not bot.game.voting_in_progress:
        await m.channel.send('Nie rozumiem. Nie trwa teraz żadne głosowanie')
        return

    votes = [vote.strip() for vote in m.content.split(',')]
    try:
        res, control = bot.game.voting.register_vote(get_member(m.author.id), votes)
    except MyBaseException as e:
        await m.channel.send(e.msg)
    else:
        await m.channel.send('Zarejestrowałem twój głos(-y) na {}'.format(', '.join(res)))
        if control:
            await send_to_manitou('Wszyscy grający oddali głosy')


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    ctx.author = get_member(ctx.author.id)
    await bot.invoke(ctx)


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE, format=f'{RULLER}\n\n%(asctime)s - %(levelname)s:\n%(message)s',
                        level=logging.WARNING)
    token = os.environ.get('TOKEN')
    keep_alive()
    bot.run(token)
