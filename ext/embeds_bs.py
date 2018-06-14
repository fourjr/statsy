import copy
import datetime
import math
import random
from time import time

import discord

import box


def random_color():
    return random.randint(0, 0xFFFFFF)


def emoji(ctx, name):
    name = name.lower().replace('ricochet', 'rico').replace('el primo', 'primo')
    name = name.replace('jessie', 'jess').replace('dynamike', 'mike')
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    if e is None:
        return name.title()
    return e


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


url = 'https://raw.githubusercontent.com/fourjr/bs-assets/master/images/'


async def format_profile(ctx, p):

    name = p.name
    tag = p.tag

    brawlers = ''.join([str(emoji(ctx, i.name)) for i in p.brawlers])

    # pic = url + 'thumbnails/high/' + p['avatar_export'] + '.png'

    trophies = p.trophies
    pb = p.highestTrophies
    victories = p.victories
    showdown = p.showdownVictories
    # best_boss = format_timestamp(p['best_time_as_boss_in_seconds'])
    # best_robo_rumble = format_timestamp(p['best_robo_rumble_time_in_seconds'])

    # exp = p['current_experience']
    try:
        bandtag = p.band.tag
        bandname = p.band.name
    except box.BoxKeyError:
        bandtag = None
        bandname = None

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{name} (#{tag})')
    # em.set_thumbnail(url=pic)
    em.set_footer(text='Powered by brawlstars-api')

    embed_fields = [
        ('Trophies', f'{trophies}/{pb} PB {emoji(ctx, "icon_trophy")}', True),
        ('Victories', f'{victories} {emoji(ctx, "star_gold_00")}', True),
        ('Showdown Wins', f'{showdown} {emoji(ctx, "icon_showdown")}', True),
        # ('Best time as Boss', f'{best_boss}', True),
        # ('Best Robo Rumble Time', best_robo_rumble, True),
        # ('Level', f'{exp} {emoji(ctx, "star_silver")}', True),
        ('Band Name', bandname, True),
        ('Band Tag', '#' + bandtag, True),
        ('Brawlers', brawlers, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    return em


async def format_band(ctx, b):
    name = b.name
    description = b.description
    # badge = url + 'bands/' + b['badge_export'] + '.png'

    score = b.trophies

    required = b.required_trophies

    members = b.members
    _experiences = sorted(members, key=lambda x: x.exp_level, reverse=True)
    experiences = []
    pushers = []

    if len(members) >= 3:
        for i in range(3):
            pushername = members[i].name
            trophies = members[i].trophies
            tag = members[i].tag
            pushers.append(
                f"**{pushername}**"
                f"\n{trophies} "
                f"{emoji(ctx, 'icon_trophy')}\n"
                f"#{tag}"
            )

            xpname = _experiences[i].name
            xpval = _experiences[i].exp_level
            xptag = _experiences[i].tag
            experiences.append(
                f"**{xpname}**"
                f"\n{emoji(ctx, 'star_silver')}"
                f" {xpval}\n"
                f"#{xptag}"
            )

    page1 = discord.Embed(description=description, color=random_color())
    page1.set_author(name=f"{name} (#{tag})")
    # page1.set_thumbnail(url=badge)
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Experienced Players for this clan.'

    fields1 = [
        ('Clan Score', f'{score} {emoji(ctx, "icon_trophy")}'),
        ('Required Trophies', f'{required} {emoji(ctx, "icon_trophy")}'),
        ('Members', f'{len(members)}/100')
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

    page1.set_footer(text='Powered by brawlstars-api')
    page2.set_footer(text='Powered by brawlstars-api')

    return [page1, page2]


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
        date = (datetime.datetime.fromtimestamp(event['time']['ends_in'] + int(time()))) - datetime.datetime.now()
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
        date = (datetime.datetime.fromtimestamp(event['time']['starts_in'] + int(time()))) - datetime.datetime.now()
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
