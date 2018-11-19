import io
import time
import os

import aiohttp
import datadog
import discord
from cachetools import TTLCache
from discord.ext import commands
from PIL import Image

from ext import utils
from ext.command import cog, command, group
from ext.embeds import clashofclans
from ext.paginator import Paginator
from locales.i18n import Translator

_ = Translator('Clash of Clans', __file__)

shortcuts = {}


class TagCheck(commands.UserConverter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, ctx, tag):
        if tag.startswith('-'):
            try:
                index = int(tag.replace('-', ''))
            except ValueError:
                pass
            else:
                return (ctx.author, index)
        tag = tag.strip('#').upper().replace('O', '0')
        if tag in shortcuts:
            tag = shortcuts[tag]
        if any(i not in self.check for i in tag):
            return False
        else:
            return tag

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass
        else:
            return user

        # Not a user so its a tag.
        tag = self.resolve_tag(ctx, argument)

        if not tag:
            raise utils.InvalidTag(_('Invalid coc-tag passed.'))
        else:
            return tag


@cog('coc')
class Clash_Of_Clans:

    """Commands relating to the Clash of Clans game made by supercell."""

    def __init__(self, bot):
        self.bot = bot
        self.alias = 'coc'
        self.conv = TagCheck()
        self.cache = TTLCache(500, 180)

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    async def __local_check(self, ctx):
        if ctx.guild:
            guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}
            return guild_info.get('games', {}).get(self.__class__.__name__, True)
        else:
            return True

    async def request(self, ctx, endpoint, *, reason='command'):
        try:
            self.cache[endpoint]
        except KeyError:
            speed = time.time()
            async with self.bot.session.get(
                f"http://{os.getenv('spike')}/redirect?url=https://api.clashofclans.com/v1/{endpoint}",
                headers={'Authorization': f"Bearer {os.getenv('clashofclans')}"}
            ) as resp:
                speed = time.time() - speed
                datadog.statsd.increment('statsy.api_latency', 1, [
                    'game:clashofclans', f'speed:{speed}', f'method:{endpoint}'
                ])
                datadog.statsd.increment('statsy.requests', 1, [
                    'game:clashofclans', f'code:{resp.status}', f'method:{endpoint}', f'reason:{reason}'
                ])
                try:
                    self.cache[endpoint] = await resp.json()
                except aiohttp.ContentTypeError:
                    er = discord.Embed(
                        title=_('Clash of Clans Server Down'),
                        color=discord.Color.red(),
                        description='This could be caused by a maintainence break.'
                    )
                    if ctx.bot.psa_message:
                        er.add_field(name=_('Please Note!'), value=ctx.bot.psa_message)
                    await ctx.send(embed=er)

                    # end and ignore error
                    raise commands.CheckFailure

        if self.cache[endpoint] == {"reason": "notFound"}:
            await ctx.send(_('The tag cannot be found!'))
            raise utils.NoTag

        return self.cache[endpoint]

    async def get_clan_from_profile(self, ctx, tag, message):
        profile = await self.request(ctx, f'players/%23{tag}')
        try:
            clan_tag = profile['clan']['tag']
        except KeyError:
            await ctx.send(message)
            raise utils.NoTag
        else:
            return clan_tag.replace("#", "")

    async def resolve_tag(self, ctx, tag_or_user, *, clan=False, index=0):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('clashofclans', index=str(index))
            except KeyError:
                try:
                    default_game = self.bot.default_game[ctx.guild.id]
                except AttributeError:
                    default_game = self.bot.default_game[ctx.channel.id]
                cmd_name = 'save' if default_game == self.__class__.__name__ else f'{self.alias}save'

                await ctx.send(_("You don't have a saved tag. Save one using `{}{} <tag>`!").format(ctx.prefix, cmd_name))
                raise utils.NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, _("You don't have a clan!"))
                return tag
        if isinstance(tag_or_user, discord.User):
            try:
                tag = await ctx.get_tag('clashofclans', tag_or_user.id, index=str(index))
            except KeyError:
                raise utils.NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, _('That person does not have a clan!'))
                return tag
        else:
            return tag_or_user

    @command()
    @utils.has_perms()
    async def profile(self, ctx, *, tag_or_user: TagCheck=None):
        """Gets the Clash of Clans profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            profile = await self.request(ctx, f'players/%23{tag}')

            ems = await clashofclans.format_profile(ctx, profile)

        await Paginator(ctx, *ems, footer_text=_('Statsy | Powered by the COC API')).start()

    @command()
    @utils.has_perms()
    async def achieve(self, ctx, *, tag_or_user: TagCheck=None):
        """Gets the Clash of Clans achievements of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            profile = await self.request(ctx, f'players/%23{tag}')

            ems = await clashofclans.format_achievements(ctx, profile)

        await Paginator(ctx, *ems, footer_text=_('Statsy | Powered by the COC API')).start()

    @command()
    @utils.has_perms()
    async def clan(self, ctx, *, tag_or_user: TagCheck=None):
        """Gets a clan by tag or by profile. (tagging the user)"""
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, f'clans/%23{tag}')

            ems = await clashofclans.format_clan(ctx, clan)

        await Paginator(ctx, *ems, footer_text=_('Statsy | Powered by the COC API')).start()

    @group()
    @utils.has_perms()
    async def members(self, ctx, *, tag_or_user: TagCheck=None):
        """Gets all the members of a clan."""
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, f'clans/%23{tag}')

            ems = await clashofclans.format_members(ctx, clan)

        await Paginator(ctx, *ems, footer_text=str(clan["members"]) + _('/50 members')).start()

    @members.command()
    @utils.has_perms()
    async def best(self, ctx, *, tag_or_user: TagCheck=None):
        """Finds the best members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, f'clans/%23{tag}')

            if clan['members'] < 4:
                return await ctx.send(_('Clan must have at least than 4 players for these statistics.'))
            else:
                em = await clashofclans.format_most_valuable(ctx, clan)
                await ctx.send(embed=em)

    @members.command()
    @utils.has_perms()
    async def worst(self, ctx, *, tag_or_user: TagCheck=None):
        """Finds the worst members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            clan = await self.request(ctx, f'clans/%23{tag}')

            if clan['members'] < 4:
                return await ctx.send(_('Clan must have at least than 4 players for these statistics.'))
            else:
                em = await clashofclans.format_least_valuable(ctx, clan)
                await ctx.send(embed=em)

    @command()
    async def save(self, ctx, tag, index: str='0'):
        """Saves a Clash of Clans tag to your discord profile."""
        tag = self.conv.resolve_tag(ctx, tag)

        if not tag:
            raise utils.InvalidTag('Invalid cr-tag passed')

        await ctx.save_tag(tag, 'clashofclans', index=index.replace('-', ''))

        try:
            default_game = self.bot.default_game[ctx.guild.id]
        except AttributeError:
            default_game = self.bot.default_game[ctx.channel.id]
        cmd_name = 'profile' if default_game == self.__class__.__name__ else f'{self.alias}profile'

        if index == '0':
            prompt = _('Check your stats with `{}{}`!').format(ctx.prefix, cmd_name)
        else:
            prompt = _('Check your stats with `{}{} -{}`!').format(ctx.prefix, cmd_name, index)

        await ctx.send('Successfully saved tag. ' + prompt)

    @command()
    @utils.has_perms()
    async def usertag(self, ctx, *, member: discord.User=None):
        """Checks the saved tag(s) of a member"""
        member = member or ctx.author
        tag = await ctx.get_tag('clashofclans', id=member.id, index='all')
        em = discord.Embed(description='Tags saved', color=utils.random_color())
        em.set_author(name=member.name, icon_url=member.avatar_url)
        for i in tag:
            em.add_field(name=f'Tag index: {i}', value=tag[i])
        await ctx.send(embed=em)

    @command()
    @utils.has_perms()
    async def war(self, ctx, *, tag_or_user: TagCheck=None):
        """Check your current war status."""
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)
        async with ctx.typing():
            war = await self.request(ctx, f'clans/%23{tag}/currentwar')
            if "reason" in war:
                return await ctx.send(_("This clan's war logs aren't public."))
            if war['state'] == 'notInWar':
                return await ctx.send(_("This clan isn't in a war right now!"))

            async with ctx.session.get(war['clan']['badgeUrls']['large']) as resp:
                clan_img = Image.open(io.BytesIO(await resp.read()))
            async with ctx.session.get(war['opponent']['badgeUrls']['large']) as resp:
                opp_img = Image.open(io.BytesIO(await resp.read()))

            image = await self.bot.loop.run_in_executor(None, self.war_image, ctx, clan_img, opp_img)
            em = await clashofclans.format_war(ctx, war)
            await ctx.send(file=discord.File(image, 'war.png'), embed=em)

    def war_image(self, ctx, clan_img, opp_img):

        bg_image = Image.open("data/war-bg.png")
        size = bg_image.size

        image = Image.new("RGBA", size)
        image.paste(bg_image)

        c_box = (60, 55, 572, 567)
        image.paste(clan_img, c_box, clan_img)

        o_box = (928, 55, 1440, 567)
        image.paste(opp_img, o_box, opp_img)

        file = io.BytesIO()
        image.save(file, format="PNG")
        file.seek(0)
        return file


def setup(bot):
    cog = Clash_Of_Clans(bot)
    bot.add_cog(cog)
