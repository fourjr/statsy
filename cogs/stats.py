import discord
from discord.ext import commands
from ext import embeds
import json

class InvalidTag(commands.BadArgument):
    '''Raised when a tag is invalid.'''
    pass

class TagCheck(commands.MemberConverter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, tag):
        tag = tag.strip('#').upper().replace('O','0')

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
        tag = self.resolve_tag(argument)

        if not tag:
            raise InvalidTag('Invalid cr-tag passed.')
        else:
            return tag

class Stats:

    def __init__(self, bot):
        self.bot = bot
        self.cr = bot.cr
        self.conv = TagCheck()

    async def resolve_tag(self, ctx, tag_or_user):
        if not tag_or_user:
            try:
                tag = ctx.get_tag()
            except Exception as e:
                print(e)
                await ctx.send('You dont have a saved tag.')
                raise e
            else:
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag(tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
                raise e
            else:
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, tag_or_user: TagCheck=None):
        '''Get the clash royale profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_profile(tag)
            except Exception as e:
                await ctx.send(f'`{e}`')
                raise e
            em = await embeds.format_profile(ctx, profile)
        await ctx.send(embed=em)

    @commands.command()
    async def save(self, ctx, *, tag):
        '''Save a tag to your clash royale profile.

        Ability to save multiple tags coming soon.
        '''
        tag = self.conv.resolve_tag(tag)
        if not tag:
            return await ctx.send('Invalid Tag!') # TODO: Better message.

        ctx.add_tag(tag)

        await ctx.send('Successfuly saved tag.')




def setup(bot):
    cog = Stats(bot)
    bot.add_cog(cog)