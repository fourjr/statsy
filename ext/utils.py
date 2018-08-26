import random

import discord
from discord.ext import commands


class InvalidTag(commands.BadArgument):
    """Raised when a tag is invalid."""

    message = 'Player tags should only contain these characters:\n' \
              '**Numbers:** 0, 2, 8, 9\n' \
              '**Letters:** P, Y, L, Q, G, R, J, C, U, V'


class InvalidPlatform(commands.BadArgument):
    """Raised when a tag is invalid."""
    message = 'Platforms should only be one of the following:\n' \
              'pc, ps4, xb1'


class NoTag(Exception):
    pass


def has_perms():
    perms = {
        'send_messages': True,
        'embed_links': True,
        'external_emojis': True
    }

    return commands.bot_has_permissions(**perms)


def statsy_guild():
    def predicate(ctx):
        if ctx.guild:
            return ctx.guild.id == 444482551139008522
        return False
    return commands.check(predicate)


def developer():
    def predicate(ctx):
        return ctx.author.id in ctx.bot.developers
    return commands.check(predicate)


def random_color():
    return random.randint(0, 0xFFFFFF)


def emoji(ctx, name, should_format=True):
    name = str(name)
    if should_format:
        name = name.lower()
        replace = {
            '': ['.', ' ', '_', '-'],
            'chestgold': 'chestgolden',
            'rico': 'ricochet',
            'primo': 'elprimo',
            'pekka': 'p.e.k.k.a',
            'jess': 'jessie',
            'mike': 'dynamike'
        }
        for i in replace:
            if isinstance(replace[i], list):
                for k in replace[i]:
                    name = name.replace(k, i)
            else:
                name = name.replace(replace[i], i)

    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    return e or name


def cdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]
