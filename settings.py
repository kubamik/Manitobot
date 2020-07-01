import discord
from globals import bot
import os

PREFIX = os.getenv('BOT_PREFIX', "")

GUILD_NAME = "Warsztaty WWW"
PLAYER_ROLE_NAME = PREFIX+"gracz"
TRUP_ROLE_NAME = PREFIX+"trup"
SPECTATOR_ROLE_NAME = PREFIX+"obserwator"
MANITOU_ROLE_NAME = PREFIX+"manitou"
PRZEGRALEM_ROLE_NAME = "przegralem"

NOTATNIK_MANITOU_CHANNEL_NAME = "notatnik-manitou"
GLOSOWANIA_CHANNEL_NAME = "głosowania"
TOWN_CHANNEL_NAME = "miasto"

GUILD = discord.utils.get(bot.guilds, name=GUILD_NAME)
GUILD_ID = GUILD.id
PLAYER_ROLE_ID = discord.utils.get(GUILD.roles, name=PLAYER_ROLE_NAME).id
TRUP_ROLE_ID = discord.utils.get(GUILD.roles, name=TRUP_ROLE_NAME).id
SPECTATOR_ROLE_ID = discord.utils.get(GUILD.roles, name=SPECTATOR_ROLE_NAME).id
MANITOU_ROLE_ID = discord.utils.get(GUILD.roles, name=MANITOU_ROLE_NAME).id
PRZEGRALEM_ROLE_ID = discord.utils.get(GUILD.roles, name=PRZEGRALEM_ROLE_NAME).id

NOTATNIK_MANITOU_CHANNEL_ID = discord.utils.get(GUILD.text_channels, name=NOTATNIK_MANITOU_CHANNEL_NAME).id
GLOSOWANIA_CHANNEL_ID = discord.utils.get(GUILD.text_channels, name=GLOSOWANIA_CHANNEL_NAME).id
TOWN_CHANNEL_ID = discord.utils.get(GUILD.text_channels, name=TOWN_CHANNEL_NAME).id
FRAKCJE_CATEGORY_ID = discord.utils.get(GUILD.text_channels, name=TOWN_CHANNEL_NAME).category_id

FAC2CHANN_ID = {
    "Bandyci": discord.utils.get(GUILD.text_channels, name="bandyci"),
    "Indianie": discord.utils.get(GUILD.text_channels, name="indianie"),
    "Ufoki": discord.utils.get(GUILD.text_channels, name="ufoki"),
    "Inkwizycja": discord.utils.get(GUILD.text_channels, name="inkwizycja"),
}

RULLER = "=" * 48
