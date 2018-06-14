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
    name = name.replace('.','').lower().replace(' ','').replace('_','').replace('-','')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    return e or name

class Fortnite:
    """Commands related to the Fortnite game"""
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)

    def timestamp(self, minutes):
        return str(datetime.timedelta(minutes=minutes))[:-3]

    async def resolve_username(self, ctx, username, platform):
        if not any((username, platform)):
            try:
                return await ctx.get_tag('fortnite', f'{ctx.author.id}: {platform}')
            except KeyError:
                await ctx.send(f'You don\'t have a saved tag. Save one using `{ctx.prefix}fnsave <tag>!`')
                raise NoTag()
        else:
            if platform not in ('pc', 'ps4', 'xb1'):
                raise InvalidPlatform()
            if isinstance(username, discord.Member):
                try:
                    return await ctx.get_tag('fortnite', f'{username.id}: {platform}')
                except KeyError:
                    await ctx.send('That person doesnt have a saved tag!')
                    raise NoTag()
            else:
                return username

    async def __error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, FortniteServerError):
            await ctx.send('Fortnite API is currently undergoing maintenance. Please try again later.')    

    async def post(self, endpoint, payload):
        headers = {
            'Authorization': os.getenv('fortnite'),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        async with self.session.post('https://fortnite-public-api.theapinetwork.com/prod09'  + endpoint, data=urlencode(payload), headers=headers) as resp:
            if resp.status != 200:
                raise FortniteServerError
            try:
                return await resp.json()
            except json.JSONDecodeError:
                raise FortniteServerError

    async def get_player_uid(self, ctx, name):
        data = await self.post('/users/id', {'username': name})
        if data.get('code') in ('1012', '1006'):
            await ctx.send('The username cannot be found!')
            raise NoTag

        return data['uid']

    @commands.command()
    async def fnsave(self, ctx, platform: lower, *, username: str):
        """Saves a fortnite tag to your discord profile."""
        await ctx.save_tag(username, 'fortnite', f'{ctx.author.id}: {platform}')
        await ctx.send(f'Successfully saved tag. Check your stats with `{ctx.prefix}fnprofile`!')

    @commands.command()
    async def fnprofile(self, ctx, platform: lower, *, username: TagOrUser=None):
        """Gets the fortnite profile of a player with a provided platform"""
        async with ctx.typing():
            username = await self.resolve_username(ctx, username, platform)
            uid = await self.get_player_uid(ctx, username)
            player = await self.post('/users/public/br_stats_all', {'user_id': uid, 'window': 'alltime', 'platform': platform})

            ems = []
            top = {'solo': (10, 25), 'duo': (5, 12), 'squad': (3, 6)}

            if player['totals']['matchesplayed']:
                kdr = player['totals']['wins']/player['totals']['matchesplayed']*100
            else:
                kdr = 0

            fields = [
                (f'Kills {emoji(ctx, "fnskull")}', player['totals']['kills']),
                (f'Victory Royale! {emoji(ctx, "fnvictoryroyale")}', f"{player['totals']['wins']} ({kdr:.2f})"),
                ('Kill Death Ratio', player['totals']['kd']),
                ('Time Played', self.timestamp(player['totals']['minutesplayed']))
            ]
            ems.append(discord.Embed(description=f'Overall Statistics', color=random_color()))
            ems[0].set_author(name=player['username'])
            for name, value in fields:
                ems[0].add_field(name=str(name), value=str(value))

            for n, mode in enumerate(('solo', 'duo', 'squad')):
                fields = [
                    ('Score', player[platform][f'score_{mode}']),
                    (f'Kills {emoji(ctx, "fnskull")}', player[platform][f'kills_{mode}']),
                    ('Total Battles', player[platform][f'matchesplayed_{mode}']),
                    (f'Victory Royale! {emoji(ctx, "fnvictoryroyale")}', f"{player[platform][f'placetop1_{mode}']} ({player[platform][f'winrate_{mode}']}%)"),
                    (f'Top {emoji(ctx, "fnleague")}', 'Top {}: {}\nTop {}: {}'.format(
                            top[mode][0],
                            player[platform][f'placetop{top[mode][0]}_{mode}'],
                            top[mode][1],
                            player[platform][f'placetop{top[mode][1]}_{mode}']
                        )
                    ),
                    ('Kill Death Ratio', player[platform][f'kd_{mode}']),
                    ('Time Played', self.timestamp(player[platform][f'minutesplayed_{mode}']))
                ]
                ems.append(discord.Embed(description=f'{mode.title()} Statistics', color=random_color()))
                ems[n+1].set_author(name=player['username'])

                for name, value in fields:
                    ems[n+1].add_field(name=str(name), value=str(value))

            session = PaginatorSession(
                ctx=ctx, 
                pages=ems,
                footer_text=f'Statsy - Powered by fortniteapi.com'
            )
        await session.run()

def setup(bot):
    bot.add_cog(Fortnite(bot))
