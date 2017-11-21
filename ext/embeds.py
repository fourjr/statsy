import discord
from collections import OrderedDict
import json
import random
import copy

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
    for card in p.deck:
        deck += str(emoji(ctx, card.name)) + str(card.level) + ' '
    return deck

async def format_least_valuable(ctx, clan):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3
    to_kick = sorted(clan.members, key=lambda m: m.score)[:4]

    em = discord.Embed(
        color=random_color(), 
        description='Here are the least valuable members of the clan currently.'
        )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
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

async def format_most_valuable(ctx, clan):
    
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3

    best = sorted(clan.members, key=lambda m: m.score, reverse=True)[:4]

    em = discord.Embed(
        color=random_color(), 
        description='Here are the most valuable members of the clan currently.'
        )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
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



def get_chests(ctx, p):
    cycle = p.chest_cycle
    pos = cycle.position
    chests = '| '+str(emoji(ctx, 'chest' + p.get_chest(0).lower())) + ' | '
    chests += ''.join([str(emoji(ctx, 'chest' + p.get_chest(x).lower())) for x in range(1,10)])
    special = ''
    for i, attr in enumerate(cdir(cycle)):
        if attr != 'position':
            e = emoji(ctx, 'chest'+attr.replace('_',''))
            if getattr(cycle, attr):
                c_pos = int(getattr(cycle, attr))
                until = c_pos-pos
                special += f'{e}+{until} '
    return (chests, special)

async def format_deck(ctx, p):
    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color(), description=get_deck(ctx, p))
    em.set_author(name=p, icon_url=av)
    em.title = 'Battle Deck'
    em.set_thumbnail(url=emoji(ctx, p.favourite_card).url)
    em.set_footer(text='Statsy - Powered by cr-api.com')
    return em

async def format_chests(ctx, p):
    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    em.set_author(name=p, icon_url=av)
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_thumbnail(url=emoji(ctx, 'chest' + p.get_chest(0).lower()).url)
    em.add_field(name=f'Chests ({p.chest_cycle.position} opened)', value=get_chests(ctx, p)[0])
    em.add_field(name="Chests Until", value=get_chests(ctx, p)[1])
    em.set_footer(text='Statsy - Powered by cr-api.com')
    return em

async def format_members(ctx, c):
    em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f"{c.name} (#{c.tag})")
    em.set_thumbnail(url=c.badge_url)
    embeds = []
    counter = 0
    for m in c.members:
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


async def format_seasons(ctx, p):
    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    embeds = []

    if p.seasons:
        for season in p.seasons:
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
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

async def format_profile(ctx, p):

    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=str(p), icon_url=av)
    em.set_thumbnail(url=p.arena.image_url)

    deck = get_deck(ctx, p)

    chests = get_chests(ctx, p)[0]

    cycle = p.chest_cycle

    pos = cycle.position
    special = ''
    trophies = f"{p.current_trophies}/{p.highest_trophies} PB {emoji(ctx, 'trophy')}"

    s = None
    if p.seasons:
        s = p.seasons[0]
        global_r = s.end_global
        season = f"Highest: {s.highest} {emoji(ctx, 'crownblue')}  \n" \
                 f"Finish: {s.ending} {emoji(ctx, 'trophy')} \n" \
                 f"Global Rank: {global_r} {emoji(ctx, 'rank')}" 
    else:
        season = None


    special = get_chests(ctx, p)[1]

    shop_offers = ''
    if p.shop_offers.legendary:
        shop_offers += f"{emoji(ctx, 'chestlegendary')}+{p.shop_offers.legendary} " 
    if p.shop_offers.epic:
        shop_offers += f"{emoji(ctx, 'chestepic')}+{p.shop_offers.epic} "
    if p.shop_offers.arena:
        shop_offers += f"{emoji(ctx, 'arena11')}+{p.shop_offers.arena} "


    embed_fields = [
        ('Trophies', trophies, True),
        ('Level', f"{p.level} ({'/'.join(str(x) for x in p.experience)}) {emoji(ctx, 'experience')}", True),
        ('Clan Name', f"{p.clan_name} {emoji(ctx, 'clan')}" if p.clan_name else None, True),
        ('Clan Tag', f"#{p.clan_tag} {emoji(ctx, 'clan')}" if p.clan_tag else None, True),
        ('Clan Role', f"{p.clan_role} {emoji(ctx, 'clan')}" if p.clan_role else None, True),
        ('Games Played', f"{p.games_played} {emoji(ctx, 'battle')}", True),
        ('Wins/Losses/Draws', f"{p.wins}/{p.losses}/{p.draws} {emoji(ctx, 'battle')}", True),
        ('Win Streak', f"{p.win_streak} {emoji(ctx, 'battle')}", True),
        ('Three Crown Wins', f"{p.three_crown_wins} {emoji(ctx, '3crown')}", True),
        ('Favourite Card', f"{p.favourite_card.replace('_',' ')} {emoji(ctx, p.favourite_card)}", True),
        ('Legendary Trophies', f"{p.legend_trophies} {emoji(ctx, 'legendarytrophy')}", True),
        ('Tournament Cards Won', f"{p.tournament_cards_won} {emoji(ctx, 'cards')}", True),
        ('Challenge Cards Won', f"{p.challenge_cards_won} {emoji(ctx, 'cards')}", True),
        ('Challenge Max Wins', f"{p.max_wins} {emoji(ctx, 'tournament')}", True),
        ('Total Donations', f"{p.total_donations} {emoji(ctx, 'cards')}", True),
        ('Global Rank', f"{p.global_rank} {emoji(ctx, 'crownred')}", True),
        ('Battle Deck', deck, True),
        (f'Chests ({pos} opened)', chests, False),
        ('Chests Until', special, True),
        ('Shop Offers (Days)', shop_offers, False),
        (f'Previous Season Results ({s.number})' if s else None, season, False),
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value=f"None {emoji(ctx, 'noclan')}")

    em.set_footer(text='Statsy - Powered by cr-api.com')
    
    return em

async def format_clan(ctx, c):
    page1 = discord.Embed(description = c.description, color=random_color())
    page1.set_author(name=f"{c.name} (#{c.tag})")
    page1.set_footer(text='Statsy - Powered by cr-api.com')
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Donators/Contributors for this clan.'
    page1.set_thumbnail(url=c.badge_url)
    
    contributors = list(reversed(sorted(c.members, key=lambda x: x.crowns)))
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

    if len(c.members) >= 3:
        for i in range(3):
            donators.append(
                f"**{_donators[i].name}**"
                f"\n{_donators[i].donations} "
                f"{emoji(ctx, 'cards')}\n" 
                f"#{_donators[i].tag}"
                )
    
    if len(c.members) >= 3:
        for i in range(3):
            ccc.append(
                f"**{contributors[i].name}**" 
                f"\n{contributors[i].crowns} " 
                f"{emoji(ctx, 'crownred')}\n" 
                f"#{contributors[i].tag}"
                )

    fields1 = [
        ('Type', c.type_name + ' 📩'),
        ('Score', str(c.score) + ' Trophies ' + str(emoji(ctx, 'trophy'))),
        ('Donations/Week', str(c.donations) + ' Cards ' + str(emoji(ctx, 'cards'))),
        ('Clan Chest', str(c.clan_chest.crowns) + '/' + str(c.clan_chest.required) + ' '+str(emoji(ctx, 'chestclan'))),
        ('Location', c.region + ' 🌎'),
        ('Members', str(len(c.members)) + f"/50 {emoji(ctx, 'clan')}"),
        ('Required Trophies', f"{c.required_trophies} {emoji(ctx, 'trophy')}"),
        ('Global Rank', f"{'Unranked' if c.rank == 0 else c.rank} {emoji(ctx, 'rank')}")
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

