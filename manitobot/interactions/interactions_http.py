import logging

import discord
from discord.http import Route

from .interaction import CommandInteraction, ComponentInteraction


def parse_interaction_create(self, data):
    try:  # error here stops main bot loop
        if 'channel_id' not in data:
            return
        channel, _ = self._get_guild_channel(data)
        if data.get('type') == 2:
            inter = CommandInteraction(state=self, channel=channel, data=data)
            self.dispatch('command_interaction', inter)
        elif data.get('type') == 3:
            inter = ComponentInteraction(state=self, channel=channel, data=data)
            self.dispatch('component_interaction', inter)
    except Exception:
        logging.exception('Serious exception - interaction parsing')


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


def bulk_overwrite_global_slash_commands(self, application_id, commands):
    r = discord.http.Route('PUT', '/applications/{application_id}/commands', application_id=application_id)

    return self.request(r, json=commands)


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


def bulk_overwrite_guild_slash_commands(self, application_id, guild_id, commands):
    r = discord.http.Route('PUT', '/applications/{application_id}/guilds/{guild_id}/commands',
                           application_id=application_id, guild_id=guild_id)

    return self.request(r, json=commands)


def batch_edit_slash_commands_permissions(self, application_id, guild_id, permissions):
    r = discord.http.Route('PUT', '/applications/{application_id}/guilds/{guild_id}/commands/permissions',
                           application_id=application_id, guild_id=guild_id)

    return self.request(r, json=permissions)


discord.http.HTTPClient.get_global_slash_commands = get_global_slash_commands
discord.http.HTTPClient.create_global_slash_command = create_global_slash_command
discord.http.HTTPClient.edit_global_slash_command = edit_global_slash_command
discord.http.HTTPClient.delete_global_slash_command = delete_global_slash_command
discord.http.HTTPClient.bulk_overwrite_global_slash_commands = bulk_overwrite_global_slash_commands

discord.http.HTTPClient.get_guild_slash_commands = get_guild_slash_commands
discord.http.HTTPClient.create_guild_slash_command = create_guild_slash_command
discord.http.HTTPClient.edit_guild_slash_command = edit_guild_slash_command
discord.http.HTTPClient.delete_guild_slash_command = delete_guild_slash_command
discord.http.HTTPClient.bulk_overwrite_guild_slash_commands = bulk_overwrite_guild_slash_commands
discord.http.HTTPClient.batch_edit_slash_commands_permissions = batch_edit_slash_commands_permissions


def send_files_components(self, channel_id, *, files, content=None, tts=False, embed=None, nonce=None,
                          allowed_mentions=None, message_reference=None, components=None):
    r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
    form = []

    payload = {'tts': tts}
    if content:
        payload['content'] = content
    if embed:
        payload['embed'] = embed
    if nonce:
        payload['nonce'] = nonce
    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions
    if message_reference:
        payload['message_reference'] = message_reference
    if components:
        payload['components'] = components

    form.append({'name': 'payload_json', 'value': discord.utils.to_json(payload)})
    if len(files) == 1:
        file = files[0]
        form.append({
            'name': 'file',
            'value': file.fp,
            'filename': file.filename,
            'content_type': 'application/octet-stream'
        })
    else:
        for index, file in enumerate(files):
            form.append({
                'name': 'file%s' % index,
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream'
            })

    return self.request(r, form=form, files=files)


def send_message_components(self, channel_id, content, *, tts=False, embed=None, nonce=None, allowed_mentions=None,
                 message_reference=None, components=None):
    r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
    payload = {}

    if content:
        payload['content'] = content

    if tts:
        payload['tts'] = True

    if embed:
        payload['embed'] = embed

    if nonce:
        payload['nonce'] = nonce

    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions

    if message_reference:
        payload['message_reference'] = message_reference

    if components:
        payload['components'] = components

    return self.request(r, json=payload)


def ack_interaction_update(self, token, interaction_id):
    r = discord.http.Route('POST', '/interactions/{interaction_id}/{token}/callback',
                           interaction_id=interaction_id, token=token)
    payload = {'type': 6}

    return self.request(r, json=payload)


def interaction_edit_message(self, token, interaction_id, **data):
    r = discord.http.Route('POST', '/interactions/{interaction_id}/{token}/callback',
                           interaction_id=interaction_id, token=token)
    payload = {'type': 7, 'data': data}

    return self.request(r, json=payload)


discord.http.HTTPClient.send_files_components = send_files_components
discord.http.HTTPClient.send_message_components = send_message_components
discord.http.HTTPClient.ack_interaction_update = ack_interaction_update
discord.http.HTTPClient.interaction_edit_message = interaction_edit_message
