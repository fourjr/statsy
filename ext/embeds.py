import discord
from collections import OrderedDict

def emoji(ctx, name, emojiresp=False):
    server_ids = [315043391081676810, 337918174475452426, 337919522163916815, 337975017469902848]
    emojis = []
    for id in server_ids:
        g = ctx.bot.get_guild(id)
        for e in g.emojis:
            emojis.append(e)
    if name is 'chestmagic': name = 'chestmagical'
    name = name.replace('.','').replace(' ', '').lower()
    emoji = discord.utils.get(emojis, name=name)
    if emojiresp:
        if emoji != None:
            return emoji
        else:
            return name
    else:
        try:
            return str(f'<:{emoji.name}:{emoji.id}>')
        except:
            return name

async def format_profile(ctx, p):
    embed = discord.Embed(description=f'[StatsRoyale p](https://statsroyale.com/p/{p.tag})', color=0xe74c3c)
    embed.set_author(name=f"{p.name} (#{p.tag})", icon_url = ctx.author.avatar_url)
    embed.set_thumbnail(url=p.clan_badge_url or 'https://i.imgur.com/Y3uXsgj.png')

    deck = ''
    for i in range(8):
        deck += str(emoji(ctx, p.deck[i].name)) + str(p.deck[i].level)
        
    embeddict = OrderedDict({
        'Trophies' : f"{p.current_trophies}/{p.highest_trophies} PB {emoji(ctx, 'trophy')}",
        'Clan Info' : f'Clan: {p.clan_name} (#{p.clan_tag}) \nRole: {p.clan_role}',
        'Deck': deck,
        f'Chests ({p.chest_cycle.position} opened)' : f"{' '.join([emoji(ctx, 'chest' + p.get_chest(x).lower()) for x in range(10)])} \n{emoji(ctx, 'chestsupermagical')} +{p.chest_cycle.super_magical or p.chest_cycle.super_magical-p.chest_cycle.position} {emoji(ctx, 'chestlegendary')} + {p.chest_cycle.legendary or p.chest_cycle.legendary-p.chest_cycle.position}{emoji(ctx, 'chestepic')} + {p.chest_cycle.epic or p.chest_cycle.super_magical-p.chest_cycle.position} {emoji(ctx, 'chestmagical')} + {p.chest_cycle.magical or p.chest_cycle.super_magical-p.chest_cycle.position}",
        'Shop Offers (Days)': f"{emoji(ctx, 'chestlegendary')}{p.shop_offers.legendary} {emoji(ctx, 'chestepic')}{p.shop_offers.epic} {emoji(ctx, 'arena11')}{p.shop_offers.arena}",
        'Wins/Losses/Draws': f'{p.wins}/{p.losses}/{p.draws} ({p.win_streak} win streak)'
        })

    for f, v in embeddict.items():
        embed.add_field(name=f, value=v)
    
    return embed
    # TODO: Make embeds better.