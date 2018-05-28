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

import asyncio
import datetime
import inspect
import io
import json
import os
import re
import platform
import sys
import textwrap
import time
import traceback
from collections import defaultdict
from contextlib import redirect_stdout

import aiohttp
import clashroyale
import discord
import psutil
from abrawlpy import Client as bsClient
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from ext import embeds_cr_statsroyale as embeds
from ext.context import CustomContext
from ext.paginator import PaginatorSession


class crClient(clashroyale.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_made = [0, 0, 0]

    # async def request(self, url):
    #     self.requests_made[2] += 1
    #     try:
    #         ret = await super().request(url)
    #     except Exception as e:
    #         self.requests_made[1] += 1
    #         raise e
    #     else:
    #         self.requests_made[0] += 1
    #         return ret

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''

    message = 'Player tags should only contain these characters:\n' \
              '**Numbers:** 0, 2, 8, 9\n' \
              '**Letters:** P, Y, L, Q, G, R, J, C, U, V'

class NoTag(Exception):
    pass

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
        389369383639842817,
        390674234239746055
        ]

    developers = [
        325012556940836864,
        180314310298304512,
        273381165229146112,
        168143064517443584
    ]

    def __init__(self, token=None):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crClient(self.config['cr-token'],\
            session=self.session, is_async=True, timeout=5)
        self.bs = bsClient('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjcmVhdGlvbiI6MTUxOTc3MDk4ODQ0MywidXNlcklEIjoiMTgwMzE0MzEwMjk4MzA0NTEyIn0.PpwJXH32hyK7_NDUVXYLVFFPIT3fdzhM5YLbMSWw34Q', session=self.session)
        # 4JR's token ^^ 
        self.mongo = AsyncIOMotorClient('mongodb+srv://statsy:cRh199QzDdKaOhX9@statsy-lpu1v.mongodb.net')
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.remove_command('help')
        self.messages_sent = 0
        self.maintenance_mode = False
        self.psa_message = None
        self.dev_mode = platform.system() != 'Linux'
        self.loop.create_task(self.backup_task())
        self.load_extensions()

        self.log_hook = discord.Webhook.partial(450623469495779328, 'fkuVOFeWm79odmlCbtPFA2qNAj80Q5w5UynLDxf0DCDulvgnqSGghVa4y7Ezv9CsegiB', adapter=discord.AsyncWebhookAdapter(self.session))
        self.error_hook = discord.Webhook.partial(450622686616485888, 'I49t55RNZp-sAQix4Gk4isnnbnuo_CE9nrLfE2EIHiNAsueaex9HYlsIxUINxJD6k80I', adapter=discord.AsyncWebhookAdapter(self.session))

        token = token or self.token
        try:
            self.run(token.strip('"'), bot=True, reconnect=True)
        except Exception as e:
            print(f'Error in starting the bot. Check your token.\n{e}')

    @property
    def config(self):
        with open('data/config.json') as f:
            return json.load(f)

    def get_game_emojis(self):
        emojis = []
        for id in self.emoji_servers:
            g = self.get_guild(id)
            for e in g.emojis:
                emojis.append(e)
        return emojis

    def _add_commands(self):
        '''Adds commands automatically'''
        for _, attr in inspect.getmembers(self):
            if isinstance(attr, commands.Command):
                self.add_command(attr)

    def load_extensions(self, cogs=None, path='cogs.'):
        '''Loads the default set of extensions or a seperate one if given'''
        base_extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        for extension in cogs or base_extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception:
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

    def restart(self):
        '''Forcefully restart the bot.'''
        os.execv(sys.executable, ['python'] + sys.argv)

    async def get_prefix(self, message):
        '''Returns the prefix.
        '''

        if self.dev_mode:
            return './'

        id = getattr(message.guild, 'id', None)

        cfg = await self.mongo.config.guilds.find_one({'guild_id': id}) or {}

        prefixes = [
            f'<@{self.user.id}> ',
            f'<@!{self.user.id}> ',
            cfg.get('prefix', '!')
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

        self.constants = await self.cr.get_constants()
        with open('backup/brawlstars/constants.json') as f:
            self.bsconstants = json.load(f)

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
        self.game_emojis = self.get_game_emojis()
        if not self.dev_mode:
            await self.log_hook.send(f'```{fmt}```')

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
        await self.wait_until_ready()
        ctx = await self.get_context(message, cls=CustomContext)
        if self.dev_mode and ctx.guild.id != 345787308282478592:
            return
        if ctx.command is None:
            return
        else:
            if self.maintenance_mode is True:
                if message.author.id not in self.developers:
                    return await ctx.send('The bot is under maintenance at the moment!')
            else:
                await self.invoke(ctx)

    async def on_command_error(self, ctx, error, description=None):
        error = getattr(error, 'original', error)
        if isinstance(error, clashroyale.errors.RequestError):
            await ctx.send('CR Commands are temporarily down due to the API. Give us a bit.')
        elif isinstance(error, InvalidTag):
            await ctx.send(error.message)
        elif isinstance(error, (NoTag, discord.Forbidden)):
            pass
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument) and ctx.command.name == 'save':
            try:
                await ctx.invoke(ctx.command, tag=ctx.args[2])
            except Exception as e:
                await self.on_command_error(ctx, e)
        elif isinstance(error, commands.MissingRequiredArgument):
            prefix = (await self.get_prefix(ctx.message))[2]
            await ctx.send(
                embed=discord.Embed(
                    color=embeds.random_color(),
                    title=f'``Usage: {prefix}{ctx.command.signature}``',
                    description=ctx.command.help)
                )
        else:
            if not description:
                await ctx.send('Something went wrong and we are investigating the issue now :(')
            error_message = 'Ignoring exception in command {}:\n'.format(ctx.command)
            error_message += ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            em = discord.Embed(
                color=discord.Color.orange(),
                description=f"```\n{error_message}\n```",
                title=ctx.message.content)
            em.set_footer(text=f'G: {ctx.guild.id} | C: {ctx.channel.id} | U: {ctx.author.id}')
            if not self.dev_mode:
                await self.error_hook.send(content=description, embed=em)
            else:
                print(error_message, file=sys.stderr)

    async def on_message(self, message):
        '''Called when a message is sent/recieved.'''
        self.messages_sent += 1
        if message.author.bot:
            return
        await self.process_commands(message)

    async def backup_task(self):
        '''Publish to botlists.'''
        await self.wait_until_ready()
        while not self.is_closed():
            server_count = {'server_count': len(self.guilds)}
            # DBL
            await self.session.post('https://discordbots.org/api/bots/347006499677143041/stats', json=server_count, headers={'Authorization': self.botlist})
            # bots.pw
            await self.session.post('https://bots.discord.pw/api/bots/347006499677143041/stats', json=server_count, headers={
                'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiIxODAzMTQzMTAyOTgzMDQ1MTIiLCJyYW5kIjo1OSwiaWF0IjoxNTI0MjIxNTg4fQ.2hs1gnQ-w8Rvi_3oNICdX2loVnmVDMAnHAJVGm9Taj8'
            })
            # Bots for Discord
            await self.session.post('https://botsfordiscord.com/api/v1/bots/347006499677143041', json=server_count, headers={
                'Authorization': '17d4a786d15ee1e134b93a8cf84ff3a3bd025bc3bd94eee328232e1dd3b8d3b140d62d19b485b8309c9d1bd3846fb5ebf78b83111a8700dca22f00963128c52c',
                'Content-Type': 'application/json'
            })
            await asyncio.sleep(3600)

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
    StatsBot()