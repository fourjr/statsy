import discord
from collections import OrderedDict
import json
import random
import copy

def emoji(ctx, name):
    name = name.replace('.','').lower().replace(' ','').replace('_','').replace('-','')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.cremojis, name=name)
    return e

def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]

def random_color():
    return random.randint(0, 0xFFFFFF)

async def format_least_valuable(ctx, clan):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3

    to_kick = sorted(clan.members, key=lambda m: m.score)[:4]

    em = discord.Embed(color=random_color(), description='Here are the least valuable members of the clan currently.')
    em.set_author(name=clan)
    em.set_thumbnail(url=clan.badge_url)
    em.set_footer(text='StatsOverflow - Powered by cr-api.com')

    for m in reversed(to_kick):
        em.add_field(name=f'{m.name} ({m.role_name})', value=f"#{m.tag}\n{m.trophies} {emoji(ctx, 'trophy')}\n{m.crowns} {emoji(ctx, 'crownblue')}\n{m.donations} {emoji(ctx, 'cards')}")

    return em

async def format_most_valuable(ctx, clan):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3

    best = sorted(clan.members, key=lambda m: m.score, reverse=True)[:4]

    em = discord.Embed(color=random_color(), description='Here are the most valuable members of the clan currently.')
    em.set_author(name=clan)
    em.set_thumbnail(url=clan.badge_url)
    em.set_footer(text='StatsOverflow - Powered by cr-api.com')

    for m in reversed(best):
        em.add_field(name=f'{m.name} ({m.role_name})', value=f"#{m.tag}\n{m.trophies} {emoji(ctx, 'trophy')}\n{m.crowns} {emoji(ctx, 'crownblue')}\n{m.donations} {emoji(ctx, 'cards')}")

    return em

async def format_members(ctx, c):
    em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
    em.set_author(name=f"{c.name} (#{c.tag})")
    em.set_thumbnail(url=c.badge_url)
    embeds = []
    counter = 0
    for m in c.members:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
            em.set_author(name=f"{c.name} (#{c.tag})")
            em.set_thumbnail(url=c.badge_url)
        em.add_field(name=f'{m.name} ({m.role_name})', value=f"#{m.tag}\n{m.trophies} {emoji(ctx, 'trophy')}\n{m.crowns} {emoji(ctx, 'crownblue')}\n{m.donations} {emoji(ctx, 'cards')}")
        counter += 1
    embeds.append(em)
    return embeds

async def format_profile(ctx, p):

    try:
        av = p['clan']['badgeUrls']['small']
    except KeyError:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    em.set_author(name=p['name'], icon_url=av)
    em.set_thumbnail(url=p['league']['medium'])

    trophies = f"{p['trophies']}/{p['bestTrophies']} PB {emoji(ctx, 'trophy')}"


    embed_fields = [
        ('Trophies', trophies, True),
        ('XP Level', f"{p['expLevel']} {emoji(ctx, 'experience')}", True),
        ('TH Level', f"{p['townHallLevel']}", True)
        # ('Clan Name', f"{p.clan_name} {emoji(ctx, 'clan')}" if p.clan_name else None, True),
        # ('Clan Tag', f"#{p.clan_tag} {emoji(ctx, 'clan')}" if p.clan_tag else None, True),
        # ('Clan Role', f"{p.clan_role} {emoji(ctx, 'clan')}" if p.clan_role else None, True),
        # ('Games Played', f"{p.games_played} {emoji(ctx, 'battle')}", True),
        # ('Wins/Losses/Draws', f"{p.wins}/{p.losses}/{p.draws} {emoji(ctx, 'battle')}", True),
        # ('Win Streak', f"{p.win_streak} {emoji(ctx, 'battle')}", True),
        # ('Total Donations', f"{p.total_donations} {emoji(ctx, 'cards')}", True),
        # ('Global Rank', f"{p.global_rank} {emoji(ctx, 'crownred')}", True)
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value='No Clan')

    em.set_footer(text='Statsy')
    
    return em

async def format_clan(ctx, c):
    embed = discord.Embed(description = c.description, color=random_color())
    embed.set_author(name=f"{c.name} (#{c.tag})")
    embed.set_footer(text='StatsOverflow - Powered by cr-api.com')
    embed2 = copy.deepcopy(embed)
    embed.set_thumbnail(url=c.badge_url)
    embed2.description = 'Top Players/Donators/Contributors for this clan.'

    pushers = []
    for i in range(3):
        pushers.append(f"**{c.members[i].name}**\n{c.members[i].trophies} {emoji(ctx, 'trophy')}\n#{c.members[i].tag}")

    contributors = list(reversed(sorted(c.members, key=lambda x: x.crowns)))
    _donators = list(reversed(sorted(c.members, key=lambda m: m.donations)))

    donators = []

    for i in range(3):
        donators.append(f"**{_donators[i].name}**\n{_donators[i].crowns} {emoji(ctx, 'cards')}\n#{_donators[i].tag}")

    ccc = []

    for i in range(3):
        ccc.append(f"**{contributors[i].name}**\n{contributors[i].crowns} {emoji(ctx, 'crownred')}\n#{contributors[i].tag}")

    em_dict_1 = OrderedDict({
        'Type': c.type_name + ' 📩',
        'Score': str(c.score) + ' Trophies ' + str(emoji(ctx, 'trophy')),
        'Donations/Week': str(c.donations) + ' Cards ' + str(emoji(ctx, 'cards')),
        'Clan Chest': str(c.clan_chest.crowns) + '/' + str(c.clan_chest.required) + ' '+str(emoji(ctx, 'crownblue')),
        'Location': c.region + ' 🌎',
        'Members': str(len(c.members)) + f"/50 {emoji(ctx, 'clan')}",
        'Required Trophies': f"{c.required_trophies} {emoji(ctx, 'trophy')}",
        'Global Rank': f"{'Unranked' if c.rank == 0 else c.rank} {emoji(ctx, 'rank')}"
        })

    for f, v in em_dict_1.items():
        embed.add_field(name=f, value=v)

    em_dict_2 = [
        ("Top Players", '\n\n'.join(pushers)),
        ("Top Donators", '\n\n'.join(donators)),
        ("Top Contributors", '\n\n'.join(ccc))
    ]



    for f, v in em_dict_2:

        embed2.add_field(name=f, value=v)

    
    
    return [embed, embed2]

