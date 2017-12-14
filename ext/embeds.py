import discord
from collections import OrderedDict
import json
import random
import copy
import datetime
import math
import time
import crasync
from discord.ext import commands

image = 'https://raw.githubusercontent.com/cr-api/cr-api-assets/master/'

def has_perms(add_reactions=True, external_emojis=True):
    perms = {
        'send_messages': True,
        'embed_links': True
    }

    if add_reactions:
        perms['add_reactions'] = True

    if external_emojis:
        perms['external_emojis'] = True
    return commands.bot_has_permissions(**perms)

def emoji(ctx, name):
    name = name.replace('.','').lower().replace(' ','').replace('_','').replace('-','')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    return e

def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]

def random_color():
    return random.randint(0, 0xFFFFFF)

def get_card(ctx, decklink):
    for c in ctx.bot.constants.cards:
        if int(ctx.bot.constants.cards[c].deck_link) == decklink:
            return ctx.bot.constants.cards[c].name

def get_deck(ctx, p):
    deck = ''
    for card in p['profile']['currentDeckCards']:
        name = get_card(ctx, card['card'])
        deck += str(emoji(ctx, name)) + str(card['level']) + ' '
    return deck

def timestamp(datatime:int):
    return str(int((datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(datatime)).total_seconds()/60)) + ' minutes ago'

async def format_least_valuable(ctx, clan, cache=False):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3
    to_kick = sorted(clan.members, key=lambda m: m.score)[:4]

    em = discord.Embed(
        color=random_color(),
        description='Here are the least valuable members of the clan currently.'
        )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(clan.raw_data['updatedTime'])
    em.set_author(name=clan)
    em.set_thumbnail(url=clan.badge_url)
    em.set_footer(text='Statsy - Powered by cr-api.com')

    for m in reversed(to_kick):
        em.add_field(
            name=f'{m.name} ({m.role_name})',
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.crowns} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}"
                  )
    return em

async def format_most_valuable(ctx, clan, cache=False):

    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3

    best = sorted(clan.members, key=lambda m: m.score, reverse=True)[:4]

    em = discord.Embed(
        color=random_color(),
        description='Here are the most valuable members of the clan currently.'
        )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(clan.raw_data['updatedTime'])
    em.set_author(name=clan)
    em.set_thumbnail(url=clan.badge_url)
    em.set_footer(text='Statsy - Powered by cr-api.com')

    for m in reversed(best):
        em.add_field(
            name=f'{m.name} ({m.role_name})',
            value=f"#{m.tag}\n{m.trophies} "
            f"{emoji(ctx, 'trophy')}\n{m.crowns} "
            f"{emoji(ctx, 'crownblue')}\n{m.donations} "
            f"{emoji(ctx, 'cards')}"
            )

    return em

special_chests = ['Magic', 'Giant', 'Epic', 'Legendary', 'supermagical']

def get_chests(ctx, p):
    cycle = p['chests']

    chests = '| '+ str(emoji(ctx, 'chest' + cycle['0'].lower())) + ' | '
    chests += ''.join([str(emoji(ctx, 'chest' + cycle[str(x)].lower())) for x in range(8)])
    special = ''
    for i in cycle:
        if cycle[str(i)] == 'Super': cycle[str(i)] = 'supermagical'
        e = emoji(ctx, 'chest'+cycle[str(i)].lower())
        if cycle[str(i)] in special_chests:
            until = i
            special += f'{e}+{until} '
    return (chests, special)

async def format_chests(ctx, p, cache=False):
    try:
        av = image + 'badge/' + ctx.bot.constants.badges[str(p['profile']['alliance']['badge'])] + '.png'
    except:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p['profile']['name']} (#{p['profile']['hashtag']})", icon_url=av)
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_thumbnail(url=emoji(ctx, 'chest' + p['chests']['0'].lower()).url)
    em.add_field(name=f'Chests', value=get_chests(ctx, p)[0])
    em.add_field(name="Chests Until", value=get_chests(ctx, p)[1])
    em.set_footer(text='Statsy - Powered by cr-api.com')
    return em

# async def format_offers(ctx, p, cache=False):
#     av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
#     em = discord.Embed(color=random_color())
#     if ctx.bot.psa_message:
#         em.description = f'*{ctx.bot.psa_message}*'
#     if cache:
#         em.description = 'Cached data from ' + \
#             timestamp(p.raw_data['updatedTime'])
#     em.set_author(name=str(p), icon_url=av)
#     em.set_thumbnail(url=p.arena.image_url)
#     if p.shop_offers.legendary:
#         em.add_field(name=f"Legendary {emoji(ctx, 'chestlegendary')}", value=f'{p.shop_offers.legendary} Days')
#     if p.shop_offers.epic:
#         em.add_field(name=f"Epic {emoji(ctx, 'chestepic')}", value=f'{p.shop_offers.epic} Days')
#     if p.shop_offers.legendary:
#         em.add_field(name=f"Arena Offer {emoji(ctx, 'arena11')}", value=f'{p.shop_offers.arena} Days')
#     return em

async def format_cards(ctx, p):
    constants = ctx.bot.constants
    name = p['profile']['name']
    tag = p['profile']['hashtag']

    rarity = {
        'Common': 1,
        'Rare': 2,
        'Epic': 3,
        'Legendary': 4
    }

    cards = p['profile']['cards']
    found_cards = []
    notfound_cards = []

    for constcard in constants.cards:
        if constants.cards[constcard].deck_link not in cards:
            notfound_cards.append(constants.cards[constcard])
        else:
            found_cards.append(constants.cards[constcard])

    found_cards = sorted(found_cards, key=lambda x: rarity[x.rarity])
    notfound_cards = sorted(notfound_cards, key=lambda x: rarity[x.rarity])

    def get_rarity(card):
        for a in constants.cards:
            if constants.cards[a].name.lower().replace(' ', '').replace('-', '').replace('.', '') == card:
                return constants.cards[a].rarity

    fmt = ''
    found_cards_pages = []
    oldcard = ''
    newpage = False
    for card in found_cards:
        txt = card.name.lower().replace(' ', '').replace('-', '').replace('.', '')
        if isinstance(oldcard, crasync.models.CardInfo):
            if oldcard.rarity != card.rarity:
                try:
                    found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
                except IndexError:
                    found_cards_pages.append((fmt, fmt.split(':')[0]))
                fmt = str(emoji(ctx, txt))
            else:
                newpage = True
        else:
            newpage = True
        if newpage:
            fmt += str(emoji(ctx, txt))
            if len(fmt) > 1024:
                fmt = fmt.replace(str(emoji(ctx, txt)), '')
                try:
                    found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
                except IndexError:
                    found_cards_pages.append((fmt, fmt.split(':')[0]))
                fmt = str(emoji(ctx, txt))
            newpage = False
        oldcard = card
    try:
        found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
    except IndexError:
        found_cards_pages.append((fmt, fmt.split(':')[0]))

    fmt = ''
    notfound_cards_pages = []
    for card in notfound_cards:
        txt = card.name.lower().replace(' ', '')
        fmt += str(emoji(ctx, txt))
        if len(fmt) > 1024:
            fmt = fmt.replace(str(emoji(ctx, txt)), '')
            found_cards_pages.append(fmt)
            fmt = str(emoji(ctx, txt))
    notfound_cards_pages.append(fmt)

    em = discord.Embed(description='A list of cards this player has.', color=random_color())
    em.set_author(name=f"{name} (#{tag})")
    em.set_footer(text='Statsy - Powered by cr-api.com')
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    for i, r in found_cards_pages:
        if i:
            em.add_field(name=f'Found Cards ({r})', value=i, inline=False)
    for item in notfound_cards_pages:
        if item:
            em.add_field(name='Missing Cards', value=item, inline=False)
    return em

async def format_battles(ctx, p):
    constants = ctx.bot.constants
    name = p['profile']['name']
    tag = p['profile']['hashtag']

    crapi = 'http://cr-api.com/profile/'
    em = discord.Embed(description='A list of battles played recently', color=random_color())
    em.set_author(name=f"{name} (#{tag})")
    em.set_footer(text='Statsy - Powered by cr-api.com')
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    i = 0
    try:
        battles = p['matches']
        for battle in battles:
            right = []
            left = []
            _type = battle['type'].title()
            score = '-'.join((str(battle['players'][0]['stars']), str(battle['players'][1]['stars'])))
            # -1 = loss
            # 1 = win
            # 0 = draw
            if battle['players'][0]['winner'] == 1: #win
                if battle['players'][0]['stars'] == 3:
                    winner = 'blue3crown'
                else:
                    winner = 'crownblue'
            elif battle['players'][0]['winner'] == 0: #draw
                if battle['players'][0]['stars'] == 3:
                    winner = 'gray3crown'
                winner = 'crowngray'
            elif battle['players'][0]['winner'] == -1: #lose
                if battle['players'][1]['stars'] == 3:
                    winner = 'red3crown'
                else:
                    winner = 'crownred'

            if _type == '2V2':
                _type = '2v2'
                left = [battle['players'][0]['name'], \
                        battle['players'][0]['hashtag'], \
                        battle['players'][2]['name'], \
                        battle['players'][2]['hashtag']]

                right = [battle['players'][1]['name'], \
                        battle['players'][1]['hashtag'] + ')', \
                        battle['players'][3]['name'], \
                        battle['players'][3]['hashtag'] + ')']
                em.add_field(name=f'{_type} {emoji(ctx, winner)} {score}', value=f'**[{left[0]}]({crapi}{left[1]}) {emoji(ctx, "battle")} [{right[0]}]({crapi}{right[1]} \n[{left[2]}]({crapi}{left[3]}) {emoji(ctx, "battle")} [{right[2]}]({crapi}{right[3]}**', inline=False)
            else:
                left = [battle['players'][0]['name'], \
                        battle['players'][0]['hashtag']]

                right = [battle['players'][1]['name'], \
                        battle['players'][1]['hashtag'] + ')']
                em.add_field(name=f'{_type} {emoji(ctx, winner)} {score}', value=f'**[{left[0]}]({crapi}{left[1]}) {emoji(ctx, "battle")} [{right[0]}]({crapi}{right[1]}**', inline=False)
            i += 1
            if i > 5: break
    except AttributeError:
        em.description += '\nToo few battles, fight a tiny bit more to get your battles here!'
    return em

async def format_members(ctx, c, cache=False):
    em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(c.raw_data['updatedTime'])
    em.set_author(name=f"{c.name} (#{c.tag})")
    em.set_thumbnail(url=c.badge_url)
    embeds = []
    counter = 0
    for m in c['members']:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f"{c.name} (#{c.tag})")
            em.set_thumbnail(url=c.badge_url)
        em.add_field(
            name=f'{m.name} ({m.role_name})',
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.crowns} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}"
                  )
        counter += 1
    embeds.append(em)
    return embeds

async def format_top_clans(ctx, clans):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = 'Top 200 global clans right now.'
    em.set_author(name='Top Clans', icon_url=clans[0].badge_url)
    embeds = []
    counter = 0
    for c in clans:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = 'Top 200 global clans right now.'
            em.set_author(name='Top Clans', icon_url=clans[0].badge_url)
        em.add_field(
            name=c.name,
            value=f"#{c.tag}\n{c.trophies} "
                  f"{emoji(ctx, 'trophy')}\nRank: {c.rank} "
                  f"{emoji(ctx, 'rank')}\n{c.member_count}/50 "
                  f"{emoji(ctx, 'clan')}"
                  )
        counter += 1
    embeds.append(em)
    return embeds


async def format_seasons(ctx, p, cache=False):
    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    embeds = []

    if p.seasons:
        for season in p.seasons:
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            if cache:
                em.description = 'Cached data from ' + \
                    timestamp(p.raw_data['updatedTime'])
            em.set_author(name=str(p), icon_url=av)
            em.set_thumbnail(url=emoji(ctx, 'legendarytrophy').url)
            em.add_field(name="Season", value=f"{season.number}")
            em.add_field(name="Season Highest", value=f"{season.highest} {emoji(ctx, 'trophy')}")
            em.add_field(name="Season Finish", value=f"{season.ending} {emoji(ctx, 'trophy')}")
            em.add_field(name="Global Rank", value=f"{season.end_global} {emoji(ctx, 'rank')}")
            embeds.append(em)

    return embeds

async def format_card(ctx, c):
    arenas = {
        0: 'Training Camp',
        1: 'Goblin Stadium',
        2: 'Bone Pit',
        3: 'Barbarian Bowl',
        4: "P.E.K.K.A's Playhouse",
        5: 'Spell Valley',
        6: "Builder's Workshop",
        7: 'Royal Arena',
        8: 'Frozen Peak',
        9: 'Jungle Arena',
        10: 'Hog Mountain'
        }
    em = discord.Embed(description=c.description, color=random_color())
    em.set_thumbnail(url='attachment://ingame.png')
    em.set_author(name=f"{c.name} Info", icon_url='attachment://card.png')
    em.add_field(name='Rarity', value=f"{c.rarity} {emoji(ctx, 'cards')}")
    em.add_field(name='Elixir Cost', value=f"{c.elixir} {emoji(ctx, 'elixirdrop')}")
    em.add_field(name='Type', value=f"{c.type} {emoji(ctx, 'challengedraft')}")
    em.add_field(name='Arena Found', value=f"{arenas[c.arena]} {emoji(ctx, 'arena'+str(c.arena))}")
    em.set_footer(text='Statsy - Powered by cr-api.com')
    return em

async def format_profile(ctx, p, cache=False):
    constants = ctx.bot.constants
    try:
        av = image + 'badge/' + constants.badges[str(p['profile']['alliance']['badge'])] + '.png'
    except:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    arena_image = image + 'arena/arena' + str(p['profile']['arena']) + '.png'
    if p['profile']['arena'] > 12:
        arena_image = image + 'arena/league' + str(p['profile']['arena'] - 11) + '.png'
        if p['profile']['arena'] == 25:
            arena_image = 'https://raw.githubusercontent.com/cr-api/cr-api-assets/master/arena/arena11.png'
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_author(name=f"{p['profile']['name']} (#{p['profile']['hashtag']})", icon_url=av)
    em.set_thumbnail(url=arena_image)

    deck = get_deck(ctx, p)

    chests = get_chests(ctx, p)[0]

    special = ''
    trophies = f"{p['profile']['trophies']}/{p['profile']['maxscore']} PB {emoji(ctx, 'trophy')}"

    s = None
    if p['profile']['previousSeasonTrophies'] != 0:
        s = p
        season = f"Highest: {p['profile']['bestSeasonTrophies']} {emoji(ctx, 'crownblue')}  \n" \
                 f"Finish: {p['profile']['previousSeasonTrophies']} {emoji(ctx, 'trophy')} \n" \
                 f"Global Rank: {p['profile']['bestSeasonRank']} {emoji(ctx, 'rank')}"
    else:
        season = None

    special = get_chests(ctx, p)[1]

    # shop_offers = ''
    # if p.shop_offers.legendary:
    #     shop_offers += f"{emoji(ctx, 'chestlegendary')}+{p.shop_offers.legendary} "
    # if p.shop_offers.epic:
    #     shop_offers += f"{emoji(ctx, 'chestepic')}+{p.shop_offers.epic} "
    # if p.shop_offers.arena:
    #     shop_offers += f"{emoji(ctx, 'arena11')}+{p.shop_offers.arena} "


    embed_fields = [
        ('Trophies', trophies, True),
        ('Level', f"{p['profile']['level']} {emoji(ctx, 'experience')}", True),
        ('Clan Name', f"{p['profile']['alliance']['name']} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Clan Tag', f"#{p['profile']['alliance']['hashtag']} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Clan Role', f"{constants.clan.roles[p['profile']['alliance']['accessLevel']]} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Games Played', f"{p['profile']['games']} {emoji(ctx, 'battle')}", True),
        ('Wins/Losses/Draws', f"{p['profile']['wins']}/{p['profile']['losses']} {p['profile']['games']-p['profile']['wins']-p['profile']['losses']} {emoji(ctx, 'battle')}", True),
        #('Win Streak', f"{p.win_streak} {emoji(ctx, 'battle')}", True),
        ('Three Crown Wins', f"{p['profile']['threeCrownWins']} {emoji(ctx, '3crown')}", True),
        ('Favourite Card', f"{get_card(ctx, p['profile']['favoriteCard'])} {emoji(ctx, get_card(ctx, p['profile']['favoriteCard']))}", True),
        #('Legendary Trophies', f"{p.legend_trophies} {emoji(ctx, 'legendarytrophy')}", True),
        ('Tournament Cards Won', f"{p['profile']['tournament']['cardsWon']} {emoji(ctx, 'cards')}", True),
        ('Challenge Cards Won', f"{p['profile']['challenge']['cardsWon']} {emoji(ctx, 'cards')}", True),
        ('Challenge Max Wins', f"{p['profile']['challenge']['maxWins']} {emoji(ctx, 'tournament')}", True),
        ('Total Donations', f"{p['profile']['donations']} {emoji(ctx, 'cards')}", True),
        #('Global Rank', f"{p.global_rank} {emoji(ctx, 'crownred')}", True),
        ('Battle Deck', deck, True),
        (f'Chests', chests, False),
        ('Chests Until', special, True),
        #('Shop Offers (Days)', shop_offers, False),
        (f'Previous Season Results' if s else None, season, False),
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value=f"None {emoji(ctx, 'noclan')}")

    em.set_footer(text='Statsy - Powered by cr-api.com')

    return em

async def format_stats(ctx, p, cache=False):

    constants = ctx.bot.constants
    try:
        av = image + 'badge/' + constants.badges[str(p['profile']['alliance']['badge'])] + '.png'
    except:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    arena_image = image + 'arena/arena' + str(p['profile']['arena']) + '.png'
    if p['profile']['arena'] > 12:
        arena_image = image + 'arena/league' + str(p['profile']['arena'] - 11) + '.png'
        if p['profile']['arena'] == 25:
            arena_image = 'https://raw.githubusercontent.com/cr-api/cr-api-assets/master/arena/arena11.png'
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_author(name=f"{p['profile']['name']} (#{p['profile']['hashtag']})", icon_url=av)
    em.set_thumbnail(url=arena_image)

    deck = get_deck(ctx, p)
    trophies = f"{p['profile']['trophies']}/{p['profile']['maxscore']} PB {emoji(ctx, 'trophy')}"

    embed_fields = [
        ('Trophies', trophies, True),
        ('Level', f"{p['profile']['level']} {emoji(ctx, 'experience')}", True),
        ('Clan Name', f"{p['profile']['alliance']['name']} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Clan Tag', f"#{p['profile']['alliance']['hashtag']} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Clan Role', f"{constants.clan.roles[p['profile']['alliance']['accessLevel']]} {emoji(ctx, 'clan')}" if p['profile']['alliance']['hashtag'] else None, True),
        ('Favourite Card', f"{get_card(ctx, p['profile']['favoriteCard'])} {emoji(ctx, get_card(ctx, p['profile']['favoriteCard']))}", True),
        ('Battle Deck', deck, True),
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value=f"None {emoji(ctx, 'noclan')}")

    em.set_footer(text='Statsy - Powered by cr-api.com')

    return em

async def format_clan(ctx, c, cache=False):
    constants = ctx.bot.constants
    c = c['alliance']
    page1 = discord.Embed(description=c['description'], color=random_color())
    page1.set_author(name=f"{c['header']['name']} (#{c['hashtag']})")
    page1.set_footer(text='Statsy - Powered by cr-api.com')
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Donators/Contributors for this clan.'
    try:
        page1.set_thumbnail(url=image + 'badge/' + constants.badges[str(c['header']['badge'])] + '.png')
    except:
        pass

    contributors = list(reversed(sorted(c['members'], key=lambda x: x['clanChestCrowns'])))
    _donators = list(reversed(sorted(c['members'], key=lambda m: m['donations'])))

    pushers = []
    donators = []
    ccc = []

    if len(c['members']) >= 3:
        for i in range(3):
            pushers.append(
                f"**{c['members'][i]['name']}**"
                f"\n{c['members'][i]['score']} "
                f"{emoji(ctx, 'trophy')}\n"
                f"#{c['members'][i]['hashtag']}"
                )
            donators.append(
                f"**{_donators[i]['name']}**"
                f"\n{_donators[i]['donations']} "
                f"{emoji(ctx, 'cards')}\n"
                f"#{_donators[i]['hashtag']}"
                )
            ccc.append(
                f"**{contributors[i]['name']}**"
                f"\n{contributors[i]['clanChestCrowns']} "
                f"{emoji(ctx, 'crownred')}\n"
                f"#{contributors[i]['hashtag']}"
                )

    fields1 = [
        #('Type', c.type_name + ' 📩'),
        ('Score', str(c['header']['score']) + ' Trophies ' + str(emoji(ctx, 'trophy'))),
        ('Donations/Week', str(c['header']['donations']) + ' Cards ' + str(emoji(ctx, 'cards'))),
        #('Clan Chest', str(c.clan_chest.crowns) + '/' + str(c.clan_chest.required) + ' '+str(emoji(ctx, 'chestclan'))),
        ('Location', constants.country_codes[c['header']['region']].name + ' 🌎'),
        ('Members', str(len(c['members'])) + f"/50 {emoji(ctx, 'clan')}"),
        ('Required Trophies', f"{c['header']['requiredScore']} {emoji(ctx, 'trophy')}"),
        #('Global Rank', f"{'Unranked' if c.rank == 0 else c.rank} {emoji(ctx, 'rank')}")
    ]

    fields2 = [
        ("Top Players", '\n\n'.join(pushers)),
        ("Top Donators", '\n\n'.join(donators)),
        ("Top Contributors", '\n\n'.join(ccc))
    ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    for f, v in fields2:
        if v:
            page2.add_field(name=f, value=v)


    return [page1, page2]

async def format_tournaments(ctx, json, cache=False):
    rewards = {
        50: (175, 25, 10),
        100: (700, 100, 20),
        200: (400, 57, 40),
        1000: (2000, 285, 200)
    }
    em = discord.Embed(description='A list of open tournaments you can join right now!', color=random_color())
    em.set_author(name='Open Tournaments')
    em.set_thumbnail(url='https://i.imgur.com/bwql3WU.png')
    if ctx.bot.psa_message:
        em.description = ctx.bot.psa_message
    em.set_footer(text='Statsy - Powered by statsroyale.com')
    tourneys = sorted(json['tournaments'], key=lambda x: int(x['maxPlayers']))
    i = 0
    for tournament in tourneys:
        if tournament['full']: continue
        members = '/'.join((str(tournament['totalPlayers']), str(tournament['maxPlayers'])))
        tag = tournament['hashtag']
        name = tournament['title']
        timeleft = ''
        date = (datetime.datetime.fromtimestamp(tournament['timeLeft'] + int(time.time()))) - datetime.datetime.now()
        seconds = math.floor(date.total_seconds())
        minutes = max(math.floor(seconds/60), 0)
        seconds -= minutes*60
        hours = max(math.floor(minutes/60), 0)
        minutes -= hours*60
        if hours > 0: timeleft += f'{hours}h'
        if minutes > 0: timeleft += f' {minutes}m'
        if seconds > 0: timeleft += f' {seconds}s'
        gold = rewards[tournament['maxPlayers']][1]
        cards = rewards[tournament['maxPlayers']][0]

        em.add_field(name=f'{name}', value=f'Time left: {timeleft}\n{members} {emoji(ctx, "clan")}\n{gold} {emoji(ctx, "gold")}\n{cards} {emoji(ctx, "cards")}\n#{tag}')
        i += 1
        if i > 11: break

    return em