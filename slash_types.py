import discord
from discord.enums import Enum


class SlashOptionType(Enum):
    subcommand       = 1
    subcommand_group = 2
    string           = 3
    integer          = 4
    boolean          = 5
    user             = 6
    channel          = 7
    role             = 8

    @classmethod
    def from_class(cls, obj):
        objects = {
            str: 'string',
            int: 'integer',
            bool: 'boolean',
            discord.abc.User: 'user',
            discord.abc.GuildChannel: 'channel',
            discord.Role: 'role',
        }
        for tp, attr in objects.items():
            if issubclass(obj, tp):
                return getattr(cls, attr)
                print(val)
                return cls._enum_value_map_[val]
        raise TypeError('Not supported type %s' % type(obj))
