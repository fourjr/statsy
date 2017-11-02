import discord
from discord.ext import commands
import asyncio
from colorthief import ColorThief
from urllib.parse import urlparse
import io
import os

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