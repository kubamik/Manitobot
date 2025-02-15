import logging

import discord


def parse_interaction_create_decorator(func):
    def wrapper(self, data):
        try:  # error here stops main bot loop
            interaction = discord.Interaction(data=data, state=self)
            if data.get('type') == 3:
                self.dispatch('component_interaction', interaction)
                return
        except Exception:
            logging.exception('Serious exception - interaction parsing')
        func(self, data)

    return wrapper


discord.state.ConnectionState.parse_interaction_create = parse_interaction_create_decorator(
    discord.state.ConnectionState.parse_interaction_create
)
