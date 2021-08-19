import logging
import sys
import traceback

import discord
from discord.ext import commands

from settings import FRAKCJE_CATEGORY_ID, NIEPUBLICZNE_CATEGORY_ID, RULLER
from .bot_basics import bot
from .errors import GameEnd, MyBaseException, InvalidRequest
from .utility import send_to_manitou, get_guild

ISSUE_TEMPLATE = '''
MESSAGE ID: {0.message.id}
ARGS:       {0.args}
KWARGS:     {0.kwargs}
COMMAND:    {0.command.name}
CHANNEL:    {0.channel}
AUTHOR:     {0.author.display_name}
{1}
'''

INTER_ISSUE_TEMPLATE_2 = '''
KWARGS:     {0.kwargs}
COMMAND:    {0.command.name}
CHANNEL:    {0.channel}
AUTHOR:     {0.author.display_name}
{1}
'''

INTER_ISSUE_TEMPLATE_3 = '''
MESSAGE_ID: {0.message.id}
COMPONENT:  {0.component_type}
CHANNEL:    {0.channel}
AUTHOR:     {0.author.display_name}
VALUES:     {0.values}
{1}
'''

SLIM_TEMPLATE = '''
EVENT NAME: {}
ARGS:       {}
{}
'''


def setup(_):
    """Do nothing while loading extension
    """
    pass


def report_error(ctx, error):
    msg = ISSUE_TEMPLATE.format(ctx, RULLER)
    try:
        raise error
    except Exception:
        logging.exception(msg)
        raise


def report_inter_error(inter, error):
    if inter.type == 2:
        msg = INTER_ISSUE_TEMPLATE_2.format(inter, RULLER)
    else:
        msg = INTER_ISSUE_TEMPLATE_3.format(inter, RULLER)
    try:
        raise error
    except Exception:
        logging.exception(msg)
        raise


async def handle_error(send, error):
    if isinstance(error, (MyBaseException, InvalidRequest)):
        await send(error.msg, delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        await send('HONK?', delete_after=5)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        await send('Chcem coś zrobić, ale nie mogem.', delete_after=5)
    elif isinstance(error, commands.CommandInvokeError) and \
            isinstance(error.original, discord.HTTPException) and error.original.code == 10062:
        await send('Przekroczono dopuszczalny czas na odpowiedź. Spróbuj ponownie')
    elif isinstance(error, (commands.MissingRole, commands.NotOwner)):
        await send('You have no power here!', delete_after=5)
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await send('Brakuje parametru: ' + str(error.param), delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        await send('Nie ma takiej osoby wśród żywych graczy', delete_after=5)
    elif isinstance(error, commands.errors.BadArgument):
        await send(f'Błędny parametr\n||{error}||', delete_after=5)
    elif isinstance(error, commands.CommandOnCooldown):
        await send('Mam okres ochronny', delete_after=5)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, ValueError):
        await send('Podano błędny argument', delete_after=5)
    elif isinstance(error, commands.DisabledCommand):
        await send('Prace nad tą komendą trwają. Nie należy jej używać.', delete_after=5)
    elif isinstance(error, commands.PrivateMessageOnly):
        await send("Tej komendy teraz można używać tylko w DM", delete_after=5)
    elif isinstance(error, commands.NoPrivateMessage):
        await send("Tej komendy można używać tylko na serwerze", delete_after=5)
    elif isinstance(error, GameEnd):
        c = ":scroll:{}:scroll:".format(error.reason) + '\n' + '**__Grę wygrywa frakcja {}__**'.format(error.winner)
        await bot.game.winning(error.reason, error.winner)
        await send_to_manitou(c)
        for channel in get_guild().text_channels:
            if channel.category_id in (FRAKCJE_CATEGORY_ID, NIEPUBLICZNE_CATEGORY_ID):
                await channel.send(c)
    else:
        await send(':robot:Bot did an uppsie :\'( :robot:')
        return error


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.message.delete(delay=6)
    err = await handle_error(ctx.send, error)
    if err:
        report_error(ctx, error)
    

@bot.event
async def on_interaction_error(inter, error):
    async def send(content=None, *, reference=None, delete_after=None, **kwargs):
        try:
            await inter.respond(content, ephemeral=True, **kwargs)
        except discord.ClientException:
            await inter.send(content, ephemeral=True, **kwargs)
    err = await handle_error(send, error)
    if err:
        report_inter_error(inter, error)


@bot.event
async def on_error(event, *args, **_):
    E, error, _ = sys.exc_info()
    if E is commands.CommandInvokeError:
        error = error.original
    if isinstance(error, discord.HTTPException) and error.code == 10062:
        return
    msg = SLIM_TEMPLATE.format(event, args, RULLER)
    logging.exception(msg)
    info = await bot.application_info()
    await info.owner.send('An event error occured')
    traceback.print_exc()
