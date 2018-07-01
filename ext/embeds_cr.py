import copy
import datetime
import math
import random
import re

import discord
from discord.ext import commands

from locales.i18n import Translator

_ = Translator('CR Embeds', __file__)

images = 'https://RoyaleAPI.github.io/RoyaleAPI-assets/'


def has_perms(add_reactions=True, external_emojis=True):
    perms = {
        'send_messages': True,
        'embed_links': True
    }

    if add_reactions:
        perms['add_reactions'] = True

    if external_emojis:
        perms['external_emojis'] = True
    return commands.bot_has_permissions(**perms)


def emoji(ctx, name, should_format=True):
    if should_format:
        name = name.replace('.', '').lower().replace(' ', '').replace('_', '').replace('-', '')
        if name == 'chestmagic':
            name = 'chestmagical'
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    return e or name


def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]


def random_color():
    return random.randint(0, 0xFFFFFF)


def get_deck(ctx, p):
    deck = ''
    for card in p.current_deck:
        deck += str(emoji(ctx, card.name)) + str(card.level) + ' '
    return deck


def timestamp(datatime: int):
    return str(
        (datetime.datetime.utcfromtimestamp(datatime) - datetime.datetime.utcnow()).total_seconds() / 60
    ) + ' minutes ago'


def get_clan_image(p):
    try:
        return p.clan.badge.image
    except:
        return 'https://i.imgur.com/Y3uXsgj.png'


def camel_case(text: str):
    # from stackoverflow :p
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', text)
    return ' '.join(m.group(0) for m in matches).title()


async def format_least_valuable(ctx, clan, cache=False):
    for m in clan.members:
        m.score = ((m.donations / 5) + ((m.clan_chest_crowns or 0) * 10) + (m.trophies / 7)) / 3
    to_kick = sorted(clan.members, key=lambda m: m.score)[:4]

    em = discord.Embed(
        color=random_color(),
        description=_('Here are the least valuable members of the clan currently.', ctx)
    )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{clan.name} (#{clan.tag})')
    em.set_thumbnail(url=clan.badge.image)
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    for m in reversed(to_kick):
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns or 0} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}"
        )
    return em


async def format_most_valuable(ctx, clan):
    # TODO CLAN_CHEST_CROWNS
    for m in clan.members:
        m.score = ((m.donations / 5) + ((m.clan_chest_crowns or 0) * 10) + (m.trophies / 7)) / 3

    best = sorted(clan.members, key=lambda m: m.score, reverse=True)[:4]

    em = discord.Embed(
        color=random_color(),
        description=_('Here are the most valuable members of the clan currently.', ctx)
    )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{clan.name} (#{clan.tag})')
    em.set_thumbnail(url=clan.badge.image)
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    for m in reversed(best):
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"#{m.tag}\n{m.trophies} "
            f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns or 0} "
            f"{emoji(ctx, 'crownblue')}\n{m.donations} "
            f"{emoji(ctx, 'cards')}"
        )

    return em


def get_chests(ctx, cycle):
    chests = '| ' + str(emoji(ctx, 'chest' + cycle.upcoming[0].lower())) + ' | '
    chests += ''.join([str(emoji(ctx, 'chest' + cycle.upcoming[x].lower())) for x in range(1, 8)])
    special = ''
    special_chests = ['superMagical', 'magical', 'legendary', 'epic', 'giant']
    for i in special_chests:
        e = emoji(ctx, 'chest' + i.lower())
        special += f"{e}+{cycle[i] + 1} "
    return (chests, special)


async def format_chests(ctx, p, c):
    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    em.set_author(name=f'{p.name} (#{p.tag})', icon_url=av)
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_thumbnail(url=emoji(ctx, 'chest' + c.upcoming[0].lower()).url)
    em.add_field(name=_('Chests', ctx), value=get_chests(ctx, c)[0])
    em.add_field(name=_('Chests Until', ctx), value=get_chests(ctx, c)[1])
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    return em


async def format_cards(ctx, p):
    constants = ctx.bot.constants

    name = p.name
    tag = p.tag

    rarity = {
        'Common': 1,
        'Rare': 2,
        'Epic': 3,
        'Legendary': 4
    }

    found_cards = p.cards
    found_cards_id = [getattr(i, 'id', None) for i in found_cards if getattr(i, 'id', None)] #cr-api#375
    notfound_cards = [i for i in constants.cards if i.id not in found_cards_id]

    found_cards = sorted(found_cards, key=lambda x: rarity[x.rarity.title()])
    notfound_cards = sorted(notfound_cards, key=lambda x: rarity[x.rarity.title()])

    def get_rarity(card):
        for a in constants.cards:
            if a.key.replace('-', '') == card:
                return a.rarity
        return 10495

    fmt = ''
    found_cards_pages = []
    oldcard = None
    for card in found_cards:
        if not card:
            continue

        if oldcard and oldcard.rarity.title() != card.rarity.title():
            try:
                found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
            except IndexError:
                found_cards_pages.append((fmt, fmt.split(':')[0]))
            fmt = str(emoji(ctx, card.name))
        else:
            fmt += str(emoji(ctx, card.name))

            if len(fmt) > 1024:
                fmt = fmt.replace(str(emoji(ctx, card.name)), '')
                try:
                    found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
                except IndexError:
                    found_cards_pages.append((fmt, fmt.split(':')[0]))
                fmt = str(emoji(ctx, card.name))
        oldcard = card
    try:
        found_cards_pages.append((fmt, get_rarity(fmt.split(':')[1])))
    except IndexError:
        found_cards_pages.append((fmt, fmt.split(':')[0]))

    fmt = ''
    notfound_cards_pages = []
    for card in notfound_cards:
        if not card:
            continue

        fmt += str(emoji(ctx, card.name))
        if len(fmt) > 1024:
            fmt = fmt.replace(str(emoji(ctx, card.name)), '')
            notfound_cards_pages.append(fmt)
            fmt = str(emoji(ctx, card.name))
    notfound_cards_pages.append(fmt)

    em = discord.Embed(description=_('A list of cards this player has.', ctx), color=random_color())
    em.set_author(name=f"{name} (#{tag})")
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    for i, r in found_cards_pages:
        if i:
            em.add_field(name=_('Found Cards ({}, ctx)').format(r), value=i, inline=False)

    for item in notfound_cards_pages:
        if item:
            em.add_field(name=_('Missing Cards', ctx), value=item, inline=False)
    return em


async def format_battles(ctx, battles, cache=False):

    em = discord.Embed(description='A list of battles played recently', color=random_color())

    for b in battles:
        if b.type == 'PvP':
            name = b.team[0].name
            tag = b.team[0].tag
            em.set_author(name=f"{name} (#{tag})")
            break

    crapi = 'https://royaleapi.com/profile/'

    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    i = 0
    for b in battles:
        if b.winner < 0:
            # OP Lost
            winner = 'crownred'
        elif b.winner > 0:
            # OP Won
            winner = 'crownblue'
        elif b.winner == 0:
            # Draw
            winner = 'crowngray'
        score = f'{b.team_crowns}-{b.opponent_crowns}'

        try:
            value = f'**[{b.team[0].name}]({crapi}{b.team[0].tag}) {emoji(ctx, "battle")} [{b.opponent[0].name}]({crapi}{b.opponent[0].tag}) \n[{b.team[1].name}]({crapi}{b.team[1].tag}) {emoji(ctx, "battle")} [{b.opponent[1].name}]({crapi}{b.opponent[1].tag})**'
        except IndexError:
            value = f'**[{b.team[0].name}]({crapi}{b.team[0].tag}) {emoji(ctx, "battle")} [{b.opponent[0].name}]({crapi}{b.opponent[0].tag})**'

        em.add_field(name=f'{b.type} {emoji(ctx, winner)} {score}', value=value, inline=False)

        i += 1
        if i > 5:
            break
    if not battles:
        em.add_field(name=_('No battles', ctx), value=_('Player has not played any battles yet', ctx))
    return em


async def format_members(ctx, c):
    em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f"{c.name} (#{c.tag})")
    em.set_thumbnail(url=c.badge.image)
    embeds = []
    counter = 0
    for m in c.members:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f"{c.name} (#{c.tag})")
            em.set_thumbnail(url=c.badge.image)
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"#{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'trophy')}\n{m.clan_chest_crowns or 0} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}"
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_top_clans(ctx, clans, region):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} clans right now.', ctx).format(region)
    badge_image = clans[0].badge.image
    if not badge_image.startswith('http'):
        badge_image = None
    em.set_author(name='Top Clans', icon_url=badge_image)
    embeds = []
    counter = 0
    for c in clans:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 global clans right now.', ctx)

            badge_image = c.badge.image
            if not badge_image.startswith('http'):
                badge_image = None
            em.set_author(name=_('Top Clans', ctx), icon_url=badge_image)
        em.add_field(
            name=f'{emoji(ctx, c.badge.name, should_format=False)} {c.name}',
            value=f"#{c.tag}"
                  f"{emoji(ctx, 'trophy')} {c.score}"
                  f"\n{emoji(ctx, 'rank')} Rank: {c.rank} "
                  f"\n{emoji(ctx, 'clan')} {c.member_count}/50 "
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_seasons(ctx, p):
    av = get_clan_image(p)
    embeds = []
    if p.league_statistics:
        for season in p.league_statistics.to_dict().keys():
            s = p.league_statistics[season]
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f'{p.name} (#{p.tag})', icon_url=av)
            em.set_thumbnail(url=emoji(ctx, 'legendarytrophy').url)
            try:
                em.add_field(name=_('{} Season', ctx).format(season.strip('Season').title()), value=s.id)
            except:
                if p.league_statistics.get('previous_season'):
                    prev = p.league_statistics.previous_season
                    old_time = prev.id.split('-')
                    time = [int(old_time[0]), int(old_time[1]) + 1]
                    if time[1] > 12:  # check month
                        time[0] += 1
                        time[1] = 1
                    em.add_field(name=_('{} Season', ctx).format(season.strip('Season').title()), value=f'{time[0]}-{time[1]}')
            try:
                em.add_field(name=_('Season Highest', ctx), value=f"{s.best_trophies} {emoji(ctx, 'trophy')}")
            except:
                pass
            try:
                em.add_field(name=_('Season Finish', ctx), value=f"{s.trophies} {emoji(ctx, 'trophy')}")
            except:
                pass
            try:
                em.add_field(name=_('Global Rank', ctx), value=f"{s.rank} {emoji(ctx, 'rank')}")
            except:
                pass

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
    em.set_author(name=_('{} Info', ctx).format(c.name), icon_url='attachment://card.png')
    em.add_field(name=_('Rarity', ctx), value=f"{c.rarity} {emoji(ctx, 'cards')}")
    em.add_field(name=_('Elixir Cost', ctx), value=f"{c.elixir} {emoji(ctx, 'elixirdrop')}")
    em.add_field(name=_('Type', ctx), value=f"{c.type} {emoji(ctx, 'challengedraft')}")
    em.add_field(name=_('Arena Found', ctx), value=f"{arenas[c.arena]} {emoji(ctx, 'arena'+str(c.arena))}")
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    return em


async def format_profile(ctx, p, c):

    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} (#{p.tag})', icon_url=av)
    em.set_thumbnail(url=images + 'arenas/arena' + str(p.arena.arena_id) + '.png')

    deck = get_deck(ctx, p)

    chests = get_chests(ctx, c)[0]

    special = ''
    trophies = f"{p.trophies}/{p.stats.max_trophies} PB {emoji(ctx, 'trophy')}"

    s = None
    if p.league_statistics:
        current_rank = p.league_statistics.current_season.get('rank')
        if p.league_statistics.get('previous_season'):
            s = p.league_statistics.previous_season
            global_r = s.get('rank')
            season = (
                _('Highest: {} {} \n', ctx).format(s.best_trophies, emoji(ctx, 'crownblue')),
                _('Finish: {} {} \n', ctx).format(s.trophies, emoji(ctx, 'trophy')),
                _('Global Rank: {} {}', ctx).format(global_r, emoji(ctx, 'rank'))
            )
        else:
            season = None
    else:
        current_rank = None
        season = None

    if p.clan:
        clan_role = p.clan.role.title()
    else:
        clan_role = None

    special = get_chests(ctx, c)[1]

    try:
        favourite_card = f"{p.stats.favorite_card.name} {emoji(ctx, p.stats.favorite_card.key.replace('-', ''))}"
    except AttributeError:
        favourite_card = _('No favourite card :(', ctx)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.stats.level} {emoji(ctx, 'experience')}", True),
        (_('Clan Name', ctx), f"{p.clan.name} {emoji(ctx, 'clan')}" if p.clan else None, True),
        (_('Clan Tag', ctx), f"#{p.clan.tag} {emoji(ctx, 'clan')}" if p.clan else None, True),
        (_('Clan Role', ctx), f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        (_('Games Played', ctx), f"{p.games.total} {emoji(ctx, 'battle')}", True),
        (_('Wins/Losses/Draws', ctx), f"{p.games.wins}/{p.games.losses}/{p.games.draws} {emoji(ctx, 'battle')}", True),
        (_('Three Crown Wins', ctx), f"{p.stats.three_crown_wins} {emoji(ctx, '3crown')}", True),
        (_('War Day Wins', ctx), f"{p.games.war_day_wins} {emoji(ctx, 'clanwar')}", True),
        (_('Favourite Card', ctx), favourite_card, True),
        (_('Tournament Cards Won', ctx), f"{p.stats.tournament_cards_won} {emoji(ctx, 'cards')}", True),
        (_('Challenge Cards Won', ctx), f"{p.stats.challenge_cards_won} {emoji(ctx, 'cards')}", True),
        (_('Challenge Max Wins', ctx), f"{p.stats.challenge_max_wins} {emoji(ctx, 'tournament')}", True),
        (_('Total Donations', ctx), f"{p.stats.total_donations} {emoji(ctx, 'cards')}", True),
        (_('Global Rank', ctx), f"{current_rank} {emoji(ctx, 'crownred')}" if current_rank else None, True),
        (_('Battle Deck', ctx), deck, True),
        (_('Chests', ctx), chests, False),
        (_('Chests Until', ctx), special, True),
        (_('Previous Season Results ({}, ctx)').format(s.id) if s else None, season, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == _('Clan Name', ctx):
                em.add_field(name=_('Clan', ctx), value=_('None {}', ctx).format(emoji(ctx, 'noclan')))

    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    return em


async def format_stats(ctx, p, cache=False):
    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} (#{p.tag})', icon_url=av)
    em.set_thumbnail(url=images + 'arenas/arena' + str(p.arena.arena_id) + '.png')

    trophies = f"{p.trophies}/{p.stats.max_trophies} PB {emoji(ctx, 'trophy')}"
    deck = get_deck(ctx, p)

    if p.clan:
        clan_role = p.clan.role.title()
    else:
        clan_role = None

    try:
        favourite_card = f"{p.stats.favorite_card.name} {emoji(ctx, p.stats.favorite_card.key.replace('-', ''))}"
    except AttributeError:
        favourite_card = _('No favourite card :(', ctx)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.stats.level} {emoji(ctx, 'experience')}", True),
        (_('Clan Name', ctx), f"{p.clan.name} {emoji(ctx, 'clan')}" if p.clan else None, True),
        (_('Clan Tag', ctx), f"#{p.clan.tag} {emoji(ctx, 'clan')}" if p.clan else None, True),
        (_('Clan Role', ctx), f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        (_('War Day Wins', ctx), f"{p.games.war_day_wins} {emoji(ctx, 'clanwar')}", True),
        (_('Favourite Card', ctx), favourite_card, True),
        (_('Battle Deck', ctx), deck, True)
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == _('Clan Name', ctx):
                em.add_field(name=_('Clan', ctx), value=_('None {}', ctx).format(emoji(ctx, 'noclan')))

    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    return em


async def format_clan(ctx, c, cache=False):
    page1 = discord.Embed(description=c.description, color=random_color())
    page1.set_author(name=f"{c.name} (#{c.tag})")
    page1.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    page2 = copy.deepcopy(page1)
    page2.description = _('Top Players/Donators/Contributors for this clan.', ctx)
    page1.set_thumbnail(url=c.badge.image)

    _donators = list(reversed(sorted(c.members, key=lambda m: m.donations)))

    pushers = []
    donators = []

    for i in range(3):
        if len(c.members) < i + 1:
            break
        pushers.append(
            f"**{c.members[i].name}**"
            f"\n{c.members[i].trophies} "
            f"{emoji(ctx, 'trophy')}\n"
            f"#{c.members[i].tag}"
        )
        donators.append(
            f"**{_donators[i].name}**"
            f"\n{_donators[i].donations} "
            f"{emoji(ctx, 'cards')}\n"
            f"#{_donators[i].tag}"
        )

    fields1 = [
        (_('Type', ctx), c.type.title() + ' 📩'),
        (_('Score', ctx), str(c.score) + _(' Trophies ', ctx) + str(emoji(ctx, 'trophy'))),
        (_('Donations/Week', ctx), str(c.donations) + _(' Cards ', ctx) + str(emoji(ctx, 'cards'))),
        (_('Location', ctx), c.location.name + ' 🌎'),
        (_('Members', ctx), str(len(c.members)) + f"/50 {emoji(ctx, 'clan')}"),
        (_('Required Trophies', ctx), f"{c.required_score} {emoji(ctx, 'trophy')}"),
    ]

    fields2 = [
        (_('Top Players', ctx), '\n\n'.join(pushers)),
        (_('Top Donators', ctx), '\n\n'.join(donators))
    ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    for f, v in fields2:
        if v:
            page2.add_field(name=f, value=v)

    return [page1, page2]


async def format_clan_war(ctx, w):
    page1 = discord.Embed(color=random_color())
    page1.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    if ctx.bot.psa_message:
        page1.description = ctx.bot.psa_message
    if w.state == 'notInWar':
        page1.add_field(name=_('Day', ctx), value=f'{camel_case(w.state)} {emoji(ctx, "clanwar")}')
        return [page1]

    page1.set_author(name=f"{w.clan.name} (#{w.clan.tag})", icon_url=w.clan.badge.image)

    page2 = copy.deepcopy(page1)
    return_vals = [page1, page2]

    fields1 = [
        (_('Day', ctx), f'{camel_case(w.state)} {emoji(ctx, "clanwar")}'),
        (_('War Trophies', ctx), f"{w.clan.war_trophies} Trophies {emoji(ctx, 'wartrophy')}"),
        (_('Participants', ctx), f"{w.clan.participants} {emoji(ctx, 'clan')}"),
        (_('Battles Played', ctx), f"{w.clan.battles_played} {emoji(ctx, 'battle')}"),
        (_('Wins', ctx), f"{w.clan.wins} {emoji(ctx, 'crownblue')}")
    ]

    if w.state == 'matchmaking':
        pass
    elif w.state == 'collectionDay':
        pass
    elif w.state == 'warDay':
        fields1.append(('Crowns', f'{w.clan.crowns} {emoji(ctx, "3crown")}'))
        page3 = copy.deepcopy(page1)

        standings = []

        for i in w.standings:
            standings.append(
                f"**{i.name}**",
                _('\n{} Batles Played {}', ctx).format(i.battles_played, emoji(ctx, 'battle')),
                _('\n{} Wins', ctx).format(i.wins, emoji(ctx, 'crownblue')),
                _('\n{} Crowns {}', ctx).format(i.crowns, emoji(ctx, '3crown')),
                f"\n#{i.tag}"
            )

        page3.add_field(name=_('Clans Participating', ctx), value='\n\n'.join(standings))
        return_vals.append(page3)

    else:
        raise NotImplementedError(f'{w.state} not implemented in format_clan_war (L632, ext/embeds_cr_crapi)')

    members = []

    for i in range(3):
        if len(w.participants) < i + 1:
            break
        members.append(
            f"**{w.participants[i].name}**",
            _('\n{} Batles Played {}', ctx).format(w.participants[i].battles_played, emoji(ctx, 'battle')),
            _('\n{} Wins', ctx).format(w.participants[i].wins, emoji(ctx, 'crownblue')),
            _('\n{} Cards Earned {}', ctx).format(w.participants[i].cards_earned, emoji(ctx, 'cards')),
            f"\n#{w.participants[i].tag}"
        )

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    page2.add_field(name=_('Top Fighters', ctx), value='\n\n'.join(members))

    return return_vals


async def format_tournaments(ctx, t):
    rewards = {
        50: (175, 25, 10),
        100: (700, 100, 20),
        200: (400, 57, 40),
        1000: (2000, 285, 200)
    }

    em = discord.Embed(description=_('A list of open tournaments you can join right now!', ctx), color=random_color())
    em.set_author(name=_('Open Tournaments', ctx))
    em.set_thumbnail(url='https://i.imgur.com/bwql3WU.png')

    if ctx.bot.psa_message:
        em.description = ctx.bot.psa_message
    em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    tournaments = sorted(t, key=lambda x: int(x.max_capacity))
    i = 0
    for t in tournaments:
        if t.player_count == t.max_capacity:
            continue

        members = '/'.join((str(t.player_count), str(t.max_capacity)))

        timeleft = ''
        date = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(t.create_time)
        seconds = math.floor(date.total_seconds())
        minutes = max(math.floor(seconds / 60), 0)
        seconds -= minutes * 60
        hours = max(math.floor(minutes / 60), 0)
        minutes -= hours * 60
        if hours > 0:
            timeleft += f'{hours}h'
        if minutes > 0:
            timeleft += f' {minutes}m'
        if seconds > 0:
            timeleft += f' {seconds}s'

        gold = rewards[t.max_capacity][1]
        cards = rewards[t.max_capacity][0]

        join_link = 'https://fourjr-webserver.herokuapp.com/redirect?url=https://link.clashroyale.com/?joinTournament?id=' + t.tag
        value = f'Time since creation: {timeleft}\n{members} {emoji(ctx, "clan")}\n{gold} {emoji(ctx, "gold")}\n{cards} {emoji(ctx, "cards")}\n[Join now]({join_link})'
        em.add_field(name=f'{t.name} (#{t.tag})', value=value)
        i += 1
        if i > 6:
            break

    return em


async def format_tournament(ctx, t):
    page1 = discord.Embed(description=t.description, color=random_color())
    page1.set_author(name=f"{t.name} (#{t.tag})")
    page1.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))
    page2 = copy.deepcopy(page1)
    page2.description = _('Top players of this tournament', ctx)

    pushers = []
    for i in range(9):
        pushers.append(
            f"**{t.members[i].name}**"
            f"\n{t.members[i].score} "
            f"{emoji(ctx, 'trophy')}\n"
            f"#{t.members[i].tag}"
        )

        timeleft = ''
        date = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(t.create_time)
        seconds = math.floor(date.total_seconds())
        minutes = max(math.floor(seconds / 60), 0)
        seconds -= minutes * 60
        hours = max(math.floor(minutes / 60), 0)
        minutes -= hours * 60
        if hours > 0:
            timeleft += f'{hours}h'
        if minutes > 0:
            timeleft += f' {minutes}m'
        if seconds > 0:
            timeleft += f' {seconds}s'

    fields1 = [
        (_('Type', ctx), camel_case(t.type) + ' 📩'),
        (_('Status', ctx), camel_case(t.status)),
        (_('Members', ctx), f"{t.player_count}/{t.max_capacity} {emoji(ctx, 'clan')}"),
        (_('Time since creation', ctx), timeleft)
    ]

    fields2 = [
        (_('Top Players', ctx), '\n\n'.join(pushers[0:3])),
        (_('Top Players', ctx), '\n\n'.join(pushers[3:6])),
        (_('Top Players', ctx), '\n\n'.join(pushers[6:9]))
    ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    for f, v in fields2:
        if v:
            page2.add_field(name=f, value=v)

    return [page1, page2]


async def format_friend_link(ctx, p, link, default):
    av = get_clan_image(p)
    em = discord.Embed(color=random_color())
    if not link.startswith('http'):
        link = 'https://' + link

    em.description = f'[Add {ctx.author.mention} as friend {emoji(ctx, "clan")}]({link})'
    if default:
        prefix = (await ctx.bot.get_prefix(ctx.message))[2]
        em.set_footer(text=_('Run `{}friendlink disable` to disable this feature', ctx).format(prefix))
    else:
        em.set_footer(text=_('Statsy - Powered by RoyaleAPI.com', ctx))

    em.set_author(name=f'{p.name} (#{p.tag})', icon_url=av)
    em.set_thumbnail(url=images + 'arenas/arena' + str(p.arena.arena_id) + '.png')

    trophies = f"{p.trophies}/{p.stats.max_trophies} PB {emoji(ctx, 'trophy')}"
    deck = get_deck(ctx, p)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.stats.level} {emoji(ctx, 'experience')}", True),
        (_('Battle Deck', ctx), deck, False)
    ]

    for n, v, i in embed_fields:
        em.add_field(name=n, value=v, inline=i)

    return em
