import discord
from collections import OrderedDict
import json
import random
import copy
import datetime
import math
import time
from discord.ext import commands

images = 'https://cr-api.github.io/cr-api-assets/'

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

def get_deck(ctx, p):
    deck = ''
    for card in p.current_deck:
        deck += str(emoji(ctx, card.name)) + str(card.level) + ' '
    return deck

def timestamp(datatime:int):
    return str(int((datetime.datetime.utcfromtimestamp(datatime) - datetime.datetime.utcnow()).total_seconds()/60)) + ' minutes ago'

def get_clan_image(p):
    try:
        return p.clan.badge.image
    except:
        return 'https://i.imgur.com/Y3uXsgj.png'

async def format_least_valuable(ctx, clan, cache=False):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.clan_chest_crowns*10) + (m.trophies/7)) / 3
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
    em.set_thumbnail(url=clan.badge.image)
    em.set_footer(text='Statsy - Powered by cr-api.com')

    for m in reversed(to_kick):
        em.add_field(
            name=f'{m.name} ({m.role_name})', 
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}"
                  )
    return em

async def format_most_valuable(ctx, clan, cache=False):
    
    for m in clan.members:
        m.score = ((m.donations/5) + (m.clan_chest_crowns*10) + (m.trophies/7)) / 3

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
    em.set_thumbnail(url=clan.badge.image)
    em.set_footer(text='Statsy - Powered by cr-api.com')

    for m in reversed(best):
        em.add_field(
            name=f'{m.name} ({m.role_name})', 
            value=f"#{m.tag}\n{m.trophies} "
            f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns} "
            f"{emoji(ctx, 'crownblue')}\n{m.donations} "
            f"{emoji(ctx, 'cards')}"
            )

    return em

def get_chests(ctx, p):
    cycle = p.chest_cycle
    chests = '| '+str(emoji(ctx, 'chest' + p.chest_cycle.upcoming[0].lower())) + ' | '
    chests += ''.join([str(emoji(ctx, 'chest' + p.chest_cycle.upcoming[x].lower())) for x in range(1,8)])
    special = ''
    special_chests = ['superMagical', 'magical', 'legendary', 'epic', 'giant']
    for i in special_chests:
        e = emoji(ctx, 'chest' + i.lower())
        special += f"{e}+{p.chest_cycle[i]} "
    return (chests, special)

async def format_chests(ctx, p, cache=False):
    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    em.set_author(name=p, icon_url=av)
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_thumbnail(url=emoji(ctx, 'chest' + p.chest_cycle.upcoming[0].lower()).url)
    em.add_field(name=f'Chests', value=get_chests(ctx, p)[0])
    em.add_field(name="Chests Until", value=get_chests(ctx, p)[1])
    em.set_footer(text='Statsy - Powered by cr-api.com')
    return em

async def format_cards(ctx, soup):
    constants = ctx.bot.constants
    profile = soup.find('div', attrs={'class':'layout__page'}) \
            .find('div', attrs={'class':'layout__content layout__container'}) \
            .find('div', attrs={'class':'profile ui__card'})

    name = profile.find('div', attrs={'class':'profileHeader profile__header'}) \
            .find('div', attrs={'class':'ui__headerMedium profileHeader__name'}).getText().strip() \
            \
            .strip(profile.find('div', attrs={'class':'profileHeader profile__header'}) \
            .find('div', attrs={'class':'ui__headerMedium profileHeader__name'}) \
            .find('span', attrs={'class':'profileHeader__userLevel'}).getText().strip())

    tag = profile.find('div', attrs={'class':'profileTabs profile__tabs'}) \
            .find('a', attrs={'class':'ui__mediumText ui__link ui__tab '}) \
            ['href'].strip('/profile/')

    rarity = {
        'Common': 1,
        'Rare': 2,
        'Epic': 3,
        'Legendary': 4
    }
    found_cards = profile.find('div', attrs={'class':'cards__group'}) \
                .find('div', attrs={'class':'profileCards__cards'}) \
                .find_all('div')

    notfound_cards = profile.find_all('div', attrs={'class':'cards__group'})[1] \
                    .find('div', attrs={'class':'profileCards__cards'}) \
                    .find_all('div')

    def get_rarity(card):
        try:
            return constants.cards[card.find('a')['href'].lower().replace('/card/', '').replace('+', ' ').replace('.', '').replace('-', '')].rarity
        except TypeError:
            return 10495

    def get_rarity_s(card):
        for a in constants.cards:
            if constants.cards[a].raw_data['key'].replace('-', '') == card:
                return constants.cards[a].rarity
        return 10495

    def key(x):
        val = get_rarity(x)
        if val == 10495: return val
        else: return rarity[val]

    found_cards = sorted(found_cards, key=key)
    notfound_cards = sorted(notfound_cards, key=key)

    fmt = ''
    found_cards_pages = []
    oldcard = ''
    for card in found_cards:
        if card is None: continue
        try:
            txt = card.find('div', attrs={'class':'ui__tooltip ui__tooltipTop ui__tooltipMiddle cards__tooltip'}) \
            .getText().strip()
        except:
            continue

        if get_rarity(oldcard) != get_rarity(card):
            try:
                found_cards_pages.append((fmt, get_rarity_s(fmt.split(':')[1])))
            except IndexError:
                found_cards_pages.append((fmt, fmt.split(':')[0]))
            fmt = str(emoji(ctx, txt))
        else:
            fmt += str(emoji(ctx, txt))
            if len(fmt) > 1024:
                fmt = fmt.replace(str(emoji(ctx, txt)), '')
                try:
                    found_cards_pages.append((fmt, get_rarity_s(fmt.split(':')[1])))
                except IndexError:
                    found_cards_pages.append((fmt, fmt.split(':')[0]))
                fmt = str(emoji(ctx, txt))
        oldcard = card
    try:
        found_cards_pages.append((fmt, get_rarity_s(fmt.split(':')[1])))
    except IndexError:
        found_cards_pages.append((fmt, fmt.split(':')[0]))

    fmt = ''
    notfound_cards_pages = []
    for card in notfound_cards:
        if card is None: continue
        try:
            txt = card.find('div', attrs={'class':'ui__tooltip ui__tooltipTop ui__tooltipMiddle cards__tooltip'}) \
            .getText().strip()
        except:
            continue
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

async def format_battles(ctx, soup):
    constants = ctx.bot.constants
    profile = soup.find('div', attrs={'class':'layout__page'}) \
            .find('div', attrs={'class':'layout__content layout__container'}) \
            .find('div', attrs={'class':'profile ui__card'})

    name = profile.find('div', attrs={'class':'profileHeader profile__header'}) \
            .find('div', attrs={'class':'ui__headerMedium profileHeader__name'}).getText().strip() \
            \
            .strip(profile.find('div', attrs={'class':'profileHeader profile__header'}) \
            .find('div', attrs={'class':'ui__headerMedium profileHeader__name'}) \
            .find('span', attrs={'class':'profileHeader__userLevel'}).getText().strip())

    tag = profile.find('div', attrs={'class':'profileTabs profile__tabs'}) \
            .find('a', attrs={'class':'ui__mediumText ui__link ui__tab '}) \
            ['href'].strip('/profile/')

    crapi = 'http://cr-api.com/profile/'
    em = discord.Embed(description='A list of battles played recently', color=random_color())
    em.set_author(name=f"{name} (#{tag})")
    em.set_footer(text='Statsy - Powered by cr-api.com')
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    i = 0
    try:
        battles = profile.find('div', attrs={'class':'replay profile__replays'}) \
                .find_all('div', attrs={'class':'replay__container'})
        for battle in battles:
            right = []
            left = []
            _type = battle['data-type'].title()
            score = battle.find('div', attrs={'class':'replay__header'}) \
                    .find('div', attrs={'class':'replay__record'}).getText().strip()
            sc = score.split('-')
            if int(sc[0]) > int(sc[1]):
                if int(sc[0]) == 3:
                    winner = 'blue3crown'
                else:
                    winner = 'crownblue'
            elif int(sc[1]) > int(sc[0]):
                if int(sc[1]) == 3:
                    winner = 'red3crown'
                else:
                    winner = 'crownred'
            else:
                if int(sc[0]) == 3:
                    winner = 'gray3crown'
                winner = 'crowngray'
            match = battle.find('div', attrs={'class':'replay__match'})
            left.append(match.find('div', attrs={'class':'replay__player replay__leftPlayer'}) \
                    .find('div', attrs={'class':'replay__playerName'}) \
                    .find('div', attrs={'class':'replay__userInfo'}) \
                    .find('div', attrs={'class':'replay__userName'}))
            left.append(left[0].getText().strip())
            try:
                left.append(left[0].find('a', attrs={'class':'ui__link'}) \
                    ['href'].replace('/profile/', ''))
            except KeyError:
                continue

            right.append(match.find('div', attrs={'class':'replay__player replay__rightPlayer'}) \
                    .find('div', attrs={'class':'replay__playerName'}) \
                    .find('div', attrs={'class':'replay__userInfo'}) \
                    .find('div', attrs={'class':'replay__userName'}))
            right.append(right[0].getText().strip())
            try:
                right.append(right[0].find('a', attrs={'class':'ui__link'}) \
                    ['href'].replace('/profile/', ''))
            except KeyError:
                continue
            else:
                if right[2] is not None: right[2] += ')'

            if _type == '2V2':
                _type = '2v2'

                try:
                    left.append(match.find('div', attrs={'class':'replay__player replay__leftPlayer'}) \
                    .find('div', attrs={'class':'replay__playerName'}) \
                    .find('div', attrs={'class':'replay__userInfo'}) \
                    .find_all('div', attrs={'class':'replay__userName'})[1])
                    left.append(left[3].getText().strip())
                    left.append(left[3].find('a', attrs={'class':'ui__link'}) \
                        ['href'].replace('/profile/', ''))
                except KeyError:
                    continue
                try:
                    right.append(match.find('div', attrs={'class':'replay__player replay__rightPlayer'}) \
                            .find('div', attrs={'class':'replay__playerName'}) \
                            .find('div', attrs={'class':'replay__userInfo'}) \
                            .find_all('div', attrs={'class':'replay__userName'})[1])
                    right.append(right[3].getText().strip())
                    right.append(right[3].find('a', attrs={'class':'ui__link'}) \
                        ['href'].replace('/profile/', ''))
                except KeyError:
                    continue
                else:
                    if right[5] is not None: right[5] += ')'

                em.add_field(name=f'{_type} {emoji(ctx, winner)} {score}', value=f'**[{left[1]}]({crapi}{left[2]}) {emoji(ctx, "battle")} [{right[1]}]({crapi}{right[2]} \n[{left[4]}]({crapi}{left[5]}) {emoji(ctx, "battle")} [{right[4]}]({crapi}{right[5]}**', inline=False)
            else:
                em.add_field(name=f'{_type} {emoji(ctx, winner)} {score}', value=f'**[{left[1]}]({crapi}{left[2]}) {emoji(ctx, "battle")} [{right[1]}]({crapi}{right[2]}**', inline=False)
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
    em.set_thumbnail(url=c.badge.image)
    embeds = []
    counter = 0
    for m in c.members:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f"{c.name} (#{c.tag})")
            em.set_thumbnail(url=c.badge.image)
        em.add_field(
            name=f'{m.name} ({m.role.title()})', 
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns} "
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
    em.set_author(name='Top Clans', icon_url=clans[0].badge.image)
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
            value=f"#{c.tag}\n{c.score} "
                  f"{emoji(ctx, 'trophy')}\nRank: {c.rank} "
                  f"{emoji(ctx, 'rank')}\n{c.member_count}/50 "
                  f"{emoji(ctx, 'clan')}"
                  )
        counter += 1
    embeds.append(em)
    return embeds


async def format_seasons(ctx, p, cache=False):
    av = get_clan_image(p)
    embeds = []
    if p.league_statistics:
        for season in p.league_statistics.to_dict().keys():
            s = p.league_statistics[season]
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            if cache:
                em.description = 'Cached data from ' + \
                    timestamp(p.raw_data['updatedTime'])
            em.set_author(name=str(p), icon_url=av)
            em.set_thumbnail(url=emoji(ctx, 'legendarytrophy').url)
            try: 
                em.add_field(name=season.strip('Season').title() + " Season", value=s.id)
            except: 
                prev = p.league_statistics.previous_season
                old_time = prev.id.split('-')
                time = [int(old_time[0]), int(old_time[1]) + 1]
                if time[1] > 12: #check month
                    time[0] += 1
                    time[1] = 1
                em.add_field(name=season.strip('Season').title() + " Season", value=f'{time[0]}-{time[1]}')
            try: em.add_field(name="Season Highest", value=f"{s.best_trophies} {emoji(ctx, 'trophy')}")
            except: pass
            try: em.add_field(name="Season Finish", value=f"{s.trophies} {emoji(ctx, 'trophy')}")
            except: pass
            try: em.add_field(name="Global Rank", value=f"{s.rank} {emoji(ctx, 'rank')}")
            except: pass

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

    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_author(name=str(p), icon_url=av)
    em.set_thumbnail(url=images + 'arenas/arena' + str(p.arena.arena_id) + '.png')

    deck = get_deck(ctx, p)

    chests = get_chests(ctx, p)[0]

    cycle = p.chest_cycle

    special = ''
    trophies = f"{p.trophies}/{p.stats.max_trophies} PB {emoji(ctx, 'trophy')}"

    s = None
    if p.league_statistics:
        current_rank = p.league_statistics.current_season.rank
        s = p.league_statistics.previous_season
        global_r = s.rank
        season = f"Highest: {s.best_trophies} {emoji(ctx, 'crownblue')}  \n" \
                 f"Finish: {s.trophies} {emoji(ctx, 'trophy')} \n" \
                 f"Global Rank: {global_r} {emoji(ctx, 'rank')}" 
    else:
        current_rank = None
        season = None

    if p.clan:
        clan_role = p.clan.role.title()
    else:
        clan_role = None

    special = get_chests(ctx, p)[1]

    embed_fields = [
        ('Trophies', trophies, True),
        ('Level', f"{p.level} {emoji(ctx, 'experience')}", True),
        ('Clan Name', f"{p.clan.name} {emoji(ctx, 'clan')}" if p.clan else None, True),
        ('Clan Tag', f"#{p.clan.tag} {emoji(ctx, 'clan')}" if p.clan else None, True),
        ('Clan Role', f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        ('Games Played', f"{p.games.total} {emoji(ctx, 'battle')}", True),
        ('Wins/Losses/Draws', f"{p.games.wins}/{p.games.losses}/{p.games.draws} {emoji(ctx, 'battle')}", True),
        ('Three Crown Wins', f"{p.stats.three_crown_wins} {emoji(ctx, '3crown')}", True),
        ('Favourite Card', f"{p.stats.favorite_card.name} {emoji(ctx, p.stats.favorite_card.key.replace('-', ''))}", True),
        ('Tournament Cards Won', f"{p.stats.tournament_cards_won} {emoji(ctx, 'cards')}", True),
        ('Challenge Cards Won', f"{p.stats.challenge_cards_won} {emoji(ctx, 'cards')}", True),
        ('Challenge Max Wins', f"{p.stats.challenge_max_wins} {emoji(ctx, 'tournament')}", True),
        ('Total Donations', f"{p.stats.total_donations} {emoji(ctx, 'cards')}", True),
        ('Global Rank', f"{current_rank} {emoji(ctx, 'crownred')}" if current_rank else None, True),
        ('Battle Deck', deck, True),
        (f'Chests', chests, False),
        ('Chests Until', special, True),
        (f'Previous Season Results ({s.id})' if s else None, season, False),
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

    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    if cache:
        em.description = 'Cached data from ' + \
            timestamp(p.raw_data['updatedTime'])
    em.set_author(name=str(p), icon_url=av)
    em.set_thumbnail(url=images + 'arenas/arena' + str(p.arena.arena_id) + '.png')

    trophies = f"{p.trophies}/{p.stats.max_trophies} PB {emoji(ctx, 'trophy')}"
    deck = get_deck(ctx, p)

    if p.clan:
        clan_role = p.clan.role.title()
    else:
        clan_role = None

    embed_fields = [
        ('Trophies', trophies, True),
        ('Level', f"{p.level} {emoji(ctx, 'experience')}", True),
        ('Clan Name', f"{p.clan.name} {emoji(ctx, 'clan')}" if p.clan else None, True),
        ('Clan Tag', f"#{p.clan.tag} {emoji(ctx, 'clan')}" if p.clan else None, True),
        ('Clan Role', f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        ('Favourite Card', f"{p.stats.favorite_card.name} {emoji(ctx, p.stats.favorite_card.key.replace('-', ''))}", True),
        ('Battle Deck', deck, True)
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
    page1 = discord.Embed(description = c.description, color=random_color())
    page1.set_author(name=f"{c.name} (#{c.tag})")
    page1.set_footer(text='Statsy - Powered by cr-api.com')
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Donators/Contributors for this clan.'
    page1.set_thumbnail(url=c.badge.image)
    
    contributors = list(reversed(sorted(c.members, key=lambda x: x.clan_chest_crowns)))
    _donators = list(reversed(sorted(c.members, key=lambda m: m.donations)))

    pushers = []
    donators = []
    ccc = []

    if len(c.members) >= 3:
        for i in range(3):
            pushers.append(
                f"**{c.members[i].name}**" 
                f"\n{c.members[i].trophies} " 
                f"{emoji(ctx, 'trophy')}\n" 
                f"#{c.members[i].tag}"
                )
            donators.append(
                f"**{_donators[i].name}**"
                f"\n{_donators[i].donations} "
                f"{emoji(ctx, 'cards')}\n" 
                f"#{_donators[i].tag}"
                )
            ccc.append(
                f"**{contributors[i].name}**" 
                f"\n{contributors[i].clan_chest_crowns} " 
                f"{emoji(ctx, 'crownred')}\n" 
                f"#{contributors[i].tag}"
                )

    fields1 = [
        ('Type', c.type.title() + ' 📩'),
        ('Score', str(c.score) + ' Trophies ' + str(emoji(ctx, 'trophy'))),
        ('Donations/Week', str(c.donations) + ' Cards ' + str(emoji(ctx, 'cards'))),
        ('Clan Chest', c.clan_chest.status.title() + ' ' + str(emoji(ctx, 'chestclan'))),
        ('Location', c.location.name + ' 🌎'),
        ('Members', str(len(c.members)) + f"/50 {emoji(ctx, 'clan')}"),
        ('Required Trophies', f"{c.required_score} {emoji(ctx, 'trophy')}"),
        #('Global Rank', f"{'Unranked' if c.rank is None else c.rank} {emoji(ctx, 'rank')}") 
        # **I have no idea if cr-api has this
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