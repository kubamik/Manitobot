import datetime as dt
import sqlite3
from collections import namedtuple

import aiosqlite
import discord

from settings import ELECTION_DB_PATH

Candidate = namedtuple('Candidate', 'id emoji emoji_id text description')
Election = namedtuple('Election', 'name from_date to_date message confirmation_message '
                                  'channel_id in_progress min_votes_count max_votes_count message_id')


def connect_db(func):
    async def wrapper(*args, **kwargs):
        db = None
        try:
            db = await aiosqlite.connect(ELECTION_DB_PATH)
            data = await func(db, *args, **kwargs)
        finally:
            if db:
                await db.close()
        return data
    return wrapper


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
                id INTEGER,
                emoji TEXT,
                emoji_id INTEGER,
                text TEXT,
                description TEXT,
                election_id INTEGER,
                PRIMARY KEY (id, election_id),
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


def get_current_elections():
    with sqlite3.connect(ELECTION_DB_PATH) as db:
        return db.execute('''SELECT id, from_date, to_date, in_progress FROM elections 
                             WHERE to_date > ?''',
                          (dt.datetime.utcnow().isoformat(),)).fetchall()


@connect_db
async def create_election(db, name, election_id, from_date, to_date, message,
                          confirmation_message, min_votes_count, max_votes_count, channel_id, candidates):
    await db.execute('''
        INSERT INTO elections (
            id, name, from_date, to_date, message, confirmation_message, 
            channel_id, min_votes_count, max_votes_count, in_progress
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (election_id, name, from_date, to_date, message, confirmation_message,
          channel_id, min_votes_count, max_votes_count))
    await db.commit()
    for candidate in candidates:
        await db.execute('''
            INSERT INTO candidates (id, emoji, emoji_id, text, description, election_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', tuple([candidate.get(v) for v in ('id', 'emoji', 'emoji_id', 'text', 'description')] + [election_id]))
    await db.commit()


async def query_election(query):
    async with aiosqlite.connect(ELECTION_DB_PATH) as db:
        async with db.execute(query) as cursor:
            return await cursor.fetchall()


@connect_db
async def check_voting_rights(db, member, election_id):
    async with db.execute('''SELECT from_date FROM elections WHERE id = ?''', (election_id,)) as cursor:
        from_date = (await cursor.fetchone())[0]
    return member.joined_at.timestamp() < dt.datetime.fromisoformat(from_date).timestamp()


@connect_db
async def start_election(db, election_id):
    await db.execute('''UPDATE elections SET in_progress = 1 WHERE id = ?''', (election_id,))
    await db.commit()


@connect_db
async def get_election(db, election_id):
    async with db.execute('''SELECT name, from_date, to_date, message, confirmation_message, channel_id, 
                             in_progress, min_votes_count, max_votes_count, message_id 
                             FROM elections WHERE id = ?''', (election_id,)) as cursor:
        return Election(*await cursor.fetchone())


@connect_db
async def get_candidates(db, election_id):
    candidates = []
    cursor = await db.execute('''SELECT id, emoji, emoji_id, text, description 
                             FROM candidates WHERE election_id = ?''', (election_id,))
    db_candidates = await cursor.fetchall()
    for candidate in db_candidates:
        id_, emoji, emoji_id, text, description = candidate
        candidates.append(Candidate(id=id_, emoji_id=emoji_id, emoji=emoji,
                                    text=text, description=description))
    return candidates


@connect_db
async def set_election_message_id(db, election_id, message_id):
    await db.execute('''UPDATE elections SET message_id = ? WHERE id = ?''', (message_id, election_id))
    await db.commit()


@connect_db
async def register_election_vote(db, user_id, election_id, candidates_ids):
    if await db.execute('''SELECT * FROM votes WHERE user_id = ? AND election_id = ?''', (user_id, election_id)):
        await db.execute('''DELETE FROM votes WHERE user_id = ? AND election_id = ?''', (user_id, election_id))
    for candidate_id in candidates_ids:
        await db.execute('''INSERT INTO votes (user_id, election_id, candidate_id) VALUES (?, ?, ?) ''',
                         (user_id, election_id, candidate_id))
    await db.commit()


@connect_db
async def get_confirmation_message(db, election_id, candidates_ids):
    names = []
    for candidate_id in candidates_ids:
        async with db.execute('''SELECT text FROM candidates WHERE id = ?''', (candidate_id,)) as cursor:
            names.append((await cursor.fetchone())[0])
    async with db.execute('''SELECT confirmation_message FROM elections WHERE id = ?''', (election_id,)) as cursor:
        message = (await cursor.fetchone())[0]
    return message.format(', '.join(names))


@connect_db
async def end_election(db, election_id):
    await db.execute('''UPDATE elections SET in_progress = 0 WHERE id = ?''', (election_id,))
    await db.commit()


@connect_db
async def get_election_results(db, election_name):
    async with db.execute('''SELECT candidates.text, COUNT(*) AS "Count" 
                             FROM votes
                             INNER JOIN candidates ON votes.candidate_id = candidates.id
                             INNER JOIN elections ON votes.election_id = elections.id
                             WHERE elections.name = ?
                             GROUP BY candidate_id, candidates.text
                             ORDER BY "Count" DESC''',
                          (election_name,)) as cursor:
        return await cursor.fetchall()
