import abc
import inspect
from abc import abstractmethod
from enum import IntEnum

import discord


class ComponentMessage:
    """Like discord.Message but with support for message components
    """
    components = None

    def __init__(self, *, state, channel, data):
        self.component_data = data.pop('components', list())
        self.message = discord.Message(state=state, channel=channel, data=data)
        self._handle_components()

    def _handle_components(self):
        self.components = list()
        for action in self.component_data:
            self.components.append(
                [Button.from_dict(comp) if comp['type'] == ComponentTypes.Button else Select.from_dict(comp)
                 for comp in action['components']])

    @classmethod
    def from_message(cls, message, data=None, components=None):
        self = object.__new__(cls)
        self.message = message
        if data is not None:
            self.component_data = data.pop('components', list())
            self._handle_components()
        elif components:
            self.component_data = None
            self.components = components
        return self

    def __getattr__(self, item):
        return getattr(self.message, item)

    async def edit(self, **fields):
        await self.message.edit(**fields)
        if 'components' in fields:
            self.components = fields['components']

    def _update(self, data):
        self.component_data = data.pop('components', list())
        self.message._update(data)
        self._handle_components()


class ComponentTypes(IntEnum):
    ActionRow = 1
    Button = 2
    Select = 3


class ButtonStyle(IntEnum):
    Primary = 1
    Secondary = 2
    Success = 3
    Destructive = 4
    Link = 5


class ComponentCallback:
    def __init__(self, custom_id, callback):
        if len(custom_id) > 100:
            raise ValueError('custom_id cannot be longer than 100 characters')
        if not inspect.iscoroutinefunction(callback):
            raise TypeError('component callback has to be a coroutine')
        self.custom_id = str(custom_id)
        self.callback = callback


class SelectOption:
    def __init__(self, label, value, description=None, emoji=None, default=False):
        if not isinstance(label, str) or description and not isinstance(description, str):
            raise TypeError('label and description have to be str')
        if emoji and not isinstance(emoji, (discord.PartialEmoji, str, discord.Emoji)):
            raise TypeError('emoji has to be the type of PartialEmoji')
        elif emoji:
            if isinstance(emoji, str):
                emoji = discord.PartialEmoji(name=emoji)
            elif isinstance(emoji, discord.Emoji):
                emoji = discord.PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        if not isinstance(default, bool):
            raise TypeError('default has to be boolean')

        self.label = label
        self.value = str(value)
        self.description = description
        self.emoji = emoji
        self.default = default

    def to_dict(self):
        d = {
            'label': self.label,
            'value': self.value,
            'default': self.default,
        }
        if self.description:
            d['description'] = self.description
        if self.emoji:
            d['emoji'] = self.emoji.to_dict()
        return d

    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        if 'emoji' in data:
            data['emoji'] = discord.PartialEmoji.from_dict(data['emoji'])
        return cls(**data)

    @classmethod
    def from_discord_option(cls, option: discord.SelectOption):
        return cls(label=option.label, value=option.value, description=option.description, emoji=option.emoji,
                   default=option.default)


class Component(abc.ABC):
    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        pass

    @classmethod
    @abstractmethod
    def from_discord_component(self, component: discord.Component):
        pass


class Button(Component):
    def __init__(self, style, label=None, emoji=None, url=None, disabled=False, custom_id=None, **_):
        if not isinstance(style, ButtonStyle):
            raise TypeError('style has to be one of ButtonStyle')
        if label and len(label) > 80:
            raise ValueError('label cannot be longer than 80 characters')
        if emoji and not isinstance(emoji, (discord.PartialEmoji, str, discord.Emoji)):
            raise TypeError('emoji has to be the type of PartialEmoji')
        elif emoji:
            if isinstance(emoji, str):
                emoji = discord.PartialEmoji(name=emoji)
            elif isinstance(emoji, discord.Emoji):
                emoji = discord.PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        if not isinstance(disabled, bool):
            raise TypeError('disabled must be boolean')

        if url and style is not ButtonStyle.Link:
            raise ValueError('url cannot be passed when not using Link style')
        elif not url and style is ButtonStyle.Link:
            raise ValueError('url nas to be passed when using Link style')

        if not custom_id and style is not ButtonStyle.Link:
            raise ValueError('custom_id has to be passed when not using Link style')
        if url and custom_id:
            raise ValueError('cannot provide both custom_id and url')

        self.custom_id = str(custom_id)
        self.disabled = disabled
        self.url = url
        self.style = style
        self.label = label
        self.emoji = emoji

    def to_dict(self):
        d = {
            'type': discord.ComponentType.button,
            'disabled': self.disabled,
            'style': int(self.style),
        }
        if self.url:
            d['url'] = self.url
        if self.label:
            d['label'] = self.label
        if self.emoji:
            d['emoji'] = self.emoji.to_dict()
        if self.custom_id:
            d['custom_id'] = self.custom_id
        return d

    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        data.pop('type')
        data['style'] = ButtonStyle(data['style'])
        data['emoji'] = data.get('emoji') and discord.PartialEmoji.from_dict(data.get('emoji'))
        return cls(**data)

    @classmethod
    def from_discord_component(cls, button: discord.Button):
        return cls(style=button.style, label=button.label, emoji=button.emoji, url=button.url,
                   disabled=button.disabled, custom_id=button.custom_id)


class Select:
    def __init__(self, custom_id, options, placeholder=None, min_values=1, max_values=1, disabled=False, **_):
        if len(options) > 25:
            raise ValueError('options cannot have more than 25 elements')
        if len(options) < max_values or min_values > max_values or min_values < 0:
            raise ValueError('wrong value of min_values/max_values')
        if (placeholder and not isinstance(placeholder, str)) or not isinstance(min_values, int) \
                or not isinstance(max_values, int) or not isinstance(disabled, bool):
            raise TypeError('Wrong types')

        if not all([isinstance(option, SelectOption) for option in options]) and \
                len(set((option.value for option in options))) == len(options):
            raise TypeError('All options have to be SelectOption and have unique value param')

        self.custom_id = str(custom_id)
        self.options = options
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self):
        d = {
            'type': discord.ComponentType.select,
            'custom_id': self.custom_id,
            'options': [option.to_dict() for option in self.options],
            'min_values': self.min_values,
            'max_values': self.max_values,
            'disabled': self.disabled,
        }
        if self.placeholder:
            d['placeholder'] = self.placeholder
        return d

    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        data.pop('type')
        data['options'] = [SelectOption.from_dict(option) for option in data['options']]
        return cls(**data)

    @classmethod
    def from_discord_component(cls, select: discord.SelectMenu):
        return cls(custom_id=select.custom_id, options=[SelectOption.from_discord_option(option)
                                                        for option in select.options],
                   placeholder=select.placeholder, min_values=select.min_values, max_values=select.max_values,
                   disabled=select.disabled)
