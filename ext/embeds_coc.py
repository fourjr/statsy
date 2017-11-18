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

async def format_least_valuable(ctx, c):
    for m in c['memberList']:
        try:
            m['score'] = ((m['donations']/5) + (m['versusTrophies']/7) + (m['trophies']/7)) / 3
        except KeyError:
            m['score'] = ((m['donations']/5) + 0 + (m['trophies']/7)) / 3

    to_kick = sorted(c['memberList'], key=lambda m: m['score'])[:4]

    em = discord.Embed(color=random_color(), description='Here are the least valuable members of the clan currently.')
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    em.set_footer(text='Statsy - Powered by the COC API')

    for m in reversed(to_kick):
        try:
            versus_trophies = m['versusTrophies']
        except KeyError:
            versus_trophies = None
        em.add_field(name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})', value=f"{m['tag']}\n{m['trophies']} {emoji(ctx, 'trophy')}\n{versus_trophies} {emoji(ctx, 'axes')}\n{m['donations']} {emoji(ctx, 'troops')}")

    return em

async def format_most_valuable(ctx, c):
    for m in c['memberList']:
        try:
            m['score'] = ((m['donations']/5) + (m['versusTrophies']/7) + (m['trophies']/7)) / 3
        except KeyError:
            m['score'] = ((m['donations']/5) + 0 + (m['trophies']/7)) / 3

    best = sorted(c['memberList'], key=lambda m: m['score'], reverse=True)[:4]

    em = discord.Embed(color=random_color(), description='Here are the most valuable members of the clan currently.')
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    em.set_footer(text='Statsy - Powered by the COC API')

    for m in reversed(best):
        try:
            versus_trophies = m['versusTrophies']
        except KeyError:
            versus_trophies = None
        em.add_field(name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})', value=f"{m['tag']}\n{m['trophies']} {emoji(ctx, 'trophy')}\n{versus_trophies} {emoji(ctx, 'axes')}\n{m['donations']} {emoji(ctx, 'troops')}")

    return em


async def format_members(ctx, c):
    em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    embeds = []
    counter = 0
    for m in c['memberList']:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description = 'A list of all members in this clan.', color=random_color())
            em.set_author(name=f"{c['name']} ({c['tag']})")
            em.set_thumbnail(url=c['badgeUrls']['medium'])
        try:
            versus_trophies = m['versusTrophies']
        except:
            versus_trophies = None
        em.add_field(name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})', value=f"{m['tag']}\n{m['trophies']} {emoji(ctx, 'trophy')}\n{versus_trophies} {emoji(ctx, 'axes')}\n{m['donations']} {emoji(ctx, 'troops')}")
        counter += 1
    embeds.append(em)
    return embeds

async def format_achievements(ctx, p):
    em = discord.Embed(description=f"All of {p['name']}'s achievements", color=random_color())
    em.set_author(name=f"{p['name']} ({p['tag']})")
    embeds = []
    counter = 0
    for achievement in p['achievements']:
        if counter % 4 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description=f"All of {p['name']}'s achievements", color=random_color())
            em.set_author(name=f"{p['name']} ({p['tag']})")
        try:
            status = achievement['completionInfo']
        except KeyError:
            status = "N/A"
        em.add_field(name=f"{achievement['name']} ({achievement['stars']})", value=f"**Requirement:** {achievement['info']}\n**Status:** {status}", inline=False)
        counter += 1
    embeds.append(em)
    return embeds

async def format_war(ctx, w):
    em = discord.Embed(description='In War' if w['state'] == 'inWar' else w['state'].title(), color=random_color())
    em.set_author(name=f"{w['clan']['name']} ({w['clan']['tag']}) vs {w['opponent']['name']} ({w['opponent']['tag']})")
    em.set_image(url="attachment://war.png")
    em.add_field(name=w['clan']['name'], value='--------------')
    em.add_field(name=w['opponent']['name'], value='--------------')
    em.add_field(name='Level', value=f"{w['clan']['clanLevel']} {emoji(ctx, 'experience')}")
    em.add_field(name='Level', value=f"{w['opponent']['clanLevel']} {emoji(ctx, 'experience')}")
    em.add_field(name='Attacks', value=f"{w['clan']['attacks']} {emoji(ctx, 'sword')}")
    em.add_field(name='Attacks', value=f"{w['opponent']['attacks']} {emoji(ctx, 'sword')}")
    em.add_field(name='Stars', value=f"{w['clan']['stars']} {emoji(ctx, 'cocstar')}")
    em.add_field(name='Stars', value=f"{w['opponent']['stars']} {emoji(ctx, 'cocstar')}")
    em.add_field(name='Destruction', value=f"{w['clan']['destructionPercentage']}%")
    em.add_field(name='Destruction', value=f"{w['opponent']['destructionPercentage']}%")
    return em

async def format_profile(ctx, p):
    embeds = []
    try:
        av = p['clan']['badgeUrls']['small']
    except KeyError:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p['name']} ({p['tag']})", icon_url=av)
    try:
        em.set_thumbnail(url=p['league']['iconUrls']['medium'])
    except KeyError:
        em.set_thumbnail(url="https://i.imgur.com/JsVQPza.png")

    trophies = f"{p['trophies']}/{p['bestTrophies']} PB {emoji(ctx, 'trophy')}"
    try:
        clan = p['clan']
    except KeyError:
        clan = None
    try:
        war_stars = p['warStars']
    except KeyError:
        war_stars = None


    embed_fields = [
        ('Trophies', trophies, True),
        ('XP Level', f"{p['expLevel']} {emoji(ctx, 'experience')}", True),
        ('TH Level', f"{p['townHallLevel']} {emoji(ctx, 'townhall'+str(p['townHallLevel']))}", True),
        ('Clan Name', f"{clan['name']} {emoji(ctx, 'clan')}" if clan else None, True),
        ('Clan Tag', f"{clan['tag']} {emoji(ctx, 'clan')}" if clan else None, True),
        ('Clan Role', f"{'Elder' if p['role'] == 'admin' else p['role'].title()} {emoji(ctx, 'clan')}" if clan else None, True),
        ('War Stars', f"{war_stars} {emoji(ctx, 'cocstar')}", True),
        ('Successful Attacks', f'{p["attackWins"]} {emoji(ctx, "sword")}', True),
        ('Successful Defenses', f'{p["defenseWins"]} {emoji(ctx, "cocshield")}', True),
        ("Donations", f"{p['donations']}/{p['donationsReceived']} Received {emoji(ctx, 'troops')}", True)
        ]

    try:
        embed_fields.append(('BH Level', f"{p['builderHallLevel']} {emoji(ctx, 'builderhall'+str(p['builderHallLevel']))}", True))
        embed_fields.append(("Builder Trophies", f"{p['versusTrophies']}/{p['bestVersusTrophies']} PB {emoji(ctx, 'axes')}", True))
    except KeyError:
        pass

    try:
        embed_fields.append(('Current Season', f"{p['legendStatistics']['currentSeason']['trophies']} {emoji(ctx, 'trophy')}", True))
        embed_fields.append(('Best Season', f"{p['legendStatistics']['bestSeason']['trophies']} {emoji(ctx, 'trophy')}\n{p['legendStatistics']['bestSeason']['rank']} {emoji(ctx, 'rank')}", True))
    except KeyError:
        pass
    try:
        embed_fields.append(('Last BH Season', f"{p['legendStatistics']['previousVersusSeason']['trophies']} {emoji(ctx, 'axes')}\n{p['legendStatistics']['previousVersusSeason']['rank']} {emoji(ctx, 'rank')}", True))
        embed_fields.append(('Best BH Season', f"{p['legendStatistics']['bestVersusSeason']['trophies']} {emoji(ctx, 'axes')}\n{p['legendStatistics']['bestVersusSeason']['rank']} {emoji(ctx, 'rank')}", True))
    except KeyError:
        pass

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value='No Clan')

    em.set_footer(text='Statsy - Powered by the COC API')
    embeds.append(em)
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p['name']}'s Collection ({p['tag']})", icon_url=av)
    troops = []
    builders = []
    heroes = []
    spells = []
    for troop in p['troops']:
        if troop['village'] == "home":
            troops.append(f'{emoji(ctx, "coc"+troop["name"].lower().replace(" ", ""))}{troop["level"]}')
        else:
            builders.append(f'{emoji(ctx, "coc"+troop["name"].lower().replace(" ", ""))}{troop["level"]}')
    for spell in p['spells']:
        spells.append(f'{emoji(ctx, "coc"+spell["name"].lower().replace(" ", ""))}{spell["level"]}')
    for hero in p['heroes']:
        heroes.append(f'{emoji(ctx, "coc"+hero["name"].lower().replace(" ", ""))}{hero["level"]}')
    em.add_field(name="Home Troops", value='  '.join(troops), inline=False)
    try:
        em.add_field(name="Builder Troops", value='  '.join(builders), inline=False)
    except:
        em.add_field(name="Builder Troops", value='None')
    try:
        em.add_field(name="Spells", value='  '.join(spells), inline=False)
    except:
        em.add_field(name="Spells", value='None')
    try:
        em.add_field(name="Heroes", value='  '.join(heroes), inline=False)
    except:
        em.add_field(name="Heroes", value='None')
    embeds.append(em)
    return embeds

async def format_clan(ctx, c):
    embed = discord.Embed(description = c['description'], color=random_color())
    embed.set_author(name=f"{c['name']} ({c['tag']})")
    embed2 = copy.deepcopy(embed)
    embed.set_thumbnail(url=c['badgeUrls']['medium'])
    embed2.description = 'Top Players/Donators for this clan.'

    pushers = []
    for i in range(3):
        pushers.append(f"**{c['memberList'][i]['name']}**\n{c['memberList'][i]['trophies']} {emoji(ctx, 'trophy')}\n{c['memberList'][i]['tag']}")

    _donators = list(reversed(sorted(c['memberList'], key=lambda m: m['donations'])))
    _builders = list(reversed(sorted(c['memberList'], key=lambda m: m['versusTrophies'])))

    donators = []
    builders = []

    for i in range(3):
        donators.append(f"**{_donators[i]['name']}**\n{_donators[i]['donations']} {emoji(ctx, 'troops')}\n{_donators[i]['tag']}")

    for i in range(3):
        builders.append(f"**{_builders[i]['name']}**\n{_builders[i]['versusTrophies']} {emoji(ctx, 'axes')}\n{_builders[i]['tag']}")

    em_1 = [
        ('Score Home/Builder', f'{c["clanPoints"]}/{c["clanVersusPoints"]} {emoji(ctx, "trophy")}'),
        ('Required Trophies', f"{c['requiredTrophies']} {emoji(ctx, 'trophy')}"),
        ('Type', f"{'Invite Only' if c['type'] == 'inviteOnly' else c['type'].title()} 📩"),
        ('Location', f"{c['location']['name']} 🌎"),
        ('Members', f"{c['members']}/50 {emoji(ctx, 'clan')}"),
        ('War Activity', c['warFrequency'].title())
        ]

    if c['isWarLogPublic']:
        em_1.append(('War Win/Loss/Draw', f"{c['warWins']}/{c['warLosses']}/{c['warTies']}"))
        em_1.append(('War Win Streak', str(c['warWinStreak'])))

    for f, v in em_1:
        embed.add_field(name=f, value=v)

    em_dict_2 = [
        ("Top Home Players", '\n\n'.join(pushers)),
        ("Top Donators", '\n\n'.join(donators)),
        ("Top Builder Players", '\n\n'.join(builders))
    ]


    for f, v in em_dict_2:

        embed2.add_field(name=f, value=v)

    
    
    return [embed, embed2]

