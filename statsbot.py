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

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''
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
        376365022752014345
        ]

    developers = [
        273381165229146112,
        319395783847837696,
        180314310298304512,
        377742732501843968,
        319778485239545868,
        325012556940836864
    ]

    def __init__(self):
        super().__init__(command_prefix=None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cr = crasync.Client(self.session)
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = defaultdict(int)
        self.process = psutil.Process(os.getpid())
        self.remove_command('help')
        self.messages_sent = 0
        self.maintenance_mode = False
        self.psa_message = None
        self.loop.create_task(self.backup_task())
        self.load_extensions()
        self.cogs['Bot_Related'] = self

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
        em.color = 0xf9c93d
        try:
            await ctx.send(embed=em)
        except discord.Forbidden:
            await ctx.send(em.title + em.description)

    @commands.command(hidden=True)
    async def psa(self, ctx, *, message):
        if ctx.author.id not in self.developers:
            return

        em = discord.Embed(color=0xf9c93d)
        em.title = 'Created Announcement'
        em.description = message

        if message.lower() in 'clearnone':
            em.title = 'Cleared PSA Message'
            em.description = '✅'
            self.psa_message = None
        else:
            self.psa_message = message

        await ctx.send(embed=em)


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

    @commands.command(name='bot',aliases=['about', 'info', 'botto'])
    async def _bot(self, ctx):
        '''Shows information and stats about the bot.'''
        cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/cgrok/statsy/commit/%H) %s (%cr)"'

        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')

        revision = os.popen(cmd).read().strip()

        em = discord.Embed()
        em.add_field(name='Latest Changes', value=revision, inline=False)
        em.timestamp = datetime.datetime.utcnow()
        status = str(ctx.guild.me.status)
        if status == 'online':
            em.set_author(name="Bot Information", icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name="Bot Information", icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name="Bot Information", icon_url='https://i.imgur.com/dCLTaI3.png')
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

        if self.psa_message:
            em.description = f'*{self.psa_message}*'
        else:
            em.description = 'Statsy is a realtime game stats bot made by Kyber, Kwug and 4JR.'

        cbot = '<:certifiedbot:308880575379275776>'

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
        em.add_field(name='Library', value='discord.py')
        em.add_field(name='Github', value='[Click Here](https://github.com/grokkers/cr-statsbot)')
        em.add_field(name='Upvote This Bot!', value=f'https://discordbots.org/bot/statsy {cbot}')
        em.set_footer(text=f'Bot ID: {self.user.id}')

        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def update(self, ctx):
        '''Update the bot.'''
        if ctx.author.id not in self.developers:
            return
        with open('data/config.json') as f:
            password = json.load(f).get('password')

        em = discord.Embed(color=0xf9c93d)
        em.title = 'Updating Bot'
        em.description = 'Pulling from repository and restarting `stats.service`.'
        await ctx.send(embed=em)
        command = 'sh ../stats.sh'
        p = os.system(f'echo {password}|sudo -S {command}')

    @commands.command(hidden=True)
    async def tokenupdate(self, ctx, _token):
        '''Update the bot's botlist token'''
        if ctx.author.id not in self.developers:
            return
        with open('data/config.json') as f:
            config = json.load(f)
        config['botlist'] = _token
        with open('data/config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send('Updated bot list token, restarting bot.')
        await ctx.invoke(StatsBot.update)


    def format_cog_help(self, name, cog, prefix):
        '''Formats the text for a cog help'''
        sigs = []

        for cmd in self.commands:
            if cmd.hidden:
                continue
            if cmd.instance is cog:
                sigs.append(len(cmd.qualified_name)+len(prefix))
                if hasattr(cmd, 'all_commands'):
                    for c in cmd.all_commands.values():
                        sigs.append(len('\u200b  └─ ' + c.name)+1)

        maxlen = max(sigs)

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

        em = discord.Embed(title=name.replace('_',' '))
        em.color = embeds.random_color()
        em.description = '*'+(self.psa_message or inspect.getdoc(cog))+'*'
        em.add_field(name='Commands', value=fmt)
        em.set_footer(text=f'Type {prefix}help command for more info on a command.')

        return em

    def format_command_help(self, command, prefix):
        '''Formats command help.'''
        name = command.replace(' ', '_')
        cog = self.cogs.get(name)
        if cog is not None:
            return self.format_cog_help(name, cog, prefix)
        cmd = self.get_command(command)
        if cmd is not None:
            return discord.Embed(
                    color=embeds.random_color(),
                    title=f'`{prefix}{cmd.signature}`', 
                    description=cmd.help
                    )
                
    @commands.command()
    async def help(self, ctx, *, command=None):
        """Shows the help message."""
        prefix = (await self.get_prefix(ctx.message))[2]

        if command:
            em = self.format_command_help(command, prefix)
            if em:
                return await ctx.send(embed=em)
            else:
                return await ctx.send('Could not find a cog or command by that name.')

        pages = []

        for name, cog in sorted(self.cogs.items()):
            em = self.format_cog_help(name, cog, prefix)
            pages.append(em)

        p_session = PaginatorSession(ctx, 
            footer_text=f'Type {prefix}help command for more info on a command.',
            pages=pages
            )

        await p_session.run()

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Displays full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """
        source_url = 'https://github.com/cgrok/statsy'
        if command is None:
            return await ctx.send(source_url)

        obj = self.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        if not obj.callback.__module__.startswith('discord'):
            location = os.path.relpath(src.co_filename).replace('\\', '/')
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'

        final_url = f'<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

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
            await ctx.message.add_reaction('\u2705') #tick
        if err:
            await ctx.message.add_reaction('\u2049') #x
        else:
            await ctx.message.add_reaction('\u2705')

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
