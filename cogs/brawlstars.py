import discord
import asyncio
from discord.ext import commands
from bs4 import BeautifulSoup
from __main__ import InvalidTag
from ext import embeds_bs
from ext import embeds
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
        self.url = 'https://bsproxy.herokuapp.com/'
        self.conv = TagCheck()

    async def get_band_from_profile(self, ctx, tag, message):
        url = 'https://bsproxy.herokuapp.com/' + 'players/' + tag

        async with ctx.session.get(url) as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')
        try:
            band_tag = soup.find('main') \
                .find('section', attrs={'class':'ui-card pt-4'}) \
                .find('div', attrs={'class':'container'}) \
                .find('div', attrs={'class':'stat-section'}) \
                .find_all('div', attrs={'class':'col-12 mt-1'})[2] \
                .find('div', attrs={'class':'band-history-entry'}) \
                .find('a') \
                .find('div', attrs={'class':'card jumpc mb-2'}) \
                .find('div', attrs={'class':'card-body'}) \
                .find('div', attrs={'class':'band-info'}) \
                .find('div', attrs={'class':'band-tag'}).getText().strip('#')
        except AttributeError:
            await ctx.send(message)
            raise ValueError(message)
        else:
            return band_tag

    async def resolve_tag(self, ctx, tag_or_user, band=False):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('brawlstars')
            except Exception as e:
                print(e)
                await ctx.send('You don\'t have a saved tag.')
                raise e
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, 'You don\'t have a band!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag('brawlstars', tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
                raise e
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
            url = self.url + 'players/' + tag + '?refresh=1'
            async with ctx.session.get(url) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')

            em = await embeds_bs.format_profile(ctx, soup, tag)
            await ctx.send(embed=em[0], file=em[1])

    @commands.command()
    @embeds.has_perms()
    async def bsband(self, ctx, tag_or_user:TagCheck=None):
        '''Get Brawl Stars band information.'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user, band=True)
            url = self.url + 'bands/' + tag + '?refresh=1'
            async with ctx.session.get(url) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')

            ems = await embeds_bs.format_band(ctx, soup, tag)
        session = PaginatorSession(
            ctx=ctx,
            pages=ems,
            file = ems[2]
            )
        await session.run()

    @commands.command()
    @embeds.has_perms()
    async def bsevents(self, ctx):
        '''Shows the upcoming events!'''
        async with ctx.channel.typing():
            async with ctx.session.get(self.url + 'events/') as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')
            ems = await embeds_bs.format_events(ctx, soup)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
            )
        await session.run()


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
