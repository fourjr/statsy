import copy
import datetime
import math
import re

import discord

from ext.utils import emoji, random_color
from locales.i18n import Translator

_ = Translator('CR Embeds', __file__)

images = 'https://royaleapi.github.io/cr-api-assets/'


def camel_case(text):
    # from stackoverflow :p
    if text is None:
        return text
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', text)
    return ' '.join(m.group(0) for m in matches).title()


def get_card_level(level, max_level):
    rarity_mapping = {
        13: 0,  # common
        11: 2,  # rare
        8: 5,   # epic
        5: 8,   # legendary
    }
    try:
        return level + rarity_mapping[max_level]
    except KeyError as e:
        raise NotImplementedError(f'get_card_level({level}, {max_level}) - {max_level} not implemented') from e


def get_deck(ctx, p):
    deck = ''
    for card in p.current_deck:
        deck += str(emoji(ctx, card.name)) + str(get_card_level(card.level, card.max_level)) + ' '
    return deck


def timestamp(datatime: int):
    return str(
        (datetime.datetime.utcfromtimestamp(datatime) - datetime.datetime.utcnow()).total_seconds() / 60
    ) + ' minutes ago'


async def format_least_valuable(ctx, clan, wars):
    def war_score(tag):
        score = 0
        for w in wars:
            if tag in [i.tag for i in w.participants]:
                score += 1

        return score

    for m in clan.member_list:
        m.war_score = war_score(m.tag)
        m.score = ((m.donations / 5) + (m.war_score / 3) + (m.trophies / 7)) / 3

    to_kick = sorted(clan.member_list, key=lambda m: m.score)[:4]

    em = discord.Embed(
        color=random_color(),
        description=_('Here are the least valuable members of the clan currently.', ctx)
    )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{clan.name} ({clan.tag})')
    em.set_thumbnail(url=ctx.cog.cr.get_clan_image(clan))
    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    for m in reversed(to_kick):
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}\n"
                  f"{m.war_score} {emoji(ctx, 'clanwar')}"
        )
    return em


async def format_most_valuable(ctx, clan, wars):
    def war_score(tag):
        score = 0
        for w in wars:
            if tag in [i.tag for i in w.participants]:
                score += 1

        return score

    for m in clan.member_list:
        m.war_score = war_score(m.tag)
        m.score = ((m.donations / 5) + (m.war_score / 3) + (m.trophies / 7)) / 3

    best = sorted(clan.member_list, key=lambda m: m.score, reverse=True)[:4]

    em = discord.Embed(
        color=random_color(),
        description=_('Here are the most valuable members of the clan currently.', ctx)
    )
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{clan.name} ({clan.tag})')
    em.set_thumbnail(url=ctx.cog.cr.get_clan_image(clan))
    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    for m in reversed(best):
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"{m.tag}\n{m.trophies} "
            f"{emoji(ctx, 'crownblue')}\n{m.donations} "
            f"{emoji(ctx, 'cards')}\n"
            f"{m.war_score} {emoji(ctx, 'clanwar')}"
        )

    return em


def get_chests(ctx, cycle):
    chests = '| ' + str(emoji(ctx, 'chest' + cycle[0].name.replace(' Chest', ''))) + ' | '
    chests += ''.join([str(emoji(ctx, 'chest' + cycle[x].name.replace(' Chest', ''))) for x in range(1, 8)])
    special = ''

    for i in range(9, 15):
        try:
            e = emoji(ctx, 'chest' + cycle[i].name.replace(' Chest', '').lower())
            special += f"{e}+{cycle[i].index + 1} "
        except IndexError:
            break

    return (chests, special)


async def format_chests(ctx, p, c):
    av = ctx.cog.cr.get_clan_image(p)
    em = discord.Embed(color=random_color())
    em.set_author(name=f'{p.name} ({p.tag})', icon_url=av)
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    chests = get_chests(ctx, c)
    em.set_thumbnail(url=emoji(ctx, 'chest' + c[0].name.replace(' Chest', '').lower()).url)
    em.add_field(name=_('Chests', ctx), value=chests[0])
    em.add_field(name=_('Chests Until', ctx), value=chests[1])
    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    return em


async def format_cards(ctx, p):
    constants = ctx.cog.cr.constants

    name = p.name
    tag = p.tag

    rarity = {
        'Common': 1,
        'Rare': 2,
        'Epic': 3,
        'Legendary': 4
    }

    found_cards = p.cards
    notfound_cards = [i for i in constants.cards if i.name not in [k.name for k in found_cards]]

    def get_rarity(card):
        for i in constants.cards:
            if i.name == card or i.key.replace('-', '') == card:
                return i.rarity

    found_cards = sorted(found_cards, key=lambda x: rarity[get_rarity(x.name)])
    notfound_cards = sorted(notfound_cards, key=lambda x: rarity[get_rarity(x.name)])

    fmt = ''
    found_cards_pages = []
    oldcard = None
    for card in found_cards:
        if not card:
            continue
        card.rarity = get_rarity(card.name)

        if oldcard and oldcard.rarity != card.rarity:
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
    em.set_author(name=f"{name} ({tag})")
    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    for i, r in found_cards_pages:
        if i:
            em.add_field(name=_('Found Cards ({})', ctx).format(r), value=i, inline=False)

    for item in notfound_cards_pages:
        if item:
            em.add_field(name=_('Missing Cards', ctx), value=item, inline=False)
    return em


async def format_battles(ctx, battles):

    em = discord.Embed(description='A list of battles played recently', color=random_color())

    for b in battles:
        if b.type == 'PvP':
            name = b.team[0].name
            tag = b.team[0].tag
            em.set_author(name=f"{name} ({tag})")
            break

    crapi = 'https://royaleapi.com/profile/'

    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'

    i = 0
    for b in battles:
        b.winner = b.team[0].crowns - b.opponent[0].crowns
        if b.winner < 0:
            # OP Lost
            winner = 'crownred'
        elif b.winner > 0:
            # OP Won
            winner = 'crownblue'
        elif b.winner == 0:
            # Draw
            winner = 'crowngray'
        score = f'{b.team[0].crowns}-{b.opponent[0].crowns}'

        try:
            value = f'**[{b.team[0].name}]({crapi}{b.team[0].tag}) {emoji(ctx, "battle")} [{b.opponent[0].name}]({crapi}{b.opponent[0].tag}) \n[{b.team[1].name}]({crapi}{b.team[1].tag}) {emoji(ctx, "battle")} [{b.opponent[1].name}]({crapi}{b.opponent[1].tag})**'
        except IndexError:
            value = f'**[{b.team[0].name}]({crapi}{b.team[0].tag}) {emoji(ctx, "battle")} [{b.opponent[0].name}]({crapi}{b.opponent[0].tag})**'

        em.add_field(name=f'{camel_case(b.type)} {emoji(ctx, winner)} {score}', value=value, inline=False)

        i += 1
        if i > 5:
            break
    if not battles:
        em.add_field(name=_('No battles', ctx), value=_('Player has not played any battles yet', ctx))
    return em


async def format_members(ctx, c, ws):
    em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f"{c.name} ({c.tag})")
    em.set_thumbnail(url=ctx.cog.cr.get_clan_image(c))
    embeds = []
    counter = 0

    def war_score(tag):
        score = 0
        for w in ws:
            if tag in [i.tag for i in w.participants]:
                score += 1

        return score

    for m in c.member_list:
        if counter % 6 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(description=_('A list of all members in this clan.', ctx), color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f"{c.name} ({c.tag})")
            em.set_thumbnail(url=ctx.cog.cr.get_clan_image(c))
        em.add_field(
            name=f'{m.name} ({camel_case(m.role)})',
            value=f"{m.tag}\n{m.trophies} "
                  f"{emoji(ctx, 'crownblue')}\n{m.donations} "
                  f"{emoji(ctx, 'cards')}\n"
                  f"{war_score(m.tag)} {emoji(ctx, 'clanwar')}"
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_lb(ctx, players, tag, emoji_name, *statistics, **kwargs):
    color = random_color()
    embeds = [discord.Embed(
        title=_('{} Leaderboard', ctx).format(kwargs.get('name', ctx.command.name.title())),
        description='',
        color=color
    )]

    n = 0
    found_user = [False, 0]
    users = []
    previous_page = False
    for p in players:
        user = ctx.guild.get_member(int(p.split('-')[0]))

        stat = players[p]
        for i in statistics:
            stat = stat[i]

        if user:
            str_n = f'0{n + 1}' if n + 1 < 10 else n + 1
            embeds[-1].description += f'`{str_n}.` {emoji(ctx, emoji_name)} `{stat}`: {players[p]["name"]} ({players[p]["tag"]}) - {user}\n'
            n += 1

            if found_user[0]:
                cur_line = len(embeds[-1].description.splitlines()) - 1
                try:
                    users[found_user[1] + 3] = embeds[-1].description.splitlines()[cur_line]
                except IndexError:
                    cur_line = 9
                    users[found_user[1] + 3] = embeds[len(embeds) - 2].description.splitlines()[cur_line]
                cur_line -= 1

                found_user[1] += 1
                if found_user[1] >= 2:
                    found_user[0] = False

            if p == f'{ctx.author.id}-{tag}':
                cur_line = len(embeds[-1].description.splitlines()) - 1
                users = ['', '', f'**{embeds[-1].description.splitlines()[cur_line]}**', '', '']
                found_user[0] = True
                cur_line -= 2
                for i in range(2):
                    try:
                        users[i] = embeds[-1].description.splitlines()[cur_line]
                    except IndexError:
                        if not previous_page:
                            cur_line = 8
                            previous_page = True
                        try:
                            users[i] = embeds[-2].description.splitlines()[cur_line]
                        except IndexError:
                            break
                    cur_line += 1

            if (n % 10) == 0:
                embeds.append(discord.Embed(
                    title=_('{} Leaderboard', ctx).format(kwargs.get('name', ctx.command.name.title())),
                    description='',
                    color=color
                ))

    try:
        list(players.keys()).index(f'{ctx.author.id}-{tag}')
    except ValueError:
        value = _("Your data has not been recieved yet. Either your tag isn't saved or you have to wait a while", ctx)
    else:
        value = '\n'.join(users)

    for x in embeds:
        if x.description:
            x.add_field(name=_('Your position', ctx), value=value)
        else:
            embeds.remove(x)

    return embeds


async def format_top_players(ctx, players, region):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} players right now.', ctx).format(region)
    badge_image = ctx.cog.cr.get_clan_image(players[0])
    em.set_author(name='Top Players', icon_url=badge_image)
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

            badge_image = ctx.cog.cr.get_clan_image(players[0])
            em.set_author(name=_('Top Players', ctx), icon_url=badge_image)

        try:
            clan_name = c.clan.name
        except AttributeError:
            clan_name = 'No Clan'

        em.add_field(
            name=f'{emoji(ctx, c.arena.id)} {c.name}',
            value=f"{c.tag}"
                  f"\n{emoji(ctx, 'trophy')}{c.trophies}"
                  f"\n{emoji(ctx, 'rank')} Rank: {c.rank} "
                  f"\n{emoji(ctx, 'rank')} Previous Rank: {c.previous_rank}"
                  f"\n{emoji(ctx, 'clan')} {clan_name}"
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
    badge_image = ctx.cog.cr.get_clan_image(clans[0])
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
                em.description = _('Top 200 {} clans right now.', ctx).format(region)

            badge_image = ctx.cog.cr.get_clan_image(clans[0])
            em.set_author(name=_('Top Clans', ctx), icon_url=badge_image)

        em.add_field(
            name=f'{emoji(ctx, c.badge_id, should_format=False)} {c.name}',
            value=f"{c.tag}"
                  f"\n{emoji(ctx, 'trophy')}{c.clan_score}"
                  f"\n{emoji(ctx, 'rank')} Rank: {c.rank} "
                  f"\n{emoji(ctx, 'rank')} Previous Rank: {c.previous_rank}"
                  f"\n{emoji(ctx, 'clan')} {c.members}/50 "
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_top_clan_wars(ctx, clans, region):
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    else:
        em.description = _('Top 200 {} clans by clan wars right now.', ctx).format(region)
    badge_image = ctx.cog.cr.get_clan_image(clans[0])
    em.set_author(name='Top Clans By Clan Wars', icon_url=badge_image)
    embeds = []
    counter = 0
    for c in clans:
        if counter % 12 == 0 and counter != 0:
            embeds.append(em)
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            else:
                em.description = _('Top 200 {} clans by clan wars right now.', ctx).format(region)

            badge_image = ctx.cog.cr.get_clan_image(clans[0])
            em.set_author(name=_('Top Clans', ctx), icon_url=badge_image)

        em.add_field(
            name=f'{emoji(ctx, c.badge_id, should_format=False)} {c.name}',
            value=f"{c.tag}"
                  f"\n{emoji(ctx, 'wartrophy')}{c.clan_score}"
                  f"\n{emoji(ctx, 'rank')} Rank: {c.rank} "
                  f"\n{emoji(ctx, 'rank')} Previous Rank: {c.previous_rank}"
                  f"\n{emoji(ctx, 'clan')} {c.members}/50 "
        )
        counter += 1
    embeds.append(em)
    return embeds


async def format_seasons(ctx, p):
    av = ctx.cog.cr.get_clan_image(p)
    embeds = []
    if p.league_statistics:
        for season in p.league_statistics.to_dict().keys():
            s = p.league_statistics[season]
            em = discord.Embed(color=random_color())
            if ctx.bot.psa_message:
                em.description = f'*{ctx.bot.psa_message}*'
            em.set_author(name=f'{p.name} ({p.tag})', icon_url=av)
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


async def format_deck(ctx, p):
    deck_link = 'https://link.clashroyale.com/deck/en?deck='
    elixir = 0

    for i in p.current_deck:
        card = ctx.cog.cr.get_card_info(i.name)
        deck_link += f'{card.id};'
        elixir += card.elixir

    elixir = elixir / len(p.current_deck)

    deck = f'{get_deck(ctx, p)}\n{elixir:.1f}{emoji(ctx, "elixirdrop")}'

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} ({p.tag})', icon_url=ctx.cog.cr.get_clan_image(p))
    em.add_field(name='Current Deck', value=f'{deck}[Copy this deck!]({deck_link}) {emoji(ctx, "copydeck")}')
    em.set_footer(text='Statsy - Powered by the CR API')

    return em


async def format_card(ctx, c):
    arenas = {i.arena: i.title for i in ctx.cog.cr.constants.arenas}

    em = discord.Embed(description=c.description, color=random_color())
    em.set_author(name=_('{} Info', ctx).format(c.name), icon_url='attachment://card.png')
    em.add_field(name=_('Rarity', ctx), value=f"{c.rarity} {emoji(ctx, 'cards')}")
    em.add_field(name=_('Elixir Cost', ctx), value=f"{c.elixir} {emoji(ctx, 'elixirdrop')}")
    em.add_field(name=_('Type', ctx), value=f"{c.type} {emoji(ctx, 'challengedraft')}")
    em.add_field(name=_('Arena Found', ctx), value=f"{arenas[c.arena]} {emoji(ctx, 'arena'+str(c.arena))}")
    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    return em


async def format_profile(ctx, p, c):

    av = ctx.cog.cr.get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} ({p.tag})', icon_url=av)
    em.set_thumbnail(url=ctx.cog.cr.get_arena_image(p))

    deck = get_deck(ctx, p)

    chests = get_chests(ctx, c)[0]

    trophies = f"{p.trophies}/{p.best_trophies} PB {emoji(ctx, 'trophy')}"

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

    try:
        clan_name = p.clan.name
        clan_tag = p.clan.tag
        clan_role = camel_case(p.role)
    except AttributeError:
        clan_name = clan_tag = clan_role = None

    special = get_chests(ctx, c)[1]

    try:
        favourite_card = f"{p.current_favourite_card.name} {emoji(ctx, p.current_favourite_card.name)}"
    except AttributeError:
        favourite_card = _('No favourite card :(', ctx)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.exp_level} {emoji(ctx, 'experience')}", True),
        (_('Clan Name', ctx), f"{clan_name} {emoji(ctx, 'clan')}" if clan_name else None, True),
        (_('Clan Tag', ctx), f"{clan_tag} {emoji(ctx, 'clan')}" if clan_tag else None, True),
        (_('Clan Role', ctx), f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        (_('Clans Joined', ctx), f"{p.achievements[0].value} {emoji(ctx, 'clan')}", True),
        (_('Games Played', ctx), f"{p.battle_count} {emoji(ctx, 'battle')}", True),
        (_('Friendly Battles Won', ctx), f"{p.achievements[9].value} {emoji(ctx, 'battle')}", True),
        (_('Wins/Losses', ctx), f"{p.wins}/{p.losses} {emoji(ctx, 'battle')}", True),
        (_('Three Crown Wins', ctx), f"{p.three_crown_wins} {emoji(ctx, '3crown')}", True),
        (_('War Day Wins', ctx), f"{p.war_day_wins} {emoji(ctx, 'clanwar')}", True),
        (_('Favourite Card', ctx), favourite_card, True),
        (_('Tournaments Played', ctx), f"{p.achievements[7].value} {emoji(ctx, 'tournament')}", True),
        (_('Tournament Cards Won', ctx), f"{p.tournament_cards_won} {emoji(ctx, 'cards')}", True),
        (_('Challenge Cards Won', ctx), f"{p.challenge_cards_won} {emoji(ctx, 'cards')}", True),
        (_('Challenge Max Wins', ctx), f"{p.challenge_max_wins} {emoji(ctx, 'tournament')}", True),
        (_('Total Donations', ctx), f"{p.total_donations} {emoji(ctx, 'cards')}", True),
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

    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    return em


async def format_stats(ctx, p):
    av = ctx.cog.cr.get_clan_image(p)
    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{p.name} ({p.tag})', icon_url=av)
    em.set_thumbnail(url=ctx.cog.cr.get_arena_image(p))

    trophies = f"{p.trophies}/{p.best_trophies} PB {emoji(ctx, 'trophy')}"
    deck = get_deck(ctx, p)

    try:
        clan_name = p.clan.name
        clan_tag = p.clan.tag
        clan_role = camel_case(p.role)
    except AttributeError:
        clan_name = clan_tag = clan_role = None

    try:
        favourite_card = f"{p.current_favourite_card.name} {emoji(ctx, p.current_favourite_card.name)}"
    except AttributeError:
        favourite_card = _('No favourite card :(', ctx)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.exp_level} {emoji(ctx, 'experience')}", True),
        (_('Clan Name', ctx), f"{clan_name} {emoji(ctx, 'clan')}" if clan_name else None, True),
        (_('Clan Tag', ctx), f"{clan_tag} {emoji(ctx, 'clan')}" if clan_tag else None, True),
        (_('Clan Role', ctx), f"{clan_role} {emoji(ctx, 'clan')}" if clan_role else None, True),
        (_('War Day Wins', ctx), f"{p.war_day_wins} {emoji(ctx, 'clanwar')}", True),
        (_('Favourite Card', ctx), favourite_card, True),
        (_('Battle Deck', ctx), deck, True)
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)
        else:
            if n == _('Clan Name', ctx):
                em.add_field(name=_('Clan', ctx), value=_('None {}', ctx).format(emoji(ctx, 'noclan')))

    em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    return em


async def format_clan(ctx, c):
    page1 = discord.Embed(description=c.description, color=random_color())
    page1.set_author(name=f"{c.name} ({c.tag})")
    page1.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    page2 = copy.deepcopy(page1)
    page2.description = _('Top Players/Donators/Contributors for this clan.', ctx)
    page1.set_thumbnail(url=ctx.cog.cr.get_clan_image(c))

    _donators = list(reversed(sorted(c.member_list, key=lambda m: m.donations)))

    pushers = []
    donators = []

    for i in range(3):
        if len(c.member_list) < i + 1:
            break
        pushers.append(
            f"**{c.member_list[i].name}**"
            f"\n{c.member_list[i].trophies} "
            f"{emoji(ctx, 'trophy')}\n"
            f"{c.member_list[i].tag}"
        )
        donators.append(
            f"**{_donators[i].name}**"
            f"\n{_donators[i].donations} "
            f"{emoji(ctx, 'cards')}\n"
            f"{_donators[i].tag}"
        )

    fields1 = [
        (_('Type', ctx), camel_case(c.type) + ' 📩'),
        (_('Score', ctx), str(c.clan_score) + _(' Trophies ', ctx) + str(emoji(ctx, 'trophy'))),
        (_('Donations/Week', ctx), str(c.donations_per_week) + _(' Cards ', ctx) + str(emoji(ctx, 'cards'))),
        (_('Location', ctx), c.location.name + ' 🌎'),
        (_('Members', ctx), f"{len(c.member_list)}/50 {emoji(ctx, 'clan')}"),
        (_('Required Trophies', ctx), f"{c.required_trophies} {emoji(ctx, 'trophy')}"),
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
    page1.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    if ctx.bot.psa_message:
        page1.description = ctx.bot.psa_message

    if w.state == 'notInWar':
        page1.add_field(name=_('Day', ctx), value=f'{camel_case(w.state)} {emoji(ctx, "clanwar")}')
        return [page1]

    page1.set_author(name=f"{w.clan.name} ({w.clan.tag})", icon_url=ctx.cog.cr.get_clan_image(w))

    page2 = copy.deepcopy(page1)
    return_vals = [page1, page2]

    fields1 = [
        (_('Day', ctx), f'{camel_case(w.state)} {emoji(ctx, "clanwar")}'),
        (_('War Trophies', ctx), f"{w.clan.clan_score} Trophies {emoji(ctx, 'wartrophy')}"),
        (_('Participants', ctx), f"{w.clan.participants} {emoji(ctx, 'clan')}"),
        (_('Battles Played', ctx), f"{w.clan.battles_played} {emoji(ctx, 'battle')}"),
        (_('Wins', ctx), f"{w.clan.wins} {emoji(ctx, 'crownblue')}")
    ]

    if w.state in ('matchmaking', 'collectionDay'):
        pass
    elif w.state == 'warDay':
        fields1.append(('Crowns', f'{w.clan.crowns} {emoji(ctx, "3crown")}'))
        page3 = copy.deepcopy(page1)

        standings = []

        for i in w.clans:
            standings.append(''.join((
                f"**{i.name}**",
                _('\n{} Batles Played {}', ctx).format(i.battles_played, emoji(ctx, 'battle')),
                _('\n{} Wins', ctx).format(i.wins, emoji(ctx, 'crownblue')),
                _('\n{} Crowns {}', ctx).format(i.crowns, emoji(ctx, '3crown')),
                f"\n{i.tag}"
            )))

        page3.add_field(name=_('Clans Participating', ctx), value='\n\n'.join(standings))
        return_vals.append(page3)

    else:
        raise NotImplementedError(f'{w.state} not implemented in format_clan_war (L632, ext/embeds_cr_crapi)')

    members = []

    for i in range(3):
        if len(w.participants) < i + 1:
            break
        members.append(''.join((
            f"**{w.participants[i].name}**",
            _('\n{} Batles Played {}', ctx).format(w.participants[i].battles_played, emoji(ctx, 'battle')),
            _('\n{} Wins', ctx).format(w.participants[i].wins, emoji(ctx, 'crownblue')),
            _('\n{} Cards Earned {}', ctx).format(w.participants[i].cards_earned, emoji(ctx, 'cards')),
            f"\n{w.participants[i].tag}"
        )))

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
    em.set_footer(text=_('Statsy | Powered by RoyaleAPI', ctx))

    tournaments = sorted(t, key=lambda x: int(x.max_players))
    i = 0
    for t in tournaments:
        if t.current_players == t.max_players:
            continue

        members = '/'.join((str(t.current_players), str(t.max_players)))

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

        gold = rewards[t.max_players][1]
        cards = rewards[t.max_players][0]

        join_link = 'https://fourjr-webserver.herokuapp.com/redirect?url=https://link.clashroyale.com/?joinTournament?id=' + t.tag
        value = f'Time since creation: {timeleft}\n{members} {emoji(ctx, "clan")}\n{gold} {emoji(ctx, "gold")}\n{cards} {emoji(ctx, "cards")}\n[Join now]({join_link})'
        em.add_field(name=f'{t.name} ({t.tag})', value=value)
        i += 1
        if i > 6:
            break

    return em


async def format_tournament(ctx, t):
    page1 = discord.Embed(description=t.description, color=random_color())
    page1.set_author(name=f"{t.name} ({t.tag})")
    page1.set_footer(text=_('Statsy | Powered by the CR API', ctx))
    page2 = copy.deepcopy(page1)
    page2.description = _('Top players of this tournament', ctx)

    pushers = []
    for i in range(9):
        if i < len(t.members_list):
            break
        pushers.append(
            f"**{t.members_list[i].name}**"
            f"\n{t.members_list[i].score} "
            f"{emoji(ctx, 'trophy')}\n"
            f"{t.members_list[i].tag}"
        )

    timeleft = ''
    date = datetime.datetime.utcnow() - datetime.datetime.strptime(t.created_time, '%Y%m%dT%H%M%S.%fZ')
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

    join_link = 'https://fourjr-webserver.herokuapp.com/redirect?url=https://link.clashroyale.com/?joinTournament?id=' + t.tag

    fields1 = [
        (_('Type', ctx), camel_case(t.type) + ' 📩'),
        (_('Status', ctx), camel_case(t.status)),
        (_('Members', ctx), f"{len(t.members_list)}/{t.max_capacity} {emoji(ctx, 'clan')}"),
        (_('Time since creation', ctx), timeleft),
        (_('Join now', ctx), _('[Click here]({})', ctx).format(join_link))
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
    av = ctx.cog.cr.get_clan_image(p)
    if not link.startswith('http'):
        link = 'https://' + link

    em = discord.Embed(
        description=f'[Add]({link}) {ctx.author.mention} [as friend {emoji(ctx, "clan")}]({link})',
        color=random_color()
    )

    if default:
        prefix = (await ctx.bot.get_prefix(ctx.message))[2]
        em.set_footer(text=_('Run `{}link disable` to disable this feature', ctx).format(prefix))
    else:
        em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    em.set_author(name=f'{p.name} ({p.tag})', icon_url=av)
    em.set_thumbnail(url=ctx.cog.cr.get_arena_image(p))

    trophies = f"{p.trophies}/{p.best_trophies} PB {emoji(ctx, 'trophy')}"
    deck = get_deck(ctx, p)

    embed_fields = [
        (_('Trophies', ctx), trophies, True),
        (_('Level', ctx), f"{p.exp_level} {emoji(ctx, 'experience')}", True),
        (_('Battle Deck', ctx), deck, False)
    ]

    for n, v, i in embed_fields:
        em.add_field(name=n, value=v, inline=i)

    return em


async def format_clan_link(ctx, c, link, default):
    av = ctx.cog.cr.get_clan_image(c)
    if not link.startswith('http'):
        link = 'https://' + link

    em = discord.Embed(
        description=f"[Join]({link}) {ctx.author.mention}['s clan! {emoji(ctx, 'clan')}]({link})",
        color=random_color()
    )

    if default:
        prefix = (await ctx.bot.get_prefix(ctx.message))[2]
        em.set_footer(text=_('Run `{}link disable` to disable this feature', ctx).format(prefix))
    else:
        em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    em.set_author(name=f'{c.name} ({c.tag})')
    em.set_thumbnail(url=ctx.cog.cr.get_arena_image(av))

    embed_fields = [
        (_('Type', ctx), camel_case(c.type) + ' 📩'),
        (_('Score', ctx), str(c.clan_score) + _(' Trophies ', ctx) + str(emoji(ctx, 'trophy'))),
        (_('Donations/Week', ctx), str(c.donations_per_week) + _(' Cards ', ctx) + str(emoji(ctx, 'cards'))),
        (_('Location', ctx), c.location.name + ' 🌎'),
        (_('Members', ctx), f"{len(c.member_list)}/50 {emoji(ctx, 'clan')}"),
        (_('Required Trophies', ctx), f"{c.required_trophies} {emoji(ctx, 'trophy')}"),
    ]

    for n, v, i in embed_fields:
        em.add_field(name=n, value=v, inline=i)

    return em


async def format_deck_link(ctx, d, link, default):
    deck = ''
    elixir = 0
    for n, i in enumerate(d):
        for c in ctx.cog.cr.constants.cards:
            if str(c.id) == i:
                deck += str(emoji(ctx, c.name))
                elixir += c.elixir
                if n == 3:
                    deck += '\n'
                break

    elixir = elixir / len(d)
    deck += f'\n{elixir:.1f}{emoji(ctx, "elixirdrop")} [Copy this deck!]({link}) {emoji(ctx, "copydeck")}'
    em = discord.Embed(
        title=f'Deck shared by {ctx.author.name}',
        description=deck,
        color=random_color()
    )
    if not link.startswith('http'):
        link = 'https://' + link

    if default:
        prefix = (await ctx.bot.get_prefix(ctx.message))[2]
        em.set_footer(text=_('Run `{}link disable` to disable this feature', ctx).format(prefix))
    else:
        em.set_footer(text=_('Statsy | Powered by the CR API', ctx))

    return em


def format_clan_stats(clan, war):
    try:
        war_trophies = war.clan.clan_score
    except AttributeError:
        war_trophies = 'Not in war at the moment'

    return '\n'.join(
        (
            f'<:clan:376373812012384267> {len(clan.member_list)}/50',
            f'<:trophy:376367869551706112> {clan.clan_score}',
            f'<:wartrophy:448423299668770816> {war_trophies}',
            f'<:trophy:376367869551706112> {clan.required_trophies} required',
            f'<:cards:376367863935664130> {clan.donations_per_week}/week'
        )
    )
