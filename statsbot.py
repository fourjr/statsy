'''
MIT License

Copyright (c) 2017 grokkers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
import crasync
from discord.ext import commands
from ext.context import CustomContext
from ext.paginator import PaginatorSession
from ext import embeds
from collections import defaultdict
from contextlib import redirect_stdout
import datetime
import traceback
import asyncio
import aiohttp
import psutil
import time
import json
import sys
import os
import re
import inspect
import io
import textwrap

class crasyncClient(crasync.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_made = [0, 0, 0]

    async def request(self, url):
        self.requests_made[2] += 1
        try:
            ret = await super().request(url)
        except Exception as e:
            self.requests_made[1] += 1
            raise e
        else:
            self.requests_made[0] += 1
            return ret

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''

    message = 'Player tags should only contain these characters:\n' \
              '**Numbers:** 0, 2, 8, 9\n' \
              '**Letters:** P, Y, L, Q, G, R, J, C, U, V'

class StatsBot(commands.AutoShardedBot):
    '''
    Custom client for statsy made by Kyber
    '''
    emoji_servers = [
        376364364636094465,
        376368487037140992,
        376364990023729152,
        377742732501843968,
        376365022752014345,
        386872710225068042,
        389369383639842817
        ]

    developers = [
        325012556940836864,
        180314310298304512,
        273381165229146112,
        168143064517443584
    ]

    def __init__(self):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasyncClient(self.session, timeout=3)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.remove_command('help')
        self.messages_sent = 0
        self.maintenance_mode = False
        self.psa_message = None
        self.loop.create_task(self.backup_task())
        self._add_commands()
        self.load_extensions()

    def get_game_emojis(self):
        emojis = []
        for id in self.emoji_servers:
            g = self.get_guild(id)
            for e in g.emojis:
                emojis.append(e)
        return emojis

    def _add_commands(self):
        '''Adds commands automatically'''
        for name, attr in inspect.getmembers(self):
            if isinstance(attr, commands.Command):
                self.add_command(attr)

    def load_extensions(self, cogs=None, path='cogs.'):
        '''Loads the default set of extensions or a seperate one if given'''
        base_extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        for extension in cogs or base_extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'LoadError: {extension}')
                traceback.print_exc()

    @property
    def token(self):
        '''Returns your token wherever it is'''
        try:
            with open('data/config.json') as f:
                return json.load(f)['token'].strip('"')
        except FileNotFoundError:
            return None

    @property
    def botlist(self):
        '''Returns your botlist token wherever it is'''
        try:
            with open('data/config.json') as f:
                return json.load(f)['botlist'].strip('"')
        except FileNotFoundError:
            return None

    @classmethod
    def init(bot, token=None):
        '''Starts the actual bot'''
        bot = StatsBot()
        token = token or bot.token
        try:
            bot.run(token.strip('"'), bot=True, reconnect=True)
        except Exception as e:
            print('Error in starting the bot. Check your token.')

    def restart(self):
        '''Forcefully restart the bot.'''
        os.execv(sys.executable, ['python'] + sys.argv)

    async def get_prefix(self, message):
        '''Returns the prefix.

        need to switch to a db soon
        '''
        with open('data/guild.json') as f:
            cfg = json.load(f)

        id = str(getattr(message.guild, 'id', None))

        prefixes = [
            f'<@{self.user.id}> ',
            f'<@!{self.user.id}> ',
            cfg.get(id, '!')
            ]

        return prefixes

    async def on_connect(self):
        '''
        Called when the bot has established a
        gateway connection with discord
        '''
        print('----------------------------')
        print('StatsBot connected!')
        print('----------------------------')

        # self._add_commands()
        # had to put this here due to an issue with the
        # latencies property
        # Fixed now
        self.constants = await self.cr.get_constants()
        # await self.change_presence(game=discord.Game(name='!help'))

    async def on_ready(self):
        '''
        Called when guild streaming is complete
        and the client's internal cache is ready.
        '''
        fmt = 'StatsBot is ready!\n' \
              '----------------------------\n' \
              f'Logged in as: {self.user}\n' \
              f'Client ID: {self.user.id}\n' \
              '----------------------------\n' \
              f'Guilds: {len(self.guilds)}\n' \
              f'Users: {len(self.users)}\n' \
              '----------------------------'
        print(fmt)
        channel = self.get_channel(376622292106608640)
        self.game_emojis = self.get_game_emojis()
        await channel.send(f'```{fmt}```')

    async def on_shard_connect(self, shard_id):
        '''
        Called when a shard has successfuly
        connected to the gateway.
        '''
        print(f'Shard `{shard_id}` ready!')
        print('----------------------------')

    async def on_command(self, ctx):
        '''Called when a command is invoked.'''
        cmd = ctx.command.qualified_name.replace(' ', '_')
        self.commands_used[cmd] += 1

    async def process_commands(self, message):
        '''Utilises the CustomContext subclass of discord.Context'''
        ctx = await self.get_context(message, cls=CustomContext)
        cog = self.get_cog('Brawl_Stars')
        if ctx.command is None:
            return
        else:
            if self.maintenance_mode is True:
                if message.author.id not in self.developers:
                    return await ctx.send('The bot is under maintenance at the moment!')
            # if ctx.command.instance is cog:
            #     if ctx.author.id in self.developers:
            #         await self.invoke(ctx)
            #     else:
            #         await ctx.send('Brawl Stars commands are temporarily disabled. Please be patient!')
            else:
                await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, InvalidTag):
            await ctx.send(error.message)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            prefix = (await self.get_prefix(ctx.message))[2]
            await ctx.send(
                embed=discord.Embed(
                    color=embeds.random_color(),
                    title=f'``Usage: {prefix}{ctx.command.signature}``',
                    description=ctx.command.help)
                )
        else:
            error_message = 'Ignoring exception in command {}:\n'.format(ctx.command)
            error_message += ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            log_channel = self.get_channel(376622292106608640)
            em = discord.Embed(
                color=discord.Color.orange(),
                description=f"```\n{error_message}\n```",
                title=ctx.message.content)
            em.set_footer(text=f'G: {ctx.guild.id} | C: {ctx.channel.id}')
            print(error_message, file=sys.stderr)
            await log_channel.send(embed=em)

    async def on_message(self, message):
        '''Called when a message is sent/recieved.'''
        self.messages_sent += 1
        if message.author.bot:
            return
        await self.process_commands(message)

    async def backup_task(self):
        '''Backup tags.'''
        await self.wait_until_ready()
        channel = self.get_channel(378546850376056832)
        url = 'https://hastebin.com/documents'

        em = discord.Embed(color=0x00FFFF)
        em.set_author(
            name='Tag Backup',
            icon_url=self.user.avatar_url
            )

        while not self.is_closed():
            with open('data/stats.json') as f:
                data = f.read()

            async with self.session.post(url=url, data=data) as resp:
                k = await resp.json()

            key = k['key']

            em.description = f'http://hastebin.com/{key}.json'
            await channel.send(embed=em)
            await self.session.post('https://discordbots.org/api/bots/347006499677143041/stats', json={"server_count": len(self.guilds)}, headers={'Authorization': self.botlist})
            await asyncio.sleep(36000)

    @commands.command()
    async def ping(self, ctx):
        """Pong! Returns average shard latency."""
        em = discord.Embed()
        em.title ='Pong! Websocket Latency: '
        em.description = f'{self.latency * 1000:.4f} ms'
        em.color = 0xf9c93d
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)

if __name__ == '__main__':
    StatsBot.init()
