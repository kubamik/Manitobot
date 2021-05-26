import abc

from discord.ext import commands

from settings import TOWN_CHANNEL_ID


class MyBaseException(abc.ABC, Exception):
    @property
    @abc.abstractmethod
    def msg(self):
        pass


class InvalidRequest(commands.CommandError):
    def __init__(self, msg=None, flag=None):
        self.msg = msg
        self.flag = flag


class NoEffect(commands.CommandError):
    def __init__(self, reason="No reason"):
        self.reason = reason


class GameEnd(commands.CommandError):
    def __init__(self, reason, winner):
        self.winner = winner
        self.reason = reason


class WrongRolesNumber(commands.CommandError, MyBaseException):
    msg: str = 'Błędna liczba postaci. Oczekiwano {}, Otrzymano {}.'

    def __init__(self, should_be: int, is_: int):
        self.msg = self.msg.format(should_be, is_)


class NoSuchSet(commands.CommandError, MyBaseException):
    msg: str = 'Nie ma takiego składu'


class WrongValidVotesNumber(commands.CommandError, MyBaseException):
    msg: str = 'Podano złą liczbę poprawnych głosów - {}. Oczekiwano - {}.'

    def __init__(self, is_, should_be):
        self.msg = self.msg.format(is_, should_be)


class GameStartedException(commands.CheckFailure, MyBaseException):
    msg: str = 'Nie można wykonać tej akcji podczas gry'


class SelfDareError(commands.CheckFailure, MyBaseException):
    msg: str = 'Nie możesz się sam wyzwać'


class DayOnly(commands.CheckFailure, MyBaseException):
    msg: str = 'Tej komendy można używać tylko w trakcie dnia'


class NightOnly(commands.CheckFailure, MyBaseException):
    msg: str = 'Tej komendy można używać tylko w trakcie nocy'


class DuelInProgress(commands.CheckFailure, MyBaseException):
    msg: str = 'Tej komendy nie można używać w trakcie pojedynku'


class AuthorNotOnVoice(commands.CheckFailure, MyBaseException):
    msg: str = 'Musisz być na kanale głosowym, aby użyć tej komendy'


class AuthorPlaying(commands.CheckFailure, MyBaseException):
    msg: str = 'Gra została rozpoczęta, nie możesz nie grać'


class AuthorNotPlaying(commands.CheckFailure, MyBaseException):
    msg: str = 'Nie grasz lub nie żyjesz'


class MemberNotPlaying(commands.MemberNotFound, MyBaseException):
    msg: str = 'Ta osoba nie gra lub nie żyje'


class VotingNotAllowed(commands.CommandError, MyBaseException):
    msg: str = 'Nie trwa teraz żadne głosowanie'


class WrongGameType(commands.CommandError, MyBaseException):
    msg: str = 'Obecny tryb gry nie obsługuje tego polecenia'


class GameNotStarted(commands.CommandError, MyBaseException):
    msg: str = 'Gra nie została rozpoczęta'


class NotTownChannel(commands.CheckFailure, MyBaseException):
    msg: str = f'Tej komendy można używać tylko na kanale <#{TOWN_CHANNEL_ID}>'


class VotingInProgress(commands.CheckFailure, MyBaseException):
    msg: str = 'Tej komendy nie można używać w trakcie głosowania'


class VotingNotInProgress(commands.CheckFailure, MyBaseException):
    msg: str = 'Nie trwa głosowanie'


class TooLessVotingOptions(commands.CommandError, MyBaseException):
    msg: str = 'Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}'

    def __init__(self, is_: int, should_be: int = 1):
        self.msg = self.msg.format(is_, should_be)
