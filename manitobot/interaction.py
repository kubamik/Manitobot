import discord

from .slash_types import SlashOptionType


class Interaction:
    """Interaction get from discord when user used slash command. Used as slash command context.
    Without support for subcommands.
    """
    def __init__(self, *, state, channel, data):
        self._state = state
        self.id = int(data['id'])
        self.channel = channel
        self.type = int(data['type'])
        self.application_id = int(data.get('application_id', 0)) or None  # not sure if field is present
        self.token = data.get('token')
        self.acked = False
        self.guild_id = int(data.get('application_id', 0)) or None
        try:
            self.command = self.name = data.get('data').get('name')
            self.command_id = int(data.get('data').get('id', 0)) or None
        except AttributeError:
            self.command = None
            self.command_id = None

        try:
            author = data.get('member', data)['user']
            self._handle_author(author)
            self._handle_member(data['member'])
        except KeyError:
            pass

        self.kwargs = {}
        if 'options' in data['data']:
            for option in data['data']['options']:
                k, v = self._parse_option(option)
                self.kwargs[k] = v

        webhook_data = {
            'id': self.application_id,
            'type': 1,
            'token': self.token,
        }
        self._webhook = discord.Webhook.from_state(webhook_data, state=state)

    @discord.utils.cached_property
    def guild(self):
        return getattr(self.channel, 'guild', None)

    @property
    def guild_name(self):
        if self.guild_id:
            return self.name + '_' + str(self.guild_id)
        return self.name

    def _handle_author(self, author):  # Copied from dpy
        self.author = self._state.store_user(author)
        if isinstance(self.guild, discord.Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member):  # Copied from dpy
        author = self.author
        try:
            author._update_from_message(member)
        except AttributeError:
            self.author = discord.Member._from_message(message=self, data=member)

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
