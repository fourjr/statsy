import aiohttp
import asyncio
import json
import time
import os

from cachetools import TTLCache
import datadog
import discord
from box import Box
from discord.ext import commands

import box
from ext import utils
from ext.command import command
from ext.embeds import brawlstars
from ext.paginator import Paginator
from locales.i18n import Translator

_ = Translator('Brawl Stars', __file__)

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

    """Commands relating to the Brawl Stars game made by supercell."""

    def __init__(self, bot):
        self.bot = bot
        self.conv = TagCheck()
        self.cache = TTLCache(500, 180)

    async def get_band_from_profile(self, ctx, tag, message):
        profile = await self.request(ctx, f'/players/{tag}')
        try:
            return profile.band.tag
        except box.BoxKeyError:
            return await ctx.send(message)

    async def resolve_tag(self, ctx, tag_or_user, band=False):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('brawlstars')
            except KeyError:
                await ctx.send(_("You don't have a saved tag. Save one using `{}bssave <tag>`!", ctx).format(ctx.prefix))
                raise utils.NoTag
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, _("You don't have a band!", ctx))
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = await ctx.get_tag('brawlstars', tag_or_user.id)
            except KeyError:
                await ctx.send('That person doesnt have a saved tag!')
                raise utils.NoTag
            else:
                if band is True:
                    return await self.get_band_from_profile(ctx, tag, _('That person does not have a band!', ctx))
                return tag
        else:
            return tag_or_user

    async def request(self, ctx, endpoint, *, leaderboard=False, reason='command'):
        try:
            self.cache[endpoint]
        except KeyError:
            if leaderboard:
                speed = time.time()
                async with ctx.session.get(
                    f'https://leaderboard.brawlstars.com/{endpoint}.jsonp?_={int(time.time()) - 4}'
                ) as resp:
                    speed = time.time() - speed
                    datadog.statsd.increment('statsy.requests', 1, [
                        'game:brawlstars', f'code:{resp.status}', f'method:{endpoint}', f'reason:{reason}'
                    ])
                    self.cache[endpoint] = json.loads((await resp.text()).replace('jsonCallBack(', '')[:-2])
            else:
                try:
                    speed = time.time()
                    async with ctx.session.get(
                        f"https://brawlapi.cf/api{endpoint}",
                        headers={'Authorization': 'abc3bab08ebe97e3ac56243b0e2793596f877051bf1c03186f23a96002cb172eb155be45492b7a9d'},
                        timeout=15
                    ) as resp:
                        speed = time.time() - speed
                        datadog.statsd.increment('statsy.api_latency', 1, [
                            'game:brawlstars', f'speed:{speed}', f'method:{endpoint}'
                        ])
                        datadog.statsd.increment('statsy.requests', 1, [
                            'game:brawlstars', f'code:{resp.status}', f'method:{endpoint}', f'reason:{reason}'
                        ])
                        try:
                            if resp.status == 200:
                                self.cache[endpoint] = await resp.json()
                            else:
                                raise utils.APIError
                        except (aiohttp.ContentTypeError, utils.APIError):
                            er = discord.Embed(
                                title=_('Brawl Stars Server Down', ctx),
                                color=discord.Color.red(),
                                description=f'This could be caused by a maintainence break or an API issue ({resp.status}).'
                            )
                            if ctx.bot.psa_message:
                                er.add_field(name=_('Please Note!', ctx), value=ctx.bot.psa_message)
                            await ctx.send(embed=er)

                            # end and ignore error
                            raise commands.CheckFailure
                except asyncio.TimeoutError:
                    await ctx.send(_('Unable to find the tag. The tag is either invalid or there is a maintainence break.', ctx))
                    raise utils.NoTag

        return Box(self.cache[endpoint], camel_killer_box=True)

    @command()
    async def bssave(self, ctx, tag, index: str = '0'):
        """Saves a Brawl Stars tag to your discord profile."""
        tag = self.conv.resolve_tag(tag)

        if not tag:
            raise utils.InvalidTag

        await ctx.save_tag(tag, 'brawlstars', index=index.replace('-', ''))
        if index == '0':
            prompt = _('Check your stats with `{}bsprofile`!', ctx).format(ctx.prefix)
        else:
            prompt = _('Check your stats with `{}bsprofile -{}`!', ctx).format(ctx.prefix, index)

        await ctx.send(_('Successfully saved tag.', ctx) + ' ' + prompt)

    @command()
    @utils.has_perms()
    async def bsprofile(self, ctx, tag_or_user: TagCheck=None):
        """Get general Brawl Stars player information."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.channel.typing():
            profile = await self.request(ctx, f'/players/{tag}')
            em = await brawlstars.format_profile(ctx, profile)

        await ctx.send(embed=em)

    @command(aliases=['bsbrawler'])
    async def bsbrawlers(self, ctx, tag_or_user: TagCheck=None):
        """Get general Brawl Stars player information."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.channel.typing():
            profile = await self.request(ctx, f'/players/{tag}')
            ems = await brawlstars.format_brawlers(ctx, profile)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def bsband(self, ctx, tag_or_user: TagCheck=None):
        """Get Brawl Stars band information."""
        tag = await self.resolve_tag(ctx, tag_or_user, band=True)

        async with ctx.channel.typing():
            band = await self.request(ctx, f'/bands/{tag}')
            ems = await brawlstars.format_band(ctx, band)

        await Paginator(ctx, *ems).start()

    @command(enabled=False)
    @utils.has_perms()
    async def bsevents(self, ctx):
        """Shows the upcoming events!"""
        async with ctx.channel.typing():
            events = await self.request('/events')
            ems = await brawlstars.format_events(ctx, events)

        await Paginator(ctx, *ems).start()

    @command(aliases=['bsrobo'])
    @utils.has_perms()
    async def bsroborumble(self, ctx):
        """Shows the robo rumble leaderboard"""
        async with ctx.channel.typing():
            leaderboard = await self.request(ctx, 'rumbleboard', leaderboard=True)
            ems = brawlstars.format_robo(ctx, leaderboard)

        await Paginator(ctx, *ems).start()

    @command(aliases=['bsboss'])
    @utils.has_perms()
    async def bsbossfight(self, ctx):
        """Shows the boss fight leaderboard"""
        async with ctx.channel.typing():
            leaderboard = await self.request(ctx, 'bossboard', leaderboard=True)
            ems = brawlstars.format_boss(ctx, leaderboard)

        await Paginator(ctx, *ems).start()


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
