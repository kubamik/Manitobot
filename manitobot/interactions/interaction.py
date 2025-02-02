import asyncio
from abc import ABC
from typing import Optional, Sequence, Any, List, Union

import discord
from discord import Poll, File, Embed, AllowedMentions, MessageFlags, Attachment, ForumTag
from discord.abc import Snowflake
from discord.http import handle_message_parameters
from discord.utils import MISSING
import discord.webhook.async_ as async_webhook

from manitobot.interactions.components import ComponentMessage, ComponentTypes, Button, Select
from manitobot.interactions.commands_types import SlashOptionType


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
                'type': ComponentTypes.ActionRow,
                'components': [comp.to_dict() for comp in action]
                } for action in self.components_list
            ]

        return None

    @classmethod
    def from_message(cls, message: discord.Message, /, *, timeout: Optional[float] = None):
        # TODO: Implement this method
        raise NotImplementedError()

    def is_finished(self):
        return True


class BaseInteraction(ABC):
    """Base interaction for all types of interactions sent by discord"""
    def __init__(self, state, channel, data):
        self._state = state
        self._session = state.http._HTTPClient__session
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

    async def ack(self, ephemeral=False):
        if self.acked:
            raise discord.ClientException('Response already created')
        self.acked = True

        await self._ack_interaction(type_=discord.InteractionResponseType.deferred_channel_message.value,
                                    ephemeral=ephemeral)

    async def _ack_interaction(self, type_, ephemeral=False):
        adapter = async_webhook.async_context.get()
        http = self._state.http
        params = async_webhook.interaction_response_params(type_, {'flags': (1 << 6) * ephemeral})
        await adapter.create_interaction_response(
            self.id, self.token,
            session=self._session,
            proxy=http.proxy,
            proxy_auth=http.proxy_auth,
            params=params)

    async def respond(
        self,
        content: Optional[Any] = None,
        *,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        components: List[List[Button | Select]] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        allowed_mentions: AllowedMentions = MISSING,
        suppress_embeds: bool = False,
        silent: bool = False,
        delete_after: Optional[float] = None,
        poll: Poll = MISSING,
    ):
        if self.acked:
            raise discord.ClientException('Response already created')

        if ephemeral or suppress_embeds or silent:
            flags = MessageFlags._from_value(0)
            flags.ephemeral = ephemeral
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING

        adapter = async_webhook.async_context.get()
        params = async_webhook.interaction_message_response_params(
            type=discord.InteractionResponseType.channel_message.value,
            content=content,
            tts=tts,
            flags=flags,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            view=Components(components) if components else MISSING,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=self._state.allowed_mentions,
            poll=poll
        )

        http = self._state.http
        await adapter.create_interaction_response(
            self.id,
            self.token,
            session=self._session,
            proxy=http.proxy,
            proxy_auth=http.proxy_auth,
            params=params,
        )

        self.acked = True

        if delete_after is not None:

            async def inner_call(delay: float = delete_after):
                await asyncio.sleep(delay)
                try:
                    await self.delete()
                except discord.HTTPException:
                    pass

            asyncio.create_task(inner_call())

    async def edit(
        self, *,
        content: Optional[str] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        components: Optional[List[List[Button | Select]]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None
    ):
        previous_mentions: Optional[AllowedMentions] = self._state.allowed_mentions
        with handle_message_parameters(
                content=content,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                view=Components(components) if isinstance(components, list) else components,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=previous_mentions,
        ) as params:
            adapter = async_webhook.async_context.get()
            http = self._state.http
            await adapter.edit_original_interaction_response(
                self.application_id,
                self.token,
                session=self._session,
                proxy=http.proxy,
                proxy_auth=http.proxy_auth,
                payload=params.payload,
                multipart=params.multipart,
                files=params.files,
            )

    async def delete(self):
        adapter = async_webhook.async_context.get()
        http = self._state.http
        await adapter.delete_original_interaction_response(
            self.application_id,
            self.token,
            session=self._session,
            proxy=http.proxy,
            proxy_auth=http.proxy_auth,
        )

    async def send(
        self,
        content: str = MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = False,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        components: List[List[Button | Select]] = MISSING,
        thread: Snowflake = MISSING,
        thread_name: str = MISSING,
        suppress_embeds: bool = False,
        silent: bool = False,
        applied_tags: List[ForumTag] = MISSING,
        poll: Poll = MISSING,
    ):
        if not self.acked:
            await self.ack(ephemeral)

        payload = {
            'id': self.application_id,
            'type': 3,
            'token': self.token,
        }
        webhook = async_webhook.Webhook.from_state(data=payload, state=self._state)

        return await webhook.send(
            content=content,
            tts=tts,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            view=Components(components) if components else None,
            thread=thread,
            thread_name=thread_name,
            suppress=suppress_embeds,
            silent=silent,
            applied_tags=applied_tags,
            poll=poll,
            wait=True
        )


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
        await self._ack_interaction(type_=discord.InteractionResponseType.deferred_message_update.value)

    async def edit_message(
        self,
        *,
        content: Optional[Any] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        components: Optional[List[List[Button | Select]]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        delete_after: Optional[float] = None,
        suppress_embeds: bool = MISSING,
    ):
        if self.acked:
            raise discord.ClientException('Response already created')

        if suppress_embeds is not MISSING:
            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
        else:
            flags = MISSING

        adapter = async_webhook.async_context.get()
        params = async_webhook.interaction_message_response_params(
            type=discord.InteractionResponseType.message_update.value,
            content=content,
            embed=embed,
            embeds=embeds,
            view=Components(components) if isinstance(components, list) else components,
            attachments=attachments,
            previous_allowed_mentions=self._state.allowed_mentions,
            allowed_mentions=allowed_mentions,
            flags=flags,
        )

        http = self._state.http
        await adapter.create_interaction_response(
            self.id,
            self.token,
            session=self._session,
            proxy=http.proxy,
            proxy_auth=http.proxy_auth,
            params=params,
        )

        self.acked = True

        if delete_after is not None:

            async def inner_call(delay: float = delete_after):
                await asyncio.sleep(delay)
                try:
                    await self.delete()
                except discord.HTTPException:
                    pass

            asyncio.create_task(inner_call())
