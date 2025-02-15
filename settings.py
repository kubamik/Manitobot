import os.path
import typing

__version__ = '1.8.0'

PROD = os.environ.get('TEST') != '1'
LOCAL = os.environ.get('LOCAL') == '1'
WEB_HOSTED = os.environ.get('WEB') == '1'

if PROD:
    GUILD_ID = 710039683798794270
    BOT_ID = 692390349053886515
    MY_ID = 388764073191538688

    # Game roles
    PLAYER_ROLE_ID = 710051008608469012
    TRUP_ROLE_ID = 710051039218368513
    MANITOU_ROLE_ID = 710050970352222229
    SPECTATOR_ROLE_ID = 710052408205770772
    DUEL_WINNER_ID = 710051109242404864
    DUEL_LOSER_ID = 710051419117453313
    SEARCHED_ID = 710053492152074363
    HANGED_ID = 710051077718016013

    # Server roles
    VERIFIED_ROLE_ID = 1294737515579834471
    PING_OTHER_GAMES_ROLE_ID = 1193327333097078904
    PING_GAME_ROLE_ID = 779091611736604693
    PING_DECLARATION_ROLE_ID = 779091574801301505
    PING_POLL_ROLE_ID = 891811707272454194
    NEWCOMER_ROLE_ID = 720235063144349720
    LOSER_ROLE_ID = None
    TRUSTED_ROLE_ID = 1294271996611399732
    QUALIFIED_MANITOU_ROLE_ID = 879495334093525052
    MOD_ROLE_ID = 1294725954614067262
    EX_ADMIN_ROLE_ID = 1212855030474866698
    ADMIN_ROLE_ID = 710040986260209715

    NON_ADMIN_ROLES_COLOURS = {
        TRUSTED_ROLE_ID: 0xd33682,
        QUALIFIED_MANITOU_ROLE_ID: 0xdc322f,
        MOD_ROLE_ID: 0x6c71c4,
        EX_ADMIN_ROLE_ID: 0x268bd2
    }
    ADMIN_ROLE_COLOUR = 0xffa9f9

    HOISTED_NON_ADMIN_ROLES = {
        QUALIFIED_MANITOU_ROLE_ID,
        MOD_ROLE_ID,
    }
    HOIST_ADMIN = True

    # Channels
    TOWN_CHANNEL_ID = 1294275336976072855
    VOICE_CHANNEL_ID = 1294271220035879054
    NOTATNIK_MANITOU_CHANNEL_ID = 1294288047394787419
    ANKIETAWKA_CHANNEL_ID = 710050073181945896
    FAC2CHANN_ID: typing.Dict[str, int] = {
        "Bandyci": 1339574497094664213,
        "Indianie": 1294274808892096555,
        "Ufoki": 1339574605253447681,
        "Inkwizycja": 1294281671385813023
    }
    CONTROL_PANEL_ID = 770344422625378325
    SET_CHANNEL_ID = 890289302230171658
    SYSTEM_MESSAGES_CHANNEL_ID = 1074755791258660924
    BOT_TRAP_CHANNEL_ID = 1294749837312659517
    VERIFICATION_CHANNEL_ID = 1294744305658757120

    # Categories
    FRAKCJE_CATEGORY_ID = 710039683798794272
    NIEPUBLICZNE_CATEGORY_ID = 1121883941809430600

    # Emojis
    GUN_ID = 717099650087387158
    FAC2EMOJI: typing.Dict[str, int] = {
        "Bandyci": 770345428977582090,
        "Indianie": 770345346983002209,
        "Ufoki": 770345372865265724,
        "Inkwizycja": 770345470677483566
    }
    PING_BLUE_ID = 891944199539277844
    PING_YELLOW_ID = 891944199673491516
    PING_GREEN_ID = 891944200751427594
    PING_PINK_ID = 1192602506010820648
    DIE415_ID = 1222996818854543361
    DIE421_ID = 1222996820846706791
    DIE456_ID = 1222996822578954240
    DIE462_ID = 1222996824390893568

    # Messages
    PING_MESSAGE_ID = 891966724767899729
    OTHER_PING_MESSAGE_ID = 1208193767568572497
    VERIFICATION_MESSAGE_ID = None

else:
    GUILD_ID = 694111942729662474
    BOT_ID = 709695265413791829
    MY_ID = 388764073191538688

    # Game roles
    PLAYER_ROLE_ID = 694112133880741888
    TRUP_ROLE_ID = 694112166105841724
    MANITOU_ROLE_ID = 694112018596233246
    SPECTATOR_ROLE_ID = 694112245814263869
    DUEL_WINNER_ID = 701077841848172544
    DUEL_LOSER_ID = 701078158102888538
    SEARCHED_ID = 701076474320650310
    HANGED_ID = 701462743504519308

    # Server roles
    VERIFIED_ROLE_ID = 1333105146724356107
    NEWCOMER_ROLE_ID = 720307369245933649
    ADMIN_ROLE_ID = 694112331537317898
    QUALIFIED_MANITOU_ROLE_ID = 694112331537317898
    TRUSTED_ROLE_ID = 694112331537317898
    MOD_ROLE_ID = 694112331537317898
    EX_ADMIN_ROLE_ID = 694112331537317898
    LOSER_ROLE_ID = None
    PING_POLL_ROLE_ID = 780379731962494997
    PING_GAME_ROLE_ID = 780379814846267392
    PING_DECLARATION_ROLE_ID = 891953544469569556

    NON_ADMIN_ROLES_COLOURS = {
        TRUSTED_ROLE_ID: 0x268bd2,
        QUALIFIED_MANITOU_ROLE_ID: 0x2aa198,
        MOD_ROLE_ID: 0xd33682,
        EX_ADMIN_ROLE_ID: 0x859900
    }
    ADMIN_ROLE_COLOUR = 0xdc322f

    HOISTED_NON_ADMIN_ROLES = {
        QUALIFIED_MANITOU_ROLE_ID,
        MOD_ROLE_ID,
    }
    HOIST_ADMIN = True

    # Channels
    TOWN_CHANNEL_ID = 694112761386500146
    VOICE_CHANNEL_ID = 694111942729662478
    NOTATNIK_MANITOU_CHANNEL_ID = 694113999691972638
    ANKIETAWKA_CHANNEL_ID = 714773492544962643
    FAC2CHANN_ID = {
        "Bandyci": 694112800221560872,
        "Indianie": 706155488202457229,
        "Ufoki": 706155509069381733,
        "Inkwizycja": 706155539788202107
    }
    CONTROL_PANEL_ID = 770310603691786311
    SET_CHANNEL_ID = 890289714534428773
    SYSTEM_MESSAGES_CHANNEL_ID = 728954765140164721
    BOT_TRAP_CHANNEL_ID = 1333104040602763264
    VERIFICATION_CHANNEL_ID = 814479709463117835

    # Categories
    FRAKCJE_CATEGORY_ID = 694112717266616372
    NIEPUBLICZNE_CATEGORY_ID = 799603854349041674

    # Emojis
    GUN_ID = 717105928067088384
    FAC2EMOJI = {
        "Bandyci": 1339233746666389627,
        "Indianie": 770306713735266336,
        "Ufoki": 1339242153041465345,
        "Inkwizycja": 770303863844241410
    }
    PING_BLUE_ID = None
    PING_YELLOW_ID = None
    PING_GREEN_ID = None
    PING_PINK_ID = None
    DIE415_ID = 1222996818854543361
    DIE421_ID = 1222996820846706791
    DIE456_ID = 1222996822578954240
    DIE462_ID = 1222996824390893568

    # Messages
    PING_MESSAGE_ID = None
    OTHER_PING_MESSAGE_ID = None
    VERIFICATION_MESSAGE_ID = 1333103562435068056
    


EMOJI2COMMAND: typing.Dict[str, typing.Tuple[str, str]] = {  # for DayState methods - emoji: (label, method_name)
    '⏪': ('Cofnij', 'undo'),
    '❌': ('Anuluj', 'cancel'),
    '🗳️': ('Głosowanie', 'voting'),
    '🎲': ('Wylosuj', 'random'),
    '🔒': ('Blokuj', 'lock'),
    '⏩': ('Dalej', 'end')
}

REMOVABLE: typing.List[str] = [EMOJI2COMMAND['🔒'][1]]  # state commands to accept in `reaction_remove` event

RULLER = '=' * 48

CONFIG = {
    'DM_Manitou': True
}

LOG_FILE = 'error.log'
FULL_LOG_FILE = 'full.log'

SETS_DB_PATH = os.path.join('data', 'sets.sqlite3')

ELECTION_DB_PATH = os.path.join('data', 'elections.sqlite3')
ELECTION_BACKUP_CHANNEL_ID = 1223309118295642124

REFERENCE_TIMEZONE = 'Europe/Warsaw'
