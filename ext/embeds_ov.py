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

async def format_profile(ctx, p):
    em = discord.Embed(color=random_color())
    if not p:
        em.description = "There aren't any stats for this region!"
        return em

    embed_fields = []

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    em.set_footer(text='Statsy - Powered by the OWAPI')
    return em
