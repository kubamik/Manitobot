import logging

import discord
from discord.ext import commands

from bot_basics import bot
from errors import AuthorNotPlaying, GameEnd, WrongGameType, GameNotStarted, MemberNotPlaying, MyBaseException, \
    InvalidRequest
from settings import FRAKCJE_CATEGORY_ID, NIEPUBLICZNE_CATEGORY_ID, RULLER
from utility import send_to_manitou, get_guild


ISSUE_TEMPLATE = '''
MESSAGE ID: {0.message.id}
ARGS:       {0.args}
KWARGS:     {0.kwargs}
COMMAND:    {0.command.name}
CHANNEL:    {0.channel}
AUTHOR:     {0.author.display_name}
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


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.message.delete(delay=6)

    if isinstance(error, MyBaseException):
        await ctx.send(error.msg, delete_after=5)
    elif isinstance(error, InvalidRequest):
        await ctx.send(error.msg)  # TODO: Remove raising InvalidRequest everywhere
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('HONK?', delete_after=5)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        await ctx.send('Chcem coś zrobić, ale nie mogem.', delete_after=5)
    elif isinstance(error, (commands.MissingRole, commands.NotOwner)):
        await ctx.send('You have no power here!', delete_after=5)
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Brakuje parametru: ' + str(error.param), delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('Nie ma takiej osoby wśród żywych graczy', delete_after=5)
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send(f'Błędny parametr\n||{error}||', delete_after=5)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send('Mam okres ochronny', delete_after=5)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, ValueError):
        await ctx.send('Podano błędny argument', delete_after=5)
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send('Prace nad tą komendą trwają. Nie należy jej używać.', delete_after=5)
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("Tej komendy teraz można używać tylko w DM", delete_after=5)
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Tej komendy teraz można używać tylko na kanale frakcji", delete_after=5)
    elif isinstance(error, GameEnd):
        c = ":scroll:{}:scroll:".format(error.reason) + '\n' + '**__Grę wygrywa frakcja {}__**'.format(error.winner)
        await bot.game.winning(error.reason, error.winner)
        await send_to_manitou(c)
        for channel in get_guild().text_channels:
            if channel.category_id == FRAKCJE_CATEGORY_ID or channel.category_id == NIEPUBLICZNE_CATEGORY_ID:
                await channel.send(c)
    else:
        await ctx.send(':robot:Bot did an uppsie :\'( :robot:')
        report_error(ctx, error)


@bot.event
async def on_error(event, *args, **_):
    msg = SLIM_TEMPLATE.format(event, args, RULLER)
    logging.exception(msg)
    info = await bot.application_info()
    await info.owner.send('An event error occured')
