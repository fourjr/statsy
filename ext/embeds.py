import discord
from collections import OrderedDict
import json
import random

def emoji(ctx, name):
    name = name.replace('.','').lower().replace(' ','').replace('_','')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.cremojis, name=name)
    return e

def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]

def random_color():
    random_colors = [
        'blue', 'blurple', 'dark_blue', 'dark_gold', 
            'dark_green', 'dark_grey', 'dark_magenta', 
            'dark_orange', 'dark_purple', 'dark_red', 
            'dark_teal', 'darker_grey', 'default', 'gold', 
            'green', 'greyple', 'light_grey', 'lighter_grey', 
            'magenta', 'orange', 'purple', 'red', 'teal'
            ] # (Good Colors)
    c = random.choice(random_colors)

    return getattr(discord.Color, c)()

def get_deck(ctx, p):
    deck = ''
    for card in p.deck:
        deck += str(emoji(ctx, card.name)) + str(card.level) + ' '
    return deck

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
    em.set_footer(text='CR-Stats - Powered by cr-api.com')
    return em

async def format_chests(ctx, p):
    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color(), description=p.tag)
    em.set_author(name=p, icon_url=av)
    em.title = 'Chests'
    em.set_thumbnail(url=emoji(ctx, 'chest' + p.get_chest(0).lower()).url)
    em.add_field(name=f'Chests ({p.chest_cycle.position} opened)', value=get_chests(ctx, p)[0])
    em.add_field(name="Chests Until", value=get_chests(ctx, p)[1])
    em.set_footer(text='CR-Stats - Powered by cr-api.com')
    return em

async def format_profile(ctx, p):


    av = p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png'
    color = 0x00FFFF
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p.name} (#{p.tag})", icon_url=av)
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
        ('Clan Name', p.clan_name, True),
        ('Clan Tag', f'#{p.clan_tag}' if p.clan_tag else None, True),
        ('Clan Role', p.clan_role, True),
        ('Games Played', f"{p.games_played} {emoji(ctx, 'battle')}", True),
        ('Wins/Losses/Draws', f"{p.wins}/{p.losses}/{p.draws} {emoji(ctx, 'battle')}", True),
        ('Win Streak', f"{p.win_streak} {emoji(ctx, 'battle')}", True),
        ('Three Crown Wins', f"{p.three_crown_wins} {emoji(ctx, 'crownblue')}", True),
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
        ('Shop Offers (Days)', shop_offers, True),
        (f'Previous Season Results ({s.number})' if s else None, season, False),
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value='No Clan')

    em.set_footer(text='CR-Stats - Powered by cr-api.com')
    
    return em

async def format_clan(ctx, c):
    embed = discord.Embed(description = c.description, color=random_color())
    embed.set_author(name=f"{c.name} (#{c.tag})")
    embed.set_thumbnail(url=c.badge_url)

    pushers = []
    for i in range(3):
        pushers.append(f"{c.members[i].name}: {c.members[i].trophies} {emoji(ctx, 'trophy')}\n#{c.members[i].tag}")

    contributors = list(reversed(sorted(c.members, key=lambda x: x.crowns)))
    ccc = []

    for i in range(3):
        ccc.append(f"{c.members[i].name}: {c.members[i].crowns} {emoji(ctx, 'crownred')}\n#{c.members[i].tag}")

    embeddict = OrderedDict({
        'Type': c.type_name,
        'Score': str(c.score) + ' Trophies ' + str(emoji(ctx, 'trophy')),
        'Donations/Week': str(c.donations) + ' Cards ' + str(emoji(ctx, 'cards')),
        'Clan Chest': str(c.clan_chest.crowns) + '/' + str(c.clan_chest.required) + ' '+str(emoji(ctx, 'crownblue')),
        'Location': c.region,
        'Members': str(len(c.members)) + '/50',
        'Top Players': '\n\n'.join(pushers),
        'Top Contributors': '\n\n'.join(ccc)
        })

    for f, v in embeddict.items():
        embed.add_field(name=f, value=v)

    embed.set_footer(text='CR-Stats - Powered by cr-api.com')
    
    return embed

