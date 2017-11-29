import discord
from discord.ext import commands
from collections import defaultdict
from ext.paginator import PaginatorSession
from ext import embeds
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
import crasync


class Bot_Related:
    '''Commands that pertain to bot utility.'''
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def psa(self, ctx, *, message):
        if ctx.author.id not in self.bot.developers:
            return

        em = discord.Embed(color=0xf9c93d)
        em.title = 'Created Announcement'
        em.description = message

        if message.lower() in 'clearnone':
            em.title = 'Cleared PSA Message'
            em.description = '✅'
            self.bot.psa_message = None
        else:
            self.bot.psa_message = message

        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def maintenance(self, ctx):
        if ctx.author.id not in self.bot.developers:
            return

        if self.bot.maintenance_mode is True:
            await self.bot.change_presence(
                status=discord.Status.online,
                game=None
                )

            self.bot.maintenance_mode = False

            await ctx.send('`Maintenance mode turned off.`')

        else:
            await self.bot.change_presence(
                status=discord.Status.dnd,
                game=discord.Game(name='maintenance!')
                )

            self.bot.maintenance_mode = True

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
        await ctx.send(f'**Invite link:** \n<{discord.utils.oauth_url(self.bot.user.id, perms)}>')

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

        total_online = len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.bot.users)
        channels = sum(1 for g in self.bot.guilds for _ in g.channels)

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
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

        if self.bot.psa_message:
            em.description = f'*{self.bot.psa_message}*'
        else:
            em.description = 'Statsy is a realtime game stats bot made by Kyber, Kwug and 4JR.'

        cbot = '<:certifiedbot:308880575379275776>'

        em.add_field(name='Current Status', value=str(status).title())
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name='Latency', value=f'{self.bot.latency*1000:.2f} ms')
        em.add_field(name='Guilds', value=len(self.bot.guilds))
        em.add_field(name='Members', value=f'{total_online}/{total_unique} online')
        em.add_field(name='Channels', value=f'{channels} total')
        memory_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name='RAM Usage', value=f'{memory_usage:.2f} MiB')
        em.add_field(name='CPU Usage',value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name='Commands Run', value=sum(self.bot.commands_used.values()))
        em.add_field(name='Saved Tags', value=saved_tags)
        em.add_field(name='Library', value='discord.py')
        em.add_field(name='Github', value='[Click Here](https://github.com/grokkers/cr-statsbot)')
        em.add_field(name='Upvote This Bot!', value=f'https://discordbots.org/bot/statsy {cbot}')
        em.set_footer(text=f'Bot ID: {self.bot.user.id}')

        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def update(self, ctx):
        '''Update the bot.'''
        if ctx.author.id not in self.bot.developers:
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
        if ctx.author.id not in self.bot.developers:
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

        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if cmd.instance is cog:
                sigs.append(len(cmd.qualified_name)+len(prefix))
                if hasattr(cmd, 'all_commands'):
                    for c in cmd.all_commands.values():
                        sigs.append(len('\u200b  └─ ' + c.name)+1)

        maxlen = max(sigs)

        fmt = ''
        for cmd in self.bot.commands:
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
        em.description = '*'+(self.bot.psa_message or inspect.getdoc(cog))+'*'
        em.add_field(name='Commands', value=fmt)
        em.set_footer(text=f'Type {prefix}help command for more info on a command.')

        return em

    def format_command_help(self, command, prefix):
        '''Formats command help.'''
        name = command.replace(' ', '_')
        cog = self.bot.cogs.get(name)
        if cog is not None:
            return self.format_cog_help(name, cog, prefix)
        cmd = self.bot.get_command(command)
        if cmd is not None:
            return discord.Embed(
                    color=embeds.random_color(),
                    title=f'`{prefix}{cmd.signature}`', 
                    description=cmd.help
                    )
                
    @commands.command()
    async def help(self, ctx, *, command=None):
        """Shows the help message."""
        prefix = (await self.bot.get_prefix(ctx.message))[2]

        if command:
            em = self.format_command_help(command, prefix)
            if em:
                return await ctx.send(embed=em)
            else:
                return await ctx.send('Could not find a cog or command by that name.')

        pages = []

        for name, cog in sorted(self.bot.cogs.items()):
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
        To display the source code of a subcommand you can separate it spaces. 
        e.g. `!source members best`
        """
        source_url = 'https://github.com/cgrok/statsy'
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
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

        if ctx.author.id not in self.bot.developers: return
        
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
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
            if self.bot.token in value:
                value = value.replace(self.bot.token,"[EXPUNGED]")
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
                self.bot._last_result = ret
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

    @property
    def gitpw(self): 
        with open('data/config.json') as f: 
            return json.load(f)['gittoken']
    
    @commands.command()
    async def suggest(self, ctx, summary:str, *, details:str='-'):
        '''Suggest a game! Or a feature!'''
        details += textwrap.dedent(f'''
\n\n**User Information**
User: {str(ctx.author)} ({str(ctx.author.id)}) 
Guild: {str(ctx.guild)} ({str(ctx.guild.id)})
Channel: {str(ctx.channel)} ({str(ctx.channel.id)})''')
        async with self.bot.session.post('https://api.github.com/repos/cgrok/statsy/issues', json={"title": summary, "body": details, "labels":['suggestion', 'discord']}, headers={'Authorization': f'Bearer {self.gitpw}'}) as resp:
            if 300 > resp.status >= 200:
                issueinfo = await resp.json()
            else:
                await bot.get_channel(373646610560712704).send(f'Suggestion (APIDOWN)\n\n{summary}\n------\n{body}')
                await ctx.send('Suggestion submitted.')

        await ctx.send(f'Suggestion submitted. You can follow up on your suggestion through the link below! \n<{issueinfo["html_url"]}>')

    @commands.command()
    async def bug(self, ctx, summary:str, *, details:str='-'):
        '''Report a bug!'''
        details += textwrap.dedent(f'''
\n\n**User Information**
User: {str(ctx.author)} ({str(ctx.author.id)}) 
Guild: {str(ctx.guild)} ({str(ctx.guild.id)})
Channel: {str(ctx.channel)} ({str(ctx.channel.id)})''')
        async with self.bot.session.post('https://api.github.com/repos/cgrok/statsy/issues', json={"title": summary, "body": details, "labels":['bug', 'discord']}, headers={'Authorization': f'Bearer {self.gitpw}'}) as resp:
            if 300 > resp.status >= 200:
                issueinfo = await resp.json()
            else:
                await bot.get_channel(373646610560712704).send(f'Suggestion (APIDOWN)\n\n{summary}\n------\n{body}')
                await ctx.send('Suggestion submitted.')

        await ctx.send(f'Suggestion submitted. You can follow up on your suggestion through the link below! \n<{issueinfo["html_url"]}>')

    @commands.command(name='guilds')
    async def _guilds(self, ctx):
        if ctx.author.id not in self.bot.developers:
            return
        nano = 0
        tiny = 0
        small = 0
        medium = 0
        large = 0
        massive = 0
        for guild in self.bot.guilds:
            if len(guild.members) < 10:
                nano += 1
            elif len(guild.members) < 100:
                tiny += 1
            elif len(guild.members) < 500:
                small += 1
            elif len(guild.members) < 1000:
                medium += 1
            elif len(guild.members) < 5000:
                large += 1
            else: massive += 1
        await ctx.send(textwrap.dedent(f'''```css
Nano Servers    [ <10  ]:  {nano}
Tiny Servers    [ 10+  ]:  {tiny}
Small Servers   [ 100+ ]:  {small}
Medium Servers  [ 500+ ]:  {medium}
Large Servers   [ 1000+]:  {large}
Massive Servers [ 5000+]:  {massive}```'''))

def setup(bot):
    c = Bot_Related(bot)
    bot.add_cog(c)