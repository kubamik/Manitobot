import asyncio
from typing import List, Optional

import discord
from discord.ext import commands

from .bot_basics import bot
from .errors import TooLessVotingOptions
from .utility import get_player_role, get_town_channel, send_to_manitou
from .vote import Vote

V_INSTRUCTION = '''INSTRUKCJA
Aby zagłosować wyślij tu dowolny wariant dowolnej opcji. \
Wiele głosów należy oddzielić przecinkami. Wielkość znaków nie ma znaczenia.'''


async def start_voting(title: str, required_votes: int, options: List[List[str]],
                       not_voting: Optional[List[discord.Member]] = None, vtype: Optional[str] = None):
    if len(options) < max(1, required_votes):
        raise TooLessVotingOptions(len(options))
    not_voting = not_voting or list()
    bot.game.voting = Vote(required_votes, options, not_voting, vtype)
    options_readable = ""
    for option in options:
        options_readable += "**{}**\n\n".format(", ".join(option))
    title = title.split('\n')
    etitle = "Głosowanie: {}".format(title[0])
    description = title[1].format(required_votes) + '\n\n' + options_readable
    embed = discord.Embed(title=etitle, colour=discord.Colour(0x00aaff), description=description)
    embed.set_footer(text=V_INSTRUCTION)
    players = get_player_role().members
    not_voting = bot.game.voting.not_voting
    tasks = []
    for player in players:
        if player not in not_voting:
            tasks.append(player.send(embed=embed))
    await asyncio.gather(*tasks, return_exceptions=True)


async def see_end_voting(ctx: commands.Context, end: bool):
    summary = bot.game.voting.summary
    embed = bot.game.voting.generate_embed(end)
    tasks = []
    if end:
        await get_town_channel().send(embed=embed)
        for member in set(get_player_role().members) - set(bot.game.voting.not_voting):
            async for m in member.history(limit=1):
                tasks.append(m.edit(embed=embed))
        type2func = {
            'duel': 'result_duel',
            'hang': 'hang_sumarize',
            'hangif': 'if_hang',
            'search': 'search_summary'
        }
        vtype = bot.game.voting.vote_type
        bot.game.voting = None
        if vtype in type2func:
            tasks.append(getattr(bot.game.days[-1], type2func[vtype])(ctx, summary))
    else:
        tasks.append(send_to_manitou(embed=embed))
    await asyncio.gather(*tasks, return_exceptions=False)
