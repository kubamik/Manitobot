import discord

from .interaction import Interaction


def parse_interaction_create(self, data):
    if 'channel_id' not in data:
        return
    channel, _ = self._get_guild_channel(data)
    inter = Interaction(state=self, channel=channel, data=data)
    self.dispatch('interaction', inter)


def ack_interaction(self, token, interaction_id):
    r = discord.http.Route('POST', '/interactions/{interaction_id}/{token}/callback',
                           interaction_id=interaction_id, token=token)
    payload = {'type': 5}

    return self.request(r, json=payload)


def respond_interaction(self, token, interaction_id, content, *, tts=False, embed=None, embeds=None,
                        allowed_mentions=None, ephemeral=False):
    r = discord.http.Route('POST', '/interactions/{interaction_id}/{token}/callback',
                           interaction_id=interaction_id, token=token)
    json = {'type': 4}
    payload = {}

    if content:
        payload['content'] = content

    if tts:
        payload['tts'] = True

    if embed or embeds:
        payload['embeds'] = [embed] if embed else embeds

    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions

    if ephemeral:
        payload['flags'] = 1 << 6

    json['data'] = payload
    return self.request(r, json=json)


discord.state.ConnectionState.parse_interaction_create = parse_interaction_create
discord.http.HTTPClient.ack_interaction = ack_interaction
discord.http.HTTPClient.respond_interaction = respond_interaction


def get_global_slash_commands(self, application_id):
    r = discord.http.Route('GET', '/applications/{application_id}/commands', application_id=application_id)
    return self.request(r)


def create_global_slash_command(self, application_id, command):
    r = discord.http.Route('POST', '/applications/{application_id}/commands', application_id=application_id)
    return self.request(r, json=command)


def edit_global_slash_command(self, application_id, command_id, command):
    r = discord.http.Route('PATCH', '/applications/{application_id}/commands/{command_id}',
                           application_id=application_id, command_id=command_id)
    return self.request(r, json=command)


def delete_global_slash_command(self, application_id, command_id):
    r = discord.http.Route('DELETE', '/applications/{application_id}/commands/{command_id}',
                           application_id=application_id, command_id=command_id)
    return self.request(r)


def get_guild_slash_commands(self, application_id, guild_id):
    r = discord.http.Route('GET', '/applications/{application_id}/guilds/{guild_id}/commands',
                           application_id=application_id, guild_id=guild_id)
    return self.request(r)


def create_guild_slash_command(self, application_id, guild_id, command):
    r = discord.http.Route('POST', '/applications/{application_id}/guilds/{guild_id}/commands',
                           application_id=application_id, guild_id=guild_id)
    return self.request(r, json=command)


def edit_guild_slash_command(self, application_id, guild_id, command_id, command):
    r = discord.http.Route('PATCH', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
                           application_id=application_id, command_id=command_id, guild_id=guild_id)
    return self.request(r, json=command)


def delete_guild_slash_command(self, application_id, guild_id, command_id):
    r = discord.http.Route('DELETE', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
                           application_id=application_id, command_id=command_id, guild_id=guild_id)
    return self.request(r)


discord.http.HTTPClient.get_global_slash_commands = get_global_slash_commands
discord.http.HTTPClient.create_global_slash_command = create_global_slash_command
discord.http.HTTPClient.edit_global_slash_command = edit_global_slash_command
discord.http.HTTPClient.delete_global_slash_command = delete_global_slash_command
discord.http.HTTPClient.get_guild_slash_commands = get_guild_slash_commands
discord.http.HTTPClient.create_guild_slash_command = create_guild_slash_command
discord.http.HTTPClient.edit_guild_slash_command = edit_guild_slash_command
discord.http.HTTPClient.delete_guild_slash_command = delete_guild_slash_command
