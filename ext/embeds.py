import discord
from collections import OrderedDict
from crasync.models import CHESTS


def emoji(ctx, name):
    name = name.replace('.','').lower().replace(' ','')
    if name == 'chestmagic':
        name = 'chestmagical'
    e = discord.utils.get(ctx.bot.cremojis, name=name)
    return str(e)

def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]

async def format_profile(ctx, p):

    em = discord.Embed(color=discord.Color.gold())
    em.set_author(name=f"{p.name} (#{p.tag})", icon_url=ctx.author.avatar_url)
    em.set_thumbnail(url=p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png')

    deck = ''
    for card in p.deck:
        print(card.name)
        deck += str(emoji(ctx, card.name)) + str(card.level) + ' '

    chests = '| '+emoji(ctx, 'chest' + p.get_chest(0).lower()) + ' | '
    chests += ' '.join([emoji(ctx, 'chest' + p.get_chest(x).lower()) for x in range(1,10)])

    cycle = p.chest_cycle
    pos = cycle.position
    special = ''
    trophies = f"{p.current_trophies}/{p.highest_trophies} PB {emoji(ctx, 'trophy')}"
    try:
        global_r = "N/A" if not p.seasons[0].end_global else p.seasons[0].end_global
        season = f"Number: {p.seasons[0].number}\nHighest: {p.seasons[0].highest} {emoji(ctx, 'trophy')}\nFinish: {p.seasons[0].ending} {emoji(ctx, 'trophy')}\nGlobal Rank: {global_r}"
    except:
        season = 'N/A'

    for i, attr in enumerate(cdir(cycle)):
        if attr != 'position':
            e = emoji(ctx, 'chest'+attr.replace('_',''))
            c_pos = int(getattr(cycle, attr))
            until = c_pos-pos
            special += f'{e}+{until} '


    shop_offers = f"{emoji(ctx, 'chestlegendary')}+{p.shop_offers.legendary}" \
                  f"{emoji(ctx, 'chestepic')}+{p.shop_offers.epic} {emoji(ctx, 'arena11')}"\
                  f"+{p.shop_offers.arena}"


    embed_fields = [
        ('Trophies', trophies, True),
        ('Wins/Losses/Draws', f'{p.wins}/{p.losses}/{p.draws}', True),
        ('Win Streak', p.win_streak, True),
        ('Clan Name', p.clan_name, True),
        ('Clan Tag', f'#{p.clan_tag}' if p.clan_tag else 'None', True),
        ('Clan Role', p.clan_role, True),
        ('Battle Deck', deck, True),
        (f'Chests ({pos} opened)', chests, False),
        ('Chests Until', special, True),
        ('Shop Offers (Days)', shop_offers, True),
        ('Previous Season Results', season, True)
        ]

    for n, v, i in embed_fields:
        em.add_field(name=n, value=v, inline=i)

    em.set_footer(text='StatsBot - Powered by cr-api.com')
    
    return em
    # TODO: Make embeds better.

async def format_clan(ctx, c):
    embed = discord.Embed(description = c.description, color=0x3498db)
    embed.set_author(name=f"{c.name} (#{c.tag})")
    embed.set_thumbnail(url=c.badge_url)

    embeddict = OrderedDict({
        'Type': c.type_name,
        'Score': c.score + ' Trophies',
        'Donations/Week': c.donations + ' Cards',
        'Clan Chest': c.clan_chest.crowns + '/' + c.clan_chest.required,
        'Location': c.region,
        'Members': len(c.members) + '/50'
        })

    for f, v in embeddict.items():
        embed.add_field(name=f, value=v)
    
    return embed

