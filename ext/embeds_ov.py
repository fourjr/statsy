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

async def format_profile(ctx, name, p):
    embeds = []
    em = discord.Embed(color=random_color(), title='Competitive')
    try:
        em.set_author(name=name, icon_url=p['competitive']['overall_stats']['avatar'])
    except:
        em.set_author(name=name)

    em.set_thumbnail(url=p['competitive']['overall_stats']['rank_image'])

    embed_fields = [
        ('Level', p['competitive']['overall_stats']['prestige']*100+p['competitive']['overall_stats']['level'], True),
        ('Win-Loss-Draw', f"{p['competitive']['overall_stats']['wins']}-{p['competitive']['overall_stats']['losses']}-{p['competitive']['overall_stats']['ties']}", True),
        ('Games Played', p['competitive']['overall_stats']['games'], True),
        ('Win Rate', p['competitive']['overall_stats']['win_rate'], True)

        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    embeds.append(em)
    return embeds
