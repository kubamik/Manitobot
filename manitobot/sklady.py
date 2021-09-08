from typing import Dict, List

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
    "16": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel", "Szuler",
           "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Cicha_Stopa", "Janosik"],
    "17UFO": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel",
              "Szuler", "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Wojownik", "Pożeracz_Umysłów", "Detektor",
              "Zielona_Macka"],
    "18UFOJ": ["Dziwka", "Szeryf", "Pastor", "Pijany_Sędzia", "Dobry_Rew", "Burmistrz", "Hazardzista", "Mściciel",
               "Szuler", "Zły_Rew", "Szaman", "Szamanka", "Samotny_Kojot", "Wojownik", "Pożeracz_Umysłów", "Detektor",
               "Zielona_Macka", "Janosik"]
}


def list_sets() -> str:
    c = ""
    for key in SETS:
        c += key + "\n"
    return c


def get_set(set_name: str) -> List[str]:
    return SETS[set_name]


def set_exists(set_name: str) -> bool:
    return set_name in SETS


def print_set(set_name: str) -> str:
    if not set_exists(set_name):
        raise NoSuchSet
    return postacie.print_list(SETS[set_name])
