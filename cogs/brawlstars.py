import asyncio
import json
import time
import random
import os

import brawlstats
import datadog
import discord
import requests
from cachetools import TTLCache
from datetime import datetime
from discord.ext import commands

import box
from ext import utils
from ext.command import cog, command
from ext.context import NoContext
from ext.embeds import brawlstars
from ext.paginator import Paginator, WikiPaginator
from locales.i18n import Translator

_ = Translator('Brawl Stars', __file__)

shortcuts = {
    'juice': '2PP00',
    'pulp': 'PY9JLV',
    'cactus': 'QCGV8PG',
    'whiskey': 'QCCQCGV',
    'barrel': 'QCGVPV8',
    'boom': 'QCGUUYJ'
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
            timeout=30,
            url=os.getenv('bs_url')
        )
        self.constants = box.Box(
            json.loads(requests.get('https://fourjr.herokuapp.com/bs/constants').text),
            camel_killer_box=True
        )
        if not self.bot.dev_mode:
            self.bot.event_notifications_loop = self.bot.loop.create_task(self.event_notifications())
            self.bot.clan_update = self.bot.loop.create_task(self.clan_update_loop())

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
        profile = await self.request('get_player', tag)
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

    async def request(self, method, *args, **kwargs):
        leaderboard = kwargs.pop('leaderboard', False)
        reason = kwargs.pop('reason', 'command')
        try:
            data = self.cache[f'{method}{args}{kwargs}']
        except KeyError:
            if leaderboard:
                speed = time.time()
                async with self.bot.session.get(
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
            profile = await self.request('get_player', tag)
            em = brawlstars.format_profile(ctx, profile)

        await ctx.send(embed=em)

    @command()
    async def brawlers(self, ctx, *, tag_or_user: TagCheck=None):
        """Get general Brawl Stars player information."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            ems = brawlstars.format_brawlers(ctx, profile)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def club(self, ctx, *, tag_or_user: TagCheck=None):
        """Get Brawl Stars club information."""
        tag = await self.resolve_tag(ctx, tag_or_user, club=True)

        async with ctx.typing():
            club = await self.request('get_club', tag)
            ems = brawlstars.format_club(ctx, club)

        await Paginator(ctx, *ems).start()

    @command(aliases=['toplayers'])
    @utils.has_perms()
    async def topplayers(self, ctx):
        """Returns the global top 200 players."""
        async with ctx.typing():
            player = await self.request('get_leaderboard', 'players')
            ems = brawlstars.format_top_players(ctx, player)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def topclubs(self, ctx):
        """Returns the global top 200 players."""
        async with ctx.typing():
            club = await self.request('get_leaderboard', 'clubs')
            ems = brawlstars.format_top_clubs(ctx, club)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def events(self, ctx, type: utils.lower='all'):
        """Shows the upcoming events!"""
        if type not in ('all', 'current', 'upcoming'):
            return await ctx.send('Invalid type. Pick from either `current` or `upcoming`')

        async with ctx.typing():
            events = await self.request('get_events')
            ems = brawlstars.format_events(ctx, events, type)

        for i in ems:
            try:
                await Paginator(ctx, *i).start()
            except:
                await ctx.send('Unable to get event data')

    @command(aliases=['robo'])
    @utils.has_perms()
    async def roborumble(self, ctx):
        """Shows the robo rumble leaderboard"""
        await ctx.send('Too many people to show!')
        # async with ctx.typing():
        #     leaderboard = await self.request('rumbleboard', leaderboard=True)
        #     ems = brawlstars.format_robo(ctx, leaderboard)

        # await Paginator(ctx, *ems).start()

    @utils.has_perms()
    async def biggame(self, ctx):
        """Shows the big game leaderboard"""
        async with ctx.typing():
            leaderboard = await self.request('bossboard', leaderboard=True)
            ems = brawlstars.format_boss(ctx, leaderboard)

        await Paginator(ctx, *ems).start()

    @command()
    @utils.has_perms()
    async def randombrawler(self, ctx):
        """Gets a random brawler"""
        async with ctx.typing():
            brawler = random.choice([i for i in self.constants.characters if i.tID]).tID
            await brawlstars.format_random_brawler_and_send(ctx, brawler)

    @command(aliases=['brawler', 'wiki'])
    @utils.has_perms()
    async def brawlerstats(self, ctx, *, brawler_name: str.lower):
        """Gets a random brawler"""
        try:
            brawler = next(i for i in self.constants.characters if (i.tID or '').lower() == brawler_name)
        except StopIteration:
            await ctx.send('Invalid brawler name')
        else:
            brawler_power = None
            try:
                tag = await ctx.get_tag('brawlstars', ctx.author.id)
            except KeyError:
                pass
            else:
                try:
                    player = await self.request('get_player', tag)
                except brwalstats.RequestError:
                    pass
                else:
                    try:
                        brawler_power = next(i.power for i in player.brawlers if i.name == brawler.tID.title())
                    except StopIteration:
                        pass

            ems = brawlstars.format_brawler_stats(ctx, brawler)
            await WikiPaginator(ctx, brawler_power, *ems).start()

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
                player = await self.request('get_player', tag, reason='magic caching')
            except ValueError:
                return

            datadog.statsd.increment('statsy.magic_caching.request', 1, [f'user:{user.id}', f'guild:{guild_id}', 'game:brawlstars'])

            try:
                await self.request('get_club', player.club.tag, reason='magic caching')
            except (AttributeError, IndexError):
                pass
        except (utils.NoTag, commands.CheckFailure):
            pass

    async def event_notifications(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            colors = {
                'Gem Grab': 0x9B3DF3,
                'Showdown': 0x81D621,
                'Heist': 0xD65CD3,
                'Bounty': 0x01CFFF,
                'Brawl Ball': 0x8CA0DF,
                'Robo Rumble': 0xAE0026,
                'Big Game': 0xDC2422,
                'Boss Fight': 0xDC2422
            }

            events = await self.request('get_events')
            wait_time = min(i.start_time_in_seconds for i in events.upcoming)
            await asyncio.sleep(wait_time)

            guilds = self.bot.mongo.config.guilds.find({'event_notify': {'$exists': True}})
            announce = [i for i in events.upcoming if i.start_time_in_seconds == wait_time]
            async for g in guilds:
                channel = self.bot.get_guild(int(g['guild_id'])).get_channel(int(g['event_notify']))

                for event in announce:
                    em = discord.Embed(
                        color=colors[event.game_mode],
                        timestamp=self.bs.get_datetime(event.end_time, unix=False)
                    ).add_field(
                        name=f'{utils.e(event.game_mode)} {event.game_mode}: {event.map_name}',
                        value=f'{utils.e(event.modifier_name)} {event.modifier_name}' if event.has_modifier else 'No Modifiers'
                    ).set_author(
                        name='New Event!'
                    ).set_image(
                        url=event.map_image_url
                    ).set_footer(
                        text='End Time'
                    )

                    try:
                        await channel.send(embed=em)
                    except (AttributeError, discord.NotFound):
                        pass

    async def get_clubs(self, *tags):
        clans = []
        for t in tags:
            clans.append(await self.request('get_club', t, reason='clanstats'))
            await asyncio.sleep(0.5)
        return clans

    async def clanupdate(self, clan=None):
        if not clan:
            guilds = await self.bot.mongo.config.guilds.find({'bsclubinfo': {'$exists': True}}).to_list(None)
        else:
            guilds = [clan]

        for g in guilds:
            m = g['bsclubinfo']
            clans = await self.get_clubs(*m['clubs'])

            embed = discord.Embed(title="Club Statistics!", color=0xf1c40f, timestamp=datetime.utcnow())
            total_members = 0

            for i in range(len(clans)):
                embed.add_field(name=clans[i].name, value=brawlstars.format_club_stats(clans[i]))
                total_members += len(clans[i].members)

            embed.add_field(name='More Info', value=f"{utils.e('friends')} {total_members}/{100*len(clans)}", inline=False)

            try:
                channel = self.bot.get_channel(int(m['channel']))
                message = await channel.get_message(int(m['message']))
            except AttributeError:
                message = None

            if not message:
                try:
                    message = await self.bot.get_channel(int(m['channel'])).send('Clan Stats')
                except AttributeError:
                    await self.bot.mongo.find_one_and_delete({'guild_id': str(g['guild_id'])})
                    break

            await message.edit(content='', embed=embed)
            return message

    async def on_raw_reaction_add(self, payload):
        data = await self.bot.mongo.config.guilds.find_one({'guild_id': str(payload.guild_id), 'bsclubinfo.message': str(payload.message_id)})
        if data:
            member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

            if member == self.bot.user:
                return

            message = await self.clanupdate(data)
            await message.clear_reactions()
            await message.add_reaction(':refresh:477405504512065536')

    async def clan_update_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.clanupdate()
            await asyncio.sleep(600)


def setup(bot):
    cog = Brawl_Stars(bot)
    bot.add_cog(cog)
