import random

import globals
from utility import *


class Hang:
    def __init__(self, candidates):
        self.candidates = candidates
        self.hang = None
        self.to_hang = []
        self.hanged = None
        self.hang_final = False
        self.change = False

    async def if_hang(self, ctx, votes):
        if len(votes["Tak"]) > len(votes["Nie"]):
            self.hang = True
            c = "Decyzją miasta wieszamy"
        else:
            self.hang = False
            c = "Miasto idzie spać"
        await get_town_channel().send(c)
        await get_glosowania_channel().send(c)

    async def hang_sumarize(self, ctx, votes):
        results = []
        for member, vote in sorted(votes, key=lambda v: len(v[1]),
                                   reverse=True):
            results.append((await converter(ctx, member), len(vote)))
        i = 0
        self.to_hang = [results[0][0]]
        self.hang_final = True
        try:
            while results[i][1] == results[i + 1][1]:
                self.to_hang.append(results[i + 1][0])
                i += 1
        except IndexError:
            pass
        if len(self.to_hang) == 1:
            c = "Powieszony(-a) ma zostać **{}**".format(
                self.to_hang[0].display_name)
            self.hanged = self.to_hang[0]
            await self.hanged.add_roles(get_hanged_role())
        else:
            c = "Potrzebne jest głosowanie uzupełniające dla:\n"
            for member in self.to_hang:
                c += "**{}**\n".format(member.display_name)
        await get_town_channel().send(c)
        await get_glosowania_channel().send(c)

    async def hang_finalize(self, ctx):
        if len(get_hanged_role().members) > 1:
            await ctx.send("Powiesić można tylko jedną osobę")
            raise InvalidRequest
        self.hanged = None
        try:
            self.hanged = get_hanged_role().members[0]
            if self.hanged not in get_player_role().members:
                await ctx.send("**{}** jest wieszany, a nie gra".format(
                    member.display_name))
                raise InvalidRequest
        except IndexError:
            if not self.change:
                self.hanged = random.choice(self.candidates)
            else:
                c = "Nikt nie zostaje powieszony"
                await get_town_channel().send(c)
                await get_glosowania_channel().send(c)
                return
        c = "Powieszony(-a) zostaje **{}**".format(self.hanged.display_name)
        role = globals.current_game.player_map[self.hanged].role_class
        await get_town_channel().send(c)
        await get_glosowania_channel().send(c)
        await self.hanged.remove_roles(get_hanged_role())
        await role.die('hang')

    async def peace(self):
        self.change = True
        for member in get_hanged_role().members:
            await member.remove_roles(get_hanged_role())


class Search(Hang):
    def __init__(self):
        self.searchers = {}
        self.searched = {}
        self.to_search = []
        self.to_revote = []
        self.search = False
        self.search_final = False
        self.hang_time = False

    def add_report(self, author, gracz):
        if self.search:
            raise InvalidRequest("Nie można już zgłaszać")
        if gracz not in self.searched:
            self.searched[gracz] = []
        if author not in self.searchers:
            self.searchers[author] = []
        if gracz in self.searched and author in self.searched[gracz]:
            raise InvalidRequest("Zgłosiłeś już tego gracza")
        self.searched[gracz].append(author)
        self.searchers[author].append(gracz)
        # print("searchers\n", self.searchers.items())
        # print("searched\n", self.searched.items())

    def remove_report(self, author, gracz):
        if gracz not in self.searched or author not in self.searched[gracz]:
            raise InvalidRequest("Nie zgłosiłeś tego gracza")
        if self.search:
            raise InvalidRequest("Nie można już zgłaszać")
        del self.searched[gracz][self.searched[gracz].index(author)]
        del self.searchers[author][self.searchers[author].index(gracz)]
        if len(self.searched[gracz]) == 0:
            del self.searched[gracz]
        if len(self.searchers[author]) == 0:
            del self.searchers[author]
        # print("searchers\n", self.searchers.items())
        # print("searched\n", self.searched.items())

    def report_print(self):
        c = "__Zgłoszenia ({}):__\n".format(len(self.searched.keys()))
        for player, members in self.searched.items():
            c += "**{}** *przez* ".format(get_nickname(player.id)) + ", ".join(
                map(lambda m: get_nickname(m.id), members))
            c += "\n"
        c += "\nDo dyspozycji są {} przeszukania".format(
            globals.current_game.searches)
        return c

    def remove_member(self, gracz):
        try:
            for member in self.searched[gracz]:
                del self.searchers[member][self.searchers[member].index(gracz)]
                if len(self.searchers[member]) == 0:
                    del self.searchers[member]
            del self.searched[gracz]
        except KeyError:
            pass
        try:
            for member in self.searchers[gracz]:
                del self.searched[member][self.searched[member].index(gracz)]
                if len(self.searched[member]) == 0:
                    del self.searched[member]
            del self.searchers[gracz]
        except KeyError:
            pass

    async def search_summary(self, ctx, votes):
        results = []
        for member, vote in sorted(votes, key=lambda v: len(v[1]),
                                   reverse=True):
            results.append((await converter(ctx, member), len(vote)))
        ser_num = 1 + len(self.to_search)
        last = results[0][1]
        self.to_revote = [results[0][0]]
        for member, number in results[1:]:
            if number != last:
                if ser_num > globals.current_game.searches:
                    break
                self.to_search += self.to_revote
                self.to_revote = []
                last = number
                if ser_num == globals.current_game.searches:
                    break
            self.to_revote.append(member)
            ser_num += 1
        await self.search_end(self.to_search)

    async def search_end(self, searching):
        self.to_search = searching
        self.search_final = True
        c = "Przeszukani zostaną:\n"
        for member in self.to_search:
            c += "**{}**\n".format(member.display_name)
            await member.add_roles(get_searched_role())
        if len(self.to_revote) > 0:
            c += '\nPotrzebne jest dodatkowe głosowanie dla:\n'
            for member in self.to_revote:
                c += "**{}**\n".format(member.display_name)
        await get_town_channel().send(c)
        await get_glosowania_channel().send(c)

    async def search_finalize(self, ctx):
        self.hang_time = True
        if len(get_searched_role().members) > globals.current_game.searches:
            await ctx.send("Przeszukiwanych jest więcej niż przeszukań")
            raise InvalidRequest
        for member in get_searched_role().members:
            if member not in get_player_role().members:
                await ctx.send("**{}** jest przeszukiwany, a nie gra".format(
                    member.display_name))
                raise InvalidRequest
        self.to_search = list(get_searched_role().members)
        while len(self.to_search) < globals.current_game.searches:
            self.to_search.append(random.choice(
                list(set(get_player_role().members) - set(self.to_search))))
        c = "Przeszukani zostają:\n"
        for member in get_searched_role().members:
            c += "**{}**\n".format(member.display_name)
        await get_town_channel().send(c)
        await get_glosowania_channel().send(c)
        for member in get_searched_role().members:
            c = globals.current_game.statue.day_search(member)
            await get_town_channel().send(c)
            await get_glosowania_channel().send(c)
            await member.remove_roles(get_searched_role())
        Hang.__init__(self, self.to_search)
