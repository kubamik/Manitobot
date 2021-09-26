import sqlite3
from typing import Dict, List, Tuple, Optional

from settings import SETS_DB_PATH
from . import postacie
from .errors import NoSuchSet

SETS: Dict[str, List[str]] = {
    "0": [],
    "1": ["Sędzia"],
    "4": ["Sędzia", "Burmistrz", "Szeryf", "Janosik"],
    "5": ["Sędzia", "Burmistrz", "Szeryf", "Szaman", "Janosik"],
    "7": ["Szeryf", "Pastor", "Dobry_Rew", "Mściciel", "Zły_Rew", "Szaman", "Szamanka"],
    "11": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Mściciel", "Złodziej", "Zły_Rew", "Szaman",
           "Szamanka", "Wojownik"],
    "12": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Mściciel", "Złodziej", "Zły_Rew", "Szaman",
           "Szamanka", "Wojownik", "Janosik"],
    "13": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Mściciel", "Szuler", "Zły_Rew",
           "Szaman", "Szamanka", "Wojownik", "Janosik"],
    "14": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Mściciel", "Szuler", "Zły_Rew",
           "Szaman", "Szamanka", "Samotny_Kojot", "Cicha_Stopa", "Janosik"],
    "15": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel", "Szuler",
           "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Cicha_Stopa", "Janosik"],
    "16": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista",
           "Agent_Ubezpieczeniowy", "Mściciel", "Złodziej", "Szuler", "Zły_Rew", "Szaman", "Szamanka", "Wojownik",
           "Płonący_Szał"],
    "17": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel",
           "Szuler", "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Wojownik", "Pożeracz_Umysłów", "Detektor",
           "Zielona_Macka"],
    "18": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel",
           "Szuler", "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Wojownik", "Pożeracz_Umysłów", "Detektor",
           "Zielona_Macka", "Janosik"]
}


SET_NAME = r'[\w-]{3,}$'


def setup_sets_db() -> List[str]:
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS sets '
                    '(name TEXT, role_count INTEGER, author INTEGER, description TEXT, roles TEXT)')
        db_names = cur.execute('SELECT role_count, name FROM sets').fetchall()
    db_names += [(len(v), name) for name, v in SETS.items()]
    names = [t[1] for t in sorted(db_names)]
    return names


def add_set(author_id, name, description, roles):
    r_count = len(roles)
    roles = '/'.join(roles)
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO sets VALUES(?, ?, ?, ?, ?)', [name, r_count, author_id, description, roles])


def list_sets(names) -> str:
    c = ""
    for name in names:
        c += name + "\n"
    return c


def get_set(set_name: str) -> Tuple[Optional[int], Optional[str], List[str]]:
    try:
        return None, None, SETS[set_name]
    except KeyError:
        pass
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT author, description, roles FROM sets WHERE name=?', [set_name])
        author_id, desc, roles = cur.fetchall()[0]
    return author_id, desc, roles.split('/')


def get_sets(count: int) -> List[Tuple[str, Optional[int], Optional[str]]]:
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT name, author, description FROM sets WHERE role_count={count}')
        sets = cur.fetchall()
    if str(count) in SETS:
        sets.append((str(count), None, None))
    return sorted(sets)


def get_set_author_and_count(name: str) -> Tuple[int, int]:
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT author, role_count FROM sets WHERE name=?', [name])
        data = cur.fetchall()
    if not data:
        raise NoSuchSet
    return data[0][0], data[0][1]


def update_set(set_name: str, name: str = None, description: str = None) -> None:
    vals = []
    changes = ''
    if name:
        changes = 'name=?'
        vals.append(name)
    if description is not None:
        changes = 'description=?'
        vals.append(description)
    vals.append(set_name)
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f'UPDATE sets SET {changes} WHERE name=?', vals)


def delete_set(name: str) -> None:
    with sqlite3.connect(SETS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM sets WHERE name=?', [name])


def set_exists(set_name: str) -> bool:
    return set_name in SETS


def print_set(set_name: str) -> str:
    if not set_exists(set_name):
        raise NoSuchSet
    return postacie.print_list(SETS[set_name])
