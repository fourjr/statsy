import copy
from datetime import datetime
import math
from time import time

import discord

from ext.utils import random_color, emoji
from locales.i18n import Translator

_ = Translator('BS Embeds', __file__)

url = 'https://raw.githubusercontent.com/fourjr/bs-assets/master/images/'


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
    brawlers = ' '.join([f'{emoji(ctx, i.name)} {i.upgrades_power}' for i in p.brawlers])

    pic = f'{url}thumbnails/high/{p.avatar_id}.png'

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} (#{p.tag})')
    em.set_thumbnail(url=pic)
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

    embed_fields = [
        (_('Trophies', ctx), f"{p.trophies}/{p.highest_trophies} PB {emoji(ctx, 'icon_trophy')}", True),
        (_('3v3 Victories', ctx), f"{p.victories} {emoji(ctx, 'star_gold_00')}", True),
        (_('Solo Showdown Wins', ctx), f"{p.solo_showdown_victories} {emoji(ctx, 'soloshowdown')}", True),
        (_('Duo Showdown Wins', ctx), f"{p.duo_showdown_victories} {emoji(ctx, 'duoshowdown')}", True),
        ('Best time as Boss', f"{p.best_time_as_boss} {emoji(ctx, 'bossfight')}", True),
        ('Best Robo Rumble Time', f"{p.best_robo_rumble_time} {emoji(ctx, 'roborumble')}", True),
        # ('Level', f"{p.exp} {emoji(ctx, 'star_silver')}", True),
        ('Band Name', p.band.name, True),
        ('Band Tag', f'#{p.band.tag}', True),
        ('Brawlers', brawlers, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    return em


async def format_brawlers(ctx, p):
    ems = []

    ranks = [
        1,
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

    for n, i in enumerate(p.brawlers):
        if n % 9 == 0:
            ems.append(discord.Embed(color=random_color()))
            ems[-1].set_author(name=f'{p.name} (#{p.tag})')
            ems[-1].set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))

        rank = ranks.index([r for r in ranks if i.trophies >= r][-1]) + 1
        val = f"Level {i.upgrades_power}\n{i.trophies}/{i.highest_trophies} PB {emoji(ctx, 'icon_trophy')}" + '　' + f'(Rank {rank})'
        ems[-1].add_field(name=f"{i.name.replace('Franky', 'Frank')} {emoji(ctx, i.name)}", value=val)

    return ems


async def format_band(ctx, b):
    # badge = f'{url}bands/' + b['badge_export'] + '.png'

    # _experiences = sorted(b.members, key=lambda x: x.exp_level, reverse=True)
    # experiences = []
    # pushers = []

    # if len(b.members) >= 3:
    #     for i in range(3):
    #         pushername = b.members[i].name
    #         trophies = b.members[i].trophies
    #         tag = b.members[i].tag
    #         pushers.append(
    #             f"**{pushername}**"
    #             f"\n{trophies} "
    #             f"{emoji(ctx, 'icon_trophy')}\n"
    #             f"#{tag}"
    #         )

    #         xpname = _experiences[i].name
    #         xpval = _experiences[i].exp_level
    #         xptag = _experiences[i].tag
    #         experiences.append(
    #             f"**{xpname}**"
    #             f"\n{emoji(ctx, 'star_silver')}"
    #             f" {xpval}\n"
    #             f"#{xptag}"
    #         )

    page1 = discord.Embed(description=b.description, color=random_color())
    page1.set_author(name=f"{b.name} (#{b.tag})")
    page1.set_footer(text=_('Statsy | Powered by brawlapi.cf', ctx))
    # page1.set_thumbnail(url=badge)
    # page2 = copy.deepcopy(page1)
    # page2.description = 'Top Players/Experienced Players for this clan.'

    fields1 = [
        ('Clan Score', f'{b.trophies} {emoji(ctx, "icon_trophy")}'),
        ('Required Trophies', f'{b.required_trophies} {emoji(ctx, "icon_trophy")}'),
        ('Members', f'{b.members_count}/100')
    ]
    # fields2 = [
    #     ("Top Players", '\n\n'.join(pushers)),
    #     ("Top Experience", '\n\n'.join(experiences))
    # ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    # for f, v in fields2:
    #     if v:
    #         page2.add_field(name=f, value=v)

    # return [page1, page2]
    return [page1]


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
    coin_emoji = str(emoji(ctx, 'icon_coin'))

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
    delta = datetime.utcnow() - datetime.strptime(leaderboard['updated'], '%Y-%m-%d %H:%M:%S')
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

    for rnd in range(math.ceil(len(leaderboard['bestTeams']) / 5)):
        em = discord.Embed(
            title='Top Teams in Robo Rumble',
            description=_('Top {} teams!\nLast updated: {} ago', ctx).format(len(leaderboard['bestTeams']), fmt),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 5 + rnd):
            minutes, seconds = divmod(leaderboard['bestTeams'][i]['duration'], 60)
            rankings = ''
            for num in range(1, 4):
                rankings += str(emoji(ctx, leaderboard['bestTeams'][i][f'brawler{num}'])) + ' ' + leaderboard['bestTeams'][i][f'player{num}'] + '\n'
            em.add_field(name=f'{minutes}m {seconds}s', value=rankings)

        embeds.append(em)

    return embeds


def format_boss(ctx, leaderboard):
    delta = datetime.utcnow() - datetime.strptime(leaderboard['updated'], '%Y-%m-%d %H:%M:%S')
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

    for rnd in range(math.ceil(len(leaderboard['bestPlayers']) / 10)):
        em = discord.Embed(
            title='Top Bosses in Boss Fight ',
            description=_('Top {} bosses!\n\nLast updated: {} ago\nMap: {}', ctx).format(len(leaderboard['bestPlayers']), fmt, leaderboard['activeLevel']),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 10 + rnd):
            minutes, seconds = divmod(leaderboard['bestPlayers'][i]['duration'], 60)
            rankings = str(emoji(ctx, leaderboard['bestPlayers'][i]['brawler'])) + ' ' + leaderboard['bestPlayers'][i]['player'] + '\n'
            em.add_field(name=f'{minutes}m {seconds}s', value=rankings)

        embeds.append(em)

    return embeds
