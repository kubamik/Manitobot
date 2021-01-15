from discord.ext import commands


class InvalidRequest(commands.CommandError):
    def __init__(self, reason=None, flag=None):
        self.reason = reason
        self.flag = flag


class NoEffect(commands.CommandError):
    def __init__(self, reason="No reason"):
        self.reason = reason


class GameEnd(commands.CommandError):
    def __init__(self, reason, winner):
        self.winner = winner
        self.reason = reason


class WrongRolesNumber(commands.CommandError):
    msg = 'Błędna liczba postaci. Oczekiwano {}, Otrzymano {}.'

    def __init__(self, should_be: int, is_: int):
        self.msg = self.msg.format(should_be, is_)


class NoSuchSet(commands.CommandError):
    pass


class WrongValidVotesNumber(commands.CommandError):
    pass


class GameStartedException(commands.CheckFailure):
    pass


class SelfDareError(commands.CheckFailure):
    pass


class DayOnly(commands.CheckFailure):
    pass


class NightOnly(commands.CheckFailure):
    pass


class DuelInProgress(commands.CheckFailure):
    pass


class AuthorNotOnVoice(commands.CheckFailure):
    pass


class AuthorPlaying(commands.CheckFailure):
    pass


class AuthorNotPlaying(commands.CheckFailure):
    pass


class MemberNotPlaying(commands.MemberNotFound):
    pass


class VotingNotAllowed(commands.CommandError):
    pass


class WrongGameType(commands.CommandError):
    pass


class GameNotStarted(commands.CommandError):
    pass


class VotingInProgress(commands.CheckFailure):
    pass


class VotingNotInProgress(commands.CheckFailure):
    pass


class TooLessVotingOptions(commands.CommandError):
    msg = 'Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}'

    def __init__(self, is_: int, should_be: int = 1):
        self.msg = self.msg.format(is_, should_be)
