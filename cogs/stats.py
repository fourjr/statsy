import discord
from discord.ext import commands
from ext import embeds
import json
from __main__ import InvalidTag
from ext.paginator import PaginatorSession


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

    async def get_clan_from_profile(self, ctx, tag, message):
        profile = await self.cr.get_profile(tag)
        clan_tag = profile.clan_tag
        if clan_tag is None:
            await ctx.send(message)
            raise ValueError(message)
        else:
            return clan_tag


    async def resolve_tag(self, ctx, tag_or_user, clan=False):
        if not tag_or_user:
            try:
                tag = ctx.get_tag()
            except Exception as e:
                print(e)
                await ctx.send('You don\'t have a saved tag.')
                raise e
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'You don\'t have a clan!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag(tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
                raise e
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'That person does not have a clan!')
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the clash royale profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_profile(tag)
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                em = await embeds.format_profile(ctx, profile)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def deck(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the current deck of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_profile(tag)
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                em = await embeds.format_deck(ctx, profile)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def chests(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the next chests of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_profile(tag)
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                em = await embeds.format_chests(ctx, profile)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def clan(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets a clan by tag or by profile. (tagging the user)'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            try:
                clan = await self.cr.get_clan(tag)
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                em = await embeds.format_clan(ctx, clan)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def members(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the members of a clan. (tagging the user)'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        async with ctx.typing():
            try:
                clan = await self.cr.get_clan(tag)
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                ems = await embeds.format_members(ctx, clan)
                if len(ems) > 1:
                    session = PaginatorSession(ctx, pages=ems)
                    await session.run()
                else:
                    await ctx.send(embed=ems[0])
            
    @commands.command()
    async def save(self, ctx, *, tag):
        '''Saves a Clash Royale tag to your discord profile.

        Ability to save multiple tags coming soon.
        '''
        tag = self.conv.resolve_tag(tag)

        if not tag:
            return await ctx.send('Invalid Tag!') # TODO: Better message.

        ctx.save_tag(tag)

        await ctx.send('Successfuly saved tag.')




def setup(bot):
    cog = Stats(bot)
    bot.add_cog(cog)
