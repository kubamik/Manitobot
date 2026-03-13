from __future__ import annotations

import abc
import inspect
from abc import abstractmethod
from typing import Optional, overload, Literal, List

import discord
from collections.abc import Callable, Awaitable


class ComponentCallback:
    @overload
    def __init__(self, custom_id: str, callback: Callable[[discord.Interaction, str], Awaitable[None]], 
                 component_type: Literal[discord.ComponentType.button] = discord.ComponentType.button):
        ...
    @overload
    def __init__(self, custom_id: str, callback: Callable[[discord.Interaction, str, List[str]], Awaitable[None]], 
                 component_type: Literal[discord.ComponentType.select]):
        ...
    
    def __init__(self, custom_id: str, callback: Callable, component_type: discord.ComponentType = discord.ComponentType.button):
        if len(custom_id) > 100:
            raise ValueError('custom_id cannot be longer than 100 characters')
        if not inspect.iscoroutinefunction(callback):
            raise TypeError('component callback has to be a coroutine')
        if component_type not in (discord.ComponentType.button, discord.ComponentType.select):
            raise ValueError('component_type has to be one of ComponentType.button or ComponentType.select')

        self.custom_id = str(custom_id)
        self.callback = callback
        self.component_type = component_type


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
    def from_discord_component(cls, component: discord.Component):
        pass


class Button(Component):
    def __init__(self, style, label=None, emoji=None, url=None, disabled=False, custom_id=None, **_):
        if not isinstance(style, discord.ButtonStyle):
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

        if url and style is not discord.ButtonStyle.link:
            raise ValueError('url cannot be passed when not using Link style')
        elif not url and style is discord.ButtonStyle.link:
            raise ValueError('url nas to be passed when using Link style')

        if not custom_id and style is not discord.ButtonStyle.link:
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
            'type': discord.ComponentType.button.value,
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
        data['style'] = discord.ButtonStyle(data['style'])
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
            'type': discord.ComponentType.select.value,
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


class Components(discord.ui.View):
    """
    Class to *mock* discord.ui.View to put components in messages
    """

    def __init__(self, components):
        super().__init__()
        self.components_list = components

    def to_components(self):
        if self.components_list:
            custom_ids = set()
            for action in self.components_list:
                for c in action:
                    if c.custom_id in custom_ids:
                        raise ValueError('custom_ids have to be unique in one message')
                    custom_ids.add(c.custom_id)
            return [{
                'type': discord.ComponentType.action_row.value,
                'components': [comp.to_dict() for comp in action]
                } for action in self.components_list
            ]

        return []

    @classmethod
    def from_message(cls, message: discord.Message, /, *, timeout: Optional[float] = None) -> Components:
        components = []
        for action in message.components:
            if action.type == discord.ComponentType.action_row:
                components.append([])
                for comp in action.children:
                    if comp.type == discord.ComponentType.button:
                        components[-1].append(Button.from_discord_component(comp))
                    elif comp.type == discord.ComponentType.select:
                        components[-1].append(Select.from_discord_component(comp))
        return cls(components)

    def is_finished(self):
        return True
