import asyncio
import io
import re

from cachetools import TTLCache
import clashroyale
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from statsbot import InvalidTag, NoTag
from ext import embeds_cr as embeds
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
            raise InvalidTag('Invalid cr-tag passed.')
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
        if any(i not in self.check for i in tag):
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
            raise InvalidTag(_('Invalid cr-tag passed.', ctx))
        else:
            return tag


class Clash_Royale:

    """Commands relating to the Clash Royale game made by supercell."""

    def __init__(self, bot):
        self.bot = bot
        self.cr = bot.cr
        self.conv = TagCheck()
        self.cache = TTLCache(500, 180)

    async def __local_check(self, ctx):
        guild_info = await self.bot.mongo.config.guilds.find_one({'guild_id': ctx.guild.id}) or {}
        return guild_info.get('games', {}).get(self.__class__.__name__, True)

    async def __error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, clashroyale.NotFoundError):
            await ctx.send(_('The tag cannot be found!', ctx))
        elif isinstance(error, clashroyale.RequestError):
            er = discord.Embed(
                title=_('RoyaleAPI Server Down', ctx),
                color=discord.Color.red(),
                description=error.code
            )
            if ctx.bot.psa_message:
                er.add_field(name=_('Please Note!', ctx), value=ctx.bot.psa_message)
            await ctx.send(embed=er)

    async def request(self, method, *args):
        try:
            data = self.cache[f'{method}{args}']
        except KeyError:
            data = await getattr(self.cr, method)(*args)
            if method in ('get_player', 'get_clan', 'get_player_chests') and isinstance(data, list):
                data = data[0]
            if isinstance(data, list):
                self.cache[f'{method}{args}'] = data
            else:
                self.cache[f'{method}{args}'] = data.raw_data
        else:
            if not isinstance(data, list):
                data = clashroyale.BaseAttrDict(self.cr, data, None)
        return data

    async def get_clan_from_profile(self, ctx, tag, message):
        p = await self.request('get_player', tag)
        if p.clan is None:
            await ctx.send(message)
            raise NoTag(message)
        return p.clan.tag

    async def resolve_tag(self, ctx, tag_or_user, *, clan=False, index=0):
        if not tag_or_user:
            try:
                tag = await ctx.get_tag('clashroyale', index=str(index))
            except KeyError:
                await ctx.send(_("You don't have a saved tag. Save one using `{}save <tag>`!", ctx).format(ctx.prefix))
                raise NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, _("You don't have a clan!", ctx))
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = await ctx.get_tag('clashroyale', tag_or_user.id, index=str(index))
            except KeyError:
                await ctx.send(_('That person doesnt have a saved tag!', ctx))
                raise NoTag
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'That person does not have a clan!')
                return tag
        else:
            return tag_or_user

    async def on_message(self, m):
        if self.bot.dev_mode or not m.guild or not self.bot.is_ready():
            return

        if not ('http://link.clashroyale.com' in m.content or 'https://link.clashroyale.com' in m.content):
            return

        guild_config = await self.bot.mongo.config.guilds.find_one({'guild_id': m.guild.id}) or {}
        friend_config = guild_config.get('friend_link')

        default = False

        if friend_config is None and self.bot.get_user(402656158667767808) not in m.guild.members:
            default = friend_config = True

        if friend_config:
            ctx = await self.bot.get_context(m)
            if ctx.guild:
                ctx.language = (await self.bot.mongo.config.guilds.find_one({'guild_id': ctx.guild.id}) or {}).get('language', 'messages')
            else:
                ctx.language = 'messages'

            tag = m.content[m.content.find('?tag=') + 5:m.content.find('&token=')]
            token = m.content[m.content.find('&token=') + 7:m.content.find('&token=') + 7 + 8]
            link = f'https://link.clashroyale.com?tag={tag}&token={token}/'
            profile = await self.request('get_player', tag)

            if m.content.find('android') != -1:
                platform = m.content.find('platform=android') + len('platform=android')
            elif m.content.find('iOS') != -1:
                platform = m.content.find('platform=iOS') + len('platform=ios')
            else:
                platform = m.content.find('&token=') + 7 + 8

            text = m.content[0:m.content.find('http')] + ' ' + m.content[platform:]

            em = await embeds.format_friend_link(ctx, profile, link, default)
            try:
                await m.delete()
            except (discord.NotFound, commands.BotMissingPermissions):
                pass

            await m.channel.send(text, embed=em)

    @commands.group(invoke_without_command=True)
    async def friendlink(self, ctx):
        """Check your guild's friend link status"""
        if not ctx.guild:
            return await ctx.send(_('Friend link is always disabled in DMs.'), ctx)
        guild_config = await self.bot.mongo.config.guilds.find_one({'guild_id': ctx.guild.id}) or {}
        friend_config = guild_config.get('friend_link')

        default = False

        if friend_config is None and self.bot.get_user(402656158667767808) not in ctx.guild.members:
            default = friend_config = True

        resp = _('Current status: {}', ctx).format(friend_config)
        if default:
            resp += _(' (default, ctx)')
        await ctx.send(resp)

    @friendlink.command()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        """Enables friend link"""
        if not ctx.guild:
            return await ctx.send(_("Configuring friend link status isn't allowed in DMs", ctx))
        await self.bot.mongo.config.guilds.find_one_and_update(
            {'guild_id': ctx.guild.id}, {'$set': {'friend_link': True}}, upsert=True
        )
        await ctx.send(_('Successfully set friend link to be enabled.', ctx))

    @friendlink.command()
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        """Disables friend link"""
        if not ctx.guild:
            return await ctx.send(_("Configuring friend link status isn't allowed in DMs", ctx))
        await self.bot.mongo.config.guilds.find_one_and_update(
            {'guild_id': ctx.guild.id}, {'$set': {'friend_link': False}}, upsert=True
        )
        await ctx.send(_('Successfully set friend link to be disabled.', ctx))

    @commands.group(invoke_without_command=True, aliases=['player'])
    @embeds.has_perms(False)
    async def profile(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the clash royale profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            cycle = await self.request('get_player_chests', tag)
            em = await embeds.format_profile(ctx, profile, cycle)

        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, alises=['statistics'])
    @embeds.has_perms(False)
    async def stats(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the clash royale profile of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            em = await embeds.format_stats(ctx, profile)

        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, aliases=['season'])
    @embeds.has_perms()
    async def seasons(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the season results a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            ems = await embeds.format_seasons(ctx, profile)

        if len(ems) > 0:
            session = PaginatorSession(
                ctx=ctx,
                pages=ems
            )
            await session.run()
        else:
            await ctx.send(f"**{profile.name}** doesn't have any season results.")

    @commands.group(invoke_without_command=True)
    @embeds.has_perms(False)
    async def chests(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the next chests of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            cycle = await self.request('get_player_chests', tag)
            em = await embeds.format_chests(ctx, profile, cycle)

        await ctx.send(embed=em)

    @commands.command()
    @embeds.has_perms(False)
    async def cards(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Get a list of cards the user has and does not have"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            em = await embeds.format_cards(ctx, profile)

        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, aliases=['matches'])
    @embeds.has_perms(False)
    async def battles(self, ctx, tag_or_user: TagCheck=(None, 0)):
        """Get the latest 5 battles by the player!"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            battles = await self.request('get_player_battles', tag)
            em = await embeds.format_battles(ctx, battles)

        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def clan(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets a clan by tag or by profile. (tagging the user)"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request('get_clan', tag)
            ems = await embeds.format_clan(ctx, clan)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @commands.group(aliases=['clan_war', 'clan-war'], invoke_without_command=True)
    @embeds.has_perms()
    async def clanwar(self, ctx, tag_or_user: TagCheck=(None, 0)):
        """Shows your clan clan war statistics"""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            war = await self.request('get_clan_war', tag)
            ems = await embeds.format_clan_war(ctx, war)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def topclans(self, ctx, *, region: str = ''):
        """Returns the global top 50 clans."""
        async with ctx.typing():
            if region:
                for i in self.bot.constants.regions:
                    if i.name.lower() == region or str(i.id) == region or i.key.replace('_', '').lower() == region:
                        region = i.key
                        name = i.name
            else:
                name = 'Global'

            clans = await self.request('get_top_clans', region)
            ems = await embeds.format_top_clans(ctx, clans, name)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def members(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets all the members of a clan."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request('get_clan', tag)
            war = await self.request('get_clan_war_log', tag)

            ems = await embeds.format_members(ctx, clan, war)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems,
            footer_text=f'{len(clan.members)}/50 members'
        )
        await session.run()

    @members.command()
    @embeds.has_perms(False)
    async def best(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Finds the best members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request('get_clan', tag)
            war = await self.request('get_clan_war_log', tag)

            if len(clan.members) < 4:
                await ctx.send('Clan must have at least 4 players for these statistics.')
            else:
                em = await embeds.format_most_valuable(ctx, clan, war)
                await ctx.send(embed=em)

    @members.command()
    @embeds.has_perms(False)
    async def worst(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Finds the worst members of the clan currently."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1], clan=True)

        async with ctx.typing():
            clan = await self.request('get_clan', tag)
            war = await self.request('get_clan_war_log', tag)

            if len(clan.members) < 4:
                return await ctx.send('Clan must have at least 4 players for these statistics.')
            else:
                em = await embeds.format_least_valuable(ctx, clan, war)
                await ctx.send(embed=em)

    @commands.command()
    async def save(self, ctx, tag, index: str='0'):
        """Saves a Clash Royale tag to your discord profile."""
        tag = self.conv.resolve_tag(ctx, tag)

        if not tag:
            raise InvalidTag('Invalid cr-tag passed')

        await ctx.save_tag(tag[0], 'clashroyale', index=index.replace('-', ''))

        if index == '0':
            prompt = f'Check your stats with `{ctx.prefix}profile`!'
        else:
            prompt = f'Check your stats with `{ctx.prefix}profile -{index}`!'

        await ctx.send('Successfully saved tag. ' + prompt)

    @commands.command()
    @embeds.has_perms(False)
    async def usertag(self, ctx, member: discord.Member = None):
        """Checks the saved tag(s) of a member"""
        member = member or ctx.author
        tag = await self.resolve_tag(ctx, member, index='all')
        em = discord.Embed(description='Tags saved', color=embeds.random_color())
        em.set_author(name=member.name, icon_url=member.avatar_url)
        for i in tag:
            em.add_field(name=f'Tag index: {i}', value=tag[i])
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    @embeds.has_perms(False, False)
    async def deck(self, ctx, *, tag_or_user: TagCheck=(None, 0)):
        """Gets the current deck of a player."""
        tag = await self.resolve_tag(ctx, tag_or_user[0], index=tag_or_user[1])

        async with ctx.typing():
            profile = await self.request('get_player', tag)
            await self.format_deck_and_send(ctx, profile)

    @commands.command(name='card')
    @embeds.has_perms(False)
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
        constants = self.bot.constants

        found_card = None
        for c in constants.cards:
            if c.name.lower() == card.lower():
                found_card = c

        if found_card is None:
            return await ctx.send("That's not a card!")

        em = await embeds.format_card(ctx, found_card)
        try:
            with open(f"data/cards/{card.replace(' ', '-').replace('.','')}.png", 'rb') as c:
                with open(f"data/cards_ingame/{card.replace(' ', '-').replace('.','')}.png", 'rb') as i:
                    await ctx.send(embed=em, files=[discord.File(c, 'card.png'), discord.File(i, 'ingame.png')])
        except FileNotFoundError:
            await ctx.send(embed=em)

    @commands.command(aliases=['tourney'])
    @embeds.has_perms(False)
    async def tournament(self, ctx, tag: TagOnly):
        """View statistics about a tournament"""
        async with ctx.typing():
            t = await self.request('get_tournament', tag[0])
            ems = await embeds.format_tournament(ctx, t)

        session = PaginatorSession(
            ctx=ctx,
            pages=ems
        )
        await session.run()

    @commands.command(aliases=['tourneys'])
    @embeds.has_perms(False)
    async def tournaments(self, ctx):
        """Show a list of open tournaments that you can join!"""
        async with ctx.typing():
            t = await self.request('get_open_tournaments')
            em = await embeds.format_tournaments(ctx, t)

        await ctx.send(embed=em)

    async def format_deck_and_send(self, ctx, profile):
        author = profile.name

        deck_image = await self.bot.loop.run_in_executor(
            None,
            self.get_deck_image,
            ctx, profile, author
        )

        copydeck = '<:copydeck:376367880289124366>'

        em = discord.Embed(
            description=f'[Copy this deck! {copydeck}]({profile.deck_link})', color=embeds.random_color()
        )
        if self.bot.psa_message:
            em.description = f'*{self.bot.psa_message}*'
        em.set_author(name=f'{profile.name} (#{profile.tag})', icon_url=embeds.get_clan_image(profile))
        em.set_image(url='attachment://deck.png')
        em.set_footer(text='Statsy - Powered by RoyaleAPI.com')

        await ctx.send(file=discord.File(deck_image, 'deck.png'), embed=em)

        deck_image.close()

    def get_deck_image(self, ctx, profile, deck_author=None):
        """Construct the deck with Pillow and return image."""

        deck = profile.current_deck

        card_w = 302
        card_h = 363
        card_x = 30
        card_y = 30
        font_size = 50
        txt_y_line1 = 430
        txt_y_line2 = 500
        txt_x_name = 50
        txt_x_cards = 700
        txt_x_elixir = 1872

        bg_image = Image.open("data/deck-bg.png").convert("RGBA")
        size = bg_image.size

        font_file_regular = "data/fonts/OpenSans-Regular.ttf"
        font_file_bold = "data/fonts/OpenSans-Bold.ttf"

        image = Image.new("RGBA", size)
        image.paste(bg_image)

        deck_name = 'Deck'
        cards = [c.name.replace(' ', '-').replace('.', '').lower() for c in deck]

        # cards
        for i, card in enumerate(cards):
            card_image_file = "data/cards/{}.png".format(card)
            try:
                card_image = Image.open(card_image_file).convert("RGBA")
            except FileNotFoundError:
                self.bot.loop.create_task(
                    ctx.send(f'Card not supported yet! Notify us by doing `{ctx.prefix}bug {card} not supported!`')
                )
            else:
                # size = (card_w, card_h)
                # card_image.thumbnail(size)
                box = (
                    card_x + card_w * i,
                    card_y,
                    card_x + card_w * (i + 1),
                    card_h + card_y
                )
                image.paste(card_image, box, card_image)

        # elixir
        total_elixir = sum(c.elixir for c in deck)
        card_count = len(deck)

        average_elixir = "{:.3f}".format(total_elixir / card_count)

        # text
        # Take out hyphnens and capitlize the name of each card

        txt = Image.new("RGBA", size)
        txt_name = Image.new("RGBA", (txt_x_cards - 30, size[1]))
        font_regular = ImageFont.truetype(font_file_regular, size=font_size)
        font_bold = ImageFont.truetype(font_file_bold, size=font_size)

        d = ImageDraw.Draw(txt)
        d_name = ImageDraw.Draw(txt_name)

        line1 = profile.arena.name
        line2 = f'{profile.trophies} Trophies'

        # card_text = '\n'.join([line0, line1])

        deck_author_name = deck_author

        d_name.text(
            (txt_x_name, txt_y_line1), deck_name, font=font_bold,
            fill=(0xff, 0xff, 0xff, 255))
        d_name.text(
            (txt_x_name, txt_y_line2), deck_author_name, font=font_regular,
            fill=(0xff, 0xff, 0xff, 255))
        d.text(
            (txt_x_cards, txt_y_line1), line1, font=font_regular,
            fill=(0xff, 0xff, 0xff, 255))
        d.text(
            (txt_x_cards, txt_y_line2), line2, font=font_regular,
            fill=(0xff, 0xff, 0xff, 255))
        d.text(
            (txt_x_elixir, txt_y_line1), "Avg elixir", font=font_bold,
            fill=(0xff, 0xff, 0xff, 200))
        d.text(
            (txt_x_elixir, txt_y_line2), average_elixir, font=font_bold,
            fill=(0xff, 0xff, 0xff, 255))

        image.paste(txt, (0, 0), txt)
        image.paste(txt_name, (0, 0), txt_name)

        # scale down and return
        scale = 0.5
        scaled_size = tuple([x * scale for x in image.size])
        image.thumbnail(scaled_size)

        file = io.BytesIO()

        image.save(file, optimize=False, quality=10, format='PNG')

        file.seek(0)

        return file


def setup(bot):
    cog = Clash_Royale(bot)
    bot.add_cog(cog)
