import asyncio
import datetime
import io
import json
from random import randint

import aiosqlite
import discord
from discord.ext import commands

from settings import DIE415_ID, DIE421_ID, DIE456_ID, DIE462_ID
from .basic_models import ManiBot
from .election_service import create_election, query_election, check_voting_rights, register_election_vote, \
    setup_election_db, start_election, get_candidates, set_election_message_id, end_election, get_election_results, \
    get_current_elections, get_confirmation_message, get_election, Candidate
from .interactions import Select, SelectOption
from .interactions.components import ComponentMessage, ComponentCallback
from .interactions.interaction import ComponentInteraction
from .my_checks import admin_cmd
from .utility import get_election_backup_channel


class Election(commands.Cog, name='Wybory'):
    def __init__(self, bot: ManiBot):
        self.bot = bot
        setup_election_db()
        self.schedule_elections()

    def schedule_elections(self):
        loop = self.bot.loop
        elections = get_current_elections()
        now = datetime.datetime.now().isoformat()
        for election_id, start_date, end_date, in_progress in elections:
            if start_date > now:
                loop.call_later(start_date.timestamp() - datetime.datetime.now().timestamp(), loop.create_task,
                                self.start_election(election_id))
            elif not in_progress:
                loop.call_soon(loop.create_task, self.start_election(election_id))
            elif end_date > now:
                self.bot.add_component_callback(ComponentCallback(f'election-vote-{election_id}',
                                                                  self.register_vote))
                loop.call_later(end_date.timestamp() - datetime.datetime.now().timestamp(), loop.create_task,
                                self.end_election(election_id))

    @commands.command(name='losuj_kww')
    @admin_cmd()
    async def rand_kww(self, ctx, *, komitet):
        """Przydziela losowy numer kandydatowi zgodnie z standardem RFC 1149.5
        """
        await ctx.send('Losuję numer komitetu...')
        await asyncio.sleep(2)
        match randint(0, 3):
            case 0:
                await ctx.send(f'<:kostka4:{DIE415_ID}>')
            case 1:
                await ctx.send(f'<:kostka4:{DIE421_ID}>')
            case 2:
                await ctx.send(f'<:kostka4:{DIE456_ID}>')
            case 3:
                await ctx.send(f'<:kostka4:{DIE462_ID}>')
        await asyncio.sleep(1)
        await ctx.send(f'Wylosowany numer KWW {komitet} to 4.')

    @staticmethod
    async def register_vote(ctx: ComponentInteraction):
        await ctx.ack(ephemeral=True)
        votes = ctx.values
        election_id = ctx.custom_id.removeprefix('election-vote-')
        if not (await check_voting_rights(ctx.author, election_id)):
            await ctx.send('Nie masz prawa głosu w tych wyborach', ephemeral=True)

        await register_election_vote(ctx.author.id, election_id, votes)
        message = await get_confirmation_message(election_id, votes)
        await get_election_backup_channel().send(ctx.author.mention + ': ' + ', '.join(votes))
        await ctx.send(message)

    @commands.command(name='wybory')
    @admin_cmd()
    async def election(self, ctx: commands.Context, name: str):
        """Tworzy wybory na podstawie pliku JSON dołączonego do wiadomości.
        Powinien zawierać pola tekstowe from_date, to_date, message, confirmation_message, channel_id, min_votes_count,
        max_votes_count.
        Oraz pole candidates będące listą obiektów z polami id, emoji, emoji_id, text, description.
        """
        if len(ctx.message.attachments) != 1:
            await ctx.send('Niepoprawna liczba załączników')
            return

        data = await ctx.message.attachments[0].read()
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            await ctx.send('Niepoprawny format pliku')
            return

        election_id = ctx.message.id
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        message = data.get('message')
        confirmation_message = data.get('confirmation_message')
        channel_id = data.get('channel_id')
        min_votes_count = data.get('min_votes_count', 1)
        max_votes_count = data.get('max_votes_count')
        candidates = data.get('candidates')

        if not (all([from_date, to_date, message, confirmation_message, channel_id, candidates, max_votes_count])
                and isinstance(candidates, list) and all(isinstance(c, dict) for c in candidates)
                and all(c.get('id') and c.get('text') for c in candidates)):
            await ctx.send('Brak obowiązkowych danych')
            return

        try:
            await create_election(name, election_id, from_date, to_date, message, confirmation_message,
                                  min_votes_count, max_votes_count, channel_id, candidates)
        except aiosqlite.IntegrityError:
            await ctx.send('Wybory o podanej nazwie już istnieją')
            return

        loop = self.bot.loop
        start = datetime.datetime.fromisoformat(from_date)
        loop.call_later(max(0.0, start.timestamp() - datetime.datetime.now().timestamp()), loop.create_task,
                        self.start_election(election_id))

    @commands.command(name='wyniki')
    @admin_cmd()
    async def election_results(self, ctx: commands.Context, election_name: str):
        """Wyświetla wyniki wyborów o podanym ID
        """
        results = await get_election_results(election_name)
        await ctx.send(f'Wyniki wyborów {election_name}:\n' + '\n'.join(f'{text}: {votes}' for text, votes in results))

    @commands.command(aliases=['queryel'], hidden=True)
    @commands.is_owner()
    async def query_election(self, ctx: commands.Context, *, query):
        """ⒹWykonuje zapytanie SQL na bazie danych wyborów
        """
        results = await query_election(query)
        content = '\n'.join(map(str, results))
        if content:
            await ctx.send(f'Results of:\n{query}',
                           file=discord.File(io.BytesIO(content.encode('utf-8')),
                                             filename='query_results.txt'))
        else:
            await ctx.send(f'Query executed successfully:\n{query}')

    @staticmethod
    def create_select(candidates, election_id, min_votes, max_votes):
        options = []
        for candidate in candidates:
            emoji = discord.PartialEmoji(id=candidate.emoji_id, name=candidate.emoji) \
                if candidate.emoji_id else candidate.emoji
            options.append(SelectOption(label=candidate.text, value=candidate.id,
                                        description=candidate.description, emoji=emoji))

        return Select(custom_id=f'election-vote-{election_id}', placeholder='Oddaj głos', options=options,
                      min_values=min_votes, max_values=max_votes)

    async def start_election(self, election_id):
        await self.bot.wait_until_ready()
        await start_election(election_id)
        election = await get_election(election_id)
        _, _, to_date, message, _, channel_id, _, min_votes, max_votes, _ = election
        candidates = await get_candidates(election_id)
        channel = self.bot.get_channel(channel_id)

        select = self.create_select(candidates, election_id, min_votes, max_votes)

        msg = await channel.send(message, components=[[select]])
        await set_election_message_id(election_id, msg.id)
        end = datetime.datetime.fromisoformat(to_date)
        loop = self.bot.loop
        loop.call_later(end.timestamp() - datetime.datetime.now().timestamp(), loop.create_task,
                        self.end_election(election_id))
        self.bot.add_component_callback(ComponentCallback(f'election-vote-{election_id}', self.register_vote))

    async def end_election(self, election_id):
        await self.bot.wait_until_ready()
        await end_election(election_id)
        election = await get_election(election_id)
        channel_id, message_id = election.channel_id, election.message_id
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        select = self.create_select([Candidate(
            emoji_id=None, emoji=None, text='Placeholder', description=None, id=1,
        )], election_id, 1, 1)
        select.disabled = True
        await message.edit(components=[[select]])

        self.bot.remove_component_callback(f'election-vote-{election_id}')

