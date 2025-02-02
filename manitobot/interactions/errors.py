import discord


class ComponentsError(discord.DiscordException):
    """Base exception class for message components
    """
    pass


class CustomIdNotFound(ComponentsError):
    """Exception that's raised when a custom_id is not found in the components list
    """
    def __init__(self, custom_id):
        super().__init__('custom_id not found')
        self.custom_id = custom_id


class MismatchedComponentCallbackType(ComponentsError):
    """Exception that's raised when a component callback type does not match the component type
    """
    def __init__(self, expected_type, actual_type):
        super().__init__('mismatched component callback type')
        self.expected_type = expected_type
        self.actual_type = actual_type
