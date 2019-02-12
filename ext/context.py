import io
from urllib.parse import urlparse

import discord
import pymongo
from colorthief import ColorThief
from discord.ext import commands


class CustomContext(commands.Context):
    """Custom Context class to provide utility."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = self.bot.session
        self.force_cog = None

    @property
    def cog(self):
        """Returns the cog associated with this context's command. None if it does not exist."""
        if self.force_cog:
            return self.force_cog

        if self.command:
            return self.command.instance

    def delete(self):
        """shortcut"""
        return self.message.delete()

    async def purge(self, *args, **kwargs):
        """Shortcut to channel.purge"""
        await self.channel.purge(*args, **kwargs)

    @staticmethod
    def valid_image_url(url):
        """Checks if a url leads to an image."""
        types = ['.png', '.jpg', '.gif', '.webp']
        parsed = urlparse(url)
        if any(parsed.path.endswith(i) for i in types):
            return url.replace(parsed.query, 'size=128')
        return False

    async def get_dominant_color(self, url=None, quality=10):
        """
        Returns the dominant color of an image from a url
        """
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

    async def save_tag(self, tag, game, id=None, *, index='0'):
        id = id or self.author.id

        await self.bot.mongo.player_tags[game].find_one_and_update(
            {
                'user_id': str(id)
            },
            {
                '$set': {f'tag.{index}': tag}
            },
            upsert=True,
            return_document=pymongo.ReturnDocument.AFTER
        )

    async def remove_tag(self, game, id=None):
        id = id or self.author.id
        await self.bot.mongo.player_tags[game].find_one_and_delete({'user_id': id})

    async def get_tag(self, game, id=None, *, index='0'):
        id = id or self.author.id
        data = await self.bot.mongo.player_tags[game].find_one({'user_id': str(id)})

        if index == 'all':
            return (data or {}).get('tag', [])

        try:
            if data['tag'][index] is not None:
                return data['tag'][index]
        except (TypeError, KeyError):
            pass
        raise KeyError

    @staticmethod
    def paginate(text: str):
        """Simple generator that paginates text."""
        last = 0
        pages = []
        for curr in range(0, len(text)):
            if curr % 1980 == 0:
                pages.append(text[last:curr])
                last = curr
                appd_index = curr
        if appd_index != len(text) - 1:
            pages.append(text[last:curr])
        return list(filter(lambda a: a != '', pages))


class NoContext(CustomContext):
    """Designed to create a Context with only an author
    and no message. Some methods might fail
    """
    def __init__(self, bot, user):
        self.bot = bot
        self.author = user
        self.session = self.bot.session
        self.prefix = None
        self.guild = getattr(user, 'guild', None)

    async def send(self, *args, **kwargs):
        pass
