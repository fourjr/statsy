import aiohttp
import discord
from discord.ext import commands

from ext import embeds_ov, utils
from ext.paginator import PaginatorSession

from ext.command import command
from locales.i18n import Translator

_ = Translator('Overwatch', __file__)


class TagCheck(commands.MemberConverter):

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass
        else:
            return user

        # Not a user so its a tag.
        return argument.replace("#", "-")


class Overwatch:
    """Commands relating to the Overwatch game."""

    def __init__(self, bot):
        self.bot = bot
        self.conv = TagCheck()
        bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        self.session = aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36'
        })
        self.session2 = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
        })
        self.session3 = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0"
        })

    async def __local_check(self, ctx):
        if ctx.guild:
            guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': str(ctx.guild.id)}) or {}
            return guild_info.get('games', {}).get(self.__class__.__name__, True)
        else:
            return True

    def __unload(self):
        self.bot.loop.create_task(self.session.close())
        self.bot.loop.create_task(self.session2.close())
        self.bot.loop.create_task(self.session3.close())

    async def resolve_tag(self, ctx, tag_or_user, *, index=0):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('overwatch', index=str(index))
            except KeyError:
                await ctx.send(_("You don't have a saved tag. Save one using `{}owsave <tag>`!", ctx).format(ctx.prefix))
                raise utils.NoTag
            else:
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = await ctx.get_tag('overwatch', tag_or_user.id, index=str(index))
            except KeyError:
                await ctx.send(_("That person doesn't have a saved tag!", ctx))
                raise utils.NoTag
            else:
                return tag
        else:
            return tag_or_user

    @command()
    @utils.has_perms()
    async def owprofile(self, ctx, *, tag_or_user: TagCheck=None):
        """Gets the Overwatch profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user)
        tag = tag.replace('#', '-')
        ems = []

        await ctx.trigger_typing()

        try:
            async with self.session.get(f"https://owapi.net/api/v3/u/{tag}/stats") as p:
                profile = await p.json()
                if p.status == 404:
                    return await ctx.send(_('The battletag cannot be found! Make sure to include the part after the `#`', ctx))
                elif p.status == 403:
                    return await ctx.send(_('Please set your account statistics to be public to view stats.'), ctx)
            async with self.session.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                heroes = await h.json()
                if "error" in heroes:
                    async with self.session2.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                        heroes = await h.json()
                        if "error" in heroes:
                            async with self.session3.get(f"https://owapi.net/api/v3/u/{tag}/heroes") as h:
                                heroes = await h.json()

        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            try:
                ems = await embeds_ov.format_profile(
                    ctx, tag.split('-')[0], profile["kr"]['stats'], heroes["kr"]['heroes']
                )
            except Exception as e:
                raise e
            if len(ems) > 1:
                session = PaginatorSession(
                    ctx=ctx,
                    pages=ems
                )
                await session.run()
            elif len(ems) == 0:
                await ctx.send(_("There aren't any stats for this user!", ctx))
            else:
                await ctx.send(embed=ems[0])

    @command()
    async def owsave(self, ctx, tag, index: str='0'):
        """Saves a Overwatch tag to your discord profile."""
        await ctx.save_tag(tag.replace("#", "-"), 'overwatch', index=index.replace('-', ''))

        if index == '0':
            prompt = f'Check your stats with `{ctx.prefix}owprofile`!'
        else:
            prompt = f'Check your stats with `{ctx.prefix}owprofile -{index}`!'

        await ctx.send('Successfully saved tag. ' + prompt)

    @command()
    @utils.has_perms()
    async def owusertag(self, ctx, *, member: discord.Member=None):
        """Checks the saved tag(s) of a member"""
        member = member or ctx.author
        tag = await ctx.get_tag('overwatch', index='all')
        em = discord.Embed(description='Tags saved', color=embeds_ov.random_color())
        em.set_author(name=member.name, icon_url=member.avatar_url)
        for i in tag:
            em.add_field(name=f'Tag index: {i}', value=tag[i])
        await ctx.send(embed=em)


def setup(bot):
    cog = Overwatch(bot)
    bot.add_cog(cog)
