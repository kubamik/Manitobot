from collections import defaultdict
from typing import List, Tuple, Optional, Dict, Set, Mapping

import discord

from .errors import AuthorNotPlaying, VotingNotAllowed, WrongValidVotesNumber
from .utility import get_player_role


class Vote:
    def __init__(self, required_votes: int, voting_options: List[List[str]],
            not_voting: List[discord.Member], vote_type: Optional[str] = None):
        self.required_votes = required_votes
        self.voting_options = voting_options
        self.voting_results: Dict[int, List[str]] = {}
        self.players_voted: Set[discord.Member] = set()
        self.not_voting = not_voting
        self.vote_type = vote_type
        self.summary: Mapping[str, List[discord.Member]] = defaultdict(list)

    def register_vote(self, player: discord.Member, votes: List[str]) -> Tuple[List[str], bool]:
        if player not in get_player_role().members:
            raise AuthorNotPlaying('Author has to be playing to vote.')
        if player in self.not_voting:
            raise VotingNotAllowed('Author can\'t vote now.')

        voted = self.players_voted.copy()
        options = [[v.lower() for v in o] for o in self.voting_options]
        votes = set(v.lower() for v in votes)
        votes_std = [self.voting_options[options.index(option)][-1] for option in options if set(option) & votes]
        # votes_std - list of options, which ecountered in votes
        # standarize options to use last element and resolve original case

        if len(votes_std) != self.required_votes:
            raise WrongValidVotesNumber(len(votes_std), self.required_votes)
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
        for option in self.voting_options:
            voters = self.summary[option[-1]]
            voters_readable = [voter.display_name for voter in voters]
            summary_readable += '**{}** na **{}**:\n {}\n\n'.format(len(voters_readable), option[-1],
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
                not_voted = [p.display_name for p in not_voted]
                message += '\n'.join(not_voted)
        embed.description = message
        return embed
