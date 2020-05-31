can_refuse = ["Pijany_Sędzia", "Opój"]

activity_start = {
  "Szeryf":0,
  "Pijany_Sędzia":1,
  "Opój":1,
  "Pastor":0,
  "Dziwka":-1
}

role_activities = {
  "Sędzia":(-1,1,{"wins":1}),
  "Szeryf":(0,-1,{"arrest":-1}),
  "Pijany_Sędzia":(1,2,{"drink":2,"refuse":-1,"wins":1}),
  "Opój":(1,2,{"drink":2,"refuse":-1}),
  "Pastor":(0,-1,{"pasteur":-1}),
  "Dziwka":(-1,-1,{"dziw":1}),
  "Dobry_Rew":(-1,0,{"revoling":0}),
  "Zły_Rew":(-1,0,{"revoling":0}),
  "Janosik":(1,1,{"wave":1,"die":"hang_win"}),
  "Burmistrz":(-1,1,{"peace":1}),
  "Hazardzista":(2,1,{"refuse":-1, "play":-1, "die":"shooted", "refused":"Nikt nie ginie"}),
  "Mściciel":(1,1,{"refuse":-1, "kill":1, "refused":"Nikt nie ginie"}),
  "Wojownik":(1,1,{"refuse":-1, "kill":1, "refused":"Nikt nie ginie"}),
  "Zielona_Macka":(1,1,{"refuse":-1, "kill":1, "refused":"Nikt nie ginie"}),
  "Samotny_Kojot":(1,-1,{"kill":-1, "start":"lonewolf"}),
  "Płonący_Szał":(1,-1,{"kill":-1, "start":"todaychange"}),
  "Cicha_Stopa":(1, -1,{"refuse":-1, "plant":-1, "start":"has"}),
  "Złodziej":(1, 1, {"start":"unwork", "refuse":-1, "search":1, "refused":"Złodziej nie przejmuje posążka"}),
  "Purpurowa_Przyssawka":(1, 1, {"start":"unwork", "refuse":-1, "search":1, "refused":"Purpurowa_Przyssawka nie przejmuje posążka"}),
  "Szuler":(1, 1, {"refuse":-1, "cheat":1, "refused":"Szuler nie przejmuje posążka"}),
  "Szamanka":(1,1,{"refuse":-1, "herb":1}),
  "Lornecie_Oko":(1,1,{"refuse":-1, "who":1}),
  "Detektor":(1, -1, {"detect":-1}),
  "Pożeracz_Umysłów":(1, -1, {"eat":-1}),
  "Szaman":(1,1,{"refuse":-1,"szam":1,"refused":"Szaman nie sprawdzał tej nocy"}),
  "Wikary":(1, -1, {"holders":-1, "die":"angelize"}),
  "Ministrant":(0, 1, {"start":"pastored", "pasteur":1, "die":"angelize"}),
  "Misjonarz":(1, -1, {"start":"unwork", "heretic":-1, "research":1, "refuse":-1, "die":"angelize", "refused":"Misjonarz nie przejmuje posążka"}),
  "Spowiednik":(1, 1, {"eat":1, "finoff":1, "refuse":-1, "die":"angelize"}),
  "Biskup":(1, 1, {"burn":1}),
  "Lusterko":(1, -1, {"start":"uncopy", "mirror":-1, "copy":1}),
  "Lucky_Luke":(1, -1, {"start":"look", "revoling":0, "search":-1, "kill":1, "follow":1, "who":-1, "refused":"Lucky_Luke nie przejmuje posążka"})
}

role_abilities = {
  "inqui_change_on_death":"Anioł",
  "decline_duels":"Szeryf"
}

def get_activity(name, obj):
  activities = {
    "arrest":[obj.if_active, obj.if_not_prev, obj.sleep, obj.protect, obj.meantime_send, obj.search, obj.mark_arrest, obj.deactivate],
    "wins":[obj.if_day, obj.if_duel, obj.reveal, obj.change_duel],
    "hang_win":[obj.hang_win],
    "peace":[obj.if_day, obj.reveal, obj.peace_make, obj.if_hang_time],
    "dziw":[obj.if_active, obj.if_not_self, obj.check_role, obj.deactivate],
    "pasteur":[obj.if_active, obj.set_use, obj.check_faction, obj.deactivate],
    "drink":[obj.if_active, obj.if_protected, obj.deactivate, obj.sleep, obj.set_use],
    "refuse":[obj.if_active, obj.deactivate, obj.refusal],
    "play":[obj.if_active, obj.if_not_self, obj.if_protected, obj.unrefuse, obj.if_better, obj.kill, obj.special_search, obj.alone],
    "kill":[obj.if_active, obj.if_worked, obj.if_protected, obj.kill_send, obj.kill, obj.search, obj.set_use, obj.deactivate, obj.reactivate_luke],
    "shooted":[obj.if_shooted, obj.has, obj.present],
    "lonewolf":[obj.lone],
    "todaychange":[obj.got_today],
    "has":[obj.has],
    "plant":[obj.if_active, obj.if_protected, obj.if_not_self, obj.plant, obj.deactivate],
    "search":[obj.if_active, obj.if_not_worked, obj.if_protected, obj.search_send, obj.search, obj.set_use, obj.deactivate, obj.reactivate_luke, obj.make_it_work],
    "unwork":[obj.unwork],
    "cheat":[obj.if_active, obj.if_protected, obj.if_not_self, obj.search, obj.sleep, obj.set_use, obj.deactivate],
    "szam":[obj.if_active, obj.if_not_self, obj.check_role, obj.set_use, obj.szaman_yes, obj.deactivate],
    "herb":[obj.if_active, obj.if_not_self, obj.herb, obj.set_use, obj.deactivate],
    "eat":[obj.if_active, obj.check_role, obj.set_use, obj.deactivate_if],
    "who":[obj.if_active, obj.if_worked, obj.who, obj.set_use, obj.deactivate],
    "detect":[obj.if_active, obj.if_not_self, obj.detect, obj.deactivate],
    "holders":[obj.if_active, obj.if_holders, obj.deactivate],
    "angelize":[obj.if_night, obj.angel_alive, obj.angelize],
    "pastored":[obj.who_pastored],
    "heretic":[obj.if_active, obj.if_not_worked, obj.check_heresis, obj.deactivate_cond],
    "research":[obj.if_active, obj.if_member, obj.if_protected, obj.search, obj.set_use, obj.deactivate],
    "finoff":[obj.if_active, obj.if_member, obj.if_protected, obj.kill, obj.search, obj.deactivate],
    "burn":[obj.nonzero, obj.if_not_sleeped, obj.if_protected, obj.statue_none, obj.reveal, obj.kill, obj.search],
    "mirror":[obj.if_active, obj.if_not_worked, obj.if_not_self, obj.check_role, obj.make_it_work, obj.mirror_send, obj.deactivate_cond],
    "copy":[obj.if_active, obj.if_worked, obj.set_use, obj.copy],
    "uncopy":[obj.unwork, obj.unchange],
    "look":[obj.unwork, obj.unfollow, obj.luke_win],
    "follow":[obj.if_active, obj.if_worked, obj.if_not_self, obj.follow, obj.deactivate, obj.follow_send, obj.reactivate_luke]
  }
  return [] if name not in activities else activities[name]