import discord
from discord.ext import commands
#from ext import embeds
from ext import embeds_cr_crapi
from ext import embeds_cr_statsroyale
from ext import embeds_cr_statsroyale as embeds
import json
from __main__ import InvalidTag, NoTag
from ext.paginator import PaginatorSession
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import io
import string
import time
import crasync
from crasync import errors
import asyncio

shortcuts = {'SA1':'88PYQV', 'SA2':'29UQQ282', 'SA3':'28JU8P0Y', 'SA4':'8PUUGRYG', 'SA5':'8YUU2CQV', 'UNDERBELLY':'2J8UVG99'}

class TagCheck(commands.MemberConverter):

    check = 'PYLQGRJCUV0289'

    def resolve_tag(self, tag):
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
        tag = self.resolve_tag(argument)

        if not tag:
            raise InvalidTag('Invalid cr-tag passed.')
        else:
            return tag

class Clash_Royale:

    '''Commands relating to the Clash Royale game made by supercell.'''

    def __init__(self, bot):
        self.bot = bot
        self.cr = bot.cr
        self.conv = TagCheck()
        self.url = 'https://statsroyale.herokuapp.com/'


    async def get_clan_from_profile(self, ctx, tag, message):
        try:
            p = await self.cr.get_player(tag)
        except Exception as e:
            er = discord.Embed(
                title=f'Error',
                color=discord.Color.red(),
                description=e
                )
            if ctx.bot.psa_message:
                er.add_field(name='Please Note!', value=ctx.bot.psa_message)
            await ctx.send(embed=er)
        else:
            if p.clan is None:
                await ctx.send(message)
                raise ValueError(message)
            return p.clan.tag


    async def resolve_tag(self, ctx, tag_or_user, clan=False):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('clashroyale')
            except KeyError:
                await ctx.send('You don\'t have a saved tag.')
                raise NoTag()
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'You don\'t have a clan!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag('clashroyale', tag_or_user.id)
            except KeyError:
                await ctx.send('That person doesnt have a saved tag!')
                raise NoTag()
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'That person does not have a clan!')
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    @embeds.has_perms(False)
    async def profile(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the clash royale profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_player(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                print(e)
                try:
                    url = self.url + 'profile/' + tag
                    async with ctx.session.get(url + '?appjson=1&refresh=1') as resp:
                        profile = await resp.json()
                except:
                    cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
                    if cached_data:
                        profile = cached_data
                        em = await embeds_cr_crapi.format_profile(ctx, profile, cache=True)
                        await ctx.send(embed=em)
                    else:
                        er = discord.Embed(
                            title=f'Error {e.code}',
                            color=discord.Color.red(),
                            description=e.error
                            )
                        if ctx.bot.psa_message:
                            er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                        await ctx.send(embed=er)
                else:
                    em = await embeds_cr_statsroyale.format_profile(ctx, profile)
                    await ctx.send(embed=em)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
                em = await embeds_cr_crapi.format_profile(ctx, profile)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, alises=['statistics'])
    @embeds.has_perms(False)
    async def stats(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the clash royale profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_player(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                try:
                    url = self.url + 'profile/' + tag
                    async with ctx.session.get(url + '?appjson=1&refresh=1') as resp:
                        profile = await resp.json()
                except:
                    cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
                    if cached_data:
                        profile = cached_data
                        em = await embeds_cr_crapi.format_stats(ctx, profile, cache=True)
                        await ctx.send(embed=em)
                    else:
                        er = discord.Embed(
                            title=f'Error {e.code}',
                            color=discord.Color.red(),
                            description=e.error
                            )
                        if ctx.bot.psa_message:
                            er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                        await ctx.send(embed=er)
                else:
                    em = await embeds_cr_statsroyale.format_stats(ctx, profile)
                    await ctx.send(embed=em)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
                em = await embeds_cr_crapi.format_stats(ctx, profile)
                await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, aliases=['season'])
    @embeds.has_perms()
    async def seasons(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the season results a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        await ctx.trigger_typing()
        try:
            profile = await self.cr.get_player(tag)
        except (errors.NotResponding, errors.ServerError) as e:
            cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
            if cached_data:
                profile = cached_data
                em = await embeds.format_seasons(ctx, profile, cache=True)
                await ctx.send(embed=em)
            else:
                er = discord.Embed(
                    title=f'Error {e.code}',
                    color=discord.Color.red(),
                    description=e.error
                    )
                if ctx.bot.psa_message:
                    er.add_field(name='Please Note!', value=ctx.bot.psa_message)
            await ctx.send(embed=er)
        except errors.NotFoundError:
            await ctx.send('That tag cannot be found!')
        else:
            ems = await embeds_cr_crapi.format_seasons(ctx, profile)
            if len(ems) > 0:
                session = PaginatorSession(
                    ctx=ctx, 
                    pages=ems, 
                    footer_text=f'{len(ems)} seasons'
                    )
                await session.run()
            else:
                ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
                await ctx.send(f"**{profile.name}** doesn't have any season results.")
                
    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def chests(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the next chests of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_player(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                try:
                    url = self.url + 'profile/' + tag
                    async with ctx.session.get(url + '?appjson=1&refresh=1') as resp:
                        profile = await resp.json()
                except:
                    cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
                    if cached_data:
                        profile = cached_data
                        em = await embeds_cr_crapi.format_chests(ctx, profile, cache=True)
                        await ctx.send(embed=em)
                    else:
                        er = discord.Embed(
                            title=f'Error {e.code}',
                            color=discord.Color.red(),
                            description=e.error
                            )
                        if ctx.bot.psa_message:
                            er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                        await ctx.send(embed=er)
                else:
                    em = await embeds_cr_statsroyale.format_chests(ctx, profile)
                    await ctx.send(embed=em)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
                em = await embeds_cr_crapi.format_chests(ctx, profile)
                await ctx.send(embed=em)

    # @commands.group(invoke_without_command=True)
    # @embeds.has_perms(False)
    # async def offers(self, ctx, *, tag_or_user:TagCheck=None):
    #     '''Get the upcoming offers of a player'''
    #     tag = await self.resolve_tag(ctx, tag_or_user)
    #     await ctx.trigger_typing()
    #     try:
    #         profile = await self.cr.get_player(tag)
    #     except (errors.NotResponding, errors.ServerError) as e:
    #         cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
    #         if cached_data:
    #             profile = cached_data
    #             em = await embeds.format_offers(ctx, profile, cache=True)
    #             await ctx.send(embed=em)
    #         else:
    #             er = discord.Embed(
    #                 title=f'Error {e.code}',
    #                 color=discord.Color.red(),
    #                 description=e.error
    #                     )
    #             if ctx.bot.psa_message:
    #                 er.add_field(name='Please Note!', value=ctx.bot.psa_message)
    #             await ctx.send(embed=er)
    #     except errors.NotFoundError:
    #         await ctx.send('That tag cannot be found!')
    #     else:
    #         ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
    #         em = await embeds.format_offers(ctx, profile)
    #         await ctx.send(embed=em)

    @commands.command()
    @embeds.has_perms(False)
    async def cards(self, ctx, *, tag_or_user:TagCheck=None):
        '''Get a list of cards the user has and does not have'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user)
            url = self.url + 'profile/' + tag
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'}
            async with ctx.session.get(url + '?appjson=1&refresh=1', headers=headers) as resp:
                p = await resp.json()
            #try:
            em = await embeds.format_cards(ctx, p)
            await ctx.send(embed=em)
            # except AttributeError:
            #     await ctx.send('Please do the command again to get your latest results.')
            # else:
            #     await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, aliases=['matches'])
    @embeds.has_perms(False)
    async def battles(self, ctx, tag_or_user:TagCheck=None):
        '''Get the latest 5 battles by the player!'''
        async with ctx.channel.typing():
            tag = await self.resolve_tag(ctx, tag_or_user)
            url = self.url + 'profile/' + tag
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'}
            async with ctx.session.get(url + '?appjson=1&refresh=1', headers=headers) as resp:
                p = await resp.json()
            em = await embeds.format_battles(ctx, p)
            await ctx.send(embed=em)


    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def clan(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets a clan by tag or by profile. (tagging the user)'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        await ctx.trigger_typing()
        try:
            clan = await self.cr.get_clan(tag)
        except (errors.NotResponding, errors.ServerError) as e:
            try:
                url = self.url + 'clan/' + tag
                async with ctx.session.get(url + '?appjson=1&refresh=1') as resp:
                    clan = await resp.json()
            except Exception as e:
                print(e)
                cached_data = ctx.cache('get', 'clashroyale/clans', tag)
                if cached_data:
                    clan = cached_data
                    em = await embeds_cr_crapi.format_clan(ctx, clan, cache=True)
                    await ctx.send(embed=em)
                else:
                    er = discord.Embed(
                        title=f'Error {e.code}',
                        color=discord.Color.red(),
                        description=e.error
                            )
                    if ctx.bot.psa_message:
                        er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                    await ctx.send(embed=er)
            else:
                ems = await embeds_cr_statsroyale.format_clan(ctx, clan)
                session = PaginatorSession(
                    ctx=ctx,
                    pages=ems
                    )
                await session.run()
        except errors.NotFoundError:
            await ctx.send('That tag cannot be found!')
        else:
            ctx.cache('update', 'clashroyale/clans', clan.raw_data)
            ems = await embeds_cr_crapi.format_clan(ctx, clan)
            session = PaginatorSession(
                ctx=ctx,
                pages=ems
                )
            await session.run()

    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def topclans(self, ctx):
        '''Returns the global top 50 clans.'''

        await ctx.trigger_typing()
        try:
            clans = await self.cr.get_top_clans()
        except (errors.NotResponding, errors.ServerError) as e:
            er = discord.Embed(
                title=f'Error {e.code}',
                color=discord.Color.red(),
                description=e.error
                    )
            if ctx.bot.psa_message:
                er.add_field(name='Please Note!', value=ctx.bot.psa_message)
            await ctx.send(embed=er)
        else:
            ems = await embeds_cr_crapi.format_top_clans(ctx, clans)
            session = PaginatorSession(
                ctx=ctx,
                pages=ems
                )
            await session.run()

    @commands.group(invoke_without_command=True)
    @embeds.has_perms()
    async def members(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets all the members of a clan.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        await ctx.trigger_typing()
        try:
            clan = await self.cr.get_clan(tag)
        except (errors.NotResponding, errors.ServerError) as e:
            try:
                ems = await embeds_cr_statsroyale.format_members(ctx, clan)
            except:
                cached_data = ctx.cache('get', 'clashroyale/clans', tag)
                if cached_data:
                    clan = cached_data
                    em = await embeds_cr_crapi.format_members(ctx, clan, cache=True)
                    if len(ems) > 1:
                        session = PaginatorSession(
                            ctx=ctx, 
                            pages=ems, 
                            footer_text=f'{len(clan.members)}/50 members'
                            )
                        await session.run()
                    else:
                        await ctx.send(embed=ems[0])
                else:
                    er = discord.Embed(
                        title=f'Error {e.code}',
                        color=discord.Color.red(),
                        description=e.error
                            )
                    if ctx.bot.psa_message:
                        er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                    await ctx.send(embed=em)
            else:
                if len(ems) > 1:
                    session = PaginatorSession(
                        ctx=ctx, 
                        pages=ems, 
                        footer_text=f'{len(clan.members)}/50 members'
                    )
                    await session.run()
                else:
                    await ctx.send(embed=ems[0])
        except errors.NotFoundError:
            await ctx.send('That tag cannot be found!')
        else:
            ctx.cache('update', 'clashroyale/clans', clan.raw_data)
            ems = await embeds_cr_crapi.format_members(ctx, clan)
            if len(ems) > 1:
                session = PaginatorSession(
                    ctx=ctx, 
                    pages=ems, 
                    footer_text=f'{len(clan.members)}/50 members'
                    )
                await session.run()
            else:
                await ctx.send(embed=ems[0])

    @members.command()
    @embeds.has_perms(False)
    async def best(self, ctx, *, tag_or_user: TagCheck=None):
        '''Finds the best members of the clan currently.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)
        async with ctx.typing():
            try:
                clan = await self.cr.get_clan(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                cached_data = ctx.cache('get', 'clashroyale/clans', tag)
                if cached_data:
                    clan = cached_data
                    em = await embeds_cr_crapi.format_most_valuable(ctx, clan, cache=True)
                    await ctx.send(embed=em)
                else:
                    er = discord.Embed(
                        title=f'Error {e.code}',
                        color=discord.Color.red(),
                        description=e.error
                        )
                if ctx.bot.psa_message:
                    er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                await ctx.send(embed=er)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/clans', clan.raw_data)
                if len(clan.members) < 4:
                    return await ctx.send('Clan must have more than 4 players for heuristics.')
                else:
                    em = await embeds_cr_crapi.format_most_valuable(ctx, clan)
                    await ctx.send(embed=em)

    @members.command()
    @embeds.has_perms(False)
    async def worst(self, ctx, *, tag_or_user: TagCheck=None):
        '''Finds the worst members of the clan currently.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)
        async with ctx.typing():
            try:
                clan = await self.cr.get_clan(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                cached_data = ctx.cache('get', 'clashroyale/clans', tag)
                if cached_data:
                    clan = cached_data
                    em = await embeds_cr_crapi.format_least_valuable(ctx, clan, cache=True)
                    await ctx.send(embed=em)
                else:
                    er = discord.Embed(
                        title=f'Error {e.code}',
                        color=discord.Color.red(),
                        description=e.error
                        )
                if ctx.bot.psa_message:
                    er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                await ctx.send(embed=er)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/clans', clan.raw_data)
                if len(clan.members) < 4:
                    return await ctx.send('Clan must have more than 4 players for heuristics.')
                else:
                    em = await embeds_cr_crapi.format_least_valuable(ctx, clan)
                    await ctx.send(embed=em)

            
    @commands.command()
    async def save(self, ctx, *, tag):
        '''Saves a Clash Royale tag to your discord profile.

        Ability to save multiple tags coming soon.
        '''
        tag = self.conv.resolve_tag(tag)

        if not tag:
            raise InvalidTag('Invalid tag')

        ctx.save_tag(tag, 'clashroyale')

        await ctx.send('Successfully saved tag.')

    @commands.group(invoke_without_command=True)
    @embeds.has_perms(False, False)
    async def deck(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the current deck of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        async with ctx.typing():
            try:
                profile = await self.cr.get_player(tag)
            except (errors.NotResponding, errors.ServerError) as e:
                cached_data = ctx.cache('get', 'clashroyale/profiles', tag)
                if cached_data:
                    profile = cached_data
                    await self.format_deck_and_send(ctx, profile)
                else:
                    er = discord.Embed(
                        title=f'Error {e.code}',
                        color=discord.Color.red(),
                        description=e.error
                        )
                    if ctx.bot.psa_message:
                        er.add_field(name='Please Note!', value=ctx.bot.psa_message)
                    await ctx.send(embed=er)
            except errors.NotFoundError:
                await ctx.send('The tag cannot be found!')
            else:
                ctx.cache('update', 'clashroyale/profiles', profile.raw_data)
                await self.format_deck_and_send(ctx, profile)

    @commands.command()
    @embeds.has_perms(False)
    async def card(self, ctx, *, card):
        '''Get information about a Clash Royale card.'''
        aliases = {
            "log": "the log", 
            "pump": 'elixir collector', 
            'skarmy': 'skeleton army',
            'pekka': 'p.e.k.k.a',
            'mini pekka': 'mini p.e.k.k.a',
            'xbow': 'x-bow'
            }
        card = card.lower()
        if card in aliases:
            card = aliases[card]
        constants = self.bot.constants
        try:
            found_card = constants.cards[card]
        except KeyError:
            return await ctx.send("That's not a card!")
        em = await embeds.format_card(ctx, found_card)
        with open(f"data/cards/{card.replace(' ', '-').replace('.','')}.png", 'rb') as c:
            with open(f"data/cards_ingame/{card.replace(' ', '-').replace('.','')}.png", 'rb') as i:
                await ctx.send(embed=em, files=[discord.File(c, 'card.png'), discord.File(i, 'ingame.png')])


    @commands.command(aliases=['tourneys'])
    @embeds.has_perms(False)
    async def tournaments(self, ctx):
        '''Show a list of open tournaments that you can join!'''
        async with ctx.session.get(self.url + 'tournaments?appjson=1&refresh=1') as resp:
            json = await resp.json()
        em = await embeds.format_tournaments(ctx, json)
        await ctx.send(embed=em)

    async def format_deck_and_send(self, ctx, profile):
        deck = profile.current_deck
        author = profile.name

        deck_image = await self.bot.loop.run_in_executor(
            None,
            self.get_deck_image,
            profile, author
        )

        em = discord.Embed(description=f'[Copy this deck!]({profile.deck_link})', color=embeds.random_color())
        if self.bot.psa_message:
            em.description = f'*{self.bot.psa_message}*'
        em.set_author(name=f'{profile.name} (#{profile.tag})', icon_url=embeds_cr_crapi.get_clan_image(profile))
        em.set_image(url='attachment://deck.png')
        em.set_footer(text='Statsy - Powered by cr-api.com')


        await ctx.send(file=discord.File(deck_image, 'deck.png'), embed=em)

        deck_image.close()

    def get_deck_image(self, profile, deck_author=None):
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

        bg_image = Image.open("data/deck-bg.png")
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
            card_image = Image.open(card_image_file)
            # size = (card_w, card_h)
            # card_image.thumbnail(size)
            box = (card_x + card_w * i,
                   card_y,
                   card_x + card_w * (i + 1),
                   card_h + card_y)
            image.paste(card_image, box, card_image)

        # elixir
        total_elixir = sum(c.elixir for c in deck)
        card_count = 8

        average_elixir = "{:.3f}".format(total_elixir / card_count)

        # text
        # Take out hyphnens and capitlize the name of each card
        card_names = [string.capwords(c.replace('-', ' ')) for c in cards]

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

        image.save(file, format='PNG')

        file.seek(0)

        return file

def setup(bot):
    cog = Clash_Royale(bot)
    bot.add_cog(cog)
