from datetime import datetime

import discord

from ext.utils import emoji, random_color
from locales.i18n import Translator

_ = Translator('FN Embeds', __file__)


def timestamp(minutes):
    return str(datetime.timedelta(minutes=minutes))[:-3]


async def format_profile(ctx, platform, p):
    ems = []
    top = {'solo': (10, 25), 'duo': (5, 12), 'squad': (3, 6)}

    if p['totals']['matchesplayed']:
        kdr = p['totals']['wins'] / p['totals']['matchesplayed'] * 100
    else:
        kdr = 0

    fields = [
        (_('Kills {}', ctx).format(emoji(ctx, "fnskull")), p['totals']['kills']),
        (_('Victory Royale! {}', ctx).format(emoji(ctx, "fnvictoryroyale")), f"{p['totals']['wins']} ({kdr:.2f})"),
        (_('Kill Death Ratio', ctx), p['totals']['kd']),
        (_('Time Played', ctx), timestamp(p['totals']['minutesplayed']))
    ]

    ems.append(discord.Embed(description=_('Overall Statistics', ctx), color=random_color()))
    ems[0].set_author(name=p['username'])
    for name, value in fields:
        ems[0].add_field(name=str(name), value=str(value))

    for n, mode in enumerate(('solo', 'duo', 'squad')):
        kdr = p[platform][f'winrate_{mode}']
        fields = [
            (_('Score', ctx), p[platform][f'score_{mode}']),
            (_('Kills {}', ctx).format(emoji(ctx, "fnskull")), p[platform][f'kills_{mode}']),
            (_('Total Battles', ctx), p[platform][f'matchesplayed_{mode}']),
            (_('Victory Royale! {}', ctx).format(emoji(ctx, "fnvictoryroyale")), f"{p[platform][f'placetop1_{mode}']} ({kdr}%)"),
            (_('Top {}', ctx).format(emoji(ctx, "fnleague")), 'Top {}: {}\nTop {}: {}'.format(
                top[mode][0],
                p[platform][f'placetop{top[mode][0]}_{mode}'],
                top[mode][1],
                p[platform][f'placetop{top[mode][1]}_{mode}']
            )),
            (_('Kill Death Ratio', ctx), p[platform][f'kd_{mode}']),
            (_('Time Played', ctx), timestamp(p[platform][f'minutesplayed_{mode}']))
        ]
        ems.append(discord.Embed(description=_('{} Statistics', ctx).format(mode.title()), color=random_color()))
        ems[n + 1].set_author(name=p['username'])

        for name, value in fields:
            ems[n + 1].add_field(name=str(name), value=str(value))

    return ems
