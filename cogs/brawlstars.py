import discord
import asyncio
from discord.ext import commands
from bs4 import BeautifulSoup
from __main__ import InvalidTag
from ext import embeds_bs
from ext import embeds_cr_crapi as embeds
from ext.paginator import PaginatorSession

shortcuts = {'juice':'2PP00', 'pulp':'PY9JLV'}

class TagCheck(commands.MemberConverter):
    
    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, tag):
        if tag in shortcuts:
            tag = shortcuts[tag]
        tag = tag.strip('#').upper().replace('O','0')
        if any(i not in self.check for i in tag):
            return False
        else:
            return tag

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass 
        else:
            return user

        # Not a user so its a tag.
        tag = self.resolve_tag(argument)

        if not tag:
            raise InvalidTag('Invalid bs-tag passed.')
        else:
            return tag
        
class Brawl_Stars:

    '''Commands relating to the Brawl Stars game made by supercell.'''

    def __init__(self, bot):
        self.bot = bot
        self.url = 'https://brawl-stars.herokuapp.com/api/'
        self.conv = TagCheck()

    async def get_band_from_profile(self, ctx, tag, message):
        url = self.url + 'players/' + tag

        async with ctx.session.get(url) as resp:
            profile = await resp.json()
        print((profile['band'] or {}).get('tag'))
        return (profile['band'] or {}).get('tag') or await ctx.send(message)

    async def resolve_tag(self, ctx, tag_or_user, band=False):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('brawlstars')
            except KeyError as e:
                await ctx.send('You don\'t have a saved tag.')
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, 'You don\'t have a band!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag('brawlstars', tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, 'That person does not have a band!')
                return tag
        else:
            return tag_or_user

    @commands.command()
    async def bssave(self, ctx, *, tag):
        '''Saves a Brawl Stars tag to your discord profile.

        Ability to save multiple tags coming soon.
        '''
        tag = self.conv.resolve_tag(tag)

        if not tag:
            raise InvalidTag('Invalid tag') 

        ctx.save_tag(tag, 'brawlstars')

        await ctx.send('Successfully saved tag.')


    @commands.command()
    @embeds.has_perms(False)
    async def bsprofile(self, ctx, tag_or_user:TagCheck=None):
        '''Get general Brawl Stars player information.'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user)
            url = self.url + 'players/' + tag
            async with ctx.session.get(url) as resp:
                if resp.status == 404:
                    raise InvalidTag('Invalid bs-tag passed')
                profile = await resp.json()

            em = await embeds_bs.format_profile(ctx, profile)
            await ctx.send(embed=em)

    @commands.command()
    @embeds.has_perms()
    async def bsband(self, ctx, tag_or_user:TagCheck=None):
        '''Get Brawl Stars band information.'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user, band=True)
            url = self.url + 'bands/' + tag
            async with ctx.session.get(url) as resp:
                if resp.status == 404:
                    raise InvalidTag('Invalid bs-band tag provided')
                band = await resp.json()

            ems = await embeds_bs.format_band(ctx, band)
        session = PaginatorSession(
            ctx=ctx,
            pages=ems
            )
        await session.run()

    @commands.command()
    @embeds.has_perms()
    async def bsevents(self, ctx):
        '''Shows the upcoming events!'''
        async with ctx.channel.typing():
            async with ctx.session.get(self.url + 'events') as resp:
                events = await resp.json()
            ems = await embeds_bs.format_events(ctx, events)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
