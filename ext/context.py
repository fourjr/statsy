import discord
from discord.ext import commands
import asyncio
from colorthief import ColorThief
from urllib.parse import urlparse
import io
import os
import json

class CustomContext(commands.Context):
    '''Custom Context class to provide utility.'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self):
        '''Returns the bot's aiohttp client session'''
        return self.bot.session

    def delete(self):
        '''shortcut'''
        return self.message.delete()

    async def purge(self, *args, **kwargs):
        '''Shortcut to channel.purge'''
        await self.channel.purge(*args, **kwargs)

    @staticmethod
    def valid_image_url(url):
        '''Checks if a url leads to an image.'''
        types = ['.png', '.jpg', '.gif', '.webp']
        parsed = urlparse(url)
        if any(parsed.path.endswith(i) for i in types):
            return url.replace(parsed.query, 'size=128')
        return False

    async def get_dominant_color(self, url=None, quality=10):
        '''
        Returns the dominant color of an image from a url
        '''
        av = self.author.avatar_url
        url = self.valid_image_url(url or av)

        if not url:
            raise ValueError('Invalid image url passed.')
        try:
            async with self.session.get(url) as resp:
                image = await resp.read()
        except:
            return discord.Color.default()

        with io.BytesIO(image) as f:
            try:
                color = ColorThief(f).get_color(quality=quality)
            except:
                return discord.Color.dark_grey()
            
        return discord.Color.from_rgb(*color)

    def load_json(self, path=None):
        with open(path or 'data/stats.json') as f:
            return json.load(f)

    def save_json(self, data, path=None):
        with open(path or 'data/stats.json', 'w') as f:
            f.write(json.dumps(data, indent=4))

    def save_tag(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json()
        data['clashroyale'][str(id)] = [tag]
        self.save_json(data)

    def add_tag(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json()
        if str(id) not in data:
            data['clashroyale'][str(id)] = []
        data['clashroyale'][str(id)].append(tag)
        self.save_json(data)

    def remove_tag(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json()
        tags = data['clashroyale'][str(id)]
        tags.remove(tag)
        self.save_json(data)

    def get_tag(self, id=None, *, index=0):
        id = id or self.author.id
        data = self.load_json()
        tags = data['clashroyale'][str(id)]
        return tags[index]

    def load_json_coc(self, path=None):
        with open(path or 'data/stats.json') as f:
            return json.load(f)

    def save_json_coc(self, data, path=None):
        with open(path or 'data/stats.json', 'w') as f:
            f.write(json.dumps(data, indent=4))

    def save_tag_coc(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json_coc()
        data['clashofclans'][str(id)] = [tag]
        self.save_json_coc(data)

    def add_tag_coc(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json_coc()
        if str(id) not in data:
            data[str(id)] = []
        data['clashofclans'][str(id)].append(tag)
        self.save_json_coc(data)

    def remove_tag_coc(self, tag, id=None):
        id = id or self.author.id
        data = self.load_json_coc()
        tags = data['clashofclans'][str(id)]
        tags.remove(tag)
        self.save_json_coc(data)

    def get_tag_coc(self, id=None, *, index=0):
        id = id or self.author.id
        data = self.load_json_coc()
        tags = data['clashofclans'][str(id)]
        return tags[index]