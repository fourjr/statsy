import copy
import random

import discord

from locales.i18n import Translator

_ = Translator('COC Embeds', __file__)


def emoji(ctx, name):
    name = name.replace('.', '').lower().replace(' ', '').replace('_', '').replace('-', '')
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
            m['score'] = ((m['donations'] / 5) + (m['versusTrophies'] / 7) + (m['trophies'] / 7)) / 3
        except KeyError:
            m['score'] = ((m['donations'] / 5) + 0 + (m['trophies'] / 7)) / 3

    to_kick = sorted(c['memberList'], key=lambda m: m['score'])[:4]

    em = discord.Embed(color=random_color(), description=_('Here are the least valuable members of the clan currently.', ctx))
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    em.set_footer(text=_('Statsy - Powered by the COC API', ctx))

    for m in reversed(to_kick):
        try:
            versus_trophies = m['versusTrophies']
        except KeyError:
            versus_trophies = None
        em.add_field(
            name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})',
            value='\n'.join((
                f"{m['tag']}\n{m['trophies']} {emoji(ctx, 'trophy')}",
                f"{versus_trophies} {emoji(ctx, 'axes')}",
                f"{m['donations']} {emoji(ctx, 'troops')}"
            ))
        )

    return em


async def format_most_valuable(ctx, c):
    for m in c['memberList']:
        try:
            m['score'] = ((m['donations'] / 5) + (m['versusTrophies'] / 7) + (m['trophies'] / 7)) / 3
        except KeyError:
            m['score'] = ((m['donations'] / 5) + 0 + (m['trophies'] / 7)) / 3

    best = sorted(c['memberList'], key=lambda m: m['score'], reverse=True)[:4]

    em = discord.Embed(color=random_color(), description=_('Here are the most valuable members of the clan currently.', ctx))
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    em.set_footer(text=_('Statsy - Powered by the COC API', ctx))

    for m in reversed(best):
        try:
            versus_trophies = m['versusTrophies']
        except KeyError:
            versus_trophies = None
        em.add_field(
            name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})',
            value='\n'.join((
                f"{m['tag']}",
                f"{m['trophies']} {emoji(ctx, 'trophy')}",
                f"{versus_trophies} {emoji(ctx, 'axes')}",
                f"{m['donations']} {emoji(ctx, 'troops')}"
            ))
        )

    return em


async def format_members(ctx, c):
    em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
    em.set_author(name=f"{c['name']} ({c['tag']})")
    em.set_thumbnail(url=c['badgeUrls']['medium'])
    embeds = []
    counter = 0
    for m in c['memberList']:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
            em.set_author(name=f"{c['name']} ({c['tag']})")
            em.set_thumbnail(url=c['badgeUrls']['medium'])
        try:
            versus_trophies = m['versusTrophies']
        except:
            versus_trophies = None
        em.add_field(
            name=f'{m["name"]} ({"Elder" if m["role"] == "admin" else m["role"].title()})',
            value="\n".join((
                f"{m['tag']}",
                f"{m['trophies']} {emoji(ctx, 'trophy')}",
                f"{versus_trophies} {emoji(ctx, 'axes')}",
                f"{m['donations']} {emoji(ctx, 'troops')}"
            ))
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_achievements(ctx, p):
    em = discord.Embed(description=_("All of {}'s achievements", ctx).format(p['name']), color=random_color())
    em.set_author(name=f"{p['name']} ({p['tag']})")
    embeds = []
    counter = 0
    for achievement in p['achievements']:
        if counter % 4 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description=_("All of {}'s achievements", ctx).format(p['name']), color=random_color())
            em.set_author(name=f"{p['name']} ({p['tag']})")
        try:
            status = achievement['completionInfo']
        except KeyError:
            status = _('N/A', ctx)
        em.add_field(
            name=f"{achievement['name']} ({achievement['stars']})",
            value=_('**Requirement:** {}\n**Status:** {}', ctx).format(achievement['info'], status),
            inline=False
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_war(ctx, w):
    em = discord.Embed(description=_('In War', ctx) if w['state'] == 'inWar' else w['state'].title(), color=random_color())
    em.set_author(name=f"{w['clan']['name']} ({w['clan']['tag']}) vs {w['opponent']['name']} ({w['opponent']['tag']})")
    em.set_image(url="attachment://war.png")
    em.add_field(name=w['clan']['name'], value='--------------')
    em.add_field(name=w['opponent']['name'], value='--------------')
    em.add_field(name=_('Level', ctx), value=f"{w['clan']['clanLevel']} {emoji(ctx, 'experience')}")
    em.add_field(name=_('Level', ctx), value=f"{w['opponent']['clanLevel']} {emoji(ctx, 'experience')}")
    em.add_field(name=_('Attacks', ctx), value=f"{w['clan']['attacks']} {emoji(ctx, 'sword')}")
    em.add_field(name=_('Attacks', ctx), value=f"{w['opponent']['attacks']} {emoji(ctx, 'sword')}")
    em.add_field(name=_('Stars', ctx), value=f"{w['clan']['stars']} {emoji(ctx, 'cocstar')}")
    em.add_field(name=_('Stars', ctx), value=f"{w['opponent']['stars']} {emoji(ctx, 'cocstar')}")
    em.add_field(name=_('Destruction', ctx), value=f"{w['clan']['destructionPercentage']}%")
    em.add_field(name=_('Destruction', ctx), value=f"{w['opponent']['destructionPercentage']}%")
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
        war_stars = p['warStars']
        role = 'Elder' if p['role'] == 'admin' else p['role'].title()
    except KeyError:
        clan = None
        war_stars = None
        role = None

    try:
        donations = p['donations'] / p['donationsReceived']
    except ZeroDivisionError:
        donations = 0

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('XP Level', ctx), f"{p['expLevel']} {emoji(ctx, 'experience')}", True),
        (_('TH Level', ctx), f"{p['townHallLevel']} {emoji(ctx, 'townhall'+str(p['townHallLevel']))}", True),
        (_('Clan Name', ctx), f"{clan['name']} {emoji(ctx, 'clan')}" if clan else _('No Clan', ctx), True),
        (_('Clan Tag', ctx), f"{clan['tag']} {emoji(ctx, 'clan')}" if clan else _('No Clan', ctx), True),
        (_('Clan Role', ctx), f"{role} {emoji(ctx, 'clan')}" if clan else _('No Clan', ctx), True),
        (_('War Stars', ctx), f"{war_stars} {emoji(ctx, 'cocstar')}" if clan else _('No Clan', ctx), True),
        (_('Successful Attacks', ctx), f'{p["attackWins"]} {emoji(ctx, "sword")}', True),
        (_('Successful Defenses', ctx), f'{p["defenseWins"]} {emoji(ctx, "cocshield")}', True),
        (_("Donations", ctx), _('{} Received {}', ctx).format(donations, emoji(ctx, 'troops')), True)
    ]

    try:
        embed_fields.append(
            (_('BH Level', ctx), f"{p['builderHallLevel']} {emoji(ctx, 'builderhall'+str(p['builderHallLevel']))}", True)
        )
        embed_fields.append(
            (_("Builder Trophies", ctx), f"{p['versusTrophies']}/{p['bestVersusTrophies']} PB {emoji(ctx, 'axes')}", True)
        )
    except KeyError:
        pass

    try:
        embed_fields.append(
            (_('Current Season', ctx), f"{p['legendStatistics']['currentSeason']['trophies']} {emoji(ctx, 'trophy')}", True)
        )
        embed_fields.append(
            (
                _('Best Season', ctx),
                '\n'.join((
                    f"{p['legendStatistics']['bestSeason']['trophies']} {emoji(ctx, 'trophy')}",
                    f"{p['legendStatistics']['bestSeason']['rank']} {emoji(ctx, 'rank')}"
                )),
                True
            )
        )
    except KeyError:
        pass
    try:
        embed_fields.append(
            (
                _('Last BH Season', ctx),
                '\n'.join((
                    f"{p['legendStatistics']['previousVersusSeason']['trophies']} {emoji(ctx, 'axes')}",
                    f"{p['legendStatistics']['previousVersusSeason']['rank']} {emoji(ctx, 'rank')}",
                )),
                True
            )
        )
        embed_fields.append(
            (
                _('Best BH Season', ctx),
                '\n'.join((
                    f"{p['legendStatistics']['bestVersusSeason']['trophies']} {emoji(ctx, 'axes')}",
                    f"{p['legendStatistics']['bestVersusSeason']['rank']} {emoji(ctx, 'rank')}"
                )),
                True
            )
        )
    except KeyError:
        pass

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == _('Clan Name', ctx):
                em.add_field(name=_('Clan', ctx), value=_('No Clan', ctx))

    em.set_footer(text=_('Statsy - Powered by the COC API', ctx))
    embeds.append(em)
    em = discord.Embed(color=random_color())
    em.set_author(name=_('{}s Collection ({})', ctx).format(p['name'], p['tag']), icon_url=av)
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
    em.add_field(name=_("Home Troops", ctx), value='  '.join(troops), inline=False)
    if builders:
        em.add_field(name=_("Builder Troops", ctx), value='  '.join(builders), inline=False)
    else:
        em.add_field(name=_("Builder Troops", ctx), value='None')
    if spells:
        em.add_field(name=_("Spells", ctx), value='  '.join(spells), inline=False)
    else:
        em.add_field(name=_("Spells", ctx), value='None')
    if heroes:
        em.add_field(name=_("Heroes", ctx), value='  '.join(heroes), inline=False)
    else:
        em.add_field(name=_("Heroes", ctx), value='None')
    embeds.append(em)
    return embeds


async def format_clan(ctx, c):
    embed = discord.Embed(description=c['description'], color=random_color())
    embed.set_author(name=f"{c['name']} ({c['tag']})")
    embed2 = copy.deepcopy(embed)
    embed.set_thumbnail(url=c['badgeUrls']['medium'])
    embed2.description = _('Top Players/Donators for this clan.', ctx)

    pushers = []
    for i in range(3):
        if len(c['memberList']) < i + 1:
            break
        pushers.append('\n'.join((
            f"**{c['memberList'][i]['name']}**",
            f"{c['memberList'][i]['trophies']} {emoji(ctx, 'trophy')}",
            f"{c['memberList'][i]['tag']}"
        )))

    _donators = list(reversed(sorted(c['memberList'], key=lambda m: m['donations'])))
    _builders = list(reversed(sorted(c['memberList'], key=lambda m: m['versusTrophies'])))

    donators = []
    builders = []

    for i in range(3):
        donators.append(
            f"**{_donators[i]['name']}**\n{_donators[i]['donations']} {emoji(ctx, 'troops')}\n{_donators[i]['tag']}"
        )

    for i in range(3):
        builders.append(
            f"**{_builders[i]['name']}**\n{_builders[i]['versusTrophies']} {emoji(ctx, 'axes')}\n{_builders[i]['tag']}"
        )

    em_1 = [
        (_('Score Home/Builder', ctx), f'{c["clanPoints"]}/{c["clanVersusPoints"]} {emoji(ctx, "trophy")}'),
        (_('Required Trophies', ctx), f"{c['requiredTrophies']} {emoji(ctx, 'trophy')}"),
        (_('Type', ctx), f"{'Invite Only' if c['type'] == 'inviteOnly' else c['type'].title()} 📩"),
        (_('Location', ctx), f"{c['location']['name']} 🌎"),
        (_('Members', ctx), f"{c['members']}/50 {emoji(ctx, 'clan')}"),
        (_('War Activity', ctx), c['warFrequency'].title())
    ]

    if c['isWarLogPublic']:
        em_1.append(('War Win/Loss/Draw', f"{c['warWins']}/{c['warLosses']}/{c['warTies']}"))
        em_1.append(('War Win Streak', str(c['warWinStreak'])))

    for f, v in em_1:
        embed.add_field(name=f, value=v)

    em_dict_2 = [
        (_('Top Home Players', ctx), '\n\n'.join(pushers)),
        (_('Top Donators', ctx), '\n\n'.join(donators)),
        (_('Top Builder Players', ctx), '\n\n'.join(builders))
    ]

    for f, v in em_dict_2:

        embed2.add_field(name=f, value=v)

    return [embed, embed2]
