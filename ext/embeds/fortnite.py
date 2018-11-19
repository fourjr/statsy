import datetime

import discord

from ext.utils import e, random_color
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
        (_('Kills {}').format(e("fnskull")), p['totals']['kills']),
        (_('Victory Royale! {}').format(e("fnvictoryroyale")), f"{p['totals']['wins']} ({kdr:.2f})"),
        (_('Kill Death Ratio'), p['totals']['kd']),
        (_('Time Played'), timestamp(p['totals']['minutesplayed']))
    ]

    ems.append(discord.Embed(description=_('Overall Statistics'), color=random_color()))
    ems[0].set_author(name=p['username'])
    for name, value in fields:
        ems[0].add_field(name=str(name), value=str(value))

    for n, mode in enumerate(('solo', 'duo', 'squad')):
        kdr = p[platform][f'winrate_{mode}']
        fields = [
            (_('Score'), p[platform][f'score_{mode}']),
            (_('Kills {}').format(e("fnskull")), p[platform][f'kills_{mode}']),
            (_('Total Battles'), p[platform][f'matchesplayed_{mode}']),
            (_('Victory Royale! {}').format(e("fnvictoryroyale")), f"{p[platform][f'placetop1_{mode}']} ({kdr}%)"),
            (_('Top {}').format(e("fnleague")), 'Top {}: {}\nTop {}: {}'.format(
                top[mode][0],
                p[platform][f'placetop{top[mode][0]}_{mode}'],
                top[mode][1],
                p[platform][f'placetop{top[mode][1]}_{mode}']
            )),
            (_('Kill Death Ratio'), p[platform][f'kd_{mode}']),
            (_('Time Played'), timestamp(p[platform][f'minutesplayed_{mode}']))
        ]
        ems.append(discord.Embed(description=_('{} Statistics').format(mode.title()), color=random_color()))
        ems[n + 1].set_author(name=p['username'])

        for name, value in fields:
            ems[n + 1].add_field(name=str(name), value=str(value))

    return ems
