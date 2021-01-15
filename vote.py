from typing import List, Tuple, Optional, Dict, Set

import discord

from errors import AuthorNotPlaying, VotingNotAllowed, WrongValidVotesNumber
from utility import get_player_role


class Vote:
    def __init__(self, required_votes: int, voting_options: List[List[str]],
                 not_voting: List[discord.Member], vote_type: Optional[str] = None):
        self.required_votes = required_votes
        self.voting_options = voting_options
        self.voting_results: Dict[int, List[str]] = {}
        self.players_voted: Set[discord.Member] = set()
        self.not_voting = not_voting
        self.vote_type = vote_type
        self.summary: Dict[str, List[discord.Member]] = dict(zip((option[-1] for option in self.voting_options),
                                                             [[]] * len(self.voting_options)))

    def register_vote(self, player: discord.Member, votes: List[str]) -> Tuple[List[str], bool]:
        if player not in get_player_role().members:
            raise AuthorNotPlaying("Author has to be playing to vote.")
        if player in self.not_voting:
            raise VotingNotAllowed("Author can't vote now.")

        voted = self.players_voted
        options = list(map(lambda o: [v.lower() for v in o], self.voting_options))
        votes = list(map(lambda v: v.lower(), votes))
        votes_std = filter(lambda option: set(option) & set(votes), options)
        # votes_std - list of options, which ecountered in votes
        votes_std = list(map(lambda v: v[-1], votes_std))  # standarize options to use last element

        if len(votes_std) != self.required_votes:
            raise WrongValidVotesNumber('<--')
        if player.id in self.voting_results:
            for vote in self.voting_results[player.id]:
                self.summary[vote].remove(player)
        for vote in votes_std:
            self.summary[vote].append(player)
        self.voting_results[player.id] = votes_std
        self.players_voted.add(player)
        not_voted = set(get_player_role().members) - self.players_voted - set(self.not_voting)
        return votes_std, voted != self.players_voted and not not_voted

    def generate_embed(self, end: bool = False) -> discord.Embed:
        summary_readable = ""
        title = '**Głosowanie zakończone!**\n' if end else 'Podgląd głosowania\n'
        for option, voters in self.summary.items():
            voters_readable = list(map(lambda voter: voter.display_name, voters))
            summary_readable += '**{}** na **{}**:\n {}\n\n'.format(len(voters_readable), option,
                                                                    ", ".join(voters_readable))
        message = "**Wyniki**:\n\n{}".format(summary_readable)
        embed = discord.Embed(title=title, colour=discord.Colour(0x00ccff))
        not_voted = list(set(get_player_role().members)
                         - self.players_voted
                         - set(self.not_voting))
        if not end:
            if len(not_voted) == 0:
                message += "**Wszyscy grający oddali głosy**"
            else:
                message += "**Nie zagłosowali tylko:**\n"
                not_voted = list(map(lambda p: p.display_name, not_voted))
                message += '\n'.join(not_voted)
        embed.description = message
        return embed
