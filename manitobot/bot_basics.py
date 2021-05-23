import sys

import discord
from discord.ext import commands

# noinspection PyUnresolvedReferences
from . import slash_http, slash_core
from .basic_models import ManiBot

command_prefix = '&'


class Help(commands.DefaultHelpCommand):
    def get_ending_note(self):
        return '''Informacje o konkretnej komendzie:\t{0}help <komenda>
Informacje o konkretnej kategorii:\t{0}help <kategoria>
Skrócona pomoc dla Manitou:\t\t   {0}help m
Skrócona pomoc dla graczy\t\t\t {0}help g'''.format(command_prefix)

    def command_not_found(self, _):
        return f'{command_prefix}help HONK?'


intents = discord.Intents.default()
intents.members = True

bot = ManiBot(
    command_prefix=commands.when_mentioned_or(command_prefix),
    help_command=Help(no_category='Pozostałe', verify_checks=True),
    case_insensitive=True,
    intents=intents
)


@bot.listen('on_message_edit')
async def message_change(before, after):
    reaction = discord.utils.get(before.reactions, emoji='✅')
    if before.content != after.content and (reaction is None or not reaction.me):
        await bot.on_message(after)


@bot.after_invoke
async def check_marked(ctx):
    if not any(sys.exc_info()):
        try:
            await ctx.message.add_reaction('✅')
        except discord.NotFound:
            pass


@bot.command(name='pomoc')
async def help1(ctx):
    """Wysyła pomoc do wszystkich aktualnie działających komend, niezależnie czy autor może ich użyć.
    """
    h = bot.help_command
    h.verify_checks = False
    h.show_hidden = True
    h.dm_help = None
    h.dm_help_threshold = 500
    h.context = ctx
    await h.command_callback(ctx)
