FACTION_FEATURES = {
  "START_WITH_STATUE":"Bandyci"
}

factions_roles = {
  "Bandyci":["Herszt","Mściciel","Złodziej","Zły_Rew","Szantażysta","Szuler"],
  "Indianie":["Wódz","Szaman","Szamanka","Samotny_Kojot", "Wojownik", "Płonący_Szał","Lornecie_Oko","Cicha_Stopa"],
  "Ufoki":["Wielki_Ufol","Zielona_Macka","Detektor","Pożeracz_Umysłów","Purpurowa_Przyssawka"],
  "Inkwizycja":["Kardynał","Biskup","Misjonarz","Spowiednik","Wikary","Anioł","Ministrant"],
  "Bogowie":["Kaszabara","Chorągiew","Bezimienny"],
  "Murzyni":["Kali","Sprzątaczka"]
}

f_actions = {
  "Bandyci":[("search", False), ("hold", True)],
  "Indianie":[("kill", None), ("hold", True), ("kill", True), ["Samotny_Kojot"], ["Płonący_Szał"], ["Szamanka"], ["Wojownik"], ["Cicha_Stopa"]],
  "Ufoki":[["Detektor"], ["Pożeracz_Umysłów"], ("search", False),["Zielona_Macka"], ["Purpurowa_Przyssawka"], ("signal", True), ("hold", True)],
  "Inkwizycja":[["Wikary"], ["Misjonarz"], ["Spowiednik"], ("search", False), ("check", True), ("hold", True)]
}


def get_activity(obj, operation):
  f_activities = {
    "search":[obj.if_protected, obj.f_search, obj.statue_alone],
    "hold":[obj.can_hold, obj.change_holder],
    "kill":[obj.if_protected, obj.kill, obj.f_search, obj.statue_alone],
    "signal":[obj.signal],
    "check":[obj.check_role],
    "sphold":[obj.can_hold, obj.change_holder, obj.bishop_back],
    "Indianie start":[obj.can_unplant, obj.unplant]
  }
  return f_activities[operation]

f_coms = {
  "search":"W celu dokonania przeszukania lider frakcji musi użyć komendy `&szukaj NICK`",
  "hold":"W celu ustalenia posiadacza posążka lider frakcji musi użyć `&pos NICK`. Jeśli posiadacz się nie zmienia nie jest konieczne użycie komendy.",
  "kill":"W celu zabicia gracza lider frakcji musi użyć polecenia `&zabij NICK`",
  "check":"W celu sprawdzenia postaci lider frakcji musi użyć `&karta NICK`",
  "Bandyci":"Bandyci nie przejmuje(-ą) posążka",
  "Indianie":"Nikt nie ginie",
  "Ufoki":"Ufoki nie przejmuje(-ą) posążka",
  "Inkwizycja":"Inkwizycja nie przejmuje(-ą) posążka"
}

f_coms_manit = {
  "search":"{} otrzymali instrukcje do przeszukania",
  "hold":"{} otrzymali instrukcje do przekazania posążka",
  "kill":"{} otrzymali instrukcje do zabójstwa",
  "check":"{} otrzymała instrukcje do sprawdzenia karty"
}

f_coms_manit_end = {
  "search":"{} przeszukali {}",
  "kill":"{} zabili {}",
  "hold":"{} przekazali posążek {}",
  "sphold":"{} przekazali posążek {}",
  "check":"{} sprawdziła {}"
}