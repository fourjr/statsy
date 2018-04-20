import discord
from discord.ext import commands
import asyncio
from colorthief import ColorThief
from urllib.parse import urlparse
import io
import os
import time
import json
import crasync

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

    async def save_tag(self, tag, game, id=None, *, index = 0):
        id = id or self.author.id
        await self.bot.mongo.player_tags[game].find_one_and_update({'user_id': id}, {'$set':{'tag': [tag]}}, upsert=True)

    async def remove_tag(self, game, id=None):
        id = id or self.author.id
        await self.bot.mongo.player_tags[game].find_one_and_delete({'user_id': id})

    async def get_tag(self, game, id=None):
        id = id or self.author.id
        data = await self.bot.mongo.player_tags[game].find_one({'user_id': id})

        if data is not None:
            return data['tag']
        raise KeyError

    @staticmethod
    def paginate(text: str):
        '''Simple generator that paginates text.'''
        last = 0
        pages = []
        for curr in range(0, len(text)):
            if curr % 1980 == 0:
                pages.append(text[last:curr])
                last = curr
                appd_index = curr
        if appd_index != len(text)-1:
            pages.append(text[last:curr])
        return list(filter(lambda a: a != '', pages))

    def cache(self, mode, _type, obj, tag = None):
        tag = tag or obj.get('tag')
        _type = f'backup/{_type}/'
        if mode == 'update':
            obj['updatedTime'] = time.time()
            try:
                with open(_type + tag + '.json', "w+") as f:
                    f.write(json.dumps(obj, indent=4))
            except FileNotFoundError:
                pass
        elif mode == 'get':
            try:
                with open(_type + obj + '.json') as f:
                    return crasync.models.Profile(self.bot.cr, json.load(f))
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                return False
