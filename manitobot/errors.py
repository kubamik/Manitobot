import abc

from discord.ext import commands

from settings import TOWN_CHANNEL_ID, SET_CHANNEL_ID, ANNOUNCEMENTS_CHANNEL_ID


class MyBaseException(abc.ABC, Exception):
    @property
    @abc.abstractmethod
    def msg(self):
        pass


class MyCommandError(MyBaseException, abc.ABC, commands.CommandError):
    """Class for derrivation of both commands.CheckFailure and MyBaseException
    """
    pass


class MyCheckFailure(MyBaseException, abc.ABC, commands.CheckFailure):
    """Class for derrivation of both commands.CheckFailure and MyBaseException
    """
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
    msg = 'Błędna liczba postaci. Oczekiwano {}, Otrzymano {}.'

    def __init__(self, should_be: int, is_: int):
        self.msg = self.msg.format(should_be, is_)


class WrongSetNameError(MyCommandError):
    msg = 'Nazwa składu może zawierać tylko znaki alfanumeryczne, "-" i "_" i musi mieć co najmniej 3 znaki'


class SetExists(MyCommandError):
    msg = 'Set o takiej nazwie już istnieje'


class NoSuchSet(commands.CommandError, MyBaseException):
    msg = 'Nie ma takiego składu'


class DuplicateVote(commands.CommandError, MyBaseException):
    msg = 'Oddano podwójny głos na {}'

    def __init__(self, option):
        self.msg = self.msg.format(option)


class WrongVote(commands.CommandError, MyBaseException):
    msg = 'Nie ma opcji {}'

    def __init__(self, option):
        self.msg = self.msg.format(option)


class WrongValidVotesNumber(commands.CommandError, MyBaseException):
    msg = 'Podano złą liczbę poprawnych głosów - {}. Oczekiwano - {}.'

    def __init__(self, is_, should_be):
        self.msg = self.msg.format(is_, should_be)


class NotEnoughTrustLevel(MyCheckFailure):
    msg = 'Nie możesz użyć tej komendy'


class MissingAdministrativePermissions(MyCheckFailure):
    msg = 'Brak uprawnień'


class MissingManitouRole(MyCheckFailure):
    msg = 'Komenda tylko dla Manitou'


class MissingQualifications(MyCheckFailure):
    msg = 'Nie masz wystarczających kwalifikacji'


class GameStartedException(commands.CheckFailure, MyBaseException):
    msg = 'Nie można wykonać tej akcji podczas gry'


class SelfChallengeError(MyCheckFailure):
    msg = 'Nie możesz się sam wyzwać'


class AuthorIsSubjectChallengeError(MyCheckFailure):
    msg = 'W pojedynku muszą brać udział dwie różne osoby'


class DuplicateChallenge(MyCheckFailure):
    msg = 'Wyzwałeś(-aś) już tą osobę lub ona wyzwała Ciebie'


class ChallengeNotFound(MyCheckFailure):
    msg = 'Nie zostałeś(-aś) wyzwany(-a)'


class DuelAlreadyAccepted(MyCheckFailure):
    msg = 'Masz już oczekujący pojedynek'


class DuelDoublePerson(MyCommandError):
    msg = '{} jest zwycięzcą i przegranym jednocześnie'

    def __init__(self, member):
        self.msg = self.msg.format(member)


class NotDuelParticipant(MyCommandError):
    msg = '{} ma rolę {}, a nie pojedynkuje się'

    def __init__(self, member, role):
        self.msg = self.msg.format(member, role)


class ReportingLocked(MyCheckFailure):
    msg = 'Nie można już zgłaszać'


class ReportsLimitExceeded(MyCheckFailure):
    msg = 'Nie możesz zgłosić już więcej osób'
        
        
class MoreSearchedThanSearches(MyCommandError):
    msg = 'Przeszukiwanych jest więcej niż przeszukań'


class IllegalSearch(MyCommandError):
    msg = '{} ma zostać przeszukany(-a) a nie gra'

    def __init__(self, member):
        self.msg = self.msg.format(member)


class TooMuchHang(MyCommandError):
    msg = 'Powiesić można tylko jedną osobę'


class IllegalHang(MyCommandError):
    msg = '{} ma zostać powieszony(-a) a nie gra lub nie żyje'

    def __init__(self, member):
        self.msg = self.msg.format(member)


class DayOnly(commands.CheckFailure, MyBaseException):
    msg = 'Tej komendy można używać tylko w trakcie dnia'


class NightOnly(commands.CheckFailure, MyBaseException):
    msg = 'Tej komendy można używać tylko w trakcie nocy'


class WrongState(MyCheckFailure):
    msg = 'Na razie nie można używać tego polecenia'


class DuelInProgress(commands.CheckFailure, MyBaseException):
    msg = 'Tej komendy nie można używać w trakcie pojedynku'


class AuthorNotOnVoice(commands.CheckFailure, MyBaseException):
    msg = 'Musisz być na kanale głosowym, aby użyć tej komendy'


class AuthorPlaying(commands.CheckFailure, MyBaseException):
    msg = 'Gra została rozpoczęta, nie możesz nie grać'


class AuthorNotPlaying(commands.CheckFailure, MyBaseException):
    msg = 'Nie grasz lub nie żyjesz'


class MemberNotPlaying(commands.MemberNotFound, MyBaseException):
    msg = 'Ta osoba nie gra lub nie żyje'


class MembersNotPlaying(commands.MemberNotFound, MyBaseException):
    msg = 'Co najmniej jedna z osób musi grać'


class VotingNotAllowed(commands.CommandError, MyBaseException):
    msg = 'Nie trwa teraz żadne głosowanie lub nie możesz głosować'


class WrongGameType(commands.CommandError, MyBaseException):
    msg = 'Obecny tryb gry nie obsługuje tego polecenia'


class GameNotStarted(commands.CommandError, MyBaseException):
    msg = 'Gra nie została rozpoczęta'


class NotTownChannel(commands.CheckFailure, MyBaseException):
    msg = f'Tej komendy można używać tylko na kanale <#{TOWN_CHANNEL_ID}>'


class NotSetsChannel(MyCheckFailure):
    msg = f'Tej komendy można używać tylko na kanale <#{SET_CHANNEL_ID}>'


class NotPollChannel(MyCheckFailure):
    msg = f'Tej komendy można używać tylko na kanale <#{ANNOUNCEMENTS_CHANNEL_ID}>'


class VotingInProgress(commands.CheckFailure, MyBaseException):
    msg = 'Tej komendy nie można używać w trakcie głosowania'


class VotingNotInProgress(commands.CheckFailure, MyBaseException):
    msg = 'Nie trwa głosowanie'


class TooLessVotingOptions(commands.CommandError, MyBaseException):
    msg = 'Za mało kandydatur. Otrzymano {}, oczekiwano co najmniej {}'

    def __init__(self, is_: int, should_be: int = 1):
        self.msg = self.msg.format(is_, should_be)


class NotAuthor(MyCommandError):
    msg = 'Tylko autor może tego używać'


class TooLongText(MyCommandError):
    msg = 'Za długi tekst'


class TooMuchPing(MyCheckFailure):
    msg = 'Nie można pingować więcej niż raz dziennie'


class MissingMembers(MyCommandError):
    msg = 'Podaj listę osób'
