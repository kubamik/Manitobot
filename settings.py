import discord
from globals import bot
import os

PREFIX = os.getenv('BOT_PREFIX', "")
COMMAND_KEY = "/"

GUILD_NAME = "Warsztaty WWW"
PLAYER_ROLE_NAME = PREFIX+"gracz"
TRUP_ROLE_NAME = PREFIX+"trup"
SPECTATOR_ROLE_NAME = PREFIX+"obserwator"
MANITOU_ROLE_NAME = PREFIX+"manitou"
PRZEGRALEM_ROLE_NAME = "przegralem"

NOTATNIK_MANITOU_CHANNEL_NAME = "notatnik-manitou"
GLOSOWANIA_CHANNEL_NAME = "głosowania"
TOWN_CHANNEL_NAME = "miasto"


def load_ids():
    global GUILD_ID, PLAYER_ROLE_ID, TRUP_ROLE_ID, SPECTATOR_ROLE_ID, \
        MANITOU_ROLE_ID, PRZEGRALEM_ROLE_ID, NOTATNIK_MANITOU_CHANNEL_ID, \
        GLOSOWANIA_CHANNEL_ID, TOWN_CHANNEL_ID, FRAKCJE_CATEGORY_ID, \
        FAC2CHANN_ID

    GUILD = discord.utils.get(bot.guilds, name=GUILD_NAME)
    GUILD_ID = GUILD.id
    PLAYER_ROLE_ID = discord.utils.get(GUILD.roles, name=PLAYER_ROLE_NAME).id
    TRUP_ROLE_ID = discord.utils.get(GUILD.roles, name=TRUP_ROLE_NAME).id
    SPECTATOR_ROLE_ID = discord.utils.get(GUILD.roles, name=SPECTATOR_ROLE_NAME).id
    MANITOU_ROLE_ID = discord.utils.get(GUILD.roles, name=MANITOU_ROLE_NAME).id
    PRZEGRALEM_ROLE_ID = discord.utils.get(GUILD.roles, name=PRZEGRALEM_ROLE_NAME).id
    NOTATNIK_MANITOU_CHANNEL_ID = discord.utils.get(GUILD.text_channels,
                                                    name=NOTATNIK_MANITOU_CHANNEL_NAME).id
    GLOSOWANIA_CHANNEL_ID = discord.utils.get(GUILD.text_channels,
                                              name=GLOSOWANIA_CHANNEL_NAME).id
    TOWN_CHANNEL_ID = discord.utils.get(GUILD.text_channels,
                                        name=TOWN_CHANNEL_NAME).id
    FRAKCJE_CATEGORY_ID = discord.utils.get(GUILD.text_channels,
                                            name=TOWN_CHANNEL_NAME).category_id
    FAC2CHANN_ID = {
        "Bandyci": discord.utils.get(GUILD.text_channels, name="bandyci").id,
        "Indianie": discord.utils.get(GUILD.text_channels, name="indianie").id,
        "Ufoki": discord.utils.get(GUILD.text_channels, name="ufoki").id,
        "Inkwizycja": discord.utils.get(GUILD.text_channels, name="inkwizycja").id,
    }


RULLER = "="*48
