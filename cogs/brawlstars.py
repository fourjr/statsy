import aiohttp
import asyncio
import json
import time
import random
import os

import brawlstats
import datadog
import discord
import requests
from box import Box
from cachetools import TTLCache
from discord.ext import commands

import box
from ext import utils
from ext.command import cog, command
from ext.context import NoContext
from ext.embeds import brawlstars
from ext.paginator import Paginator
from locales.i18n import Translator

_ = Translator('Brawl Stars', __file__)

shortcuts = {
    'juice': '2PP00',
    'pulp': 'PY9JLV'
}


class TagCheck(commands.UserConverter):

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
            raise utils.InvalidBSTag
        else:
            return tag


@cog('bs')
class Brawl_Stars:

    """Commands relating to the Brawl Stars game made by supercell."""

    def __init__(self, bot):
        self.bot = bot
        self.alias = 'bs'
        self.conv = TagCheck()
        self.cache = TTLCache(500, 180)
        self.bs = brawlstats.core.Client(
            os.getenv('brawlstars'),
            session=bot.session,
            is_async=True,
            timeout=20,
            url=os.getenv('bs_url')
        )
        self.constants = box.Box(json.loads(requests.get('https://fourjr.herokuapp.com/bs/constants').text), camel_killer_box=True)

    async def __local_check(self, ctx):
        if ctx.guild:
            guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}
            return guild_info.get('games', {}).get(self.__class__.__name__, True)
        else:
            return True

    async def __error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, brawlstats.NotFoundError):
            await ctx.send(_('The tag cannot be found!'))
        elif isinstance(error, brawlstats.RequestError):
            er = discord.Embed(
                title=_('Brawl Stars Server Down'),
                color=discord.Color.red(),
                description='This could be caused by a maintainence break.'
            )
            if ctx.bot.psa_message:
                er.add_field(name=_('Please Note!'), value=ctx.bot.psa_message)
            await ctx.send(embed=er)

    async def get_club_from_profile(self, ctx, tag, message):
        profile = await self.request(ctx, 'get_player', tag)
        try:
            return profile.club.tag
        except AttributeError:
            return await ctx.send(message)

    async def resolve_tag(self, ctx, tag_or_user, club=False):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('brawlstars')
            except KeyError:
                try:
                    default_game = self.bot.default_game[ctx.guild.id]
                except AttributeError:
                    default_game = self.bot.default_game[ctx.channel.id]
                cmd_name = 'save' if default_game == self.__class__.__name__ else f'{self.alias}save'

                await ctx.send(_("You don't have a saved tag. Save one using `{}{} <tag>`!").format(ctx.prefix, cmd_name))
                raise utils.NoTag
            else:
                if club is True:
                    return await self.get_club_from_profile(ctx, tag, _("You don't have a club!"))
                return tag
        if isinstance(tag_or_user, discord.User):
            try:
                tag = await ctx.get_tag('brawlstars', tag_or_user.id)
            except KeyError:
                await ctx.send('That person doesnt have a saved tag!')
                raise utils.NoTag
            else:
                if club is True:
                    return await self.get_club_from_profile(ctx, tag, _('That person does not have a club!'))
            return tag
        else:
            return tag_or_user

    async def request(self, ctx, method, *args, **kwargs):
        leaderboard = kwargs.pop('leaderboard', False)
        reason = kwargs.pop('reason', 'command')
        try:
            data = self.cache[f'{method}{args}{kwargs}']
        except KeyError:
            if leaderboard:
                speed = time.time()
                async with ctx.session.get(
                    f'https://leaderboard.brawlstars.com/{method}.jsonp?_={int(time.time()) - 4}'
                ) as resp:
                    speed = time.time() - speed
                    datadog.statsd.increment('statsy.requests', 1, [
                        'game:brawlstars', f'code:{resp.status}', f'method:{method}', f'reason:{reason}'
                    ])
                    data = box.Box(json.loads((await resp.text()).replace('jsonCallBack(', '')[:-2]), camel_killer_box=True)
            else:
                speed = time.time()
                data = await getattr(self.bs, method)(*args, **kwargs)
                speed = time.time() - speed

                if isinstance(data, list):
                    status_code = 'list'
                else:
                    status_code = data.resp.status

                datadog.statsd.increment('statsy.api_latency', 1, [
                    'game:brawlstars', f'speed:{speed}', f'method:{method}'
                ])
                datadog.statsd.increment('statsy.requests', 1, [
                    'game:brawlstars', f'code:{status_code}', f'method:{method}', f'reason:{reason}'
                ])

            self.cache[f'{method}{args}{kwargs}'] = data

        return data

    @command()
    async def save(self, ctx, tag, index: str = '0'):
        """Saves a Brawl Stars tag to your discord profile."""
        tag = self.conv.resolve_tag(tag)

        if not tag:
            raise utils.InvalidBSTag

        await ctx.save_tag(tag, 'brawlstars', index=index.replace('-', ''))
        try:
            default_game = self.bot.default_game[ctx.guild.id]
        except AttributeError:
            default_game = self.bot.default_game[ctx.channel.id]
        cmd_name = 'profile' if default_game == self.__class__.__name__ else f'{self.alias}profile'

        if index == '0':
            prompt = _('Check your stats with `{}{}`!').format(ctx.prefix, cmd_name)
        else:
            prompt = _('Check your stats with `{}{} -{}`!').format(ctx.prefix, index)

        await ctx.send(_('Successfully saved tag.') + ' ' + prompt)

    @command()
    @utils.has_perms()
    async def profile(self, ctx, *, tag_or_user: TagCheck=None):
        """Get general Brawl Stars player information."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            em = brawlstars.format_profile(ctx, profile)

        await ctx.send(embed=em)

    @command()
    async def brawlers(self, ctx, *, tag_or_user: TagCheck=None):
        """Get general Brawl Stars player information."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            ems = brawlstars.format_brawlers(ctx, profile)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def club(self, ctx, *, tag_or_user: TagCheck=None):
        """Get Brawl Stars club information."""
        tag = await self.resolve_tag(ctx, tag_or_user, club=True)

        async with ctx.typing():
            club = await self.request(ctx, 'get_club', tag)
            ems = brawlstars.format_club(ctx, club)

        await Paginator(ctx, *ems).start()

    @command(aliases=['toplayers'])
    @utils.has_perms()
    async def topplayers(self, ctx):
        """Returns the global top 200 players."""
        async with ctx.typing():
            player = await self.request(ctx, 'get_leaderboard', 'players')
            ems = brawlstars.format_top_players(ctx, player.players)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def topclubs(self, ctx):
        """Returns the global top 200 players."""
        async with ctx.typing():
            club = await self.request(ctx, 'get_leaderboard', 'clubs')
            ems = brawlstars.format_top_clubs(ctx, club.clubs)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def events(self, ctx):
        """Shows the upcoming events!"""
        async with ctx.typing():
            events = await self.request(ctx, 'get_events')
            ems = brawlstars.format_events(ctx, events)

        await Paginator(ctx, *ems).start()

    @command(aliases=['robo'])
    @utils.has_perms()
    async def roborumble(self, ctx):
        """Shows the robo rumble leaderboard"""
        async with ctx.typing():
            leaderboard = await self.request(ctx, 'rumbleboard', leaderboard=True)
            ems = brawlstars.format_robo(ctx, leaderboard)

        await Paginator(ctx, *ems).start()

    @command(aliases=['boss'])
    @utils.has_perms()
    async def bossfight(self, ctx):
        """Shows the boss fight leaderboard"""
        async with ctx.typing():
            leaderboard = await self.request(ctx, 'bossboard', leaderboard=True)
            ems = brawlstars.format_boss(ctx, leaderboard)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def randombrawler(self, ctx):
        """Gets a random brawler"""
        async with ctx.typing():
            brawler = random.choice([i for i in self.constants.characters if i.tID]).tID
            await brawlstars.format_random_brawler_and_send(ctx, brawler)

    async def on_typing(self, channel, user, when):
        if self.bot.is_closed() or not await self.__local_check(channel) or user.bot:
            return

        ctx = NoContext(self.bot, user)
        if ctx.guild:
            ctx.language = (await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}).get('language', 'messages')
        else:
            ctx.language = 'messages'

        guild_id = getattr(ctx.guild, 'id', 'DM')
        try:
            datadog.statsd.increment('statsy.magic_caching.check', 1, [f'user:{user.id}', f'guild:{guild_id}', 'game:brawlstars'])
            tag = await self.resolve_tag(ctx, None)

            try:
                player = await self.request(ctx, 'get_player', tag, reason='magic caching')
            except ValueError:
                return

            datadog.statsd.increment('statsy.magic_caching.request', 1, [f'user:{user.id}', f'guild:{guild_id}', 'game:brawlstars'])

            try:
                await self.request(ctx, 'get_club', player.club.tag, reason='magic caching')
            except (AttributeError, IndexError):
                pass
        except (utils.NoTag, commands.CheckFailure):
            pass


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
