#!/usr/bin/env python3

import asyncio
import logging
import os
import discord
from discord.ext import commands

from manitobot import start_commands, manitou_commands, funny_commands, \
    management_commands, dev_commands, player_commands
from manitobot.bot_basics import bot
from manitobot.interactions import Select, SelectOption
from manitobot.errors import MyBaseException
# from manitobot.keep_alive import keep_alive
from settings import PRZEGRALEM_ROLE_ID, LOG_FILE, RULLER
from manitobot.starting import if_game
from manitobot.utility import get_member, get_guild, get_nickname, playerhelp, manitouhelp, send_to_manitou


@bot.event
async def on_ready():
    print("Hello world!")


async def send_voting_select():
    embed = discord.Embed(title='Głosowanie: Przeszukania', colour=discord.Colour(0x00aaff),
                          description='Masz 2 głosy na osoby, które mają **zostać przeszukane**')
    options = [SelectOption('Trybul', 'Trybul'), SelectOption('Tomek', 'Tomek'), SelectOption('Anioła', 'Anioła'),
               SelectOption('Kuba', 'Kuba'), SelectOption('KF', 'KF')]
    components = [[Select('voting', options, min_values=2, max_values=2)]]
    await bot.get_channel(814479709463117835).send_with_components(embed=embed, components=components)


@bot.component_callback('voting')
async def selector(ctx):
    await ctx.respond('Zarejestrowałem twój(-oje) głos(y) na: {}'.format(', '.join(ctx.values)), ephemeral=True)


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
    if m.type != discord.MessageType.default or m.author == bot.user or m.content.strip().startswith('&'):
        return

    if m.channel.type != discord.ChannelType.private:
        return

    if not if_game() or not bot.game.day or not hasattr(bot.game.day.state, 'register_vote'):
        await m.channel.send('Nie rozumiem. Nie trwa teraz żadne głosowanie')
        return

    try:
        await bot.game.day.state.register_vote(get_member(m.author.id), m.content)
    except MyBaseException as e:
        await m.channel.send(e.msg)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    if not isinstance(ctx.author, discord.Member):
        ctx.author = get_member(ctx.author.id)
    await bot.invoke(ctx)


@bot.event
async def on_command_interaction(interaction):
    try:
        try:
            interaction.command = bot.app_commands[interaction.command_id]
        except (KeyError, AttributeError):
            raise commands.CommandNotFound(interaction.name)
    except Exception as error:
        bot.dispatch('interaction_error', interaction, error)
    else:
        await bot.invoke_app_command(interaction)


@bot.event
async def on_component_interaction(interaction):
    if not hasattr(bot, 'component_callbacks'):
        bot.component_callbacks = dict()
    callback = bot.component_callbacks.get(interaction.custom_id)
    try:
        if not callback:
            raise commands.CommandNotFound(interaction.custom_id)
        await callback.callback(interaction)
    except Exception as exc:
        interaction.dispatch('interaction_error', interaction, exc)


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE, format=f'{RULLER}\n\n%(asctime)s - %(levelname)s:\n%(message)s',
                        level=logging.WARNING)
    from dotenv import load_dotenv
    load_dotenv()
    token = os.environ.get('TOKEN')
    #keep_alive()

    try:
        bot.add_cog(dev_commands.DevCommands(bot))
        bot.add_cog(funny_commands.Funny(bot))
        bot.add_cog(manitou_commands.DlaManitou(bot))
        bot.add_cog(start_commands.Starting(bot))
        bot.add_cog(player_commands.DlaGraczy(bot))
        bot.add_cog(management_commands.Management(bot))
        bot.load_extension('manitobot.error_handler')
        bot.load_extension('manitobot.day_app_commands')
        bot.get_command('g').help = playerhelp()
        bot.get_command('m').help = manitouhelp()
    except AttributeError:
        pass
    bot.loop.create_task(bot.overwrite_app_commands())
    bot.run(token)
