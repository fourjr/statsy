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
import asyncio
import aiohttp
import psutil
import time
import json
import sys
import os
import re



class StatsBot(commands.AutoShardedBot):
    '''
    Custom Client for cr-statsbot - Made by verix#7220
    '''
    def __init__(self, **attrs):
        super().__init__(command_prefix=self.get_pre, self_bot=True)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasync.Client(self.session)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.messages_sent = 0
        self.remove_command('help')
        self.add_commands()
        self.load_extensions()

    def add_commands(self):
        '''Adds commands automatically'''
        for attr in dir(self):
            cmd = getattr(self, attr)
            if isinstance(cmd, commands.Command):
                self.add_command(cmd)

    def load_extensions(self, cogs=None, path='cogs.'):
        '''Loads the default set of extensions or a seperate one if given'''
        base_extensions = [x.replace('.py', '') for x in os.listdir('cogs')]
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
        with open('data/config.json') as f:
            return = json.load(f)['token'].strip('"')

    async def get_prefix(self, message):
        '''Returns the prefix.

        Still need to do stuff with db to get server prefix.
        '''
        return '#'

    def restart(self):
        '''Forcefully restart the bot.'''
        os.execv(sys.executable, ['python'] + sys.argv)

    @classmethod
    def init(bot, token=None):
        '''Starts the actual bot'''
        bot = StatsBot()
        token = token or bot.token
        try:
            bot.run(token.strip('"'), bot=False, reconnect=True)
        except Exception as e:
            print('Error in starting the bot. Check your token.')

    async def on_connect(self):
        '''
        Called when the bot has established a 
        gateway connection with discord
        '''
        print('----------------------------')
        print('StatsBot connected!')
        print('----------------------------')

    async def on_ready(self):
        '''
        Called when guild streaming is complete 
        and the client's internal cache is ready.
        '''
        print('StatsBot is ready!')
        print('----------------------------')
        print(f'Logged in as: {self.user}')
        print(f'Guilds: {len(self.guilds)}')
        print(f'Users: {len(self.users)}')
        print(f'Channels: {len(self.channels)}')
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
        em.description = f'{self.ws.latency * 1000:.4f} ms'
        em.color = await ctx.get_dominant_color(ctx.author.avatar_url)
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)

if __name__ == '__main__':
    Selfbot.init()