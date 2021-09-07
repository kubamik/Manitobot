from collections import defaultdict
from typing import List

roles = {
    "szeryf": "**Szeryf (Miasto)** Jeżeli szeryf żyje, można nie przyjąć pojedynku (nie musi być wiadomo, "
              "kto jest szeryfem - wystarczy, że jeszcze nie umarł). Ponadto szeryf, co noc (również zerowej nocy) "
              "zamyka w więzieniu jedną osobę. Jeżeli ta osoba miała posążek, przejmuje go szeryf. Jeżeli uda mu się "
              "przetrwać z posążkiem do końca nocy, miasto wygrywa. Osoba zamknięta w więzieniu nie budzi się przez "
              "resztę nocy, poza tym nie można jej w żaden sposób zabić, (choć można ją sprawdzić np. pastorem lub "
              "szamanem).",

    "burmistrz": "**Burmistrz (Miasto)** może w dowolnym momencie gry odkryć swoją kartę, ujawniając swoją tożsamość. "
                 "Jeżeli zrobi to w momencie skazywania kogoś na powieszenie, może dodatkowo ułaskawić wieszaną "
                 "właśnie osobę (nikt nie jest wieszany w zamian). Aby się ujawnić musi użyć `&veto`, jeśli zrobi to "
                 "w momencie, gdy ktoś jest wieszany ta osoba zostaje ułaskawiona.",

    "dziwka": "**Dziwka (Miasto)** działa wyłącznie zerowej nocy. Wybiera jedną osobę, która staje się jej klientem. "
              "Manitou budzi tę osobę, dziwka poznaje kartę tej osoby, zaś ta osoba dowiaduje się, kto jest dziwką.",

    "pastor": "**Pastor (Miasto)** co noc (również zerowej nocy) wybiera osobę, którą chce wyspowiadać i dowiaduje "
              "się, z jakiego ugrupowania jest ta osoba. Frakcje jednoosobowe traktowane są jako Miasto. Osoba "
              "spowiadana nie wie, że została wyspowiadana.",

    "dobryrew": "**Dobry rewolwerowiec (Miasto)** Pojedynek z udziałem rewolwerowca oraz nierewolwerowca rozgrywany "
                "jest normalnie, jednak, jeżeli jego wynik jest inny niż zwycięstwo rewolwerowca, Manitou ogłasza, "
                "że i tak zwyciężył rewolwerowiec - wszyscy dowiadują się, że dana osoba jest rewolwerowcem, "
                "choć niekoniecznie - którym. Pojedynek z udziałem dwóch rewolwerowców przebiega dokładnie tak, "
                "jak pojedynek dwóch nierewolwerowców.",

    "opój": "**Opój (Miasto)** może dwa razy w trakcie gry wybrać osobę, z którą chce pójść się napić. Ta osoba nie "
            "będzie się budzić tej nocy, jednakże można ją zabić, przeszukać czy w jakiś inny sposób na nią "
            "oddziaływać.",

    "ochroniarz": "**Ochroniarz (Miasto)** co noc wybiera osobę, którą chroni. Ta osoba nie może tej nocy zostać "
                  "zabita, (choć może być okradana, spowiadana, spita, etc.). Ochroniarz nie może ochraniać się sam, "
                  "musi też każdej nocy ochraniać inną osobę. Gdy ochroniarz zginie w nocy, ochrona przestaje "
                  "działać.",

    "poborcapodatkow": "**Poborca podatków (Miasto)** raz w trakcie gry może na podstawie zeznań majątkowych "
                       "dowiedzieć się, kto w danej chwili posiada posążek (informacji udziela mu Manitou). "
                       "Oczywiście położenie posążka może się w trakcie nocy zmienić. Poborca podatków nie dowiaduje "
                       "się kto ma posążek, gdy ma go Lucky Luke.",

    "lekarz": "**Lekarz (Miasto)** raz w trakcie gry może wskrzesić świeżo zmarłą osobę zanim zostanie odkryta jej "
              "karta. Dotyczy to osób zmarłych w pojedynkach oraz zabitych w nocy (nie powieszonych). Lekarz działa "
              "tajnie, tj. nikt nie dowiaduje się, że jest lekarzem - pytanie, czy lekarz chce zadziałać jest "
              "zadawane, gdy wszyscy mają zamknięte oczy.",

    "hazardzista": "**Hazardzista (Miasto)** raz w trakcie gry, drugiej nocy bądź później, może rozpocząć grę w "
                   "rosyjską ruletkę. Wskazuje palcem na osobę, z którą chce zagrać. Jeśli trafił na obywatela miasta"
                   "bądź Szulera - ginie. Jeśli nie - ginie wskazana przez niego osoba, zaś hazardzista wskazuje "
                   "kolejną. Jeśli hazardzista zdobędzie posążek przekazuje go osobie, wskazując którą zginął. "
                   "Jeśli ta osoba dotrzyma go do świtu, to miasto wygrywa.",

    "agentubezpieczeniowy": "**Agent ubezpieczeniowy (Miasto)** w dowolnym momencie gry agent ubezpieczeniowy może "
                            "ujawnić, że jest agentem ubezpieczeniowym (czyt. pokazać swoją kartę).",

    "sędzia": "**Sędzia (Miasto)** raz w trakcie gry może po rozstrzygniętym pojedynku i ogłoszeniu zwycięzcy ujawnić "
              "swoją kartę i samodzielnie ogłosić wynik pojedynku. Zdolność sędziego jest silniejsza od zdolności "
              "rewolwerowca (tj. sędzia może oznajmić, że pojedynek przegra rewolwerowiec). Sędzia nie może "
              "zadekretować remisu - musi wskazać jedną osobę, która zginie. Aby się ujawnić Sędzia używa `&wygr`, "
              "jeżeli doda po spacji pseudonim gracza i zrobi to w czasie rozstrzygnięcia pojedynku gracz ten zostaje "
              "zwycięzcą.",

    "uwodziciel": "**Uwodziciel (Miasto)** zerowej nocy wybiera osobę, którą chce uwieść. Ta osoba nie może działać "
                  "na szkodę uwodziciela - w szczególności nie może nawoływać do zabicia uwodziciela (ani w dzień, "
                  "ani w nocy), ani za tym głosować, musi głosować za uwodzicielem w pojedynkach, nie może ujawnić, "
                  "że została uwiedziona, jeśli byłoby to ze szkodą dla uwodziciela, etc.",

    "pijanysędzia": "**Pijany sędzia (Miasto)** raz w trakcie gry może po rozstrzygniętym pojedynku i ogłoszeniu "
                    "zwycięzcy ujawnić swoją kartę i samodzielnie ogłosić wynik pojedynku. Zdolność ta jest "
                    "silniejsza od zdolności rewolwerowca (tj. sędzia może oznajmić, że pojedynek przegra "
                    "rewolwerowiec). Nie może zadekretować remisu - musi wskazać jedną osobę, która zginie. Ponadto "
                    "może dwa razy w trakcie gry wybrać osobę, z którą chce pójść się napić. Ta osoba nie będzie się "
                    "budzić tej nocy, jednakże można ją zabić, przeszukać czy w jakiś inny sposób na nią oddziaływać. "
                    " (Pijany sędzia to postać, którą wprowadza się do gry, gdy jest za mało osób, żeby grać zarówno "
                    "z sędzią, jak i opojem). Aby się ujawnić Pijany Sędzia używa `&wygr`, jeżeli doda po spacji "
                    "pseudonim gracza i zrobi to w czasie rozstrzygnięcia pojedynku gracz ten zostaje zwycięzcą.",

    "kat": "**Kat (Miasto)** raz w ciągu gry może zabić wybraną osobę.",

    "herszt": "**Herszt (Bandyci)** bandy jest najwyższym rangą bandytą. On też na początku gry posiada posążek.",

    "mściciel": "**Mściciel (Bandyci)** raz w trakcie gry może zabić w nocy wybraną osobę.",

    "złodziej": "**Złodziej (Bandyci)** może raz w trakcie gry próbować ukraść posążek. Wybiera osobę, którą chce "
                "okraść, i o ile ta osoba ma posążek, przejmuje go.",

    "złyrew": "**Zły rewolwerowiec (Bandyci)** pojedynek z udziałem rewolwerowca oraz nierewolwerowca rozgrywany jest "
              "normalnie, jednak, jeżeli jego wynik jest inny niż zwycięstwo rewolwerowca, Manitou ogłasza, "
              "że i tak zwyciężył rewolwerowiec - wszyscy dowiadują się, że dana osoba jest rewolwerowcem, "
              "choć niekoniecznie - którym. Pojedynek z udziałem dwóch rewolwerowców przebiega dokładnie tak, "
              "jak pojedynek dwóch nierewolwerowców.",

    "szantażysta": "**Szantażysta (Bandyci)** zerowej nocy wybiera osobę, którą chce szantażować. Ta osoba nie może "
                   "działać na szkodę szantażysty - w szczególności nawoływać do zabicia szantażysty (ani dzień, "
                   "ani w nocy), ani za tym głosować, musi głosować za szantażystą w pojedynkach, nie może ujawnić, "
                   "że została zaszantażowana, jeśli byłoby to ze szkodą dla szantażysty, etc.",

    "szuler": "**Szuler (Bandyci)** może raz w trakcie gry wybrać osobę, z którą będzie grał. Ta osoba nie będzie się "
              "budzić tej nocy, jednakże można ją zabić, przeszukać czy w jakiś inny sposób na nią oddziaływać. "
              "Ponadto, jeśli ta osoba posiada posążek, przejmuje go (wygrywając w karty) szuler.",

    "bandyta": "**Bandyta nie ma specjalnych zdolności.",

    "wódz": "**Wódz Indian (Indianie)** jest najwyższym rangą Indianinem.",

    "szaman": "**Szaman (Indianie)** raz w trakcie gry może wpaść w trans i poznać kartę jednej osoby.",

    "szamanka": "**Szamanka (Indianie)** raz w trakcie gry może podłożyć komuś truciznę. W wybranym przez Manitou "
                "momencie następnego dnia, (ale przed głosowaniami o przeszukiwaniu) ta osoba robi się zielona na "
                "twarzy i ginie.",

    "samotnykojot": "**Samotny kojot (Indianie)** Jeśli samotny kojot jest jedynym aktywnym Indianinem, "
                    "zabija dodatkowo jedną osobę.",

    "wojownik": "**Wojownik (Indianie)** raz w ciągu gry może dodatkowo zabić jedną osobę.",

    "płonącyszał": "**Płonący szał (Indianie)** Jeżeli danej nocy Indianie przejęli posążek, to zabija dodatkowo "
                   "jedną osobę.",

    "lornecieoko": "**Lornecie oko (Indianie)** może raz w trakcie gry dowiedzieć się, gdzie znajduje się posążek. "
                   "Oczywiście do następnego ruchu Indian posążek może się przemieścić.",

    "cichastopa": "**Cicha stopa (Indianie)** Jeżeli cicha stopa posiada posążek, może podłożyć go wybranej osobie. "
                  "Ta osoba jest traktowana jak właściciel posążka (tj. np., jeśli zostanie przeszukana, "
                  "to miasto wygra), jednakże nie wie o tym, że posążek posiada. Jeżeli ta osoba nie utraci posążka "
                  "do kolejnego ruchu Indian, cicha stopa może odebrać posążek.",

    "indianin": "**Indianin nie ma specjalnych zdolności.",

    "wielkiufol": "**Wielki Ufol (Ufoki)** jest najwyższym rangą ufolem.",

    "zielonamacka": "**Zielona Macka (Ufoki)** może raz w trakcie gry zabić wybraną osobę.",

    "detektor": "**Detektor (Ufoki)** co noc wybiera osobę, od której rozpoczyna detekcję. Jeżeli ta osoba ma "
                "posążek, dowiaduje się tego. Jeśli nie, to detektor dowiaduje się, w którym z dwóch łuków okręgu, "
                "na którym siedzą gracze, znajduje się posążek (jeden koniec łuku wyznaczany jest przez badaną osobę, "
                "drugi przez detektora).",

    "pożeraczumysłów": "**Pożeracz Umysłów (Ufoki)** co noc poznaje kartę wybranej osoby.",

    "purpurowaprzyssawka": "**Purpurowa przyssawka (Ufoki)** może raz w trakcie gry próbować ukraść posążek. Wybiera "
                           "osobę, którą chce przyssać, i o ile ta osoba ma posążek, przejmuje go.",

    "ufol": "**Ufol nie ma specjalnych zdolności.",

    "niewolnikkali": "**Niewolnik Kali (Murzyni)** każdej nocy wybiera sobie pana i dowiaduje się jaką on ma kartę. "
                     "Poza tym zgodnie ze swoją znaną zasadą, nie ma nic przeciwko temu, żeby Kali kradł – dwa razy w "
                     "trakcie gry może próbować ukraść swojemu panu posążek. O ile jego pan ma posążek, przejmuje go.",

    "sprzątaczka": "**Sprzątaczka (Murzyni)** każdej nocy sprząta w sufit(n/10)+1 domach, gdzie n to liczba żyjących "
                   "osób. Wybiera maksymalnie tyle osób i dowiaduje się czy któraś z nich ma posążek (nie dowiaduje "
                   "się która).",

    "kaszabara": "**Kaszabara (Bogowie)** bóg nieprzydatnych i nieudowodnionych twierdzeń. Co noc kogoś próbuje "
                 "opętać. Udaje mu się z prawdopodobieństwem 75%. Osoba opętana nie wie, że jest opętana, ale jeśli w "
                 "ciągu doby dostanie posążek składa go w ofierze Kaszabarze, który w ten sposób go przejmuje.",

    "chorągiew": "**Chorągiew (Bogowie)** bogini wymuszania przekrętów finansowych, biurokracji i utrudniania życia. "
                 "Co  noc może pojawić się w formie koszmaru jednej osobie, w którym ją przesłuchuje jedną osobę. "
                 "Osoba przesłuchiwana poznaje Chorągiew. Jeżeli zgodzi się na współpracę to Chorągiew dowiaduje się "
                 "jaką ma kartę i czy ona i któryś z jej sąsiadów ma posążek. Jeśli się nie zgodzi osoba "
                 "przesłuchiwana już się nie obudzi z tego  koszmaru – umiera na zawał serca.",

    "bezimienny": "**Bezimienny (Bogowie)** Nikt nie pamięta także czego jest bogiem. Złośliwi twierdzą, że sklerozy. "
                  "Raz w ciągu gry może wykonać dodatkowy strzał (który podobnie jak normalny strzał udaje się z "
                  "prawdopodobieństwem 75%).  Ponadto jeśli posiada posążek może go podarować dowolnie wybranej "
                  "osobie. Manitou informuje tę osobę i mówi jaka frakcja przejęła posążek.",

    "kardynał": "**Kardynał (Inkwizycja)** jest liderem Inkwizytorów",

    "misjonarz": "**Misjonarz (Inkwizycja)** każdej nocy może sprawdzić, czy dana osoba jest heretykiem. Dodatkowo "
                 "raz na grę może przeszukać osobę sprawdzaną",

    "spowiednik": "**Spowiednik (Inkwizycja)** raz na grę może poznać kartę wybranej osoby. Jeśli chce, może tę osobę "
                  "natychmiast zabić",

    "biskup": "**Biskup (Inkwizycja)** raz na grę może ujawnić się, aby zabić wybranego gracza (również w nocy). Aby "
              "się ujawnić i zabić użyj `&spal NICK`",

    "ministrant": "**Ministrant (Inkwizycja)** zna wyniki sprawdzania przez pastora. Po jego śmierci może samemu raz "
                  "na grę sprawdzić frakcję wybranego gracza. Może sprawdzić gracza będącego w więzieniu.",

    "anioł": "**Anioł (Inkwizycja)** przejmuje kartę pierwszego zabitego w nocy Inkwizytora innego niż Biskup",

    "wikary": "**Wikary (Inkwizycja)** co noc może dowiedzieć się, czy dana osoba należy do frakcji posiadaczy posążka",

    "luckyluke": "**Lucky Luke** Jest rewolwerowcem. Ponadto raz w ciągu gry może zabić wybraną osobę. Każdej nocy po "
                 "swojej turze dowiaduje się kto ma aktualnie posążek. Raz w ciągu gry może zadeklarować, "
                 "że kogoś śledzi. Jeśli w ciągu doby ta osoba dostanie posążek Luke go automatycznie przejmuje.",

    "janosik": "**Janosik** raz w ciągu gry macha :axe:, gdy powiesi się go w trakcie dnia janosik wygrywa.",

    "lusterko": "**Lusterko** każdej nocy może zobaczyć kartę wybranej osoby. Raz w ciągu gry może skopiować zdolność "
                "właśnie sprawdzonej przez siebie osoby na następną noc i dzień. Raz w ciągu gry Lusterko może wyzwać "
                "Manitou. Musi wtedy wymienić poprawnie kim jest każda grająca osoba. Jeśli mu się uda - wygrywa, "
                "jeśli nie - umiera.",

    "miastowy": "**Miastowy (Miasto)** zwykły mieszkaniec miasta",

    "detektyw": "**Detektyw (Miasto)** co noc może sprawdzić frakcję jednej osoby",

    "cattani": "**Cattani (Miasto)** co noc może sprawdzić frakcję jednej osoby",

    "komisarz": "**Komisarz (Miasto)** co noc może sprawdzić frakcję jednej osoby",

    "kurtyzana": "**Kurtyzana (Miasto)** co noc śpi z  jedną osobą, jeśli trafi na osobę\
zastrzeloną przez mafię ta osoba nie ginie",

    "wariat": "**Wariat (Miasto)** w momencie śmierci wybiera jedną osobę, która ginie razem z nim",

    "drwal": "**Drwal (Miasto)** w momencie śmierci wybiera jedną osobę, która ginie razem z nim",

    "mafiozo": "**Mafiozo (Mafia)** szeregowy członek mafii",

    "boss": "**Boss (Mafia)** szef mafii",
}

factions = {
    "szeryf": "Miasto",

    "burmistrz": "Miasto",

    "dziwka": "Miasto",

    "pastor": "Miasto",

    "dobryrew": "Miasto",

    "opój": "Miasto",

    "ochroniarz": "Miasto",

    "poborcapodatkow": "Miasto",

    "lekarz": "Miasto",

    "hazardzista": "Miasto",

    "agentubezpieczeniowy": "Miasto",

    "sędzia": "Miasto",

    "uwodziciel": "Miasto",

    "pijanysędzia": "Miasto",

    "kat": "Miasto",

    "miastowy": "Miasto",

    "herszt": "Bandyci",

    "mściciel": "Bandyci",

    "złodziej": "Bandyci",

    "złyrew": "Bandyci",

    "szantażysta": "Bandyci",

    "szuler": "Bandyci",

    "bandyta": "Bandyci",

    "wódz": "Indianie",

    "szaman": "Indianie",

    "szamanka": "Indianie",

    "samotnykojot": "Indianie",

    "wojownik": "Indianie",

    "płonącyszał": "Indianie",

    "lornecieoko": "Indianie",

    "cichastopa": "Indianie",

    "indianin": "Indianie",

    "wielkiufol": "Ufoki",

    "zielonamacka": "Ufoki",

    "detektor": "Ufoki",

    "pożeraczumysłów": "Ufoki",

    "purpurowaprzyssawka": "Ufoki",

    "ufol": "Ufoki",

    "niewolnikkali": "Murzyni",

    "sprzątaczka": "Murzyni",

    "kaszabara": "Bogowie",

    "chorągiew": "Bogowie",

    "bezimienny": "Bogowie",

    "kardynał": "Inkwizycja",

    "misjonarz": "Inkwizycja",

    "spowiednik": "Inkwizycja",

    "biskup": "Inkwizycja",

    "ministrant": "Inkwizycja",

    "anioł": "Inkwizycja",

    "wikary": "Inkwizycja"
}


def refactor(role: str) -> str:
    return role.replace(" ", "").replace("_", "").replace("-", "").lower()


def get_role_details(role: str, no: str = 'Nie ma takiej postaci') -> str:
    """Returns :param role: details with bold :param no:
    if details don't exist
    """
    c = refactor(role)
    return roles.get(c, f"**{no}**")


def give_faction(role: str) -> str:
    """Returns original faction"""
    c = refactor(role)
    if c not in factions:
        return role
    return factions[c]


def send_faction(role: str) -> str:
    """Returns original faction in bold format eventually with colon"""
    c = refactor(role)
    if c not in factions:
        return "**{}**".format(role)
    return "**{}:**".format(factions[c])


def get_faction(role: str) -> str:
    """Replaces one-pearson factions with Town"""
    c = refactor(role)
    if c not in factions:
        return "Miasto"
    return factions[c]


def print_list(role_list: List[str]) -> str:
    team = ""
    faction_count = defaultdict(int)
    for role in role_list:
        faction_count[send_faction(role)] += 1
    prev_faction = None
    for role in sorted(role_list,
                       key=lambda r: (list(roles.keys()) + list(map(refactor, role_list))).index(refactor(r))):
        # sort by order of roles list, `+ role_list` needed if some role not in rolse
        faction = send_faction(role)
        role = role.replace("-", " ")
        role = role.replace("_", " ")
        if faction == prev_faction:
            team += "{}\n".format(role)
        else:
            prev_faction = faction
            team += "\n{}".format(faction.replace('_', " "))
            if faction.endswith(":**"):
                team += " **({})**\n".format(faction_count[send_faction(role)])
                team += "{}\n".format(role.replace('_', " "))
            else:
                team += "\n"
    return team
