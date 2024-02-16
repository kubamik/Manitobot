import datetime as dt
from typing import Tuple, List, Sequence

from pytz import UTC

from settings import PING_YELLOW_ID, PING_GREEN_ID

EMOJIS = '🍓🏀🍌🌵🐳🍇🐷'
NO_EMOJI = '❌'
GM_EMOJI = '⚜'
WEEKD = ['pn', 'wt', 'śr', 'cz', 'pt', 'sb', 'nd']
WEEKDAYN = [
    'poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota',
    'niedziela'
]  # nominative
WEEKDAYA = [
    'poniedziałek', 'wtorek', 'środę', 'czwartek', 'piątek', 'sobotę',
    'niedzielę'
]  # accusative

ANKIETKA_PING = f'<:ping_yellow:{PING_YELLOW_ID}>'
DEKLARACJE_PING = f'<:ping_green:{PING_GREEN_ID}>'
ANKIETKA_BODY = """**Ankietka** na {0}.-{1}.
{2} {2} {2}

**Kiedy chcesz grać w ktulu?**
Zaznacz wszystkie opcje, które ci pasują.
Ankietki są niezobowiązujące.
"""
DEKLARACJE_BODY = """**Deklaracje** na {0} ({1}.{2:02})
{3} {3} {3}

**O której możesz i chcesz grać w ktulu?**
Zaznacz wszystkie opcje, które ci pasują.
Postaraj się o dostępność o wybranych godzinach.
"""
ANKIETKA_FOOT = "\n{0} Nie zagram"
DEKLARACJE_FOOT = """
{0} Nie zagram
{1} Mogę prowadzić grę
"""


def survey(wdstart: int, wdend: int, tz: UTC) -> Tuple[str, List[str]]:
    now = dt.datetime.now(tz)
    duration = (wdend - wdstart) % 7 + 1
    offset = (wdstart - now.weekday()) % 7
    output = ANKIETKA_BODY.format(WEEKD[wdstart], WEEKD[wdend], ANKIETKA_PING)
    time = now + dt.timedelta(days=offset)
    for i, e in zip(range(duration), EMOJIS):
        output += f"\n{e} {WEEKDAYN[time.weekday()]} {time.day}.{time.month:02}"
        if i == 0 and offset == 0:
            output += " (dzisiaj)"
        if i == 0 and offset == 1:
            output += " (jutro)"
        time += dt.timedelta(days=1)
    output += ANKIETKA_FOOT.format(NO_EMOJI)
    return output, list(EMOJIS[:duration]) + [NO_EMOJI]


def declarations(day: int, tz: UTC,
                 hours: Sequence[int]) -> Tuple[str, List[str]]:
    now = dt.datetime.now(tz).replace(hour=0,
                                      minute=0,
                                      second=0,
                                      microsecond=0,
                                      tzinfo=None)
    offset = (day - now.weekday()) % 7
    time = now + dt.timedelta(days=offset)
    if offset == 0:
        day = 'dzisiaj'
    elif offset == 1:
        day = 'jutro'
    else:
        day = WEEKDAYA[time.weekday()]
    output = DEKLARACJE_BODY.format(day, time.day, time.month, DEKLARACJE_PING)
    for h, e in zip(hours, EMOJIS):
        output += f"\n{e} <t:{int(tz.localize(time.replace(hour=h)).timestamp())}:t>"
    output += DEKLARACJE_FOOT.format(NO_EMOJI, GM_EMOJI)
    return output, list(EMOJIS[:len(hours)]) + [NO_EMOJI, GM_EMOJI]
