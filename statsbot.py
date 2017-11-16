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

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''
    pass

class StatsBot(commands.AutoShardedBot):
    '''
    Custom Client for cr-statsbot - Made by verix#7220
    '''
    emoji_servers = [
        376364364636094465, 
        376368487037140992, 
        376364990023729152, 
        377742732501843968,
        376365022752014345
        ]

    developers = [
        273381165229146112,
        319395783847837696,
        180314310298304512,
        377742732501843968
    ]

    def __init__(self):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasync.Client(self.session)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process()
        self.remove_command('help')
        self.messages_sent = 0
        self.maintenance_mode = False
        self.loop.create_task(self.backup_task())
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

        Still need to do stuff with db to get server prefix.
        '''
        with open('data/guild.json') as f:
            cfg = json.load(f)

        id = str(message.guild.id)

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

        self._add_commands()
        # had to put this here due to an issue with the 
        # latencies property
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
        channel = self.get_channel(373646610560712704)
        self.game_emojis = self.get_game_emojis()
        await channel.send(f'```{fmt}```')

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
        else:
            if self.maintenance_mode is True:
                if message.author.id not in self.developers:
                    return await ctx.send('The bot is under maintenance at the moment!')
            await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        error_message = 'Player tags should only contain these characters:\n' \
                        '**Numbers:** 0, 2, 8, 9\n' \
                        '**Letters:** P, Y, L, Q, G, R, J, C, U, V'
        if isinstance(error, InvalidTag):
            await ctx.send(error_message)
        else:
            if isinstance(error, commands.MissingRequiredArgument):
                prefix = (await self.get_prefix(ctx.message))[2]
                await ctx.send(embed=discord.Embed(color=embeds.random_color(), title=f'``Usage: {prefix}{ctx.command.signature}``', description=ctx.command.help))
            else:
                await self.get_channel(376622292106608640).send(embed=discord.Embed(color=discord.Color.orange(), description=f"```\n{type(error).__name__}: {error}\n```", title=ctx.invoked_with))
            raise error

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
        em.color = await ctx.get_dominant_color(self.user.avatar_url)
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)

    @commands.command(hidden=True)
    async def maintenance(self, ctx):
        if ctx.author.id not in self.developers:
            return

        if self.maintenance_mode is True:
            await self.change_presence(
                status=discord.Status.online,
                game=None
                )
            async with ctx.session.get("https://cdn.discordapp.com/attachments/376908250752352266/377862393490964510/stats.png") as resp:
                image = await resp.read()
            await self.user.edit(avatar=image)

            self.maintenance_mode = False

            await ctx.send('`Maintenance mode turned off.`')

        else:
            await self.change_presence(
                status=discord.Status.dnd,
                game=discord.Game(name='maintenance!')
                )
            async with ctx.session.get("https://cdn.discordapp.com/attachments/376908250752352266/377862378684940288/stats-dnd.png") as resp:
                image = await resp.read()
            await self.user.edit(avatar=image)

            self.maintenance_mode = True

            await ctx.send('`Maintenance mode turned on.`')


    @commands.command()
    async def invite(self, ctx):
        """Returns the invite url for the bot."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.embed_links = True
        perms.attach_files = True
        perms.add_reactions = True
        perms.manage_messages = True
        await ctx.send(f'**Invite link:** \n<{discord.utils.oauth_url(self.user.id, perms)}>')

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix):
        '''Change the bot prefix for your server.'''
        id = str(ctx.guild.id)
        g_config = ctx.load_json('data/guild.json')
        g_config[id] = prefix
        ctx.save_json(g_config, 'data/guild.json')
        await ctx.send(f'Changed the prefix to: `{prefix}`')

    @commands.command(name='bot',aliases=['about', 'info'])
    async def _bot(self, ctx):
        '''Shows information and stats about the bot.'''
        em = discord.Embed()
        em.timestamp = datetime.datetime.utcnow()
        status = str(ctx.guild.me.status)
        if status == 'online':
            em.set_author(name="Stats", icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name="Stats", icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name="Stats", icon_url='https://i.imgur.com/dCLTaI3.png')
            em.color = discord.Color.red()

        total_online = len({m.id for m in self.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.users)
        channels = sum(1 for g in self.guilds for _ in g.channels)

        now = datetime.datetime.utcnow()
        delta = now - self.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt
        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)
        data = ctx.load_json()
        saved_tags = len(data['clashroyale'])+len(data['clashofclans'])
        g_authors = 'verixx, fourjr, kwugfighter, FloatCobra, XAOS1502'
        em.description = 'StatsBot by kwugfighter and fourjr. Join the support server [here](https://discord.gg/maZqxnm).'

        em.add_field(name='Current Status', value=str(status).title())
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name='Latency', value=f'{self.latency*1000:.2f} ms')
        em.add_field(name='Guilds', value=len(self.guilds))
        em.add_field(name='Members', value=f'{total_online}/{total_unique} online')
        em.add_field(name='Channels', value=f'{channels} total')
        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name='RAM Usage', value=f'{memory_usage:.2f} MiB')
        em.add_field(name='CPU Usage',value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name='Commands Run', value=sum(self.commands_used.values()))
        em.add_field(name='Saved Tags', value=saved_tags)
        em.add_field(name='Github', value='[Click Here](https://github.com/grokkers/cr-statsbot)')
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.embed_links = True
        perms.attach_files = True
        perms.add_reactions = True
        perms.manage_messages = True
        em.add_field(name='Invite', value=f'[Click Here]({discord.utils.oauth_url(self.user.id, perms)})')
        em.set_footer(text=f'Statsy | Bot ID: {self.user.id}')

        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def update(self, ctx):
        '''Update the bot.'''
        if ctx.author.id not in self.developers:
            return
        with open('data/config.json') as f:
            password = json.load(f).get('password')
        await ctx.send('`Updating self and restarting...`')
        command = 'sh ../stats.sh'
        p = os.system('echo %s|sudo -S %s' % (password, command))

    @commands.command()
    async def help(self, ctx, *, command=None):
        """Shows the help message."""

        prefix = (await self.get_prefix(ctx.message))[2]

        if command is not None:
            command = self.get_command(command)
            return await ctx.send(
                embed=discord.Embed(
                    color=embeds.random_color(), 
                    title=f'``Usage: {prefix}{command.signature}``', 
                    description=command.help
                    )
                )

        sigs = []

        for cmd in self.commands:
            if cmd.hidden:
                continue
            sigs.append(len(cmd.qualified_name)+len(prefix))
            if hasattr(cmd, 'all_commands'):
                for c in cmd.all_commands.values():
                    sigs.append(len('\u200b  └─ ' + c.name)+1)

        maxlen = max(sigs)

        em = discord.Embed(color=embeds.random_color())
        em.set_footer(text='Statsy - Powered by cr-api.com')

        for cog in self.cogs.values():
            fmt = ''
            for cmd in self.commands:
                if cmd.instance is cog:
                    if cmd.hidden:
                        continue
                    fmt += f'`{prefix+cmd.qualified_name:<{maxlen}} '
                    fmt += f'{cmd.short_doc:<{maxlen}}`\n'
                    if hasattr(cmd, 'commands'):
                        for c in cmd.commands:
                            branch = '\u200b  └─ ' + c.name
                            fmt += f"`{branch:<{maxlen+1}} " 
                            fmt += f"{c.short_doc:<{maxlen}}`\n"

            cog_name = type(cog).__name__.replace('_', ' ')
            em.add_field(name=cog_name, value=fmt)

        fmt = ''

        for cmd in self.commands:
            if cmd.instance is self:
                if cmd.hidden:
                    continue
                fmt += f'`{prefix+cmd.qualified_name:<{maxlen}} '
                fmt += f'{cmd.short_doc:<{maxlen}}`\n'
                if hasattr(cmd, 'commands'):
                    for c in cmd.commands:
                        branch = '\u200b  └─ ' + c.name
                        fmt += f"`{branch:<{maxlen+1}} " 
                        fmt += f"{c.short_doc:<{maxlen}}`\n"

        em.add_field(name='Bot Related', value=fmt)

        await ctx.send(embed=em)

    @commands.command()
    async def source(self, ctx, *, command):
        '''See the source code for any command.'''
        source = str(inspect.getsource(self.get_command(command).callback))
        fmt = '​`​`​`py\n' + source.replace('​`', '\u200b​`') + '\n​`​`​`'
        if len(fmt) > 2000:
            async with ctx.session.post("https://hastebin.com/documents", data=source) as resp:
                data = await resp.json()
            key = data['key']
            return await ctx.send(f'Command source: <https://hastebin.com/{key}.py>')
        else:
            return await ctx.send(fmt)

    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates python code"""

        if ctx.author.id not in self.developers: return
        
        env = {
            'bot': self,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            #'_': self._last_result,
            'source': inspect.getsource
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()
        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            return await err.add_reaction('\u2049')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if self.token in value:
                value = value.replace(self.token,"[EXPUNGED]")
            if ret is None:
                if value:
                    try:
                        out = await ctx.send(f'```py\n{value}\n```')
                    except:
                        paginated_text = ctx.paginate(value)
                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                out = await ctx.send(f'```py\n{page}\n```')
                                break
                            await ctx.send(f'```py\n{page}\n```')
            else:
                self._last_result = ret
                try:
                    out = await ctx.send(f'```py\n{value}{ret}\n```')
                except:
                    paginated_text = ctx.paginate(f"{value}{ret}")
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            out = await ctx.send(f'```py\n{page}\n```')
                            break
                        await ctx.send(f'```py\n{page}\n```')

        if out:
            await out.add_reaction('\u2705') #tick
        if err:
            await err.add_reaction('\u2049') #x

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'



if __name__ == '__main__':
    StatsBot.init()
