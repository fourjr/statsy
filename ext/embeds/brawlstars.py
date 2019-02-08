import copy
import io
import json
import math
import re
from datetime import datetime

import box
import discord

from ext.utils import e, random_color, camel_case
from locales.i18n import Translator

_ = Translator('BS Embeds', __file__)

url = 'https://fourjr.github.io/bs-assets'


def clean(text):
    """Clean color codes from text"""
    p = re.sub(r'<c(\w|\d)+>(.+?)<\/c>', r'\2', text)
    return p or text


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


def format_profile(ctx, p):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    try:
        badge = ctx.cog.constants.alliance_badges[p.club.badge_id].name
        em.set_author(name=f'{p.name} (#{p.tag})', icon_url=f'{url}/club_badges/{badge}.png')
    except AttributeError:
        em.set_author(name=f'{p.name} (#{p.tag})')

    try:
        em.set_thumbnail(url=p.avatar_url)
    except box.BoxKeyError:
        pass
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf'))

    brawlers = ' '.join([f'{e(i.name)} {i.power}  ' if (n + 1) % 8 != 0 else f'{e(i.name)} {i.power}\n' for n, i in enumerate(p.brawlers)])

    try:
        club = p.club.name
    except AttributeError:
        club = False

    embed_fields = [
        (_('Trophies'), f"{p.trophies}/{p.highest_trophies} PB {e('bstrophy')}", False),
        (_('3v3 Victories'), f"{p.victories} {e('bountystar')}", True),
        (_('Solo Showdown Wins'), f"{p.solo_showdown_victories} {e('showdown')}", True),
        (_('Duo Showdown Wins'), f"{p.duo_showdown_victories} {e('duoshowdown')}", True),
        (_('Best time as Big Brawler'), f"{p.best_time_as_big_brawler} {e('biggame')}", True),
        (_('Best Robo Rumble Time'), f"{p.best_robo_rumble_time} {e('roborumble')}", True),
        (_('XP Level'), f"{p.exp_level} ({p.exp_fmt}) {e('xp')}", True),
        (_('Club Name'), p.club.name if club else None, True),
        (_('Club Tag'), f'#{p.club.tag}' if club else None, True),
        (_('Club Role'), p.club.role if club else None, True),
        (_('Brawlers'), brawlers, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        elif n == _('Club Name'):
            em.add_field(name=_('Club'), value=_('None'))

    return em


def format_brawlers(ctx, p):
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

    for n, i in enumerate(p.brawlers):
        if n % 6 == 0:
            ems.append(discord.Embed(color=random_color()))
            ems[-1].set_author(name=f'{p.name} (#{p.tag})')
            ems[-1].set_footer(text=_('Statsy | Powered by brawlapi.cf'))

        rank = ranks.index([r for r in ranks if i.highest_trophies >= r][-1]) + 1

        skin = e('tick') if i.has_skin else e('xmark')

        val = f"{e('xp')}　Level {i.level}\n{skin}　Skin Active?\n{e('bstrophy')}　{i.trophies}/{i.highest_trophies} PB (Rank {rank})"
        ems[-1].add_field(name=f"{e(i.name)}　{i.name.replace('Franky', 'Frank')}", value=val)

    return ems


def format_club(ctx, b):
    _experiences = sorted(b.members, key=lambda x: x.exp_level, reverse=True)
    experiences = []
    pushers = []

    if len(b.members) >= 3:
        for i in range(3):
            push_avatar = e(b.members[i].avatar_id)
            exp_avatar = e(_experiences[i].avatar_id)

            pushers.append(
                f"**{push_avatar} {b.members[i].name}**"
                f"\n{e('bstrophy')}"
                f" {b.members[i].trophies} "
                f"\n#{b.members[i].tag}"
            )

            experiences.append(
                f"**{exp_avatar} {_experiences[i].name}**"
                f"\n{e('xp')}"
                f" {_experiences[i].exp_level}"
                f"\n#{_experiences[i].tag}"
            )

    page1 = discord.Embed(description=b.description, color=random_color())
    page1.set_author(name=f"{b.name} (#{b.tag})")
    page1.set_footer(text=_('Statsy | Powered by brawlapi.cf'))
    page1.set_thumbnail(url=b.badge_url)
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Experienced Players for this club.'

    fields1 = [
        (_('Type'), f'{b.status} 📩'),
        (_('Score'), f'{b.trophies} Trophies {e("bstrophy")}'),
        (_('Members'), f'{b.members_count}/100 {e("gameroom")}'),
        (_('Required Trophies'), f'{b.required_trophies} {e("bstrophy")}'),
        (_('Online Players'), f'{b.online_members} {e("online")}')
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


def format_top_players(ctx, players):
    region = 'global'
    players = [box.Box(i, camel_killer_box=True) for i in json.loads(players.to_json())]

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} players right now.').format(region)
    em.set_author(name='Top Players', icon_url=players[0].avatar_url)
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf'))
    embeds = []
    counter = 0
    for c in players:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 {} players right now.').format(region)

            em.set_author(name=_('Top Players'), icon_url=players[0].avatar_url)
            em.set_footer(text=_('Statsy | Powered by brawlapi.cf'))

        try:
            club_name = c.club_name
        except AttributeError:
            club_name = 'No Clan'

        em.add_field(
            name=c.name,
            value=f"#{c.tag}"
                  f"\n{e('bstrophy')}{c.trophies}"
                  f"\n{e('bountystar')} Rank: {c.position} "
                  f"\n{e('xp')} XP Level: {c.exp_level}"
                  f"\n{e('gameroom')} {club_name}"
        )
        counter += 1
    embeds.append(em)
    return embeds


def format_top_clubs(ctx, clans):
    region = 'global'
    clans = [box.Box(i, camel_killer_box=True) for i in json.loads(clans.to_json())]

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} clubs right now.').format(region)
    em.set_author(name='Top Clubs', icon_url=clans[0].badge_url)
    em.set_footer(text=_('Statsy | Powered by brawlapi.cf'))
    embeds = []
    counter = 0
    for c in clans:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 {} clubs right now.').format(region)

            em.set_author(name=_('Top Clubs'), icon_url=clans[0].badge_url)
            em.set_footer(text=_('Statsy | Powered by brawlapi.cf'))

        em.add_field(
            name=c.name,
            value=f"#{c.tag}"
                  f"\n{e('bstrophy')}{c.trophies}"
                  f"\n{e('bountystar')} Rank: {c.position} "
                  f"\n{e('gameroom')} {c.members_count}/100 "
        )
        counter += 1
    embeds.append(em)
    return embeds


def format_events(ctx, events, type_):
    ems = []

    colors = {
        'Gem Grab': 0x9B3DF3,
        'Showdown': 0x81D621,
        'Heist': 0xD65CD3,
        'Bounty': 0x01CFFF,
        'Brawl Ball': 0x8CA0DF,
        'Robo Rumble': 0xAE0026,
        'Big Game': 0xDC2422,
        'Boss Fight': 0xDC2422
    }

    if type_ in ('current', 'all'):
        ems.append([])
        for i in events.current:
            ems[0].append(
                discord.Embed(
                    color=colors.get(i.game_mode, 0xfbce3f),
                    timestamp=ctx.cog.bs.get_datetime(i.end_time, unix=False)
                ).add_field(
                    name=f'{e(i.game_mode)} {i.game_mode}: {i.map_name}',
                    value=f'{e(i.modifier_name)} {i.modifier_name}' if i.has_modifier else 'No Modifiers'
                ).set_author(
                    name='Current Events'
                ).set_image(
                    url=i.map_image_url
                ).set_footer(
                    text='End Time'
                )
            )

    if type_ in ('upcoming', 'all'):
        ems.append([])
        for i in events.upcoming:
            ems[-1].append(
                discord.Embed(
                    color=colors.get(i.game_mode, 0xfbce3f),
                    timestamp=ctx.cog.bs.get_datetime(i.start_time, unix=False)
                ).add_field(
                    name=f'{e(i.game_mode)} {i.game_mode}: {i.map_name}',
                    value=f'{e(i.modifier_name)} {i.modifier_name}' if i.has_modifier else 'No Modifiers'
                ).set_author(
                    name='Upcoming Events'
                ).set_image(
                    url=i.map_image_url
                ).set_footer(
                    text='Start Time'
                )
            )

    return ems


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
            description=_('Top {} teams!\nLast updated: {} ago').format(len(leaderboard.best_teams), fmt),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 5 + rnd):
            minutes, seconds = divmod(leaderboard.best_teams[i].duration, 60)
            rankings = ''
            for num in range(1, 4):
                rankings += str(e(leaderboard.best_teams[i][f'brawler{num}'])) + ' ' + leaderboard.best_teams[i][f'player{num}'] + '\n'
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
            description=_('Top {} bosses!\n\nLast updated: {} ago\nMap: {}').format(len(leaderboard.best_players), fmt, leaderboard['activeLevel']),
            color=random_color()
        )
        em.set_footer(text='Statsy')

        for i in range(rnd, 10 + rnd):
            minutes, seconds = divmod(leaderboard.best_players[i].duration, 60)
            rankings = str(e(leaderboard.best_players[i].brawler)) + ' ' + leaderboard.best_players[i]['player'] + '\n'
            em.add_field(name=f'{minutes}m {seconds}s', value=rankings)

        embeds.append(em)

    return embeds


async def get_image(ctx, url):
    async with ctx.session.get(url) as resp:
        file = io.BytesIO(await resp.read())
    return file


async def format_random_brawler_and_send(ctx, brawler):
    image = await get_image(ctx, e(brawler).url)

    em = discord.Embed(title=brawler.title(), color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_image(url='attachment://brawler.png')

    await ctx.send(file=discord.File(image, 'brawler.png'), embed=em)


def format_club_stats(clan):
    return '\n'.join(
        (
            f"{e('gameroom')} {len(clan.members)}/100",
            f"{e('bsangel')} {clan.trophies}",
            f"{e('bstrophy2')} {clan.required_trophies} Required"
        )
    )


def format_brawler_stats(ctx, brawler):
    name = (brawler.tID or camel_case(brawler.name)).title()
    camel_name = camel_case(brawler.name, split='_').upper()
    rarity = next(i for i in ctx.cog.constants.cards if i.name == f'{brawler.name}_unlock').rarity

    colors = {
        'common': 0x94d7f4,
        'rare': 0x2edd1c,
        'epic': 0x0087fa,  # uncommon
        'super_rare': 0xb116ed,
        'mega_epic': 0xff0020,  # mythic
        'legendary': 0xfff11e
    }
    color = colors[rarity]
    ems = []
    ems.append(discord.Embed(
        # title='**`Basic Statistics`**',
        # description=,
        color=color
    ))
    ems[0].set_author(name=name, icon_url=e(brawler.tID).url)

    # page 1 - basic stats
    weapon_skill = next(i for i in ctx.cog.constants.skills if i.name == brawler.weapon_skill)
    weapon_card = next(i for i in ctx.cog.constants.cards if i.name == f'{brawler.name}_abi')
    ulti_skill = next(i for i in ctx.cog.constants.skills if i.name == brawler.ultimate_skill)
    ulti_card = next(i for i in ctx.cog.constants.cards if i.name == f'{brawler.name}_ulti')
    hp_card = next(i for i in ctx.cog.constants.cards if i.name == f'{brawler.name}_hp')

    if ulti_skill.summoned_character:
        pet = next(i for i in ctx.cog.constants.characters if i.name == ulti_skill.summoned_character)
    elif brawler.pet:
        pet = next(i for i in ctx.cog.constants.characters if i.name == brawler.pet)
    else:
        pet = None

    increase_hp = brawler.hitpoints // 20
    increase_weapon_damage = weapon_skill.damage // 20

    if ulti_skill.damage:
        increase_ulti_damage = ulti_skill.damage // 20

    ems[0].add_field(
        name='`Basic Statistics`',
        value=f"**```{ctx.cog.constants.texts[f'{camel_name}_DESC']}```**",
        inline=False
    )

    ems[0].add_field(name=f"{e('speedstat')} Speed", value=f'{brawler.speed / 300:.2f} tiles/second')
    ems[0].add_field(name=f"{e('rangestat')} Attack Range", value=f'{weapon_skill.casting_range / 3:.2f} tiles')

    if ulti_skill.casting_range and weapon_skill.casting_range != ulti_skill.casting_range:
        ems[0].add_field(name=f"{e('rangestat')} Super Range", value=f'{ulti_skill.casting_range / 3:.2f} tiles')

    ems[0].add_field(name=f"{e('reloadstat')} Reload Time", value=f'{weapon_skill.recharge_time} ms')
    ems[0].add_field(
        name=f"{e('reloadstat')} Animation Time",
        value=f'{(weapon_skill.active_time or 0) + (weapon_skill.cooldown or 0) + (weapon_skill.ms_between_attacks or 0)} ms'
    )  # might not be right :)

    # if weapon_skill.num_bullets_in_one_attack:
    #     ems[0].add_field(name=f"{e('bulletstat')} Number of bullets/attack", value=weapon_skill.num_bullets_in_one_attack)

    if weapon_skill.spread:
        ems[0].add_field(name=f"{e('bulletstat')} Bullet Spread", value=f'{weapon_skill.spread * 0.38:.2f}°')

    if pet:
        ems[0].add_field(
            name=f"`Super - {ctx.cog.constants.texts[f'{camel_name}_ULTI'].title()}`",
            value=f"**```{ctx.cog.constants.texts[f'{camel_name}_ULTI_DESC'].title()}```**",
            inline=False
        )
        increase_pet_hp = pet.hitpoints // 20
        if pet.speed:
            ems[0].add_field(name=f"{e('speedstat')} Pet Speed", value=f'{pet.speed / 300:.2f} tiles/second')

        if pet.auto_attack_damage:
            increase_pet_damage = pet.auto_attack_damage // 20
            ems[0].add_field(name=f"{e('speedstat')} Pet Attack Speed", value=f'{pet.auto_attack_speed_ms / 300:.2f} attacks/second')

    # page 1-9 brawler stats
    for i in range(9):
        ems.append(discord.Embed(
            title=f'Level {i + 1}',
            color=color
        ))
        ems[-1].set_author(name=name, icon_url=e(brawler.tID).url)

        ems[-1].add_field(
            name=f"`Attack - {weapon_card.tID.title()}`",
            value=f"**```{ctx.cog.constants.texts[f'{weapon_card.rawTID}_DESC'].title()}```**",
            inline=False
        )

        brawler.hitpoints += increase_hp
        weapon_skill.damage += increase_weapon_damage

        ems[-1].add_field(name=f"{e('healthstat')} {hp_card.powerNumberTID.title()}", value=brawler.hitpoints)
        ems[-1].add_field(name=f"{e('attackstat')} {weapon_card.powerNumberTID.title()}", value=weapon_skill.damage)
        ems[-1].add_field(name=f"{e('superstat')} Super Charge", value=f'{weapon_skill.damage * brawler.ulti_charge_mul / math.pi / 360 / 360 * 100:.2f}%')  # damage*UltiChargeMul/360/pi

        if brawler.charge_ulti_automatically:
            ems[-1].add_field(name=f"{e('superstat')} Super Regeneration", value=f'{weapon_skill.damage * brawler.charge_ulti_automatically / math.pi / 360 / 360 * 100:.2f}%/second')

        ems[-1].add_field(
            name=f"`Super - {ulti_card.tID.title()}`",
            value=f"**```{ctx.cog.constants.texts[f'{ulti_card.rawTID}_DESC'].title()}```**",
            inline=False
        )

        if ulti_skill.damage:
            ulti_skill.damage += increase_ulti_damage
            ems[-1].add_field(name=f"{e('superstat')} Super {ulti_card.powerNumberTID.title()}", value=ulti_skill.damage)

        if pet:
            pet.hitpoints += increase_pet_hp
            ems[-1].add_field(name=f"{e('healthstat')} {(ulti_card.powerNumber2TID or 'Pet HP').title()}", value=pet.hitpoints)

            if pet.auto_attack_damage:
                pet.auto_attack_damage += increase_pet_damage
                ems[-1].add_field(name=f"{e('attackstat')} {ulti_card.powerNumberTID.title()}", value=pet.auto_attack_damage)

    # star power
    star_power = next(i for i in ctx.cog.constants.cards if i.name == f'{brawler.name}_unique')
    description = clean(
        ctx.cog.constants.texts.get(f'SPEC_ABI_{star_power.type.upper()}_DESC', f'SPEC_ABI_{star_power.type.upper()}_DESC')
    ).replace('<VALUE1>', str(star_power.value)).replace('<VALUE2>', str(star_power.value2))

    ems.append(discord.Embed(
        title=f'Star Power - {star_power.tID}',
        description=description,
        color=color
    ))
    ems[-1].set_author(name=name, icon_url=e(brawler.tID).url)

    return ems
