import copy
import datetime
import inspect
import io
import json
import os
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
import psutil
from discord.ext import commands

from ext import embeds_cr as embeds
from ext.paginator import PaginatorSession

from locales.i18n import Translator

_ = Translator('Utils', __file__)


class Bot_Related:
    """Commands that pertain to bot utility."""
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
        await ctx.send(_('**Invite link:** \n<{}>', ctx).format(discord.utils.oauth_url(self.bot.user.id, perms)))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix):
        """Change the bot prefix for your server."""
        if not ctx.guild:
            return await ctx.send("Changing prefix isn't allowed in DMs")
        if prefix == '!':
            await self.bot.mongo.config.guilds.find_one_and_delete(
                {'guild_id': ctx.guild.id}
            )
        else:
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': ctx.guild.id}, {'$set': {'prefix': prefix}}, upsert=True
            )
        await ctx.send(_('Changed the prefix to: `{}`', ctx).format(prefix))

    @commands.command(name='bot', aliases=['about', 'info', 'botto'])
    async def _bot(self, ctx):
        """Shows information and stats about the bot."""
        em = discord.Embed(timestamp=datetime.datetime.utcnow())
        status = str(getattr(ctx.guild, 'me', self.bot.guilds[0].me).status)
        if status == 'online':
            em.set_author(name=_("Bot Information", ctx), icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name=_("Bot Information", ctx), icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name=_("Bot Information", ctx), icon_url='https://i.imgur.com/dCLTaI3.png')
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

        games = ('clashroyale', 'brawlstars', 'clashofclans', 'overwatch')
        saved_tags = sum([await self.bot.mongo.player_tags[i].find().count() for i in games])

        if self.bot.psa_message:
            em.description = f'*{self.bot.psa_message}*'
        else:
            em.description = _('Statsy is a realtime game stats bot made by Kyber, Kwug and 4JR.', ctx)

        em.description += '\n\n'
        em.description += _("This content is not affiliated with, endorsed, sponsored, or specifically approved by Supercell and Supercell is not responsible for it. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.", ctx)

        cbot = '<:certifiedbot:427089403060551700>'

        royaleapi_donate = '[Paypal](https://paypal.me/royaleapi) | [Patreon](https://www.patreon.com/RoyaleAPI)'

        em.add_field(name=_('Current Status', ctx), value=str(status).title())
        em.add_field(name=_('Uptime', ctx), value=uptime)
        em.add_field(name=_('Latency', ctx), value=f'{self.bot.latency*1000:.2f} ms')
        em.add_field(name=_('Guilds', ctx), value=len(self.bot.guilds))
        em.add_field(name=_('Members', ctx), value=f'{total_online}/{total_unique} online')
        em.add_field(name=_('Channels', ctx), value=f'{channels} total')
        memory_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name=_('RAM Usage', ctx), value=f'{memory_usage:.2f} MiB')
        em.add_field(name=_('CPU Usage', ctx), value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name=_('Commands Run', ctx), value=sum(self.bot.commands_used.values()))
        em.add_field(name=_('Saved Tags', ctx), value=saved_tags)
        em.add_field(name=_('Library', ctx), value='discord.py rewrite')
        em.add_field(name=_('Donate!', ctx), value=f'Support RoyaleAPI: {royaleapi_donate}')
        em.add_field(name=_('Discord', ctx), value='[Click Here](https://discord.gg/cBqsdPt)')
        em.add_field(name=_('Follow us on Twitter!', ctx), value='https://twitter.com/StatsyBot', inline=False)
        em.add_field(name=_('Upvote This Bot!', ctx), value=f'https://discordbots.org/bot/statsy {cbot}', inline=False)
        em.set_footer(text=_('Bot ID: {}', ctx).format(self.bot.user.id))

        await ctx.send(embed=em)

    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Restarts the bot."""
        if ctx.author.id not in self.bot.developers:
            return

        em = discord.Embed(color=0xf9c93d)
        em.title = 'Restarting Bot'
        em.description = 'Restarting `Statsy`.'
        await ctx.send(embed=em)
        await self.bot.logout()

    def format_cog_help(self, name, cog, prefix):
        """Formats the text for a cog help"""
        sigs = []

        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if cmd.instance is cog:
                sigs.append(len(cmd.qualified_name) + len(prefix))
                if hasattr(cmd, 'all_commands'):
                    for c in cmd.all_commands.values():
                        sigs.append(len('\u200b  └─ ' + c.name) + 1)

        if not sigs:
            return

        maxlen = max(sigs)

        fmt = ['']
        index = 0
        for cmd in self.bot.commands:
            if cmd.instance is cog:
                if cmd.hidden:
                    continue
                if len(fmt[index] + f'`{prefix+cmd.qualified_name:<{maxlen}} ' + f'{cmd.short_doc:<{maxlen}}`\n') > 1024:
                    index += 1
                    fmt.append('')
                fmt[index] += f'`{prefix+cmd.qualified_name:<{maxlen}} '
                fmt[index] += f'{cmd.short_doc:<{maxlen}}`\n'
                if hasattr(cmd, 'commands'):
                    for c in cmd.commands:
                        branch = '\u200b  └─ ' + c.name
                        if len(fmt[index] + f"`{branch:<{maxlen+1}} " + f"{c.short_doc:<{maxlen}}`\n") > 1024:
                            index += 1
                            fmt.append('')
                        fmt[index] += f"`{branch:<{maxlen+1}} "
                        fmt[index] += f"{c.short_doc:<{maxlen}}`\n"

        em = discord.Embed(
            title=name.replace('_', ' '),
            description='*' + (self.bot.psa_message or inspect.getdoc(cog)) + '*',
            color=embeds.random_color()
        )
        for n, i in enumerate(fmt):
            if n == 0:
                em.add_field(name='Commands', value=i)
            else:
                em.add_field(name=u'\u200b', value=i)
        em.set_footer(text=f'Type {prefix}help command for more info on a command.')

        return em

    def format_command_help(self, command, prefix):
        """Formats command help."""
        name = command.replace(' ', '_')
        cog = self.bot.cogs.get(name)
        if cog is not None:
            return self.format_cog_help(name, cog, prefix)
        cmd = self.bot.get_command(command)
        if cmd is not None and not cmd.hidden:
            return discord.Embed(
                color=embeds.random_color(),
                title=f'`{prefix}{cmd.signature}`',
                description=cmd.help
            )

    @commands.command(name='help')
    async def _help(self, ctx, *, command=None):
        """Shows the help message."""
        try:
            prefix = (await self.bot.get_prefix(ctx.message))[2]
        except IndexError:
            prefix = await self.bot.get_prefix(ctx.message)

        if command:
            em = self.format_command_help(command, prefix)
            if em:
                return await ctx.send(embed=em)
            else:
                return await ctx.send(_('Could not find a cog or command by that name.', ctx))

        pages = []

        for name, cog in sorted(self.bot.cogs.items()):
            if name == 'Moderation':
                # hidden cog :p
                continue
            em = self.format_cog_help(name, cog, prefix)
            pages.append(em)

        p_session = PaginatorSession(
            ctx,
            footer_text=_('Type {}help command for more info on a command.', ctx).format(prefix),
            pages=pages
        )

        await p_session.run()

    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates python code"""

        if ctx.author.id not in self.bot.developers:
            return

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
            value = stdout.getvalue().replace(os.getenv('token'), "[EXPUNGED]")
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
            await ctx.message.add_reaction('\u2705')  # tick
        if err:
            await ctx.message.add_reaction('\u2049')  # x
        else:
            await ctx.message.add_reaction('\u2705')

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    async def suggest(self, ctx, *, details: str):
        """Suggest a game! Or a feature!"""

        details += f'\n\n Posted by: {ctx.author} ({ctx.author.id})'

        async with self.bot.session.post(
            'https://api.github.com/repos/kyb3r/statsy/issues',
            json={
                'title': f'New suggestion from {ctx.author.name}',
                'body': details,
                'labels': ['suggestion', 'discord']
            },
            headers={'Authorization': f'Bearer {os.getenv("github")}'}
        ) as resp:
            if not 300 > resp.status >= 200:
                await self.bot.get_channel(373646610560712704).send(f'Suggestion (APIDOWN)\n\n{details}')
                await ctx.send('Suggestion submitted.')

        await ctx.send(_('Suggestion submitted. Thanks for the feedback!', ctx))

    @commands.command()
    async def bug(self, ctx, *, details: str):
        """Report a bug!"""

        details += f'\n\n Posted by: {ctx.author} ({ctx.author.id})'

        async with self.bot.session.post(
            'https://api.github.com/repos/kyb3r/statsy/issues',
            json={
                'title': f'New bug report from {ctx.author.name}',
                'body': details,
                'labels': ['bug', 'discord']
            },
            headers={'Authorization': f'Bearer {os.getenv("github")}'}
        ) as resp:
            if not 300 > resp.status >= 200:
                await self.bot.get_channel(373646610560712704).send(f'Bug (APIDOWN)\n\n{details}')
                await ctx.send('Bug reported.')

        await ctx.send(_('Bug Reported. Thanks for the report!', ctx))

    @commands.command(hidden=True)
    async def sudo(self, ctx, user: discord.Member, command, *, args=None):
        if ctx.author.id not in self.bot.developers:
            return
        new_ctx = copy.copy(ctx)
        new_ctx.author = user
        command = self.bot.get_command(command)
        if not command:
            return await ctx.send('Invalid command')
        args = {j.split(':')[0]: j.split(':')[1] for j in args.split(' ')} if args else {}
        await new_ctx.invoke(command, **args)

    @commands.command(name='guilds', hidden=True)
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
            else:
                massive += 1
        await ctx.send(textwrap.dedent(f"""```css
Nano Servers    [ <10  ]:  {nano}
Tiny Servers    [ 10+  ]:  {tiny}
Small Servers   [ 100+ ]:  {small}
Medium Servers  [ 500+ ]:  {medium}
Large Servers   [ 1000+]:  {large}
Massive Servers [ 5000+]:  {massive}
Total                   :  {len(self.bot.guilds)}```"""))

    @commands.command(name='commands', aliases=['cmd'], hidden=True)
    async def commands_(self, ctx):
        """Displays command usage"""
        if ctx.author.id not in self.bot.developers:
            return
        command_usage = (await self.bot.mongo.config.admin.find_one({'_id': 'master'}))['commands']
        sorted_usage = sorted(command_usage, key=lambda x: command_usage[x], reverse=True)
        sorted_commands = {i: command_usage[i] for i in sorted_usage}
        await ctx.send('```json\n' + json.dumps(sorted_commands, indent=4) + '\n```')

    @commands.command(name='language')
    async def language_(self, ctx, language=None):
        languages = {
            'spanish': 'es',
            'english': 'messages'
        }
        if not language or language not in languages:
            await ctx.send(_('Available languages: {}', ctx).format(', '.join([i.title() for i in languages.keys()])))
        else:
            await self.bot.mongo.config.guilds.find_one_and_update({'guild_id': ctx.guild.id}, {'$set': {'language': languages[language]}}, upsert=True)
            await ctx.send(_('Language set. This might take up to a minute to update.', ctx))

    @commands.command()
    async def enable(self, ctx, *, cog_name: str):
        shortcuts = {
            'coc': 'Clash_Of_Clans',
            'cr': 'Clash_Royale',
            'ow': 'Overwatch',
            'fn': 'Fortnite'
        }
        if cog_name in shortcuts:
            cog_name = shortcuts[cog_name]
        cog = self.bot.get_cog(cog_name.title().replace(' ', '_'))

        if cog in (self, self.bot.get_cog('Moderation'), None):
            await ctx.send(_('Invalid game. Pick from: {}', ctx).format(', '.join(shortcuts.keys())))
        else:
            cog_name = cog.__class__.__name__
            await self.bot.mongo.config.guilds.find_one_and_update({'guild_id': ctx.guild.id}, {'$set': {f'games.{cog_name}': True}}, upsert=True)
            await ctx.send('Successfully enabled {}'.format(cog_name))

    @commands.command()
    async def disable(self, ctx, *, cog_name: str):
        shortcuts = {
            'coc': 'Clash_Of_Clans',
            'cr': 'Clash_Royale',
            'ow': 'Overwatch',
            'fn': 'Fortnite'
        }
        if cog_name in shortcuts:
            cog_name = shortcuts[cog_name]
        cog = self.bot.get_cog(cog_name.title().replace(' ', '_'))

        if cog in (self, self.bot.get_cog('Moderation'), None):
            await ctx.send(_('Invalid game. Pick from: {}', ctx).format(', '.join(shortcuts.keys())))
        else:
            cog_name = cog.__class__.__name__
            await self.bot.mongo.config.guilds.find_one_and_update({'guild_id': ctx.guild.id}, {'$set': {f'games.{cog_name}': False}}, upsert=True)
            await ctx.send('Successfully disabled {}'.format(cog_name))

def setup(bot):
    c = Bot_Related(bot)
    bot.add_cog(c)
