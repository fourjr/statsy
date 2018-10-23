import asyncio
import io
import json
import os
import time
from base64 import b64decode
from collections import OrderedDict
from datetime import datetime

import clashroyale
import datadog
import discord
from cachetools import TTLCache
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import ReturnDocument

from ext import embeds_cr, utils
from ext.context import NoContext
from ext.command import command, group
from ext.paginator import PaginatorSession
from locales.i18n import Translator

_ = Translator('Core', __file__)

shortcuts = {
    # stus army
    'SA1': '88PYQV',
    'SA2': '29UQQ282',
    'SA3': '28JU8P0Y',
    'SA4': '8PUUGRYG',
    # underbelly
    'UNDERBELLY': '2J8UVG99',
    # dat banana boi
    'BANANA': '9Y0CVVL2',
    # the reapers
    'VOIDR': '9L2PLGRR',
    'FLAMER': '22UY8R9Q',
    'ICYR': 'CJCRRCR',
    'STORMR': 'UV2C8L2',
    'NIGHTR': '998V02G2',
    # the parliament hill
    'MAMBA': '9YC80UQ9',
    'COLLTONMOUTH': '9JJQLVU8',
    'SNAKE': '99VPJ29G',
    # the quest family
    'TQUEST': '2GV80JP',
    'TJOURNEY': '2802UYC2',
    'TIDEA': '2JPPGGJ0'
}


class TagOnly(commands.Converter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, tag):
        tag = tag.strip('#').upper()
        if tag in shortcuts:
            tag = shortcuts[tag]
        tag = tag.replace('O', '0')
        if any(i not in self.check for i in tag):
            return False
        else:
            return (tag, 0)

    async def convert(self, ctx, argument):
        tag = self.resolve_tag(argument)

        if not tag:
            raise utils.InvalidTag('Invalid cr-tag passed.')
        else:
            return tag


class TagCheck(commands.MemberConverter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, ctx, tag):
        if tag.startswith('-'):
            try:
                index = int(tag.replace('-', ''))
            except ValueError:
                pass
            else:
                return (ctx.author, index)
        tag = tag.strip('#').upper()
        if tag in shortcuts:
            tag = shortcuts[tag]
        tag = tag.replace('O', '0')
        if any(i not in self.check for i in tag) or len(tag) < 3:
            return False
        else:
            return (tag, 0)

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            arg_split = argument.split(' -')
            user = await super().convert(ctx, arg_split[0])
        except commands.BadArgument:
            pass
        else:
            try:
                return (user, int(arg_split[1]))
            except IndexError:
                return (user, 0)
            except ValueError:
                pass

        # Not a user so its a tag.
        tag = self.resolve_tag(ctx, argument)

        if not tag:
            raise utils.InvalidTag(_('Invalid cr-tag passed.', ctx))
        else:
            return tag


class Clash_Royale:

    """Commands relating to the Clash Royale game made by supercell."""

    def __init__(self, bot):
        self.bot = bot
        self.cr = bot.cr
        self.conv = TagCheck()
        self.cache = TTLCache(500, 180)
        scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/firebase.database"
        ]
        self.firebase = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(b64decode(os.getenv('firebase')).decode()), scopes=scopes)
        if not self.bot.dev_mode:
            self.bot.clan_update = self.bot.loop.create_task(self.clan_update_loop())

    async def __local_check(self, ctx=None, channel=None):
        guild = getattr(ctx or channel, 'guild', None)
        if guild:
            guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': str(guild.id)}) or {}
            return guild_info.get('games', {}).get(self.__class__.__name__, True)
        else:
            return True

    async def __error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, clashroyale.NotFoundError):
            await ctx.send(_('The tag cannot be found!', ctx))
        elif isinstance(error, clashroyale.RequestError):
            er = discord.Embed(
                title=_('Clash Royale Server Down', ctx),
                color=discord.Color.red(),
                description='This could be caused by a maintainence break.'
            )
            if ctx.bot.psa_message:
                er.add_field(name=_('Please Note!', ctx), value=ctx.bot.psa_message)
            await ctx.send(embed=er)

    async def request(self, ctx, method, *args, **kwargs):
        client = kwargs.get('client', self.cr)
        reason = kwargs.get('reason', 'command')
        try:
            data = self.cache[f'{method}{args}']
        except KeyError:
            data = await getattr(client, method)(*args)

            if isinstance(data, list):
                self.cache[f'{method}{args}'] = data
                status_code = 'list'
            else:
                self.cache[f'{method}{args}'] = data.raw_data
                status_code = data.response.status
            datadog.statsd.increment('statsy.requests', 1, [
                'game:clashroyale', f'code:{status_code}', f'method:{method}', f'reason:{reason}'
            ])
        else:
            if not isinstance(data, list):
                data = clashroyale.official_api.BaseAttrDict(self.cr, data, None)
        return data

    async def request_db(self, **kwargs):
        async with self.bot.session.request(
            kwargs.get('method', 'GET'),
            kwargs.get('url', 'https://statsy-fourjr.firebaseio.com/players.json'),
            headers={'Authorization': f'Bearer {self.firebase.get_access_token().access_token}'},
            json=kwargs.get('json', {}),
            params=kwargs.get('params', {})
        ) as resp:
            return await resp.json()

    async def get_clan_from_profile(self, ctx, tag, message):
        p = await self.request(ctx, 'get_player', tag)
        if p.clan is None:
            await ctx.send(message)
            raise utils.NoTag(message)
        return p.clan.tag

    async def resolve_tag(self, ctx, tag_or_user, *, clan=False, index=0):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('clashroyale', index=str(index))
            except KeyError:
                await ctx.send(_("You don't have a saved tag. Save one using `{}save <tag>`!", ctx).format(ctx.prefix))
                raise utils.NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, _("You don't have a clan!", ctx))
                return tag

        if isinstance(tag_or_user, discord.abc.User):
            try:
                tag = await ctx.get_tag('clashroyale', tag_or_user.id, index=str(index))
            except KeyError:
                await ctx.send(_('That person doesnt have a saved tag!', ctx))
                raise utils.NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'That person does not have a clan!')
                return tag
        else:
            return tag_or_user

    async def tournament_sender(self, ctx, t_filter, em):
        guilds = self.bot.mongo.config.guilds.find({'tournament.types': {'$in': t_filter}})
        async for g in guilds:
            guild = self.bot.get_guild(int(g['guild_id']))
            mention = g['tournament']['mention']
            change_permissions = False

            try:
                role = discord.utils.get(guild.roles, id=int(mention))
            except ValueError:
                # mention is @here or @everyone
                role_mention = mention
            except TypeError:
                # mention is None
                role_mention = None
            else:
                # since role is an actual role, check permissions
                if not role.mentionable:
                    await role.edit(mentionable=True)
                    change_permissions = True
                role_mention = role.mention

            if role_mention:
                fmt = _('{}, new tournament found!', ctx).format(role_mention)
            else:
                fmt = _('New tournament found!', ctx)
            await guild.get_channel(int(g['tournament']['channel_id'])).send(
                content=fmt,
                embed=em
            )
            if change_permissions:
                await role.edit(mentionable=False)

    async def on_message(self, m):
        await self.bot.wait_until_ready()
        if self.bot.dev_mode or not m.guild:
            return

        if m.channel.id == 480017443314597899 and m.author.bot:
            ctx = await self.bot.get_context(m)
            if ctx.guild:
                ctx.language = (await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}).get('language', 'messages')
            else:
                ctx.language = 'messages'
            try:
                tournament = await self.request(ctx, 'get_tournament', m.content.split(' ')[0], reason='tournament_log')
            except clashroyale.RequestError:
                await asyncio.sleep(0.5)
                try:
                    tournament = await self.request(ctx, 'get_tournament', m.content.split(' ')[0], reason='tournament_log')
                except clashroyale.RequestError:
                    return

            await self.tournament_sender(
                ctx,
                json.loads(' '.join(m.content.split(' ')[1:])),
                (await embeds_cr.format_tournament(ctx, tournament))[0]
            )
            return

        if not ('http://link.clashroyale.com' in m.content or 'https://link.clashroyale.com' in m.content):
            return

        # LINK
        guild_config = await self.bot.mongo.config.guilds.find_one({'guild_id': str(m.guild.id)}) or {}
        friend_config = guild_config.get('friend_link')

        default = False

        if friend_config is None and self.bot.get_user(402656158667767808) not in m.guild.members:
            default = friend_config = True

        if friend_config:
            ctx = await self.bot.get_context(m)
            if ctx.guild:
                ctx.language = (await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}).get('language', 'messages')
            else:
                ctx.language = 'messages'

            deck = m.content[m.content.find('?deck=') + 6:m.content.find('?deck=') + 8 * 8 + 7 + 6].split(';')

            if m.content.find('?deck=') != -1:
                # Deck
                link = 'https://link.clashroyale.com/deck/en?deck=' + ';'.join(deck)
                em = await embeds_cr.format_deck_link(ctx, deck, link, default)
                try:
                    await m.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

                if m.content.find('&id=') != -1:
                    id_section = m.content.find('&id=') + len('&id=')
                    for n, i in enumerate(m.content[id_section:]):
                        if i == ' ':
                            last_part = id_section + n + 1
                            break
                    last_part = id_section + n + 1
                else:
                    last_part = m.content.find('?deck=') + 8 * 8 + 7 + len('?deck=')

                text = m.content[0:m.content.find('http')] + ' ' + m.content[last_part:]
                await m.channel.send(text, embed=em)
            else:
                # Friend or Clan
                tag = m.content[m.content.find('?tag=') + 5:m.content.find('&token=')]
                token = m.content[m.content.find('&token=') + 7:m.content.find('&token=') + 7 + 8]

                if 'link.clashroyale.com/invite/clan/' in m.content:
                    link = f'https://link.clashroyale.com/invite/clan/?tag={tag}&token={token}/'
                    try:
                        clan = await self.request(ctx, 'get_clan', tag, reason='link')
                    except ValueError:
                        return
                else:
                    link = f'https://link.clashroyale.com?tag={tag}&token={token}/'
                    try:
                        profile = await self.request(ctx, 'get_player', tag, reason='link')
                    except ValueError:
                        return

                if m.content.find('android') != -1:
                    platform = m.content.find('platform=android') + len('platform=android')
                elif m.content.find('iOS') != -1:
                    platform = m.content.find('platform=iOS') + len('platform=iOS')
                else:
                    platform = m.content.find('&token=') + 7 + 8

                text = m.content[0:m.content.find('http')] + ' ' + m.content[platform:]

                if 'link.clashroyale.com/invite/clan/' in m.content:
                    em = await embeds_cr.format_clan_link(ctx, clan, link, default)
                else:
                    em = await embeds_cr.format_friend_link(ctx, profile, link, default)

                try:
                    await m.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

                await m.channel.send(text, embed=em)

    async def on_typing(self, channel, user, when):
        if self.bot.is_closed() or not await self.__local_check(channel=channel) or user.bot:
            return

        ctx = NoContext(self.bot, user)
        if ctx.guild:
            ctx.language = (await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}).get('language', 'messages')
        else:
            ctx.language = 'messages'

        guild_id = getattr(ctx.guild, 'id', 'DM')
        try:
            datadog.statsd.increment('statsy.magic_caching.check', 1, [f'user:{user.id}', f'guild:{guild_id}'])
            tag = await self.resolve_tag(ctx, user)

            try:
                player = await self.request(ctx, 'get_player', tag, reason='magic caching')
            except ValueError:
                return

            datadog.statsd.increment('statsy.magic_caching.request', 1, [f'user:{user.id}', f'guild:{guild_id}'])

            await self.request(ctx, 'get_player_chests', tag)
            try:
                await self.request(ctx, 'get_clan', player.clan.tag, reason='magic caching')
                await self.request(ctx, 'get_clan_war', player.clan.tag, reason='magic caching')
            except AttributeError:
                pass
        except (utils.NoTag, clashroyale.RequestError):
            pass

    @commands.guild_only()
    @group()
    async def link(self, ctx):
        """Check your guild's link beautifier status"""
        guild_config = await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}
        friend_config = guild_config.get('friend_link')

        default = False

        if friend_config is None and self.bot.get_user(402656158667767808) not in ctx.guild.members:
            default = friend_config = True

        resp = _('Current status: {}', ctx).format(friend_config)
        if default:
            resp += _(' (default)', ctx)
        await ctx.send(resp)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @link.command()
    async def enable(self, ctx):
        """Enables link beautifier"""
        await self.bot.mongo.config.guilds.find_one_and_update(
            {'guild_id': str(ctx.guild.id)}, {'$set': {'friend_link': True}}, upsert=True
        )
        await ctx.send(_('Successfully set link beautifier to be enabled.', ctx))

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @link.command()
    async def disable(self, ctx):
        """Disables link beautifier"""
        await self.bot.mongo.config.guilds.find_one_and_update(
            {'guild_id': str(ctx.guild.id)}, {'$set': {'friend_link': False}}, upsert=True
        )
        await ctx.send(_('Successfully set link beautifier to be disabled.', ctx))

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @command(aliases=['settourneylog'])
    async def settournamentlog(self, ctx):
        """Sets the filters and channels for the tournament log"""
        allowed_types = ['all', '50', '100', '200', '1000', 'open:all', 'open:50', 'open:100', 'open:200', 'open:1000']

        def predicate(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.send(_('What kind of tournaments do you want alerts for? Pick from these: `{}`. The numbers represent max member count. Seperate multiple types with a space.', ctx).format(
                ', '.join(allowed_types)
            ))
            types = (await self.bot.wait_for('message', check=predicate, timeout=60)).content.split(' ')
            if not all([i in allowed_types for i in types]):
                return await ctx.send(_('Invalid type(s).', ctx))

            await ctx.send(_('Do you want to mention any role when a tournament is found? Respond with a role name, `everyone`, `here` or `no`.', ctx))
            role = (await self.bot.wait_for('message', check=predicate, timeout=60)).content
            try:
                role = str((await commands.RoleConverter().convert(ctx, role)).id)
            except commands.BadArgument:
                if role == 'no':
                    role = None
                elif role in ('everyone', 'here'):
                    role = '@' + role
                else:
                    return await ctx.send(_('Invalid role.', ctx))

            await ctx.send(_('Which channel do you want the alerts to be sent to?', ctx))
            channel = (await self.bot.wait_for('message', check=predicate, timeout=60)).content
            try:
                channel = (await commands.TextChannelConverter().convert(ctx, channel)).id
            except commands.BadArgument:
                return await ctx.send(_('Invalid channel.', ctx))

        except asyncio.TimeoutError:
            return await ctx.send('Command timeout. Do the command again to restart the process.')

        await self.bot.mongo.config.guilds.find_one_and_update(
            {'guild_id': str(ctx.guild.id)}, {'$set': {
                'tournament': {
                    'channel_id': str(channel),
                    'mention': role,
                    'types': types
                }
            }}, upsert=True
        )
        await ctx.send(_('Log set!', ctx))

    @commands.has_permissions(manage_guild=True)
    @command()
    async def setclanstats(self, ctx, channel: discord.TextChannel, *clans):
        """Sets a clan log channel"""
        tag = await self.resolve_tag(ctx, ctx.author)

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)

            if not 2 <= len(clans) <= 25:
                return await ctx.send('There must be a minimum of 2 and maximum of 25 clans to use this feature.')

            cleaned_tags = []

            for tag in clans:
                tag = tag.strip('#').upper()
                if tag in shortcuts:
                    tag = shortcuts[tag]
                tag = tag.replace('O', '0')
                if any(i not in 'PYLQGRJCUV0289' for i in tag):
                    return await ctx.send(_('{} is an invalid tag. Please use the clan tags seperated by spaces.', ctx).format(tag))
                else:
                    cleaned_tags.append(tag)

            if not profile.clan or (profile.clan and profile.clan.tag.replace('#', '') not in cleaned_tags):
                return await ctx.send('You must be at least one of those clans to set a claninfo page')

            try:
                # Update existing config
                config = await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}
                message = None
                message_id = config.get('claninfo', {}).get('message')
                if message_id:
                    message = await channel.get_message(message_id)
                    if not message:
                        # Delete old message in another channel
                        try:
                            await (await self.bot.get_channel(config['claninfo']).get_message(message)).delete()
                        except AttributeError:
                            pass

                # Send a new message
                if not message:
                    message = await channel.send('Clan Info')
                    await message.add_reaction(':refresh:477405504512065536')
            except (discord.Forbidden, discord.HTTPException):
                try:
                    await message.delete()
                except NameError:
                    pass
                return await ctx.send(_('Statsy should have permissions to `Send Messages` and `Add Reactions` in #{}', ctx).format(channel.name))

            data = await self.bot.mongo.config.guilds.find_one_and_update({'guild_id': str(ctx.guild.id)}, {'$set': {
                'claninfo': {
                    'channel': str(channel.id),
                    'message': str(message.id),
                    'clans': clans
                }
            }}, upsert=True, return_document=ReturnDocument.AFTER)

            await self.clanupdate(data)
            await ctx.send(_('Configuration complete.', ctx))

    @command(aliases=['player'])
    @utils.has_perms()
    async def profile(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the clash royale profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            cycle = await self.request(ctx, 'get_player_chests', tag)
            em = await embeds_cr.format_profile(ctx, profile, cycle.get('items'))

        await ctx.send(embed=em)

    @command(alises=['statistics'])
    @utils.has_perms()
    async def stats(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the clash royale profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            em = await embeds_cr.format_stats(ctx, profile)

        await ctx.send(embed=em)

    @command(aliases=['season'])
    @utils.has_perms()
    async def seasons(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the season results a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            ems = await embeds_cr.format_seasons(ctx, profile)

        if len(ems) > 0:
            session = PaginatorSession(
                ctx=ctx,
                pages=ems
            )
            await session.run()
        else:
            await ctx.send(f"**{profile.name}** doesn't have any season results.")

    @command()
    @utils.has_perms()
    async def chests(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the next chests of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            cycle = await self.request(ctx, 'get_player_chests', tag)
            em = await embeds_cr.format_chests(ctx, profile, cycle.get('items'))

        await ctx.send(embed=em)

    @command()
    @utils.has_perms()
    async def cards(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Get a list of cards the user has and does not have"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            em = await embeds_cr.format_cards(ctx, profile)

        await ctx.send(embed=em)

    @command(aliases=['matches'])
    @utils.has_perms()
    async def battles(self, ctx, tag_or_user: TagCheck=(None, 0)):
        """Get the latest 5 battles by the player!"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            battles = await self.request(ctx, 'get_player_battles', tag)
            em = await embeds_cr.format_battles(ctx, battles)

        await ctx.send(embed=em)

    @command()
    @utils.has_perms()
    async def clan(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets a clan by tag or by profile. (tagging the user)"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, 'get_clan', tag)
            ems = await embeds_cr.format_clan(ctx, clan)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @utils.has_perms()
    @command(aliases=['clan_war', 'clan-war'], invoke_without_command=True)
    async def clanwar(self, ctx, tag_or_user: TagCheck=(None, 0)):
        """Shows your clan clan war statistics"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            war = await self.request(ctx, 'get_clan_war', tag)
            ems = await embeds_cr.format_clan_war(ctx, war)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @utils.has_perms()
    @group(aliases=['lb'], usage='<option>', invoke_without_command=True)
    async def leaderboard(self, ctx, option=None):
        await ctx.invoke(self.bot.get_command('help'), command=str(ctx.command))

    async def parse_leaderboard(self, ctx, emoji_name, *statistics, **kwargs):
        async with ctx.typing():
            db_result = await self.request_db()

            def predicate(x):
                result = db_result[x]
                for i in statistics:
                    result = result[i]
                return result

            data = sorted(db_result, key=predicate, reverse=True)
            sorted_result = OrderedDict()
            for i in data:
                sorted_result[i] = db_result[i]

            tag = await self.resolve_tag(ctx, ctx.author)
            ems = await embeds_cr.format_lb(ctx, sorted_result, tag, emoji_name, *statistics, **kwargs)

            del db_result
            del data
            del sorted_result

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

        del session
        del ems

    @utils.has_perms()
    @leaderboard.command()
    async def clansjoined(self, ctx):
        """Gets the leaderboard of XP Level"""
        await self.parse_leaderboard(ctx, 'clan', 'achievements', 0, 'value', name='Clans Joined')

    @utils.has_perms()
    @leaderboard.command(aliases=['donation'])
    async def donations(self, ctx):
        """Gets the leaderboard of total donations"""
        await self.parse_leaderboard(ctx, 'cards', 'stats', 'totalDonations')

    @utils.has_perms()
    @leaderboard.command()
    async def trophies(self, ctx):
        """Gets the leaderboard of total trophies"""
        await self.parse_leaderboard(ctx, 'trophy', 'trophies')

    @utils.has_perms()
    @leaderboard.command(aliases=['xp'])
    async def level(self, ctx):
        """Gets the leaderboard of XP Level"""
        await self.parse_leaderboard(ctx, 'experience', 'stats', 'level')

    @utils.has_perms()
    @leaderboard.command()
    async def cardswon(self, ctx):
        """Gets the leaderboard of challenge cards won"""
        await self.parse_leaderboard(ctx, 'tournament', 'stats', 'challengeCardsWon', name='Challenge Cards Won')

    @utils.has_perms()
    @leaderboard.command()
    async def challengewins(self, ctx):
        """Gets the leaderboard of challenge max wins"""
        await self.parse_leaderboard(ctx, 'tournament', 'stats', 'challengeMaxWins', name='Challenge Max Wins')

    @utils.has_perms()
    @leaderboard.command()
    async def clancards(self, ctx):
        """Gets the leaderboard of clan cards won"""
        await self.parse_leaderboard(ctx, 'cards', 'stats', 'clanCardsCollected', name='Clan Cards Collected')

    @utils.has_perms()
    @command()
    async def topplayers(self, ctx, *, region: str = None):
        """Returns the global top 200 players."""
        async with ctx.typing():
            region = name = 'global'
            if region:
                for i in self.bot.cr.constants.regions:
                    if i.name.lower() == region or str(i.id) == region or i.key.replace('_', '').lower() == region:
                        region = i.key
                        name = i.name

            try:
                clans = await self.request(ctx, 'get_top_players', region)
            except clashroyale.NotFoundError:
                return await ctx.send('Invalid region')
            ems = await embeds_cr.format_top_players(ctx, clans.get('items'), name)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @command()
    @utils.has_perms()
    async def topclanwars(self, ctx, *, region: str = None):
        """Returns the global top 200 clans by clan wars."""
        async with ctx.typing():
            region = name = 'global'
            if region:
                for i in self.bot.cr.constants.regions:
                    if i.name.lower() == region or str(i.id) == region or i.key.replace('_', '').lower() == region:
                        region = i.key
                        name = i.name

            try:
                clans = await self.request(ctx, 'get_top_clanwar_clans', region)
            except clashroyale.NotFoundError:
                return await ctx.send('Invalid region')
            ems = await embeds_cr.format_top_clan_wars(ctx, clans.get('items'), name)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @command()
    @utils.has_perms()
    async def topclans(self, ctx, *, region: str = None):
        """Returns the global top 200 clans."""
        async with ctx.typing():
            region = name = 'global'
            if region:
                for i in self.bot.cr.constants.regions:
                    if i.name.lower() == region or str(i.id) == region or i.key.replace('_', '').lower() == region:
                        region = i.key
                        name = i.name

            try:
                clans = await self.request(ctx, 'get_top_clans', region)
            except clashroyale.NotFoundError:
                return await ctx.send('Invalid region')
            ems = await embeds_cr.format_top_clans(ctx, clans.get('items'), name)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @group(invoke_without_command=True)
    @utils.has_perms()
    async def members(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets all the members of a clan."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, 'get_clan', tag)
            war = await self.request(ctx, 'get_clan_war_log', tag)

            ems = await embeds_cr.format_members(ctx, clan, war.get('items'))

        session = PaginatorSession(
            ctx=ctx,
            pages=ems,
            footer_text=f'{clan.members}/50 members'
        )
        await session.run()

    @members.command()
    @utils.has_perms()
    async def best(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Finds the best members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, 'get_clan', tag)
            war = await self.request(ctx, 'get_clan_war_log', tag)

            if len(clan.member_list) < 4:
                await ctx.send('Clan must have at least 4 players for these statistics.')
            else:
                em = await embeds_cr.format_most_valuable(ctx, clan, war.get('items'))
                await ctx.send(embed=em)

    @members.command()
    @utils.has_perms()
    async def worst(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Finds the worst members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, 'get_clan', tag)
            war = await self.request(ctx, 'get_clan_war_log', tag)

            if len(clan.member_list) < 4:
                return await ctx.send('Clan must have at least 4 players for these statistics.')
            else:
                em = await embeds_cr.format_least_valuable(ctx, clan, war.get('items'))
                await ctx.send(embed=em)

    @command()
    async def save(self, ctx, tag, index: str='0'):
        """Saves a Clash Royale tag to your discord profile."""
        async with ctx.typing():
            tag = self.conv.resolve_tag(ctx, tag)

            if not tag:
                raise utils.InvalidTag

            player = await self.request(ctx, 'get_player', tag[0])
            player.raw_data['timestamp'] = time.time()
            await ctx.save_tag(tag[0], 'clashroyale', index=index.replace('-', ''))

            if index == '0':
                prompt = _('Check your stats with `{}profile`!', ctx).format(ctx.prefix)
            else:
                prompt = _('Check your stats with `{}profile -{}`!', ctx).format(ctx.prefix, index)

            await ctx.send(_('Successfully saved tag.', ctx) + ' ' + prompt)

    @command()
    @utils.has_perms()
    async def usertag(self, ctx, member: discord.Member = None):
        """Checks the saved tag(s) of a member"""
        member = member or ctx.author
        tag = await self.resolve_tag(ctx, member, index='all')
        em = discord.Embed(description='Tags saved', color=utils.random_color())
        em.set_author(name=member.name, icon_url=member.avatar_url)
        for i in tag:
            em.add_field(name=f'Tag index: {i}', value=tag[i])
        await ctx.send(embed=em)

    @command()
    @utils.has_perms()
    async def deck(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the current deck of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request(ctx, 'get_player', tag)
            em = await embeds_cr.format_deck(ctx, profile)

            await ctx.send(embed=em)

    @command(name='card')
    @utils.has_perms()
    async def _card(self, ctx, *, card):
        """Get information about a Clash Royale card."""
        aliases = {
            'log': 'the log',
            'pump': 'elixir collector',
            'skarmy': 'skeleton army',
            'pekka': 'p.e.k.k.a',
            'mini pekka': 'mini p.e.k.k.a',
            'xbow': 'x-bow'
        }
        card = card.lower()
        if card in aliases:
            card = aliases[card]
        constants = self.bot.cr.constants

        found_card = None
        for c in constants.cards:
            if c.name.lower() == card.lower():
                found_card = c

        if found_card is None:
            return await ctx.send("That's not a card!")

        em = await embeds_cr.format_card(ctx, found_card)
        try:
            async with self.bot.session.get(utils.emoji(ctx, card).url) as resp:
                c = io.BytesIO(await resp.read())
        except AttributeError:
            # new card, no emoji
            await ctx.send(embed=em)
        else:
            await ctx.send(embed=em, files=[discord.File(c, 'card.png')])

    @command(aliases=['tourney'])
    @utils.has_perms()
    async def tournament(self, ctx, tag: TagOnly):
        """View statistics about a tournament"""
        async with ctx.typing():
            t = await self.request(ctx, 'get_tournament', tag[0])
            ems = await embeds_cr.format_tournament(ctx, t)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @command(aliases=['tourneys'])
    @utils.has_perms()
    async def tournaments(self, ctx):
        """Show a list of open tournaments that you can join!"""
        async with ctx.typing():
            t = await self.request(ctx, 'get_open_tournaments', client=self.bot.royaleapi)
            em = await embeds_cr.format_tournaments(ctx, t)

        await ctx.send(embed=em)

    async def get_clans(self, *tags):
        clans = []
        wars = []
        for t in tags:
            clans.append(await self.request(None, 'get_clan', t, reason='clanstats'))
            wars.append(await self.request(None, 'get_clan_war', t, reason='clanstats'))
            await asyncio.sleep(0.5)
        return clans, wars

    async def clanupdate(self, clan=None):
        if not clan:
            guilds = await self.bot.mongo.config.guilds.find({'claninfo': {'$exists': True}}).to_list(None)
        else:
            guilds = [clan]

        for g in guilds:
            m = g['claninfo']
            clans, wars = await self.get_clans(*m['clans'])

            embed = discord.Embed(title="Clan Statistics!", color=0xf1c40f, timestamp=datetime.utcnow())
            total_members = 0

            for i in range(len(clans)):
                embed.add_field(name=clans[i].name, value=embeds_cr.format_clan_stats(clans[i], wars[i]))
                total_members += len(clans[i].member_list)

            embed.add_field(name='More Info', value=f"<:clan:376373812012384267> {total_members}/{50*len(clans)}", inline=False)
            try:
                channel = self.bot.get_channel(int(m['channel']))
                message = await channel.get_message(int(m['message']))
            except AttributeError:
                message = None

            if not message:
                try:
                    message = await self.bot.get_channel(m['channel']).send('Clan Stats')
                except AttributeError:
                    await self.bot.mongo.find_one_and_delete({'guild_id': str(g['guild_id'])})
                    break
            await message.edit(content='', embed=embed)
            return message

    async def clan_update_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.clanupdate()
            await asyncio.sleep(600)

    async def on_raw_reaction_add(self, payload):
        data = await self.bot.mongo.config.guilds.find_one({'guild_id': str(payload.guild_id), 'claninfo.message': str(payload.message_id)})
        if data:
            member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

            if member == self.bot.user:
                return

            message = await self.clanupdate(data)
            await message.clear_reactions()
            await message.add_reaction(':refresh:477405504512065536')


def setup(bot):
    cog = Clash_Royale(bot)
    bot.add_cog(cog)
