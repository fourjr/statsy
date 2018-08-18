import json
import time

import abrawlpy
import discord
from discord.ext import commands

import box
from ext import embeds_bs, utils
from ext.paginator import PaginatorSession

shortcuts = {
    'juice': '2PP00',
    'pulp': 'PY9JLV'
}


class TagCheck(commands.MemberConverter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, tag):
        if tag in shortcuts:
            tag = shortcuts[tag]
        tag = tag.strip('#').upper().replace('O', '0')
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
            raise utils.InvalidTag('Invalid bs-tag passed.')
        else:
            return tag


class Brawl_Stars:

    '''Commands relating to the Brawl Stars game made by supercell.'''

    def __init__(self, bot):
        self.bot = bot
        self.conv = TagCheck()

    async def get_band_from_profile(self, ctx, tag, message):
        try:
            profile = await self.bot.bs.get_player(tag)
        except abrawlpy.errors.RequestError:
                await ctx.send(embed=discord.Embed(
                    title='API Down',
                    description='API Error',
                    color=0xd22630
                ))
        else:
            try:
                return profile.band.tag
            except box.BoxKeyError:
                return await ctx.send(message)

    async def resolve_tag(self, ctx, tag_or_user, band=False):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('brawlstars')
            except KeyError:
                await ctx.send('You don\'t have a saved tag.')
                raise utils.NoTag
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, 'You don\'t have a band!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = await ctx.get_tag('brawlstars', tag_or_user.id)
            except KeyError:
                await ctx.send('That person doesnt have a saved tag!')
                raise utils.NoTag
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, 'That person does not have a band!')
                return tag
        else:
            return tag_or_user

    @commands.command(enabled=False)
    async def bssave(self, ctx, *, tag):
        '''Saves a Brawl Stars tag to your discord profile.

        Ability to save multiple tags coming soon.
        '''
        tag = self.conv.resolve_tag(tag)

        if not tag:
            raise utils.InvalidTag('Invalid tag')

        await ctx.save_tag(tag, 'brawlstars')

        await ctx.send('Successfully saved tag.')

    @commands.command(enabled=False)
    async def bsprofile(self, ctx, tag_or_user: TagCheck=None):
        '''Get general Brawl Stars player information.'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user)
            try:
                profile = await self.bot.bs.get_player(tag)
            except abrawlpy.errors.RequestError:
                await ctx.send(embed=discord.Embed(
                    title='API Down',
                    description='API Error',
                    color=0xd22630
                ))
            else:
                em = await embeds_bs.format_profile(ctx, profile)
                await ctx.send(embed=em)

    @commands.command(enabled=False)
    @utils.has_perms()
    async def bsband(self, ctx, tag_or_user: TagCheck=None):
        '''Get Brawl Stars band information.'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user, band=True)
            try:
                band = await self.bot.bs.get_band(tag)
            except abrawlpy.errors.RequestError:
                return await ctx.send(embed=discord.Embed(
                    title='API Down',
                    description='API Error',
                    color=0xd22630
                ))
            else:
                ems = await embeds_bs.format_band(ctx, band)
        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @commands.command(enabled=False)
    @utils.has_perms()
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

    @commands.command(aliases=['bsrobo'])
    @utils.has_perms()
    async def bsroborumble(self, ctx):
        """Shows the robo rumble leaderboard"""
        async with ctx.channel.typing():
            async with ctx.session.get(f'https://leaderboard.brawlstars.com/rumbleboard.jsonp?_={int(time.time())}') as resp:
                leaderboard = json.loads((await resp.text()).replace('jsonCallBack(', '')[:-2])
            ems = embeds_bs.format_robo(ctx, leaderboard)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
