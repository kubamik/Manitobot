import asyncio
import discord
import json
import requests

def parse_interaction_create(self, data):
    print(data)
    url = f"https://discord.com/api/v7/interactions/{data['id']}/{data['token']}/callback"

    json_ = {
        "type": 4,
        "data": {
            "content": "Congrats on sending your command! [Some link](http://www.discord.com)"
    }
    }
    #r = discord.http.Route('POST', f"/interactions/{data['id']}/{data['token']}/callback", channel_id=int(data['channel_id']), guild_id=int(data['guild_id']))
    r = requests.post(url, json=json_)
    #channel, _ = self._get_guild_channel(data)
    #message = discord.Message(channel=channel, data=data, state=self)
    print(json.dumps(data, indent=4))

discord.state.ConnectionState.parse_interaction_create = parse_interaction_create