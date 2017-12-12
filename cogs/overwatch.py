import discord, aiohttp
from discord.ext import commands
from ext import embeds_ov
import json
from __main__ import InvalidTag
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

    async def resolve_tag(self, ctx, tag_or_user):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('overwatch')
            except Exception as e:
                print(e)
                await ctx.send('You don\'t have a saved tag.')
                raise e
            else:
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag('overwatch', tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
                raise e
            else:
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    async def ovprofile(self, ctx, region, *, tag_or_user: TagCheck=None):
        '''Gets the Overwatch profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)
        region = region.lower()
        tag = tag.replace('#', '-')
        ems = []

        await ctx.trigger_typing()

        try:
            async with self.session.get(f"https://owapi.net/api/v3/u/{tag}/stats") as p:
                profile = await p.json()
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            for region, r_name in {"kr": "Asia", "eu": "Europe", "us": "America"}.items():
                try:
                    ems_temp = await embeds_ov.format_profile(ctx, tag.split('-')[0], profile[region]['stats'])
                except:
                    pass
                else:
                    for _em in ems_temp:
                        _em.title += f" - {r_name}"
                    ems += ems_temp
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
    async def ovsave(self, ctx, *, tag):
        '''Saves a Overwatch tag to your discord.

        Ability to save multiple tags coming soon.
        '''
        ctx.save_tag(tag.replace("#", "-"), 'overwatch')
        await ctx.send('Successfuly saved tag.')



def setup(bot):
    cog = Overwatch(bot)
    bot.add_cog(cog)
