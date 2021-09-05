from abc import ABC
from typing import Optional

import discord

from manitobot.interactions.components import ComponentMessage, ComponentTypes
from manitobot.interactions.commands_types import SlashOptionType


class BaseInteraction(ABC):
    """Base interaction for all types of interactions sent by discord"""
    def __init__(self, state, channel, data):
        self._state = state
        self.id = int(data['id'])
        self.channel = channel
        self.type = int(data['type'])
        self.application_id = int(data.get('application_id', 0)) or None  # not sure if field is present
        self.token = data.get('token')
        self.acked = False
        self.guild_id = int(data.get('guild_id', 0)) or None

        try:
            author = data.get('member', data)['user']
            self.author = self._handle_user(author)
            self.author = self._handle_member(data['member'], self.author)
        except KeyError:
            pass

        webhook_data = {
            'id': self.application_id,
            'type': 1,
            'token': self.token,
        }
        self._webhook = discord.Webhook.from_state(webhook_data, state=state)

    @discord.utils.cached_property
    def guild(self):
        return getattr(self.channel, 'guild', None)

    def _handle_user(self, user):
        user_obj = self._state.store_user(user)
        if isinstance(self.guild, discord.Guild):
            found = self.guild.get_member(user_obj.id)
            if found is not None:
                user_obj = found
        return user_obj

    def _handle_member(self, member, user):
        try:
            user._update_from_message(member)
        except AttributeError:
            user = discord.Member._from_message(message=self, data=member)
        return user

    def dispatch(self, *args, **kwargs):
        self._state.dispatch(*args, **kwargs)

    async def ack(self):
        if self.acked:
            raise discord.ClientException('Response already created')
        self.acked = True
        await self._state.http.ack_interaction(self.token, self.id)

    async def respond(self, content=None, *, embed=None, embeds=None,
                      tts=False, allowed_mentions=None, ephemeral=False):
        state = self._state
        content = str(content) if content is not None else None

        if embeds is not None and embed is not None:
            raise discord.InvalidArgument('Cannot mix embed and embeds keyword arguments.')

        if embeds is not None:
            if len(embeds) > 10:
                raise discord.InvalidArgument('embeds has a maximum of 10 elements.')
            embeds = [e.to_dict() for e in embeds]
        if embed is not None:
            embed = embed.to_dict()

        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
        else:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()
        if self.acked:
            raise discord.ClientException('Response already created')
        self.acked = True
        await state.http.respond_interaction(self.token, self.id, content, tts=tts, embed=embed, embeds=embeds,
                                             allowed_mentions=allowed_mentions, ephemeral=ephemeral)

    async def edit(self, **fields):
        await self._webhook.edit_message('@original', **fields)

    async def delete(self):
        await self._webhook.delete_message('@original')

    async def send(self, content=None, *, tts=False, file=None, files=None,
                   embed=None, embeds=None, allowed_mentions=None, ephemeral=False):
        if not self.acked:
            await self.ack()

        payload = {}
        if files is not None and file is not None:
            raise discord.InvalidArgument('Cannot mix file and files keyword arguments.')
        if embeds is not None and embed is not None:
            raise discord.InvalidArgument('Cannot mix embed and embeds keyword arguments.')

        if embeds is not None:
            if len(embeds) > 10:
                raise discord.InvalidArgument('embeds has a maximum of 10 elements.')
            payload['embeds'] = [e.to_dict() for e in embeds]

        if embed is not None:
            payload['embeds'] = [embed.to_dict()]

        if content is not None:
            payload['content'] = str(content)

        if ephemeral:
            payload['flags'] = 1 << 6

        payload['tts'] = tts

        previous_mentions = getattr(self._state, 'allowed_mentions', None)

        if allowed_mentions:
            if previous_mentions is not None:
                payload['allowed_mentions'] = previous_mentions.merge(allowed_mentions).to_dict()
            else:
                payload['allowed_mentions'] = allowed_mentions.to_dict()
        elif previous_mentions is not None:
            payload['allowed_mentions'] = previous_mentions.to_dict()

        return await self._webhook._adapter.execute_webhook(wait=True, file=file, files=files, payload=payload)


class CommandInteraction(BaseInteraction):
    """Interaction get from discord when user used application command. Used as commands context.
    Without support for subcommands.
    """
    def __init__(self, *, state, channel, data):
        super(CommandInteraction, self).__init__(state, channel, data)

        try:
            self.command = self.name = data.get('data').get('name')
            self.command_id = int(data.get('data').get('id', 0)) or None
        except AttributeError:
            self.command = None
            self.command_id = None

        self.kwargs = {}
        if 'options' in data['data']:
            for option in data['data']['options']:
                k, v = self._parse_option(option)
                self.kwargs[k] = v

        target = data['data'].get('target_id')
        self.target_id = target and int(target)
        res = data['data'].get('resolved', dict())
        command_type = data['data'].get('type', 0)
        if command_type == 2 and target in res.get('users', {}):
            try:
                self.target = self._handle_user(res['users'][target])
                self.target = self._handle_member(res['members'][target], self.target)
            except KeyError:
                pass
        elif command_type == 3 and target in res.get('messages', {}):
            found = self._state._get_message(self.target_id)
            if found:
                self.target = found
            else:
                self.target = discord.Message(state=state, channel=channel, data=res['messages'][target])
        else:
            self.target = None

    def _parse_option(self, data):
        name = data.get('name')
        option_type = discord.enums.try_enum(SlashOptionType, data.get('type'))
        value = data.get('value')
        if option_type is SlashOptionType.user:
            value = int(value)
            member = self.guild and self.guild.get_member(value)
            value = member or self._state.get_user(value)
        elif option_type is SlashOptionType.channel:
            value = self._state.get_channel(int(value))
        elif option_type is SlashOptionType.role:
            value = self.guild and self.guild.get_role(int(value))
        return name, value


class ComponentInteraction(BaseInteraction):
    """Interaction get from discord when user interacted with message component.
    """
    message: Optional[ComponentMessage]

    def __init__(self, state, channel, data):
        super(ComponentInteraction, self).__init__(state, channel, data)

        if 'message' in data:
            message = data['message']
            found = self._state._get_message(int(message['id']))
            if found:
                self.message = ComponentMessage.from_message(found, message)
            else:
                self.message = ComponentMessage(state=state, channel=channel, data=message)
        else:
            self.message = None

        self.custom_id = data['data'].get('custom_id', '')
        self.component_type = int(data['data'].get('component_type', 0))
        self.values = data['data'].get('values', list())

    async def ack_for_update(self):
        if self.acked:
            raise discord.ClientException('Response already created')
        self.acked = True
        await self._state.http.ack_interaction_update(self.token, self.id)

    async def edit_message(self, **fields):
        if self.acked:
            raise discord.ClientException('Response already created')

        try:
            content = fields['content']
        except KeyError:
            pass
        else:
            if content is not None:
                fields['content'] = str(content)

        try:
            embed = fields['embed']
        except KeyError:
            pass
        else:
            if embed is not None:
                fields['embed'] = embed.to_dict()

        try:
            suppress = fields.pop('suppress')
        except KeyError:
            pass
        else:
            flags = discord.MessageFlags._from_value(self.message.flags.value)
            flags.suppress_embeds = suppress
            fields['flags'] = flags.value

        delete_after = fields.pop('delete_after', None)

        try:
            allowed_mentions = fields.pop('allowed_mentions')
        except KeyError:
            pass
        else:
            if allowed_mentions is not None:
                if self._state.allowed_mentions is not None:
                    allowed_mentions = self._state.allowed_mentions.merge(allowed_mentions).to_dict()
                else:
                    allowed_mentions = allowed_mentions.to_dict()
                fields['allowed_mentions'] = allowed_mentions

        try:
            components = [{'type': ComponentTypes.ActionRow, 'components': [comp.to_dict() for comp in action]}
                          for action in fields['components']]
        except KeyError:
            pass
        else:
            fields['components'] = components

        if fields:
            self.acked = True
            await self._state.http.interaction_edit_message(self.token, self.id, **fields)
            self.message._update(fields)

        if delete_after is not None:
            await self.message.delete(delay=delete_after)
