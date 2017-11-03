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
from collections import defaultdict
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


class StatsBot(commands.AutoShardedBot):
    '''
    Custom Client for cr-statsbot - Made by verix#7220
    '''
    emoji_servers = [
        315043391081676810, 
        337918174475452426, 
        337919522163916815, 
        337975017469902848,
        ]

    def __init__(self):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasync.Client(self.session)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.messages_sent = 0
        self.load_extensions()

    def get_cremojis(self):
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
                print(f'LoadError: {extension}\n'
                      f'{type(e).__name__}: {e}')

    @property
    def token(self):
        '''Returns your token wherever it is'''
        try:
            with open('data/config.json') as f:
                return json.load(f)['token'].strip('"')
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

        Still need to do stuff with db to get server prefix.
        '''
        return '#'

    async def on_connect(self):
        '''
        Called when the bot has established a 
        gateway connection with discord
        '''
        print('----------------------------')
        print('StatsBot connected!')
        print('----------------------------')

        self._add_commands()
        # had to put this here due to an issue with the 
        # latencies property

    async def on_ready(self):
        '''
        Called when guild streaming is complete 
        and the client's internal cache is ready.
        '''
        print('StatsBot is ready!')
        print('----------------------------')
        print(f'Logged in as: {self.user}')
        print(f'Client ID: {self.user.id})')
        print('----------------------------')
        print(f'Guilds: {len(self.guilds)}')
        print(f'Users: {len(self.users)}')
        print('----------------------------')
        self.cremojis = self.get_cremojis()

    async def on_shard_ready(self, shard_id):
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
        if ctx.command is None:
            return
        await self.invoke(ctx)

    async def on_message(self, message):
        '''Called when a message is sent/recieved.'''
        self.messages_sent += 1
        if message.author.bot:
            return 
        await self.process_commands(message)

    @commands.command()
    async def ping(self, ctx):
        """Pong! Returns your websocket latency."""
        em = discord.Embed()
        em.title ='Pong! Websocket Latency: '
        em.description = f'{self.latency * 1000:.4f} ms'
        em.color = await ctx.get_dominant_color(self.user.avatar_url)
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)

    @commands.command()
    async def invite(self, ctx):
        """Joins a server."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.embed_links = True
        perms.attach_files = True
        perms.add_reactions = True
        await ctx.send(f'**Invite link:** \n<{discord.utils.oauth_url(self.user.id, perms)}>')

if __name__ == '__main__':
    StatsBot.init()