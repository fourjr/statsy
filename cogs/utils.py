import copy
import datetime
import inspect
import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout

import datadog
import discord
import psutil
from discord.ext import commands

from ext import utils
from ext.command import command
from ext.paginator import Paginator

from locales.i18n import Translator

_ = Translator('Utils', __file__)


class Bot_Related:
    """Commands that pertain to bot utility."""
    def __init__(self, bot):
        self.bot = bot

    @utils.developer()
    @command(hidden=True)
    async def psa(self, ctx, *, message):
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

    @utils.developer()
    @command()
    async def maintenance(self, ctx):
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

    @command()
    async def invite(self, ctx):
        """Returns the invite url for the bot."""
        perms = discord.Permissions()
        perms.update(
            read_messages=True,
            external_emojis=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            manage_messages=True
        )
        await ctx.send(_('**Invite link:** \n<{}>').format(discord.utils.oauth_url(self.bot.user.id, perms)))

    @command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix):
        """Change the bot prefix for your server."""
        if not ctx.guild:
            return await ctx.send("Changing prefix isn't allowed in DMs")
        if prefix == '!':
            await self.bot.mongo.config.guilds.find_one_and_delete(
                {'guild_id': str(ctx.guild.id)}
            )
        else:
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': str(ctx.guild.id)}, {'$set': {'prefix': str(prefix)}}, upsert=True
            )
        await ctx.send(_('Changed the prefix to: `{}`').format(prefix))

    @command(name='bot', aliases=['about', 'info', 'botto'])
    async def bot_(self, ctx):
        """Shows information and stats about the bot."""
        em = discord.Embed(timestamp=datetime.datetime.utcnow())
        status = str(getattr(ctx.guild, 'me', self.bot.guilds[0].me).status)
        if status == 'online':
            em.set_author(name=_("Bot Information"), icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name=_("Bot Information"), icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name=_("Bot Information"), icon_url='https://i.imgur.com/dCLTaI3.png')
            em.color = discord.Color.red()

        total_online = len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.bot.users)
        channels = sum(1 for g in self.bot.guilds for _ in g.channels)

        delta = datetime.datetime.utcnow() - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt
        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)

        games = await self.bot.mongo.player_tags.list_collection_names()
        saved_tags = sum([await self.bot.mongo.player_tags[i].count_documents({}) for i in games])

        if self.bot.psa_message:
            em.description = f'*{self.bot.psa_message}*'
        else:
            em.description = _('Statsy is a realtime game stats bot made by Kyber, Kwug and 4JR.')

        em.description += '\n\n'
        em.description += _("This content is not affiliated with, endorsed, sponsored, or specifically approved by Supercell and Supercell is not responsible for it. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy")

        cbot = '<:certifiedbot:427089403060551700>'

        em.add_field(name=_('Current Status'), value=str(status).title())
        em.add_field(name=_('Uptime'), value=uptime)
        em.add_field(name=_('Latency'), value=f'{self.bot.latency*1000:.2f} ms')
        em.add_field(name=_('Guilds'), value=len(self.bot.guilds))
        em.add_field(name=_('Shards'), value=self.bot.shard_count)
        em.add_field(name=_('Members'), value=f'{total_online}/{total_unique} online')
        em.add_field(name=_('Channels'), value=f'{channels} total')
        memory_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name=_('RAM Usage'), value=f'{memory_usage:.2f} MiB')
        em.add_field(name=_('CPU Usage'), value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name=_('Saved Tags'), value=saved_tags)
        em.add_field(name=_('Library'), value='discord.py rewrite')
        em.add_field(name=_('Discord'), value='[Click Here](https://discord.gg/cBqsdPt)')
        em.add_field(name=_('Github'), value='[Click Here](https://github.com/cgrok/statsy)')
        em.add_field(name=_('Follow us on Twitter!'), value='https://twitter.com/StatsyBot', inline=False)
        em.add_field(name=_('Upvote This Bot!'), value=f'https://discordbots.org/bot/statsy {cbot}', inline=False)
        em.set_footer(text=_('Bot ID: {}').format(self.bot.user.id))

        await ctx.send(embed=em)

    @utils.developer()
    @command()
    async def restart(self, ctx):
        """Restarts the bot."""
        em = discord.Embed(color=0xf9c93d)
        em.title = 'Restarting Bot'
        em.description = 'Restarting `Statsy`.'
        await ctx.send(embed=em)
        await self.bot.logout()

    @utils.developer()
    @command(name='reload')
    async def reload_(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.message.add_reaction('check:383917703083327489')

    async def format_cog_help(self, ctx, name, cog, prefix):
        """Formats the text for a cog help"""
        sigs = []

        async def blank(*args):
            return True

        if not await getattr(cog, f'_{name}__local_check', blank)(ctx):
            return

        for cmd in self.bot.commands:
            if cmd.hidden or not cmd.enabled:
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
                if cmd is not None:
                    predicates = cmd.checks
                    if not predicates:
                        can_run = True

                    try:
                        can_run = (await discord.utils.async_all(predicate(ctx) for predicate in predicates))
                    except commands.CheckFailure:
                        can_run = False

                    if cmd.hidden or not cmd.enabled or not can_run:
                        continue
                    if len(fmt[index] + f'`{prefix+cmd.qualified_name:<{maxlen}} ' + f'{cmd.short_doc(ctx):<{maxlen}}`\n') > 1024:
                        index += 1
                        fmt.append('')
                    fmt[index] += f'`{prefix+cmd.qualified_name:<{maxlen}} '
                    fmt[index] += f'{cmd.short_doc(ctx):<{maxlen}}`\n'
                    if hasattr(cmd, 'commands'):
                        for c in cmd.commands:
                            branch = '\u200b  └─ ' + c.name
                            if len(fmt[index] + f"`{branch:<{maxlen+1}} " + f"{c.short_doc(ctx):<{maxlen}}`\n") > 1024:
                                index += 1
                                fmt.append('')
                            fmt[index] += f"`{branch:<{maxlen+1}} "
                            fmt[index] += f"{c.short_doc(ctx):<{maxlen}}`\n"

        em = discord.Embed(
            title=name.replace('_', ' '),
            description='*' + (self.bot.psa_message or inspect.getdoc(cog)) + '*',
            color=utils.random_color()
        )
        for n, i in enumerate(fmt):
            if n == 0:
                em.add_field(name='Commands', value=i)
            else:
                em.add_field(name=u'\u200b', value=i)
        em.set_footer(text=f'Type {prefix}help command for more info on a command.')

        return em

    async def format_command_help(self, ctx, command, prefix):
        """Formats command help."""
        name = command.replace(' ', '_')
        cog = self.bot.cogs.get(name)
        if cog is not None:
            return await self.format_cog_help(ctx, name, cog, prefix)
        cmd = self.bot.get_command(command)

        if cmd is not None:
            predicates = cmd.checks
            if not predicates:
                can_run = True
            try:
                can_run = (await discord.utils.async_all(predicate(ctx) for predicate in predicates))
            except commands.CheckFailure:
                can_run = False

            if not cmd.hidden and cmd.enabled and can_run:
                em = discord.Embed(
                    description=cmd.help,
                    color=utils.random_color()
                )

                if hasattr(cmd, 'invoke_without_command') and cmd.invoke_without_command:
                    em.title = f'Usage: {prefix}{cmd.signature}'
                else:
                    em.title = f'{prefix}{cmd.signature}'

                if not hasattr(cmd, 'commands'):
                    return em

                maxlen = max(len(prefix + str(c)) for c in cmd.commands)
                fmt = ''

                for i, c in enumerate(cmd.commands):
                    if len(cmd.commands) == i + 1:  # last
                        branch = '└─ ' + c.name
                    else:
                        branch = '├─ ' + c.name
                    fmt += f"`{branch:<{maxlen+1}} "
                    fmt += f"{c.short_doc(ctx):<{maxlen}}`\n"

                em.add_field(name='Subcommands', value=fmt)
                em.set_footer(text=f'Type {prefix}help {cmd} command for more info on a command.')

                return em

    @command(name='help')
    async def _help(self, ctx, *, command=None):
        """Shows the help message."""
        try:
            prefix = (await self.bot.get_prefix(ctx.message))[2]
        except IndexError:
            prefix = await self.bot.get_prefix(ctx.message)

        if command:
            em = await self.format_command_help(ctx, command, prefix)
            if em:
                return await ctx.send(embed=em)
            else:
                return await ctx.send(_('Could not find a cog or command by that name.'))

        pages = []

        for name, cog in sorted(self.bot.cogs.items()):
            em = await self.format_cog_help(ctx, name, cog, prefix)
            if em:
                pages.append(em)

        await Paginator(ctx, *pages, footer_text=_('Type {}help command for more info on a command.').format(prefix)).start()

    @utils.developer()
    @command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates python code"""
        env = {
            'self': self,
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
        except Exception:
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

    @command()
    async def suggest(self, ctx, *, details: str):
        """Suggest a game! Or a feature!"""
        em = discord.Embed(title=f'New Suggestion', description=details, color=utils.random_color())
        em.set_footer(text=f'G: {getattr(ctx.guild, "id", "DM")} | C: {ctx.channel.id} | U: {ctx.author.id}')
        await self.bot.get_channel(513715119520481290).send(embed=em)

        await ctx.send(_('Suggestion submitted. Thanks for the feedback!'))

    @utils.developer()
    @command()
    async def sudo(self, ctx, user: discord.User, command, *, args=None):
        new_ctx = copy.copy(ctx)
        new_ctx.author = user
        command = self.bot.get_command(command)
        if not command:
            return await ctx.send('Invalid command')
        try:
            args = {j.split(':')[0]: j.split(':')[1] for j in args.split(' ')} if args else {}
        except IndexError:
            print('Invalid args')
        try:
            await new_ctx.invoke(command, **args)
        except Exception:
            await ctx.send(traceback.format_exc())

    @command(name='guilds', hidden=True)
    async def guilds_(self, ctx):
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
Shards          [      ]:  {self.bot.shard_count}
Nano Servers    [ <10  ]:  {nano}
Tiny Servers    [ 10+  ]:  {tiny}
Small Servers   [ 100+ ]:  {small}
Medium Servers  [ 500+ ]:  {medium}
Large Servers   [ 1000+]:  {large}
Massive Servers [ 5000+]:  {massive}
Total                   :  {len(self.bot.guilds)}```"""))

    @command(name='shards', hidden=True)
    async def shards_(self, ctx):
        em = discord.Embed(title='Shard Information', color=utils.random_color())
        em.set_footer(text=f'Shard ID: {ctx.guild.shard_id}')
        latencies = [i[1] * 1000 for i in self.bot.latencies]
        for i in range(self.bot.shard_count):
            users = len({u.id for g in self.bot.guilds for u in g.members if g.shard_id == i})
            guilds = sum(g.shard_id == i for g in self.bot.guilds)
            val = f'{users} users\n{guilds} guilds\n{latencies[i]:.2f}ms ping'
            em.add_field(name=f'Shard #{i}', value=val)
        await ctx.send(embed=em)

    @command(name='language')
    @commands.has_permissions(manage_guild=True)
    async def language_(self, ctx, language=''):
        """Changes your language!
        Want to help translate? Join our support server: https://discord.gg/cBqsdPt
        """
        language = language.lower()

        languages = {
            'spanish': 'es',
            'french': 'fr',
            'english': 'messages'
        }
        if not language or language.lower() not in languages:
            await ctx.send(_('Available languages: {}').format(', '.join([i.title() for i in languages.keys()])))
        else:
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': str(ctx.guild.id)}, {'$set': {'language': languages[language.lower()]}}, upsert=True
            )
            await ctx.send(_('Language set.'))

    @command()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx, *, cog_name: str):
        """Enables certain games"""
        if not ctx.guild:
            return await ctx.send(_('All games are enabled in DMs.'), ctx)
        shortcuts = {
            'coc': 'Clash_Of_Clans',
            'cr': 'Clash_Royale',
            'bs': 'Brawl_Stars',
            'fn': 'Fortnite'
        }
        if cog_name in shortcuts:
            cog_name = shortcuts[cog_name]
        cog = self.bot.get_cog(cog_name.title().replace(' ', '_'))

        if cog in (self, self.bot.get_cog('Moderation'), None):
            await ctx.send(_('Invalid game. Pick from: {}').format(', '.join(shortcuts.keys())))
        else:
            cog_name = cog.__class__.__name__
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': str(ctx.guild.id)}, {'$set': {f'games.{cog_name}': True}}, upsert=True
            )
            await ctx.send('Successfully enabled {}'.format(' '.join(cog_name.split('_'))))

    @command()
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx, *, cog_name: str):
        """Disables certain games"""
        if not ctx.guild:
            return await ctx.send(_('All games cannot be disabled in DMs.'), ctx)
        shortcuts = {
            'coc': 'Clash_Of_Clans',
            'cr': 'Clash_Royale',
            'bs': 'Brawl_Stars',
            'fn': 'Fortnite'
        }
        if cog_name in shortcuts:
            cog_name = shortcuts[cog_name]
        cog = self.bot.get_cog(cog_name.title().replace(' ', '_'))

        if cog in (self, self.bot.get_cog('Moderation'), None):
            await ctx.send(_('Invalid game. Pick from: {}').format(', '.join(shortcuts.keys())))
        else:
            cog_name = cog.__class__.__name__
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': str(ctx.guild.id)}, {'$set': {f'games.{cog_name}': False}}, upsert=True
            )
            await ctx.send('Successfully disabled {}'.format(' '.join(cog_name.split('_'))))

    @command()
    @commands.has_permissions(manage_guild=True)
    async def setdefault(self, ctx, *, cog_name):
        if not ctx.guild:
            guild_id = str(ctx.channel.id)
        else:
            guild_id = str(ctx.guild.id)

        shortcuts = {
            'coc': 'Clash_Of_Clans',
            'cr': 'Clash_Royale',
            'bs': 'Brawl_Stars',
            'fn': 'Fortnite'
        }
        if cog_name in shortcuts:
            cog_name = shortcuts[cog_name]
        cog = self.bot.get_cog(cog_name.title().replace(' ', '_'))

        if cog in (self, self.bot.get_cog('Moderation'), None):
            await ctx.send(_('Invalid game. Pick from: {}').format(', '.join(shortcuts.keys())))
        else:
            cog_name = cog.__class__.__name__
            await self.bot.mongo.config.guilds.find_one_and_update(
                {'guild_id': guild_id}, {'$set': {'default_game': cog_name}}, upsert=True
            )
            await ctx.send('Successfully set `{}` as the default game.'.format(' '.join(cog_name.split('_'))))
            self.bot.default_game[ctx.guild.id] = cog_name

    @command()
    async def discord(self, ctx):
        """Statsy support server invite link"""
        await ctx.send('<:statsy:464784655569387540> https://discord.gg/cBqsdPt')

    async def on_guild_join(self, g):
        info = ''
        try:
            if str(g.id) in self.blacklist['guilds']:
                await g.leave()
                info = 'Guild blacklisted!'
        except AttributeError:
            pass

        texts = ''
        for c in g.text_channels:
            try:
                async for m in c.history(limit=5):
                    texts += '\n' + m.content
            except discord.Forbidden:
                pass

        if texts:
            async with self.bot.session.post(
                'https://ws.detectlanguage.com/0.2/detect',
                headers={'Authorization': f"Bearer {os.getenv('detectlanguage')}"},
                json={'q': texts}
            ) as resp:
                data = await resp.json()

            language = None
            for d in data['data']['detections']:
                if not d:
                    continue
                if d['isReliable']:
                    language = d['language']
                    break

            if language in _.translations.keys():
                await self.bot.mongo.config.guilds.find_one_and_update(
                    {'guild_id': str(g.id)}, {'$set': {'language': language}}, upsert=True
                )
        else:
            language = 'en'

        em = discord.Embed(
            title=f'Added to {g.name} ({g.id})',
            description=f'{len(g.members)} members\nLanguage: {language}\n{info}',
            timestamp=datetime.datetime.utcnow(),
            color=0x0cc243
        )
        await self.bot.guild_hook.send(embed=em)
        datadog.statsd.increment('statsy.joined', 1)

    async def on_guild_remove(self, g):
        em = discord.Embed(
            title=f'Removed from {g.name} ({g.id})',
            description=f'{len(g.members)} members',
            timestamp=datetime.datetime.utcnow(),
            color=0xd1202e
        )
        await self.bot.guild_hook.send(embed=em)
        datadog.statsd.increment('statsy.left', 1)


def setup(bot):
    c = Bot_Related(bot)
    bot.add_cog(c)
