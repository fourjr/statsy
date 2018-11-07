import copy
from datetime import datetime
import math
from time import time

import box
import discord

from ext.utils import random_color, emoji
from locales.i18n import Translator

_ = Translator('BS Embeds', __file__)

url = 'https://fourjr.github.io/bs-assets'


def format_timestamp(seconds: int):
    minutes = max(math.floor(seconds / 60), 0)
    seconds -= minutes * 60
    hours = max(math.floor(minutes / 60), 0)
    minutes -= hours * 60
    days = max(math.floor(hours / 60), 0)
    hours -= days * 60
    timeleft = ''
    if days > 0:
        timeleft += f'{days}d'
    if hours > 0:
        timeleft += f' {hours}h'
    if minutes > 0:
        timeleft += f' {minutes}m'
    if seconds > 0:
        timeleft += f' {seconds}s'

    return timeleft


async def format_profile(ctx, p):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    try:
        badge = ctx.cog.constants.alliance_badges[p.band.badge_id].name
        em.set_author(name=f'{p.name} (#{p.tag})', icon_url=f'{url}/band_badges/{badge}.png')
    except AttributeError:
        pass

    try:
        em.set_thumbnail(url=f'{url}/player_icons/{p.avatar_id}.png')
    except box.BoxKeyError:
        pass
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

    brawlers = ' '.join([f'{emoji(ctx, i.name)} {i.level}  ' if (n + 1) % 8 != 0 else f'{emoji(ctx, i.name)} {i.level}\n' for n, i in enumerate(p.brawlers)])

    exp_level = 0
    minus_exp = 30
    while p.total_exp >= 0:
        minus_exp += 10
        p.total_exp -= minus_exp
        exp_level += 1

    # :exp_level: is the current XP Level
    # :minus_exp - p.total_exp: is the amount of XP he has
    # :minus_exp: is the total amount of XP needed for that level

    account_age = ''
    months, days = divmod(p.account_age_in_days, 30)
    years, months = divmod(months, 12)
    if years:
        account_age += f'{years} year'
        if years > 1:
            account_age += 's,'
        else:
            account_age += ','

    if months:
        account_age += f' {months} month'
        if months > 1:
            account_age += 's and'
        else:
            account_age += 'and'

    account_age += f' {days} day'
    if days > 1:
        account_age += 's'

    try:
        band = p.band.name
    except box.BoxKeyError:
        band = False

    embed_fields = [
        (_('Trophies', ctx), f"{p.trophies}/{p.highest_trophies} PB {emoji(ctx, 'bstrophy')}", False),
        (_('3v3 Victories', ctx), f"{p.victories} {emoji(ctx, 'goldstar')}", True),
        (_('Solo Showdown Wins', ctx), f"{p.solo_showdown_victories} {emoji(ctx, 'soloshowdown')}", True),
        (_('Duo Showdown Wins', ctx), f"{p.duo_showdown_victories} {emoji(ctx, 'duoshowdown')}", True),
        (_('Best time as Boss', ctx), f"{p.best_time_as_boss} {emoji(ctx, 'bossfight')}", True),
        (_('Best Robo Rumble Time', ctx), f"{p.best_robo_rumble_time} {emoji(ctx, 'roborumble')}", True),
        (_('XP Level', ctx), f"{exp_level} ({minus_exp}/{minus_exp - p.total_exp}) {emoji(ctx, 'xp')}", True),
        (_('Band Name', ctx), p.band.name if band else None, True),
        (_('Band Tag', ctx), f'#{p.band.tag}' if band else None, True),
        (_('Band Role', ctx), p.band.role if band else None, True),
        (_('Account Age', ctx), account_age, False),
        (_('Brawlers', ctx), brawlers, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        elif n == _('Band Name', ctx):
            em.add_field(name=_('Band', ctx), value=_('None', ctx))

    return em


async def format_brawlers(ctx, p):
    ems = []

    ranks = [
        0,
        10,
        20,
        30,
        40,
        60,
        80,
        100,
        120,
        140,
        160,
        180,
        220,
        260,
        300,
        340,
        380,
        420,
        460,
        500
    ]

    check = '<:check:383917703083327489>'
    cross = '<:xmark:383917691318042624>'

    for n, i in enumerate(p.brawlers):
        if n % 6 == 0:
            ems.append(discord.Embed(color=random_color()))
            ems[-1].set_author(name=f'{p.name} (#{p.tag})')
            ems[-1].set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

        rank = ranks.index([r for r in ranks if i.highest_trophies >= r][-1]) + 1

        skin = check if i.has_skin else cross

        val = f"{emoji(ctx, 'xp')}　Level {i.level}\n{skin}　Skin Active?\n{emoji(ctx, 'bstrophy')}　{i.trophies}/{i.highest_trophies} PB (Rank {rank})"
        ems[-1].add_field(name=f"{emoji(ctx, i.name)}　{i.name.replace('Franky', 'Frank')}", value=val)

    return ems


async def format_band(ctx, b):
    # badge = f'{url}/band_icons/' + b.avatar_id + '.png'

    _experiences = sorted(b.members, key=lambda x: x.exp_level, reverse=True)
    experiences = []
    pushers = []

    if len(b.members) >= 3:
        for i in range(3):
            push_avatar = emoji(ctx, str(b.members[i].avatar_id).replace('21307136', '280000'))
            exp_avatar = emoji(ctx, str(_experiences[i].avatar_id).replace('21307136', '280000'))

            pushers.append(
                f"**{push_avatar} {b.members[i].name}**"
                f"{emoji(ctx, 'bstrophy')}\n"
                f"\n{b.members[i].trophies} "
                f"#{b.members[i].tag}"
            )

            experiences.append(
                f"**{exp_avatar} {_experiences[i].name}**"
                f"\n{emoji(ctx, 'xp')}"
                f" {_experiences[i].exp_level}\n"
                f"#{_experiences[i].tag}"
            )

    page1 = discord.Embed(description=b.description, color=random_color())
    page1.set_author(name=f"{b.name} (#{b.tag})")
    page1.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))
    # page1.set_thumbnail(url=badge)
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Experienced Players for this band.'

    fields1 = [
        (_('Type', ctx), f'{b.status} 📩'),
        (_('Score', ctx), f'{b.trophies} Trophies {emoji(ctx, "bstrophy")}'),
        (_('Members', ctx), f'{b.members_count}/100'),
        (_('Required Trophies', ctx), f'{b.required_trophies} {emoji(ctx, "bstrophy")}')
    ]
    fields2 = [
        ("Top Players", '\n\n'.join(pushers)),
        ("Top Experience", '\n\n'.join(experiences))
    ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    for f, v in fields2:
        if v:
            page2.add_field(name=f, value=v)

    return [page1, page2]


async def format_top_players(ctx, players):
    region = 'global'

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} players right now.', ctx).format(region)
    # badge_image = ctx.bot.cr.get_clan_image(players[0])
    em.set_author(name='Top Players')   # , icon_url=badge_image)
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))
    embeds = []
    counter = 0
    for c in players:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 {} players right now.', ctx).format(region)

            # badge_image = ctx.bot.cr.get_clan_image(players[0])
            em.set_author(name=_('Top Players', ctx))  # , icon_url=badge_image)
            em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

        try:
            band_name = c.band_name
        except box.BoxKeyError:
            band_name = 'No Clan'

        em.add_field(
            name=c.name,
            value=f"#{c.tag}"
                  f"\n{emoji(ctx, 'bstrophy')}{c.trophies}"
                  f"\n{emoji(ctx, 'bountystar')} Rank: {c.position} "
                  f"\n{emoji(ctx, 'xp')} XP Level: {c.exp_level}"
                  f"\n{emoji(ctx, 'gameroom')} {band_name}"
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_top_bands(ctx, clans):
    region = 'global'

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} bands right now.', ctx).format(region)
    # badge_image = ctx.bot.cr.get_clan_image(clans[0])
    em.set_author(name='Top Bands')  # , icon_url=badge_image)
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))
    embeds = []
    counter = 0
    for c in clans:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 {} bands right now.', ctx).format(region)

            # badge_image = ctx.bot.cr.get_clan_image(clans[0])
            em.set_author(name=_('Top Bands', ctx))  # , icon_url=badge_image)
            em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

        em.add_field(
            name=c.name,
            value=f"#{c.tag}"
                  f"\n{emoji(ctx, 'bstrophy')}{c.trophies}"
                  f"\n{emoji(ctx, 'bountystar')} Rank: {c.position} "
                  f"\n{emoji(ctx, 'gameroom')} {c.members_count}/100 "
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_events(ctx, events):
    em1 = discord.Embed(title='Ongoing events!', color=random_color())
    if ctx.bot.psa_message:
        em1.description = ctx.bot.psa_message
    em2 = copy.deepcopy(em1)
    em2.title = 'Upcoming events!'

    ongoing = events['now']
    upcoming = events['later']

    clock_emoji = u"\U0001F55B"
    first_win_emoji = str(emoji(ctx, 'first_win'))
    coin_emoji = str(emoji(ctx, 'coin'))

    for event in ongoing:
        date = (datetime.fromtimestamp(event['time']['ends_in'] + int(time()))) - datetime.utcnow()
        seconds = math.floor(date.total_seconds())
        minutes = max(math.floor(seconds / 60), 0)
        seconds -= minutes * 60
        hours = max(math.floor(minutes / 60), 0)
        minutes -= hours * 60
        timeleft = ''
        if hours > 0:
            timeleft += f'{hours}h'
        if minutes > 0:
            timeleft += f' {minutes}m'
        if seconds > 0:
            timeleft += f' {seconds}s'

        name = event['mode']['name']
        _map = event['location']
        first = event['coins']['first_win']
        freecoins = event['coins']['free']
        maxcoins = event['coins']['max']
        em1.add_field(
            name=name,
            value=(
                f'**{_map}**\n'
                f'Time Left: {timeleft} {clock_emoji}\n'
                f'First game: {first} {first_win_emoji}\n'
                f'Free coins: {freecoins} {coin_emoji}\n'
                f'Max Coins: {maxcoins} {coin_emoji}'
            )
        )

    for event in upcoming:
        date = (datetime.fromtimestamp(event['time']['starts_in'] + int(time()))) - datetime.utcnow()
        seconds = math.floor(date.total_seconds())
        timeleft = format_timestamp(seconds)

        name = event['mode']['name']
        _map = event['location']
        first = event['coins']['first_win']
        freecoins = event['coins']['free']
        maxcoins = event['coins']['max']
        em2.add_field(name=name, value=(
            f'**{_map}**\n'
            f'Time to go: {timeleft} {clock_emoji}\n'
            f'First game: {first} {first_win_emoji}\n'
            f'Free coins: {freecoins} {coin_emoji}\n'
            f'Max Coins: {maxcoins} {coin_emoji}'
        ))

    em1.set_footer(text='Powered by brawlstars-api')
    em2.set_footer(text='Powered by brawlstars-api')
    return [em1, em2]


def format_robo(ctx, leaderboard):
    delta = datetime.utcnow() - datetime.strptime(leaderboard.updated, '%Y-%m-%d %H:%M:%S')
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    fmt = '{s}s'
    if minutes:
        fmt = '{m}m ' + fmt
    if hours:
        fmt = '{h}h ' + fmt
    if days:
        fmt = '{d}d ' + fmt
    fmt = fmt.format(d=days, h=hours, m=minutes, s=seconds)

    embeds = []

    for rnd in range(math.ceil(len(leaderboard.best_teams) / 5)):
        em = discord.Embed(
            title='Top Teams in Robo Rumble',
            description=_('Top {} teams!\nLast updated: {} ago', ctx).format(len(leaderboard.best_teams), fmt),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 5 + rnd):
            minutes, seconds = divmod(leaderboard.best_teams[i].duration, 60)
            rankings = ''
            for num in range(1, 4):
                rankings += str(emoji(ctx, leaderboard.best_teams[i][f'brawler{num}'])) + ' ' + leaderboard.best_teams[i][f'player{num}'] + '\n'
            em.add_field(name=f'{minutes}m {seconds}s', value=rankings)

        embeds.append(em)

    return embeds


def format_boss(ctx, leaderboard):
    delta = datetime.utcnow() - datetime.strptime(leaderboard.updated, '%Y-%m-%d %H:%M:%S')
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    fmt = '{s}s'
    if minutes:
        fmt = '{m}m ' + fmt
    if hours:
        fmt = '{h}h ' + fmt
    if days:
        fmt = '{d}d ' + fmt
    fmt = fmt.format(d=days, h=hours, m=minutes, s=seconds)

    embeds = []

    for rnd in range(math.ceil(len(leaderboard.best_players) / 10)):
        em = discord.Embed(
            title='Top Bosses in Boss Fight ',
            description=_('Top {} bosses!\n\nLast updated: {} ago\nMap: {}', ctx).format(len(leaderboard.best_players), fmt, leaderboard['activeLevel']),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 10 + rnd):
            minutes, seconds = divmod(leaderboard.best_players[i].duration, 60)
            rankings = str(emoji(ctx, leaderboard.best_players[i].brawler)) + ' ' + leaderboard.best_players[i]['player'] + '\n'
            em.add_field(name=f'{minutes}m {seconds}s', value=rankings)

        embeds.append(em)

    return embeds
