import typing

from .commands_types import SlashOptionType


class _Arg:
    """Slash command argument
    """
    def __init__(self, doc: str = '', *, name: typing.Optional[str] = None):
        self.doc = doc
        self.name = name
        self.type = None
        self.optional = False

    def __getitem__(self, item):
        if isinstance(item, str):
            item = eval(item)
        cls = self.__class__(self.doc, name=self.name)
        cls.type = SlashOptionType.from_class(item)
        return cls

    def __call__(self, doc: str = '', *, name: typing.Optional[str] = None):
        cls = self.__class__(doc, name=name)
        cls.type = self.type
        return cls

    def to_dict(self):
        return {
            'type': self.type.value,
            'name': self.name,
            'description': self.doc,
            'required': not self.optional
        }


Arg = _Arg()


class Option:
    """Slash command option use with Choice
    """
    def __init__(self, value, name: typing.Optional[str] = None):
        self.name = name or str(value)
        self.value = value

    def to_dict(self):
        return {
            'name': self.name,
            'value': self.value,
        }


class _Choice(_Arg):
    """Slash command option choice, use when argument should take only values from some set
    """
    def __init__(self, doc: str = '', *options: Option, name: typing.Optional[str] = None):
        super().__init__(doc, name=name)
        self.options = list(options)

    def __call__(self, doc: str = '', *options: Option, name: typing.Optional[str] = None):
        cls = super().__call__(doc, name=name)
        cls.options = list(options)
        return cls

    def check_types(self):
        """Check each option for type colisions with choice
        """
        if self.type != SlashOptionType.integer and self.type != SlashOptionType.string:
            raise TypeError('Choices can only be specified to int or str type')
        for option in self.options:
            enum = SlashOptionType.from_class(type(option.value))
            if enum is not self.type:
                raise TypeError('Option value here should be type of %s or %s, not %s'
                                % (self.type, SlashOptionType.integer, enum))

    def to_dict(self):
        return {
            'type': self.type.value,
            'name': self.name,
            'description': self.doc,
            'required': not self.optional,
            'choices': [option.to_dict() for option in self.options]
        }


Choice = _Choice()
