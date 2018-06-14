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
    """These commands only work on the official Statsy support server: https://discord.gg/cBqsdPt"""

    def __init__(self, bot):
        self.bot = bot

    def __local_check(self, ctx):
        mod_role = discord.utils.get(ctx.guild.roles, id=444483190493806592)
        return ctx.guild.id == 444482551139008522 and mod_role in ctx.author.roles

    async def __after_invoke(self, ctx):
        await ctx.send(f'{ctx.command.name.title()}ed {ctx.args[2]}')

        channel = ctx.guild.get_channel(450880403171966977)
        em = discord.Embed(
            title=ctx.command.name.title(),
            description='\n'.join((
                f'{ctx.author} ({ctx.author.id}) **{ctx.command.name}ed** {ctx.args[2]} ({ctx.args[2].id})',
                f'Reason: {ctx.kwargs["reason"]}',
                f'Days: {listget(ctx.args, 3, "N.A.")}'
            )),
            timestamp=datetime.datetime.utcnow(),
            color=random.randint(0, 0xffffff)
        )
        await channel.send(embed=em)

    @commands.command(hidden=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        """Warns a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        """
        pass

    @commands.command(hidden=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Not specified'):
        """Kicks a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        """
        await member.kick(reason=f'{ctx.author}: {reason}')

    @commands.command(hidden=True)
    async def ban(self, ctx, member: discord.User, days=7, *, reason='Not specified'):
        """Bans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        """
        await ctx.guild.ban(member, reason=f'{ctx.author}: {reason}', delete_message_days=days)

    @commands.command(hidden=True)
    async def unban(self, ctx, member: discord.User, *, reason='Not specified'):
        """Unbans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        """
        await ctx.guild.unban(member, reason=f'{ctx.author}: {reason}')

    @commands.command(hidden=True)
    async def softban(self, ctx, member: discord.Member, *, reason='Not specified'):
        """Softbans a user
        Only works on the official Statsy support server: https://discord.gg/cBqsdPt
        """
        await member.ban(reason=f'{ctx.author}: {reason}', delete_message_days=0)
        await asyncio.sleep(0.2)
        await member.unban(reason=f'{ctx.author}: {reason}')

    async def on_message_edit(self, b, a):
        if self.bot.dev_mode or b.guild.id != 444482551139008522 or b.content == a.content or\
           b.author.id == 180314310298304512 or b.author == self.bot.user:
            return
        await self.bot.get_channel(456793628736618509).send(embed=discord.Embed(
            description=f'\U0001F4DD {b.author} ({b.author.id}) message ({b.id}) edited in **#{b.channel.name}**:\n**B:** {b.content}\n**A:** {a.content}',
            color=0x36393e,
            timestamp=datetime.datetime.utcnow()
        ))

    async def on_message_delete(self, m):
        if self.bot.dev_mode or m.guild.id != 444482551139008522 or m.author.id == 180314310298304512 or\
           m.author == self.bot.user:
            return
        await self.bot.get_channel(456793628736618509).send(embed=discord.Embed(
            description=f'\U0001F5D1 {m.author} ({m.author.id}) message ({m.id}) edited in **#{m.channel.name}**:\n{m.content}',
            color=0x36393e,
            timestamp=datetime.datetime.utcnow()
        ))

    async def on_member_join(self, m):
        if self.bot.dev_mode or m.guild.id != 444482551139008522:
            return
        await self.bot.get_channel(456793628736618509).send(embed=discord.Embed(
            description=f'\U0001F4E5 {m} ({m.id}) joined (created {m.created_at})',
            color=0x36393e,
            timestamp=datetime.datetime.utcnow()
        ))

    async def on_member_remove(self, m):
        if self.bot.dev_mode or m.guild.id != 444482551139008522:
            return
        await self.bot.get_channel(456793628736618509).send(embed=discord.Embed(
            description=f'\U0001F4E5 {m} ({m.id}) left (created {m.created_at})',
            color=0x36393e,
            timestamp=datetime.datetime.utcnow()
        ))

    async def on_message(self, m):
        if m.channel.id == 456803934334615552:
            member = m.guild.get_member(int(m.content))
            if member:
                member.add_roles(discord.utils.get(m.guild.roles, id=455392833130594304))
                await m.add_reaction(u'\U00002705')

def setup(bot):
    bot.add_cog(Moderation(bot))
