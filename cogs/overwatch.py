import discord, aiohttp
from discord.ext import commands
from ext import embeds_ov
import json
from __main__ import InvalidTag, NoTag
from ext.paginator import PaginatorSession
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from urllib.request import urlretrieve
import io
import string
import os


class TagCheck(commands.MemberConverter):

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass 
        else:
            return user

        # Not a user so its a tag.
        return argument.replace("#", "-")

class Overwatch:
    '''Commands relating to the Overwatch game.'''

    def __init__(self, bot):
        self.bot = bot
        self.conv = TagCheck()
        self.session = aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'})
        self.session2 = aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"})
        self.session3 = aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0"})

    def __unload(self):
        self.bot.loop.create_task(self.session.close())
        self.bot.loop.create_task(self.session2.close())
        self.bot.loop.create_task(self.session3.close())

    async def resolve_tag(self, ctx, tag_or_user):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('overwatch')
            except KeyError:
                await ctx.send(f'You don\'t have a saved tag. Save one using {ctx.prefix}owsave <tag>!')
                raise NoTag()
            else:
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = await ctx.get_tag('overwatch', tag_or_user.id)
            except KeyError:
                await ctx.send('That person doesnt have a saved tag!')
                raise NoTag()
            else:
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    async def owprofile(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the Overwatch profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)
        tag = tag.replace('#', '-')
        ems = []

        await ctx.trigger_typing()

        try:
            async with self.session.get(f"https://owapi.net/api/v3/u/{tag}/stats") as p:
                profile = await p.json()
            async with self.session.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                heroes = await h.json()
                if "error" in heroes:
                    async with self.session2.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                        heroes = await h.json()
                        if "error" in heroes:
                            async with self.session3.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                                heroes = await h.json()
                
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            try:
                ems = await embeds_ov.format_profile(ctx, tag.split('-')[0], profile["kr"]['stats'], heroes["kr"]['heroes'])
            except Exception as e:
                raise e
            if len(ems) > 1:
                session = PaginatorSession(
                    ctx=ctx, 
                    pages=ems
                    )
                await session.run()
            elif len(ems) == 0:
                await ctx.send("There aren't any stats for this user!")
            else:
                await ctx.send(embed=ems[0])

            
    @commands.command()
    async def owsave(self, ctx, *, tag):
        '''Saves a Overwatch tag to your discord.

        Ability to save multiple tags coming soon.
        '''
        await ctx.save_tag(tag.replace("#", "-"), 'overwatch')
        await ctx.send('Successfuly saved tag.')



def setup(bot):
    cog = Overwatch(bot)
    bot.add_cog(cog)
