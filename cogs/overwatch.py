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
        return argument.strip('#').upper()

class Overwatch:
    '''Commands relating to the Overwatch game.'''

    def __init__(self, bot):
        self.bot = bot
        self.conv = TagCheck()

    async def resolve_tag(self, ctx, tag_or_user):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('overwatch')
            except Exception as e:
                print(e)
                await ctx.send('You don\'t have a saved tag.')
                raise e
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'You don\'t have a clan!')
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
        tag = tag.replace('#', '-')

        async with ctx.typing():
            try:
                async with ctx.session.get(f"https://owapi.net/api/v3/u/{tag}/stats") as p:
                    profile = await p.json()
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                em = await embeds_ov.format_profile(profile[region])
                try:
                    em.set_author(name=tag.split('-')[0], icon_url=profile[region]['overall_stats']['avatar'])
                except:
                    em.set_author(name=tag.split('-')[0])
                await ctx.send(embed=em)

            
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
