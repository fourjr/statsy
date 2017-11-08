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

async def format_least_valuable(ctx, clan):
    for m in clan.members:
        m.score = ((m.donations/5) + (m.crowns*10) + (m.trophies/7)) / 3

    to_kick = sorted(clan.members, key=lambda m: m.score)[:4]

    em = discord.Embed(color=random_color(), description='Here are the least valuable members of the clan currently.')
    em.set_author(name=clan)
    em.set_thumbnail(url=clan.badge_url)
    em.set_footer(text='Statsy - Powered by the COC API')

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
    em.set_footer(text='Statsy - Powered by the COC API')

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

# async def format_achievements(ctx, a):
#     em = discord.Embed(title="Achievements", description=a['info'], color=random_color())
#     em.set_author(name=)

async def format_profile(ctx, p):
    embeds = []
    try:
        av = p['clan']['badgeUrls']['small']
    except KeyError:
        av = 'https://i.imgur.com/Y3uXsgj.png'
    em = discord.Embed(color=random_color())
    print(p)
    em.set_author(name=f"{p['name']} ({p['tag']})", icon_url=av)
    try:
        em.set_thumbnail(url=p['league']['iconUrls']['medium'])
    except KeyError:
        em.set_thumbnail(url="https://i.imgur.com/JsVQPza.png")

    trophies = f"{p['trophies']}/{p['bestTrophies']} PB {emoji(ctx, 'trophy')}"
    builder_trophies = f"{p['versusTrophies']}/{p['bestVersusTrophies']} PB {emoji(ctx, 'trophy')}"
    try:
        clan = p['clan']
    except KeyError:
        clan = None

    embed_fields = [
        ('Trophies', trophies, True),
        ('XP Level', f"{p['expLevel']} {emoji(ctx, 'experience')}", True),
        ('TH Level', f"{p['townHallLevel']} {emoji(ctx, 'townhall')}", True),
        ('BH Level', f"{p['builderHallLevel']} {emoji(ctx, 'builderhall')}", True),
        ('Clan Name', f"{clan['name']} {emoji(ctx, 'clan')}" if clan else None, True),
        ('Clan Tag', f"{clan['tag']} {emoji(ctx, 'clan')}" if clan else None, True),
        ('Clan Role', f"{p['role'].title()} {emoji(ctx, 'clan')}" if clan else None, True),
        ('War Stars', f"{p['warStars']}", True),
        ('Successful Attacks', f'{p["attackWins"]} {emoji(ctx, "sword")}', True),
        ('Successful Defenses', f'{p["defenseWins"]} {emoji(ctx, "cocshield")}', True),
        ("Builder Trophies", builder_trophies, True),
        ("Donations", f"{p['donations']}/{p['donationsReceived']} Recieved {emoji(ctx, 'troops')}", True)
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == 'Clan Name':
                em.add_field(name='Clan', value='No Clan')

    em.set_footer(text='Statsy - Powered by the COC API')
    embeds.append(em)
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p['name']}'s Troops ({p['tag']})", icon_url=av)
    troops = []
    builders = []
    heroes = []
    spells = []
    for troop in p['troops']:
        if troop['village'] == "home":
            troops.append(f'{emoji(ctx, "coc"+troop["name"].lower().replace(" ", ""))} {troop["level"]}')
        else:
            builders.append(f'{emoji(ctx, "coc"+troop["name"].lower().replace(" ", ""))} {troop["level"]}')
    em.add_field(name="Home Troops", value=' | '.join(troops))
    try:
        em.add_field(name="Builder Troops", value=' | '.join(builders))
    except:
        em.add_field(name="Builder Troops", value='None')
    embeds.append(em)
    em = discord.Embed(color=random_color())
    em.set_author(name=f"{p['name']}'s Spells and Heroes({p['tag']})", icon_url=av)
    for spell in p['spells']:
        spells.append(f'{emoji(ctx, "coc"+spell["name"].lower().replace(" ", ""))} {spell["level"]}')
    for hero in p['heroes']:
        heroes.append(f'{emoji(ctx, "coc"+hero["name"].lower().replace(" ", ""))} {hero["level"]}')
    try:
        em.add_field(name="Spells", value=' | '.join(spells))
    except:
        em.add_field(name="Spells", value='None')
    try:
        em.add_field(name="Heroes", value=' | '.join(heroes))
    except:
        em.add_field(name="Heroes", value='None')
    embeds.append(em)
    return embeds

async def format_clan(ctx, c):
    embed = discord.Embed(description = c.description, color=random_color())
    embed.set_author(name=f"{c.name} (#{c.tag})")
    embed.set_footer(text='Statsy - Powered by the COC API')
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

