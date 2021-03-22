from converters import converter
from utility import *


class Duel:
    def __init__(self):
        self.duel = False
        self.duels_result = False
        self.duels_today = 0
        self.dared = {}
        self.daring = {}
        self.duels_order = []
        self.duels_queue = []
        self.participants = ()
        self.duelers = ()

    def add_dare(self, author, member):
        if self.duels_today == bot.game.duels:
            raise InvalidRequest("Nie ma więcej pojedynków tego dnia")
        if member not in self.dared:
            self.dared[member] = []
        if author not in self.daring:
            self.daring[author] = []
        try:
            if author in self.dared[member] or member in self.dared[author]:
                raise InvalidRequest("Wyzwałeś(-aś) już tego gracza lub zostałeś(-aś) wyzwany(-a)")
        except KeyError:
            pass
        self.dared[member].append(author)
        self.daring[author].append(member)
        self.duels_order.append(member)

    def remove_dare(self, author):
        if author not in self.duels_order:
            raise InvalidRequest("Nie zostałeś(-aś) wyzwany(-a)")
        if author in self.duels_queue:
            raise InvalidRequest("Masz już oczekujący pojedynek")
        member = self.dared[author][0]
        self.daring[member].remove(author)
        self.dared[author].pop(0)
        self.duels_order.remove(author)
        '''del self.daring[member][self.daring[member].index(author)]
        del self.dared[author][0]
        del self.duels_order[self.duels_order.index(author)]'''
        return "**{}** odrzucił(-a) pojedynek od **{}**".format(author.display_name, member.display_name)

    def remove_member(self, member):  # , role_cls):#use on die
        # member = role_cls.player.member
        if member in self.daring:
            for player in self.daring[member]:
                if self.dared[player].index(member) == 0 and player in self.duels_queue:
                    self.duels_queue.remove(player)
                target = self.dared[player].index(member)
                num = 0
                for i, person in enumerate(self.duels_order):
                    if person == player:
                        if num == target:
                            self.duels_order.pop(i)
                            break
                        num += 1
                self.dared[player].remove(member)
            del self.daring[member]
        if member in self.dared:
            for player in self.dared[member]:
                self.daring[player].remove(member)
            del self.dared[member]
        while self.duels_queue.count(member) > 0:
            self.duels_queue.remove(member)
        while self.duels_order.count(member) > 0:
            self.duels_order.remove(member)
        '''if role_cls in self.duelers and self.duel:
          await self.interrupt()
          await get_town_channel().send("Pojedynek został anulowany z powodu śmierci jednego z pojedynkujących")
        await self.if_next()'''

        # print("\n\n\n\ndared", self.dared.items())
        # print('daring', self.daring.items())
        # print('queue',self.duels_queue)
        # print('order',self.duels_order)

    def accept(self, author):
        if author not in self.duels_order:
            raise InvalidRequest("Nie zostałeś wyzwany")
        if self.duels_today == bot.game.duels:
            raise InvalidRequest("Nie ma więcej pojedynków tego dnia")
        if author in self.duels_queue:
            raise InvalidRequest("Masz już oczekujący pojedynek. Następny ci nie ucieknie")
        index = 0
        for member in self.duels_order:
            if member != author and member in self.duels_queue:
                index += 1
            elif member == author:
                break
        self.duels_queue.insert(index, author)
        return "**{}** przyjął pojedynek od **{}**".format(author.display_name, self.dared[author][0].display_name)

    async def if_start(self, author, member):
        c = "**{}** wyzwał **{}** na pojedynek.\n".format(author.display_name, member.display_name)
        try:
            if bot.game.role_map["Szeryf"].alive:
                c += "<@{}> czy przyjmujesz? Użyj `&przyjmuję` lub `&odrzucam`".format(member.id)
                await get_town_channel().send(c)
            else:
                c += "Szeryf nie żyje, więc pojedynek jest automatycznie przyjęty"
                self.duels_queue.append(member)
                await get_town_channel().send(c)
                await self.if_next(True)
        except KeyError:
            c += "Szeryf nie gra, więc pojedynek jest automatycznie przyjęty"
            self.duels_queue.append(member)
            await get_town_channel().send(c)
            await self.if_next(True)

    def remove_duel(self):
        member = self.duels_queue[0]
        self.daring[self.dared[member][0]].remove(member)
        self.dared[member].pop(0)
        self.duels_order.remove(member)
        self.duels_queue.pop(0)
        '''del self.daring[self.dared[member][0]][self.daring[self.dared[member][0]].index(member)]
        del self.dared[member][0]
        del self.duels_order[self.duels_order.index(member)]
        del self.duels_queue[0]'''

    async def if_next(self, write=False):
        if len(self.duels_queue) > 0 and self.duels_order[0] == self.duels_queue[
            0] and self.duels_today < bot.game.duels:
            member = self.duels_queue[0]
            gracz = self.dared[member][0]
            await self.start_duel(gracz, member)
        elif write:
            mess = "**Ten pojedynek nie może się teraz rozpocząć**\nAktualne wyzwania do rozpatrzenia:\n" + self.dares_print()
            await get_town_channel().send(mess)

    def dares_print(self):
        c = {}
        for key in self.dared.keys():
            c[key] = self.dared[key].copy()
        mess = ''
        q = self.duels_queue.copy()
        for player in self.duels_order:
            mess += "**{}** vs. **{}**".format(c[player][0].display_name, player.display_name)
            if len(q) > 0 and player == q[0]:
                mess += " - *przyjęte*"
                q.pop(0)
            mess += "\n"
            c[player].pop(0)
        if len(self.duels_order) == 0:
            mess = 'Nie ma wyzwań'
        mess += "\nPozostało {} pojedynków".format(bot.game.duels - self.duels_today)
        return mess

    async def start_duel(self, agresor, victim):
        self.remove_duel()
        self.duelers = (
        bot.game.player_map[agresor].role_class, bot.game.player_map[victim].role_class)
        self.participants = (agresor, victim)
        # print(self.participants)
        self.duel = True
        c = "Rozpoczynamy pojedynek:\n<:legacy_gun:{}> **{}** vs. :shield:**{}**".format(GUN_ID, agresor.display_name,
                                                                                         victim.display_name)
        await get_town_channel().send(c)

    async def interrupt(self):
        if not self.duel:
            self.remove_dare(self.duels_order[0])
            return "Manitou usunął wyzwanie"
        winner_role = get_duel_winner_role()
        loser_role = get_duel_loser_role()
        self.duel = False
        self.duelers = ()
        self.duels_result = False
        bot.game.voting_allowed = False
        for player in self.participants:
            await player.remove_roles(winner_role, loser_role)
        self.participants = ()
        return "Manitou anulował trwający pojedynek"

    def duel_remember_nicks(self):
        self.data = {member.display_name: member for member in self.participants}

    async def result_duel(self, ctx, votes: dict):
        votes = votes.items()
        results = []

        for member, vote in filter(lambda v: v[0] != "Wstrzymuję_Się", votes):
            member = self.data[member]
            rev = 'revoling' in bot.game.player_map[member].role_class.my_activities
            results.append((member, len(vote) + rev * 100000))
        results = sorted(results, key=lambda r: r[1], reverse=True)
        # print(results)
        self.duels_result = True
        if results[0][1] != results[1][1]:
            self.winner = [bot.game.player_map[results[0][0]].role_class]
            c = "Pojedynek ma wygrać **{}**. Zginąć ma **{}**".format(results[0][0].display_name,
                                                                      results[1][0].display_name)
        elif results[0][1] % 100000 == 0:
            self.winner = list(self.duelers)
            c = "W wyniku pojedynku nikt nie ginie. *(na razie)*"
        else:
            self.winner = []
            c = "W wyniku pojedynku mają zginąć obaj pojedynkujący się"
        for player in self.duelers:
            if player in self.winner:
                await player.player.member.add_roles(get_duel_winner_role())
            else:
                await player.player.member.add_roles(get_duel_loser_role())
        await get_town_channel().send(c)

    async def end_duel(self, ctx):
        if not self.duels_result:
            raise InvalidRequest("Najpierw musisz przeprowadzić głosowanie na zwycięzcę")
        loser_role = get_duel_loser_role()
        winner_role = get_duel_winner_role()
        if len(set(loser_role.members + winner_role.members)) != len(loser_role.members + winner_role.members):
            raise InvalidRequest("Ktoś ma rozdwojenie jaźni - jest zwycięzcą i przegranym. Manitou musi to naprawić.")
        for member in get_duel_loser_role().members:
            if member not in self.participants:
                raise InvalidRequest("{} jakimś cudem przegrał pojedynek nie grając".format(member.display_name))
        for member in get_duel_winner_role().members:
            if member not in self.participants:
                raise InvalidRequest("{} jakimś cudem wygrał pojedynek nie grając".format(member.display_name))
        self.winner = []
        for member in self.duelers:
            if member.player.member in get_duel_winner_role().members:
                self.winner.append(member)
        self.duel = False
        self.duels_result = False
        bot.game.voting_allowed = False
        self.duels_today += 1
        if len(self.winner) == 1:
            c = "Pojedynek wygrywa **{}**".format(self.winner[0].player.member.display_name)
        elif len(self.winner) == 2:
            c = "W wyniku pojedynku nikt nie ginie"
        try:
            await get_town_channel().send(c)
        except NameError:
            pass
        for player in self.participants:
            await player.remove_roles(winner_role, loser_role)
        for player in self.duelers:
            if player not in self.winner:
                await player.die("duel")
        self.duelers = ()
        self.participants = ()
        await ctx.message.add_reaction('✅')
        await self.if_next()

    async def change_winner(self, member):
        for player in self.participants:
            await player.remove_roles(get_duel_winner_role(), get_duel_loser_role())
        for player in self.participants:
            if player == member:
                await player.add_roles(get_duel_winner_role())
            else:
                await player.add_roles(get_duel_loser_role())
