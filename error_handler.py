import logging

import discord
from discord.ext import commands

from bot_basics import bot
from errors import AuthorNotPlaying, GameEnd, WrongGameType, GameNotStarted, MemberNotPlaying
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


def report_error(ctx, error):
    msg = ISSUE_TEMPLATE.format(ctx, RULLER)
    try:
        raise error
    except Exception:
        logging.exception(msg)
        raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('HONK?', delete_after=5)
    elif isinstance(error, discord.Forbidden):
        await ctx.send('Chcem coś zrobić, ale nie mogem.')
    elif isinstance(error, (commands.MissingRole, commands.CheckAnyFailure, commands.NotOwner)):
        await ctx.send('You have no power here!', delete_after=5)
        await ctx.message.delete(delay=5)
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Brakuje parametru: ' + str(error.param), delete_after=5)
    elif isinstance(error, MemberNotPlaying):
        await ctx.send('Ta osoba nie gra lub nie żyje', delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('Nie ma takiej osoby', delete_after=5)
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send(f'Błędny parametr\n||{error}||', delete_after=5)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send('Mam okres ochronny', delete_after=5)
        await ctx.message.delete(delay=5)
    elif isinstance(error, GameNotStarted):
        await ctx.send('Gra nie została rozpoczęta', delete_after=5)
        await ctx.message.delete(delay=5)
        raise error
    elif isinstance(error, WrongGameType):
        await ctx.send('Aktualny typ gry nie obsługuje tego polecenia', delete_after=5)
        await ctx.message.delete(delay=5)
        report_error(ctx, error)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, ValueError):
        await ctx.send('Podano błędny argument', delete_after=5)
        await ctx.message.delete(delay=5)
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send('Prace nad tą komendą trwają. Nie należy jej używać.', delete_after=5)
        await ctx.message.delete(delay=5)
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.message.delete(delay=5)
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.message.delete(delay=5)
    elif isinstance(error, AuthorNotPlaying):
        await ctx.send('Musisz grać, aby użyć tej komendy', delete_after=5)
        await ctx.message.delete(delay=5)
    elif isinstance(error, commands.CheckFailure):
        await ctx.message.delete(delay=5)
    elif isinstance(error, GameEnd):
        c = ":scroll:{}:scroll:".format(error.reason) + '\n' + '**__Grę wygrywa frakcja {}__**'.format(error.winner)
        await bot.game.winning(error.reason, error.winner)
        await send_to_manitou(c)
        for channel in get_guild().text_channels:
            if channel.category_id == FRAKCJE_CATEGORY_ID or channel.category_id == NIEPUBLICZNE_CATEGORY_ID:
                await channel.send(c)
    else:
        await ctx.send(':robot:Bot did an uppsie :\'( :robot:')
        print(ctx.command, type(error))
        report_error(ctx, error)


@bot.listen()
async def on_error(event, *args, **_):
    msg = SLIM_TEMPLATE.format(event, args, RULLER)
    logging.exception(msg)
    await bot.owner_id.send('An event error occured')