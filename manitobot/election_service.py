import datetime as dt
import sqlite3
from collections import namedtuple

import aiosqlite
import discord

from settings import ELECTION_DB_PATH

Candidate = namedtuple('Candidate', 'id emoji emoji_id text description')


def setup_election_db():
    with sqlite3.connect(ELECTION_DB_PATH) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS elections (
                id INTEGER PRIMARY KEY,
                name TEXT,
                from_date TEXT, 
                to_date TEXT,
                message TEXT, 
                confirmation_message TEXT,
                channel_id INTEGER,
                in_progress INTEGER,
                min_votes_count INTEGER,
                max_votes_count INTEGER,
                message_id INTEGER,
                UNIQUE(name)
            )''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY,
                emoji TEXT,
                emoji_id INTEGER,
                text TEXT,
                description TEXT,
                election_id INTEGER,
                FOREIGN KEY (election_id) REFERENCES elections(id)
            )''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                user_id INTEGER,
                candidate_id INTEGER,
                election_id INTEGER,
                PRIMARY KEY (user_id, election_id, candidate_id),
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (election_id) REFERENCES elections(id)
            )''')


def get_incoming_elections():
    with sqlite3.connect(ELECTION_DB_PATH) as db:
        return db.execute('''SELECT id, from_date, to_date, in_progress FROM elections 
                                 WHERE from_date > ? OR to_date > ?''',
                          (dt.datetime.now().isoformat(),)).fetchall()


async def create_election(name, election_id, from_date, to_date, message,
                          confirmation_message, min_votes_count, max_votes_count, channel_id, candidates):
    with aiosqlite.connect(ELECTION_DB_PATH) as db:
        await db.execute('''
            INSERT INTO elections (
                id, name, from_date, to_date, message, confirmation_message, 
                channel_id, min_votes_count, max_votes_count, in_progress
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (election_id, name, from_date, to_date, message, confirmation_message,
              channel_id, min_votes_count, max_votes_count))
        election_id = await db.execute('SELECT last_insert_rowid()')
        for candidate in candidates:
            await db.execute('''
                INSERT INTO candidates (emoji, emoji_id, text, description, election_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (candidate.get(v) for v in ('emoji', 'emoji_id', 'text', 'description', election_id)))
        await db.commit()


async def query_election(query):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        async with db.execute(query) as cursor:
            return await cursor.fetchall()


async def check_voting_rights(member: discord.Member, election_id):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        async with db.execute('''SELECT from_date FROM elections WHERE id = ?''', (election_id,)) as cursor:
            from_date = await cursor.fetchone()[0]
        return member.joined_at >= dt.datetime.fromisoformat(from_date)


async def start_election(election_id):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        await db.execute('''UPDATE elections SET in_progress = 1 WHERE id = ?''', (election_id,))
        await db.commit()
        with db.execute('''SELECT channel_id, message, min_votes_count, max_votes_count, to_date
                           FROM elections WHERE id = ?''', (election_id,)) as cursor:
            return await cursor.fetchone()[0]


async def get_candidates(election_id):
    candidates = []
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        async with db.execute('''SELECT id, emoji, id, emoji, emoji_id, text, description 
                                 FROM candidates WHERE election_id = ?''', (election_id,)) as cursor:
            async for candidate in cursor.fetchall():
                id_, emoji, emoji_id, text, description = candidate
                candidates.append(Candidate(id=id_, emoji_id=emoji_id, emoji=emoji,
                                            text=text, description=description))
    return candidates


async def set_election_message_id(election_id, message_id):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        await db.execute('''UPDATE elections SET message_id = ? WHERE id = ?''', (message_id, election_id))
        await db.commit()


async def register_election_vote(user_id, election_id, candidates_ids):
    names = []
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        if await db.execute('''SELECT * FROM votes WHERE user_id = ? AND election_id = ?''', (user_id, election_id)):
            db.execute('''DELETE FROM votes WHERE user_id = ? AND election_id = ?''', (user_id, election_id))
        for candidate_id in candidates_ids:
            await db.execute('''INSERT INTO votes (user_id, election_id, candidate_id) VALUES (?, ?, ?) ''',
                             (user_id, election_id, candidate_id))
            async with db.execute('''SELECT text FROM candidates WHERE id = ?''', (candidate_id,)) as cursor:
                names.append(await cursor.fetchone()[0])
        await db.commit()
        async with db.execute('''SELECT confirmation_message FROM elections WHERE id = ?''', (election_id,)) as cursor:
            message = await cursor.fetchone()[0]
    return message.format(*names)


async def end_election(election_id):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        await db.execute('''UPDATE elections SET in_progress = 0 WHERE id = ?''', (election_id,))
        async with db.execute('''SELECT channel_id, message_id FROM elections WHERE id = ?''', (election_id,)) as cursor:
            return await cursor.fetchone()


async def get_election_results(election_name):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        async with db.execute('''SELECT candidates.text, COUNT(*) AS "Count" 
                                 FROM votes
                                 INNER JOIN candidates ON votes.candidate_id = candidates.id
                                 INNER JOIN elections ON votes.election_id = elections.id
                                 WHERE elections.name = ?
                                 GROUP BY candidate_id, candidates.text
                                 ORDER BY "Count" DESC''',
                              (election_name,)) as cursor:
            return await cursor.fetchall()
