#!/usr/bin/env python3

import logging
import os
import discord
from discord.ext import commands

from manitobot import start_commands, manitou_commands, funny_commands, \
    management_commands, dev_commands, player_commands, marketing_commands
from manitobot.bot_basics import bot
from manitobot.errors import MyBaseException, VotingNotAllowed
from manitobot.interactions.interaction import ComponentInteraction
from settings import PRZEGRALEM_ROLE_ID, LOG_FILE, RULLER, FULL_LOG_FILE, PROD
from manitobot.utility import get_member, get_guild, get_nickname, playerhelp, manitouhelp


@bot.event
async def on_ready():
    print("Hello world!")


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
    await ctx.send("Zostałeś przegranym {}".format(get_nickname(ctx.author.id))
                   )


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


@bot.component_callback('add_vote')
async def get_vote(ctx: ComponentInteraction):
    try:
        await ctx.ack(ephemeral=True)
        if ctx.message.id != bot.game.day.state.vote_msg.id:
            raise VotingNotAllowed
        content = await bot.game.day.state.register_vote(
            ctx.author, ctx.values)
    except AttributeError:
        raise VotingNotAllowed from None
    else:
        await ctx.send(content, ephemeral=True)


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
        await m.channel.send('Nie rozumiem. Nie trwa teraz żadne głosowanie')
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
        log_app_command.info(
            '{0.author} (<@!{0.author.id}>) used {0.name} with {0.kwargs}/{0.target}'
            .format(interaction))


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
    finally:
        log_interaction.info(
            '{0.author} (<@!{0.author.id}>) used {0.custom_id} in {0.message.content!r}'
            .format(interaction))


if __name__ == '__main__':
    logging.basicConfig(
        filename=FULL_LOG_FILE,
        format='%(asctime)s - %(name)s:%(levelname)s:%(message)s',
        level=logging.INFO)
    handler = logging.FileHandler(filename=LOG_FILE)
    formatter = logging.Formatter(
        fmt=f'{RULLER}\n\n%(asctime)s - %(levelname)s:\n%(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    log_command = logging.getLogger('command')
    log_app_command = logging.getLogger('app_command')
    log_interaction = logging.getLogger('interaction')

    if PROD is None:
        from dotenv import load_dotenv
        load_dotenv()

    token = os.environ.get('TOKEN')

    if PROD is False:
        from manitobot.keep_alive import keep_alive
        keep_alive()

    try:
        bot.add_cog(dev_commands.DevCommands(bot))
        bot.add_cog(funny_commands.Funny(bot))
        bot.add_cog(manitou_commands.DlaManitou(bot))
        bot.add_cog(start_commands.Starting(bot))
        bot.add_cog(player_commands.DlaGraczy(bot))
        bot.add_cog(management_commands.Management(bot))
        bot.add_cog(marketing_commands.Marketing(bot))
        bot.load_extension('manitobot.error_handler')
        bot.load_extension('manitobot.day_app_commands')
        bot.get_command('g').help = playerhelp()
        bot.get_command('m').help = manitouhelp()
    except AttributeError:
        pass

    bot.loop.create_task(bot.overwrite_app_commands())
    bot.run(token)
