#!/usr/bin/env python3
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from manitobot import start_commands, manitou_commands, funny_commands, \
    management_commands, dev_commands, player_commands, marketing_commands, election_commands, daily_commands
from manitobot.bot_basics import bot
from manitobot.errors import MyBaseException, VotingNotAllowed
from manitobot.interactions import CustomIdNotFound, MismatchedComponentCallbackType
from manitobot.utility import get_member, get_guild, get_nickname, playerhelp, manitouhelp
from settings import LOSER_ROLE_ID, LOG_FILE, RULLER, FULL_LOG_FILE, PROD, WEB_HOSTED, LOCAL

log_command: logging.Logger
log_interaction_command: logging.Logger
log_components: logging.Logger


@bot.event
async def on_ready():
    print("Hello world!")


@bot.command(name='przeproś')
async def be_sory(ctx):
    """Przepraszam"""
    await ctx.send("Przepraszam")


@bot.command(name='przegrywam', enabled=False, hidden=True)
async def lose(ctx):
    """Dodaje usera do zbioru przegrywów."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.add_roles(
        discord.utils.get(guild.roles, id=LOSER_ROLE_ID))
    await ctx.send("Zostałeś przegranym {}".format(get_nickname(ctx.author.id))
                   )


@bot.command(name='wygrywam', enabled=False, hidden=True)
async def not_lose(ctx):
    """Usuwa usera ze zbioru przegrywów."""
    guild = get_guild()
    member = get_member(ctx.author.id)
    await member.remove_roles(
        discord.utils.get(guild.roles, id=LOSER_ROLE_ID))
    await ctx.send("Już nie jesteś przegranym {}".format(
        get_nickname(ctx.author.id)))


@bot.command(name='przegrałem')
@commands.cooldown(rate=1, per=30 * 60)
async def you_lost(ctx):
    """Przegrałem."""
    await ctx.send("Przegrałem!")


@bot.component_callback('add_vote', component_type=discord.ComponentType.select)
async def get_vote(interaction: discord.Interaction, _, values):
    try:
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True, thinking=True)
        if interaction.message.id != bot.game.day.state.vote_msg.id:
            raise VotingNotAllowed
        content = await bot.game.day.state.register_vote(
            interaction.user, values)
    except AttributeError:
        raise VotingNotAllowed from None
    else:
        await interaction.edit_original_response(content=content)


@bot.listen('on_message')
async def my_message(m):
    if m.type != discord.MessageType.default or m.author == bot.user or m.content.strip(
    ).startswith('&'):
        return
    if m.channel.type != discord.ChannelType.private:
        return
    try:
        votes = bot.game.day.state.parse_vote(m.content)
        content = await bot.game.day.state.register_vote(
            get_member(m.author.id), votes)
    except MyBaseException as e:
        await m.channel.send(e.msg)
    except AttributeError:
        await m.channel.send('Użyj `&help`, aby wyświetlić dostępne polecenia')
    else:
        await m.author.send(content)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    if not isinstance(ctx.author, discord.Member):
        ctx.author = get_member(ctx.author.id)
    await bot.invoke(ctx)


@bot.event
async def on_command(ctx):
    if ctx.command.name != 'full_log':
        log_command.info(
            '{0.author} (<@!{0.author.id}>) used {0.command.name} by {0.message.content!r}'
            .format(ctx))

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if (interaction.type != discord.InteractionType.component
            and isinstance(interaction.command, app_commands.ContextMenu)):
        log_interaction_command.info(
            '{0.user} (<@!{0.user.id}>) used {0.command.name}'
            .format(interaction))


@bot.event
async def on_component_interaction(interaction: discord.Interaction):
    if not hasattr(bot, 'component_callbacks'):
        bot.component_callbacks = dict()
    inner_data = interaction.data
    custom_id = inner_data.get('custom_id')
    component_type = discord.ComponentType(inner_data.get('component_type'))
    callback = bot.component_callbacks.get(custom_id)
    try:
        if not callback:
            raise CustomIdNotFound(custom_id)
        if callback.component_type != component_type:
            raise MismatchedComponentCallbackType(callback.component_type, component_type)
        if component_type == discord.ComponentType.button:
            await callback.callback(interaction, custom_id)
        elif component_type == discord.ComponentType.select:
            values = inner_data.get('values', list())
            await callback.callback(interaction, custom_id, values)
    except Exception as exc:
        bot.dispatch('interaction_error', interaction, exc)
    finally:
        log_components.info(
            '{0.user} (<@!{0.user.id}>) used {1} in {0.message.content!r} ({0.message.channel.id}/{0.message.id})'
            .format(interaction, custom_id))


async def startup():
    logging.basicConfig(
        filename=FULL_LOG_FILE,
        format='%(asctime)s - %(name)s:%(levelname)s:%(message)s',
        level=logging.INFO, 
        encoding='utf8')
    handler = logging.FileHandler(filename=LOG_FILE, encoding='utf8')
    formatter = logging.Formatter(
        fmt=f'\n{RULLER}\n\n%(asctime)s - %(levelname)s:\n%(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    global log_command, log_interaction_command, log_components
    log_command = logging.getLogger('command')
    log_interaction_command = logging.getLogger('interaction_command')
    log_components = logging.getLogger('components')

    discord.utils.setup_logging(handler=handler, formatter=formatter)

    if LOCAL:
        from dotenv import load_dotenv
        load_dotenv()
    elif WEB_HOSTED:
        from manitobot.keep_alive import keep_alive
        keep_alive()

    if PROD:
        token = os.environ.get('TOKEN')
    else:
        token = os.environ.get('TEST_TOKEN')

    await bot.add_cog(dev_commands.DevCommands(bot))
    await bot.add_cog(funny_commands.Funny(bot))
    await bot.add_cog(manitou_commands.DlaManitou(bot))
    await bot.add_cog(start_commands.Starting(bot))
    await bot.add_cog(player_commands.PlayerCommands(bot))
    await bot.add_cog(management_commands.Management(bot))
    await bot.add_cog(marketing_commands.Marketing(bot))
    await bot.add_cog(election_commands.Election(bot))
    await bot.add_cog(daily_commands.DailyCommands(bot))
    await bot.load_extension('manitobot.error_handler')
    bot.get_command('g').help = playerhelp()
    bot.get_command('m').help = manitouhelp()

    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(startup())
