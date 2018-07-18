import datetime
import random
import json
import os
from urllib.parse import urlencode

import aiohttp
import discord
from discord.ext import commands

from statsbot import NoTag, InvalidPlatform
from ext.paginator import PaginatorSession

from locales.i18n import Translator

_ = Translator('Fortnite', __file__)

class FortniteServerError(Exception):
    """Raised when the Fortnite API is down"""
    pass


class TagOrUser(commands.MemberConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument


def lower(argument):
    return argument.lower()


def random_color():
    return random.randint(0, 0xffffff)


def emoji(ctx, name):
    name = name.replace('.', '').lower().replace(' ', '').replace('_', '').replace('-', '')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    return e or name


class Fortnite:
    """Commands related to the Fortnite game"""
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    async def __local_check(self, ctx):
        if ctx.guild:
            guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': ctx.guild.id}) or {}
            return guild_info.get('games', {}).get(self.__class__.__name__, True)
        else:
            return True

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    def timestamp(self, minutes):
        return str(datetime.timedelta(minutes=minutes))[:-3]

    async def resolve_username(self, ctx, username, platform):
        if not username:
            try:
                return await ctx.get_tag('fortnite', f'{ctx.author.id}: {platform}')
            except KeyError:
                await ctx.send(_("You don't have a saved tag. Save one using `{}fnsave <tag>!`", ctx).format(ctx.prefix))
                raise NoTag
        else:
            if platform not in ('pc', 'ps4', 'xb1'):
                raise InvalidPlatform
            if isinstance(username, discord.Member):
                try:
                    return await ctx.get_tag('fortnite', f'{username.id}: {platform}')
                except KeyError:
                    await ctx.send(_('That person doesnt have a saved tag!', ctx))
                    raise NoTag()
            else:
                if username.startswith('-'):
                    return await ctx.get_tag('fortnite', f'{username.id}: {platform}', index=username.replace('-', ''))
                return username

    async def __error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, FortniteServerError):
            await ctx.send(_('Fortnite API is currently undergoing maintenance. Please try again later.', ctx))

    async def post(self, endpoint, payload):
        headers = {
            'Authorization': os.getenv('fortnite'),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        async with self.session.post(
            'https://fortnite-public-api.theapinetwork.com/prod09' + endpoint,
            data=urlencode(payload), headers=headers
        ) as resp:
            if resp.status != 200:
                raise FortniteServerError
            try:
                return await resp.json()
            except (json.JSONDecodeError, aiohttp.client_exceptions.ContentTypeError):
                raise FortniteServerError

    async def get_player_uid(self, ctx, name):
        data = await self.post('/users/id', {'username': name})
        if data.get('code') in ('1012', '1006'):
            await ctx.send(_('The username cannot be found!', ctx))
            raise NoTag

        return data['uid']

    @commands.command()
    async def fnsave(self, ctx, platform: lower, *, username: str):
        """Saves a fortnite tag to your discord profile."""
        await ctx.save_tag(username, 'fortnite', f'{ctx.author.id}: {platform}')
        await ctx.send(_('Successfully saved tag. Check your stats with `{}fnprofile`!', ctx).format(ctx.prefix))

    @commands.command()
    async def fnsave(self, ctx, platform: lower, username: str, index: str='0'):
        """Saves a Fortnite tag to your discord profile."""
        await ctx.save_tag(username, 'fortnite', f'{ctx.author.id}: {platform}', index=index.replace('-', ''))

        if index == '0':
            prompt = f'Check your stats with `{ctx.prefix}fnprofile`!'
        else:
            prompt = f'Check your stats with `{ctx.prefix}fnprofile -{index}`!'

        await ctx.send('Successfully saved tag. ' + prompt)
        
    @commands.command()
    async def fnprofile(self, ctx, platform: lower, *, username: TagOrUser=None):
        """Gets the fortnite profile of a player with a provided platform"""
        async with ctx.typing():
            username = await self.resolve_username(ctx, username, platform)
            uid = await self.get_player_uid(ctx, username)
            player = await self.post('/users/public/br_stats_all', {
                'user_id': uid, 'window': 'alltime', 'platform': platform
            })

            ems = []
            top = {'solo': (10, 25), 'duo': (5, 12), 'squad': (3, 6)}

            if player['totals']['matchesplayed']:
                kdr = player['totals']['wins'] / player['totals']['matchesplayed'] * 100
            else:
                kdr = 0

            fields = [
                (_('Kills {}', ctx).format(emoji(ctx, "fnskull")), player['totals']['kills']),
                (_('Victory Royale! {}', ctx).format(emoji(ctx, "fnvictoryroyale")), f"{player['totals']['wins']} ({kdr:.2f})"),
                (_('Kill Death Ratio', ctx), player['totals']['kd']),
                (_('Time Played', ctx), self.timestamp(player['totals']['minutesplayed']))
            ]
            ems.append(discord.Embed(description=_('Overall Statistics', ctx), color=random_color()))
            ems[0].set_author(name=player['username'])
            for name, value in fields:
                ems[0].add_field(name=str(name), value=str(value))

            for n, mode in enumerate(('solo', 'duo', 'squad')):
                kdr = player[platform][f'winrate_{mode}']
                fields = [
                    (_('Score', ctx), player[platform][f'score_{mode}']),
                    (_('Kills {}', ctx).format(emoji(ctx, "fnskull")), player[platform][f'kills_{mode}']),
                    (_('Total Battles', ctx), player[platform][f'matchesplayed_{mode}']),
                    (_('Victory Royale! {}', ctx).format(emoji(ctx, "fnvictoryroyale")), f"{player[platform][f'placetop1_{mode}']} ({kdr}%)"),
                    (_('Top {}', ctx).format(emoji(ctx, "fnleague")), 'Top {}: {}\nTop {}: {}'.format(
                        top[mode][0],
                        player[platform][f'placetop{top[mode][0]}_{mode}'],
                        top[mode][1],
                        player[platform][f'placetop{top[mode][1]}_{mode}']
                    )),
                    (_('Kill Death Ratio', ctx), player[platform][f'kd_{mode}']),
                    (_('Time Played', ctx), self.timestamp(player[platform][f'minutesplayed_{mode}']))
                ]
                ems.append(discord.Embed(description=_('{} Statistics', ctx).format(mode.title()), color=random_color()))
                ems[n + 1].set_author(name=player['username'])

                for name, value in fields:
                    ems[n + 1].add_field(name=str(name), value=str(value))

            session = PaginatorSession(
                ctx=ctx,
                pages=ems,
                footer_text=_('Statsy - Powered by fortniteapi.com', ctx)
            )
        await session.run()

    @commands.command()
    async def fnusertag(self, ctx, platform: lower, *, member: discord.Member=None):
        """Checks the saved tag(s) of a member"""
        member = member or ctx.author
        tag = await ctx.get_tag('fortnite', f'{member.id}: {platform}', index='all')
        em = discord.Embed(description='Tags saved', color=random_color())
        em.set_author(name=member.name, icon_url=member.avatar_url)
        for i in tag:
            em.add_field(name=f'Tag index: {i}', value=tag[i])
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Fortnite(bot))
