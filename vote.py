import utility
from utility import InvalidRequest


class Vote:
    def __init__(self):
        self.voting_allowed = False
        self.voting_options = []
        self.voting_results = {}
        self.players_voted = set()
        self.required_votes = 0
        self.voting_required = False
        self.not_voting = []

    def voting_in_progress(self):
        return self.voting_allowed

    def register_vote(self, player, votes):
        if player not in list(
                utility.get_player_role().members) or player in list(
                utility.get_dead_role().members):
            raise InvalidRequest("Nie grasz teraz")
        if player in self.not_voting:
            raise InvalidRequest("Nie możesz teraz głosować")
        votes_std = []
        # votes_STD to lista poprawnych głosów danego gracza
        prev_std = None
        for vote in votes:
            vote_std = None
            for option in self.voting_options:
                std = option[-1]
                for variant in option:
                    if vote.lower() == variant.lower() and not prev_std == std:
                        vote_std = std
                        prev_std = std
                    elif vote.lower() == variant.lower() and prev_std == std:
                        raise InvalidRequest(
                            "Nie możesz zagłosować wielokrotnie na jedną opcję")
            if vote_std is None:
                raise InvalidRequest("Nie ma opcji " + vote)
            votes_std.append(vote_std)
        if len(votes_std) != self.required_votes:
            raise InvalidRequest("Zła liczba głosów")
        self.voting_results[player.id] = votes_std
        self.players_voted.add(player)
        not_voted = list(set(utility.get_player_role().members) - set(
            list(utility.get_dead_role().members)) - self.players_voted - set(
            self.not_voting))
        return (votes_std, not_voted)

    def summarize_votes(self):
        summary = {}
        for option in self.voting_options:
            summary[option[-1]] = []
        for player, votes in self.voting_results.items():
            for vote in votes:
                summary[vote].append(player)
        return summary

    def new_voting(self, required_votes, voting_options, not_voting):
        self.voting_allowed = True
        self.required_votes = required_votes
        self.voting_options = voting_options
        self.voting_results = {}
        self.players_voted = set()
        self.voting_required = True
        self.not_voting = not_voting
