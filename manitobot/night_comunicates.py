from .utility import *


# TODO: Duel, Voting, Summary as states, night coms combined from phrases

# [(text, activity to format number)], len can be greater than 1
new_night_com = {
    "Szeryf": [("Wybierz osobę, którą chcesz zamknąć. Użyj komendy `&zamk NICK`", "arrest")],
    "Dziwka": [("Wybierz osobę, którą chcesz zadziwić. Użyj komendy `&dziw NICK`", "dziw")],
    "Pastor": [("Wybierz osobę, którą chcesz sprawdzić. Użyj komendy `&spow NICK`", "pasteur")],
    "Opój": [(
             "Jeśli chcesz upijać użyj komendy `&pij NICK`, jeśli nie chcesz upijać użyj `&nie`. Możesz upijać jeszcze {} razy",
             "drink")],
    "Pijany_Sędzia": [(
                      "Jeśli chcesz upijać użyj komendy `&pij NICK`, jeśli nie chcesz upijać użyj `&nie`. Możesz upijać jeszcze {} razy",
                      "drink")],
    "Hazardzista": [("Jeśli chcesz zagrać w rosyjską ruletkę użyj `&graj NICK`, jeśli nie użyj `&nie`", "play")],
    "Mściciel": [
        ("Jeśli chcesz zabijać użyj `&zabij NICK`, jeśli nie użyj `&nie`. Możesz działać raz na grę.", "kill")],
    "Wojownik": [
        ("Jeśli chcesz zabijać użyj `&zabij NICK`, jeśli nie użyj `&nie`. Możesz działać raz na grę.", "kill")],
    "Zielona_Macka": [
        ("Jeśli chcesz zabijać użyj `&zabij NICK`, jeśli nie użyj `&nie`. Możesz działać raz na grę.", "kill")],
    "Samotny_Kojot": [("Jeśli chcesz zabijać użyj `&zabij NICK`, jeśli nie użyj `&nie`", "kill")],
    "Płonący_Szał": [("Jeśli chcesz zabijać użyj `&zabij NICK`, jeśli nie użyj `&nie`", "kill")],
    "Cicha_Stopa": [("Jeśli chcesz podłożyć komuś posążek użyj `&podł NICK`, jeśli nie użyj `&nie`", "plant")],
    "Złodziej": [(
                 "Jeśli chcesz spróbować ukraść posążek użyj `&szukaj`, jeśli nie użyj `&nie`. Możesz działać raz na grę.",
                 "search")],
    "Purpurowa_Przyssawka": [(
                             "Jeśli chcesz spróbować ukraść posążek użyj `&szukaj`, jeśli nie użyj `&nie`. Możesz działać raz na grę.",
                             "search")],
    "Szuler": [("Jeśli chcesz kogoś oszulerzyć użyj `&ograj NICK`, jeśli nie użyj `&nie`. Możesz działać raz na grę.",
                "cheat")],
    "Szamanka": [(
                 "Jeśli chcesz podłożyć komuś ziółka użyj `&zioł NICK`, jeśli nie użyj `&nie`. Możesz działać raz na grę.",
                 "herb")],
    "Lornecie_Oko": [(
                     "Jeśli chcesz sprawdzić kto ma posążek użyj `&kto`, jeśli nie użyj `&nie`. Możesz działać raz na grę.",
                     "who")],
    "Detektor": [("Aby sprawdzić gdzie znajduje się posążek użyj `&detekt`", "detect")],
    "Pożeracz_Umysłów": [("Aby sprawdzić czyjąś kartę użyj `&rola NICK`", "eat")],
    "Szaman": [
        ("Aby sprawdzić czyjąś kartę użyj `&szam NICK`, , jeśli nie użyj `&nie`. Możesz działać raz na grę.", "szam")],
    "Wikary": [("Aby sprawdzić czy osoba należy do frakcji posiadaczy posążka użyj `&posiad NICK`", "holders")],
    "Ministrant": [("Pastor nie żyje. Aby sprawdzić frakcję jakiegoś gracza użyj `&spow NICK`. Możesz to zrobić {} raz",
                    "pasteur")],
    "Misjonarz": [(
                  "Aby sprawdzić czy osoba jest heretykiem użyj `&heretyk NICK`. Jeśli po chcesz dodatkowo przeszukać tą osobę użyj `&przesz`, jeśli nie użyj `&nie`, możesz to zrobić jeszcze {} razy",
                  "reserch")],
    "Spowiednik": [(
                   "Aby sprawdzić kartę kracza użyj `&rola NICK`, możesz to zrobić 1 raz. Aby dobić sprawdzaną osobę użyj `&dobij`",
                   "eat")],
    "Lusterko": [(
                 "Aby sprawdzić czyjąś rolę użyj `&lustruj NICK`. Jeżeli chcesz skopiować zdolność tej osoby użyj `&kopiuj`. Możesz to zrobić jeszcze {} razy",
                 "copy")],
    "Lucky_Luke": [(
                   "Aby kogoś przeszukać użyj `&szukaj NICK`. Następnie, aby kogoś zabić użyj `&zabij NICK`, możesz zabijać jeszcze {} razy",
                   "kill"), (
                   "\nAby zacząć śledzić użyj `&śledź NICK`, możesz to zrobić jeszcze {} razy. Kiedy użyjesz wszystkich pożądanych zdolności użyj `&kto`, aby dowiedzieć się kto ma posążek.",
                   "follow")]
}

operation_com_private = {
    "arrest": "Zostałeś zamknięty. Nie obudzisz się więcej tej nocy.",
    "drink": "Zostałeś upity. Nie obudzisz się więcej tej nocy.",
    "dziw": "**{author}** właśnie Cię zadziwił(a)",
    "cheat": "Zostałeś ograny, nie obudzisz się więcej tej nocy"
}

webhook_com = {
    'wins': ("Decyzją jednoosobowej ławy przysięgłych pojedynek wygrywa **{member}**",
             'http://www.myiconfinder.com/uploads/iconsets/256-256-e9909996c50fe344c944c09c430b8346-judge.png'),
    'arrest': ("Na mocy nadanej mi przez Manitou władzy oświadczam:\n**{member}** zostaje zamknięty(-a) do wyjaśnienia",
               'https://www.shareicon.net/data/512x512/2016/04/10/747358_people_512x512.png'),
    'peace': (
    'Jako wybrany w demokratycznych (i wcale nie sfałszowanych) wyborach {role} **Bum Bum City** __uniewinniam__ wieszaną osobę!',
    'https://media.discordapp.net/attachments/691394357571485696/720236813901365308/burmistrz.png?width=671&height=671')
}

# (text, send_town, send_manitou)
meantime_operation_com = {
    "arest": ("{role} zamknął **{subject}**", False, True),
    "wins": ("{role} zadecydował, że pojedynek wygrywa **{subject}**", True, False),
    "peace": ("{role} ułaskawił wieszaną osobę", True, False)
}

operation_com_public = {
    # "wins":("Decyzją Sędziego pojedynek wygrywa **{subject}**",[get_town_channel],[]),
    "arrest": ("{role} zamknął **{subject}**", [get_town_channel], []),
    "dziw": ("{role} zadziwiła **{subject}**", [get_manitou_notebook], [get_manitou_role]),
    "pasteur": ("Pastor sprawdził {subject}", [get_manitou_notebook], [get_manitou_role]),
    "drink": ("Upity został {subject}", [get_manitou_notebook], [get_manitou_role]),
    "refuse": ("{role} odmówił skorzystania ze swojej zdolności", [get_manitou_notebook], [get_manitou_role]),
    "play": ("{role} zabił {subject}", [get_manitou_notebook], [get_manitou_role]),
    "plant": ("{role} podłożył(a) posążek {subject}", [get_manitou_notebook], [get_manitou_role]),
    "cheat": ("{role} ograł {subject}", [get_manitou_notebook], [get_manitou_role]),
    "szam": ("{role} sprawdził {subject}", [get_manitou_notebook], [get_manitou_role]),
    "who": ("{role} dowiedział(-o) się kto ma posążek", [get_manitou_notebook], [get_manitou_role]),
    "detect": ("{role} sprawdził {subject}", [get_manitou_notebook], [get_manitou_role]),
    "eat": ("{role} sprawdził rolę {subject}", [get_manitou_notebook], [get_manitou_role]),
    "herb": ("{role} podłożyła ziólka {subject}", [get_manitou_notebook], [get_manitou_role]),
    "holders": ("{role} dowiedział się czy {subject} należy do frakcji posiadaczy posążka", [get_manitou_notebook],
                [get_manitou_role]),
    "finoff": ("{role} zabił {subject}", [get_manitou_notebook], [get_manitou_role]),
    "burn": ("{role} zabił {subject}", [get_manitou_notebook], [get_manitou_role]),
    "heretic": ("{role} dowiedział się, czy {subject} jest heretykiem", [get_manitou_notebook], [get_manitou_role]),
    "research": ("{role} przeszukał {subject}", [get_manitou_notebook], [get_manitou_role])
}


async def operation_send(operation, author, role, member):
    try:
        mess_det = operation_com_public[operation]
        for channel in mess_det[1]:
            await channel().send(mess_det[0].format(subject=member.display_name, role=role.replace('_', ' ')))
        for funk in mess_det[2]:
            for person in funk().members:
                await person.send(mess_det[0].format(subject=member.display_name, role=role.replace('_', ' ')))
    except AttributeError:
        try:
            for channel in mess_det[1]:
                await channel().send(mess_det[0].format(role=role.replace('_', ' ')))
            for funk in mess_det[2]:
                for person in funk().members:
                    await person.send(mess_det[0].format(role=role.replace('_', ' ')))
        except KeyError:
            pass
    except KeyError:
        pass
    try:
        mess = operation_com_private[operation]
        await member.send(mess.format(author=author.display_name))
    except KeyError:
        pass


# new remake
'''
operation_com_private = {
  "arrest":"Zamknięto Cię, nie obudzisz się więcej tej nocy.",
  "drink":"Upito Cię, nie obudzisz się więcej tej nocy.",
  "dziw":"**{a_name}** właśnie Cię zadziwił(a)",
  "cheat":"Ograno Cię, nie obudzisz się więcej tej nocy"
}
operation_com_public = {
  "arrest":("{role}({a_name}) zamknął **{m_name}({m_role})**", True, False),
  "dziw":("{role}({a_name}) zadziwiła **{m_name}({m_role})**", False, True),
  "pasteur":("Pastor sprawdził {m_name}({m_role})", False, True),
  "drink":("Upity został {m_name}({m_role})", False, True),
  "refuse":("{role}({a_name}) odmówił skorzystania ze swojej zdolności", False, True),
  "play":("{role}({a_name}) zabił {m_name}({m_role})", False, True),
  "plant":("{role}({a_name}) podłożył(a) posążek {m_name}({m_role})", False, True),
  "cheat":("{role}({a_name}) ograł {m_name}({m_role})", False, True),
  "szam":("{role}({a_name}) sprawdził {m_name}({m_role})", False, True),
  "who":("{role}({a_name}) dowiedział(-o) się kto ma posążek", False, True),
  "detect":("{role}({a_name}) sprawdził {m_name}({m_role})", False, True),
  "eat":("{role}({a_name}) sprawdził rolę {m_name}({m_role})", False, True),
  "herb":("{role}({a_name}) podłożyła ziólka {m_name}({m_role})", False, True),
  "holders":("{role}({a_name}) dowiedział się czy {m_name}({m_role}) należy do frakcji posiadaczy posążka", False, True),
  "finoff":("{role}({a_name}) zabił {m_name}({m_role})", False, True),
  "burn":("{role}({a_name}) zabił {m_name}({m_role})", False, True),
  "heretic":("{role}({a_name}) dowiedział się, czy {m_name}({m_role}) jest heretykiem", False, True),
  "research":("{role}({a_name}) przeszukał {m_name}({m_role})", False, True)
}
async def operation_send(operation, author, member):#member, author : <class Player>
  kwargs = {
    'role':author.role.replace('_', ' '),
    'a_name':author.member.display_name,
  }
  if not member is None:
    kwargs['m_name'] = member.member.display_name,
    kwargs['m_role'] = member.role.replace('_', ' ')
  if operation in operation_com_public:
    try:
      com = webhook_com[operation]
      for webhk in await get_town_channel().webhooks():
        if webhk.name == "Manitobot {}".format(kwargs[role]):
          wbhk = webhk
          break
      else:
        wbhk = await get_town_channel().create_webhook(name="Manitobot {}".format(kwargs[role]))
      await wbhk.send(com[0].format(**kwargs), username=kwargs[a_name], avatar_url = com[1])
    except:
      mess_det = operation_com_public[operation]
      if mess_det[1]:
        await get_town_channel().send(mess_det[0].format(**kwargs))
      if mess_det[2]:
        await send_to_manitou(mess_det[0].format(**kwargs))
  try:
    mess = operation_com_private[operation]
    await member.send(mess.format(**kwargs))
  except KeyError:
    pass

'''
