import datetime
import random

import asyncio
import discord
from discord.ext import commands

def listget(l: list, index: int, default=None):
    try:
        return l[index]
    except IndexError:
        return default

class Moderation:
    '''These commands only work on the official Statsy support server: https://discord.gg/cBqsdPt'''

    def __init__(self, bot):
        self.bot = bot

    def __local_check(self, ctx):
        return ctx.guild.id == 444482551139008522 and discord.utils.get(ctx.guild.roles, id=444483190493806592) in ctx.author.roles

    async def __after_invoke(self, ctx):
        await ctx.send(f'{ctx.command.name.title()}ed {ctx.args[2]}')

        channel = ctx.guild.get_channel(450880403171966977)
        em = discord.Embed(
                title=ctx.command.name.title(),
                description=f'{ctx.author} ({ctx.author.id}) **{ctx.command.name}ed** {ctx.args[2]} ({ctx.args[2].id})\nReason: {ctx.kwargs["reason"]}\nDays: {listget(ctx.args, 3, "N.A.")}',
                timestamp=datetime.datetime.now(),
                color=random.randint(0, 0xffffff)
             )
        await channel.send(embed=em)

    @commands.command(hidden=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        '''Warns a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        '''
        pass

    @commands.command(hidden=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Not specified'):
        '''Kicks a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        '''
        await member.kick(reason=f'{ctx.author}: {reason}')

    @commands.command(hidden=True)
    async def ban(self, ctx, member: discord.User, days=7, *, reason='Not specified'):
        '''Bans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        '''
        await ctx.guild.ban(member, reason=f'{ctx.author}: {reason}', delete_message_days=days)


    @commands.command(hidden=True)
    async def unban(self, ctx, member: discord.User, *, reason='Not specified'):
        '''Unbans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        '''
        await ctx.guild.unban(member, reason=f'{ctx.author}: {reason}')

    @commands.command(hidden=True)
    async def softban(self, ctx, member: discord.Member, *, reason='Not specified'):
        '''Softbans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        '''
        await member.ban(reason=f'{ctx.author}: {reason}', delete_message_days=0)
        await asyncio.sleep(0.2)
        await member.unban(reason=f'{ctx.author}: {reason}')

def setup(bot):
    bot.add_cog(Moderation(bot))
