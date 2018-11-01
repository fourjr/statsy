import discord

from ext.utils import emoji, random_color
from locales.i18n import Translator

_ = Translator('OV Embeds', __file__)


async def format_profile(ctx, name, p, h):
    embeds = []
    if p["competitive"]:
        em = discord.Embed(color=random_color())

        avatar_url = p['competitive']['overall_stats']['avatar']
        if avatar_url.startswith('http'):
            em.set_thumbnail(url=avatar_url)

        em.set_author(name=_('{} - Competitive', ctx).format(name), icon_url=ctx.author.avatar_url)
        tier = p["competitive"]["overall_stats"]["tier"] or "none"

        level = p['competitive']['overall_stats']['prestige'] * 100 + p['competitive']['overall_stats']['level']
        wld = f"{p['competitive']['overall_stats']['wins']}-{p['competitive']['overall_stats']['losses']}-{p['competitive']['overall_stats']['ties']}"

        embed_fields = [
            (_('Level', ctx), level, True),
            (_('Win-Loss-Draw', ctx), wld, True),
            (_('Games Played', ctx), p['competitive']['overall_stats']['games'], True),
            (_('Win Rate', ctx), int(p['competitive']['overall_stats']["win_rate"]), True),
            (_("Tier", ctx), tier.title(), True),
            (_('Kills', ctx), int(p['competitive']['game_stats']["eliminations"]), True),
            (_("Top Kills in a Game", ctx), int(p["competitive"]["game_stats"]["eliminations_most_in_game"]), True),
            (_("Solo Kills", ctx), p["competitive"]["game_stats"].get("solo_kills"), True),
            (_("Final Blows", ctx), int(p["competitive"]["game_stats"]["final_blows"]), True),
            (_("Deaths", ctx), int(p["competitive"]["game_stats"]["deaths"]), True),
            (_("K/D", ctx), p["competitive"]["game_stats"]["kpd"], True),
            (_("Gold Medals", ctx), int(p["competitive"]["game_stats"]["medals_gold"]), True),
            (_("Silver Medals", ctx), int(p["competitive"]["game_stats"]["medals_silver"]), True),
            (_("Bronze Medals", ctx), int(p["competitive"]["game_stats"]["medals_bronze"]), True)
        ]

        for n, v, i in embed_fields:
            if v:
                em.add_field(name=n, value=v, inline=i)

        embeds.append(em)
    em = discord.Embed(color=random_color())

    avatar_url = p['quickplay']['overall_stats']['avatar']
    if avatar_url.startswith('http'):
        em.set_thumbnail(url=avatar_url)

    em.set_author(name=_('{} - Quickplay', ctx).format(name), icon_url=ctx.author.avatar_url)
    tier = p["quickplay"]["overall_stats"]["tier"] or "none"

    level = p['quickplay']['overall_stats']['prestige'] * 100 + p['quickplay']['overall_stats']['level']

    embed_fields = [
        (_('Level', ctx), level, True),
        (_('Wins', ctx), f"{p['quickplay']['overall_stats']['wins']}", True),
        (_('Games Played', ctx), p['quickplay']['overall_stats']['games'], True),
        (_("Tier", ctx), tier.title(), True),
        (_("Kills", ctx), int(p["quickplay"]["game_stats"]["eliminations"]), True),
        (_("Top Kills in a Game", ctx), int(p["quickplay"]["game_stats"]["eliminations_most_in_game"]), True),
        (_("Solo Kills", ctx), int(p["quickplay"]["game_stats"]["solo_kills"]), True),
        (_("Final Blows", ctx), int(p["quickplay"]["game_stats"]["final_blows"]), True),
        (_("Deaths", ctx), int(p["quickplay"]["game_stats"]["deaths"]), True),
        (_("K/D", ctx), p["quickplay"]["game_stats"]["kpd"], True),
        (_("Gold Medals", ctx), int(p["quickplay"]["game_stats"]["medals_gold"]), True),
        (_("Silver Medals", ctx), int(p["quickplay"]["game_stats"]["medals_silver"]), True),
        (_("Bronze Medals", ctx), int(p["quickplay"]["game_stats"]["medals_bronze"]), True)
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    embeds.append(em)
    name_dict = {
        "torbjorn": "Torbjörn",
        "dva": "D.Va",
        "soldier76":
        "Soldier: 76",
        "lucio": "Lúcio",
        "mccree": "McCree"
    }

    stats = {
        _("Time Played", ctx): "time_played",
        _("Kills", ctx): "eliminations",
        _("K/D", ctx): "eliminations_per_life",
        _("Best Kill Streak", ctx): "kill_streak_best",
        _("Total Damage", ctx): "all_damage_done",
        _("Hero Damage", ctx): "hero_damage_done",
        _("On Fire", ctx): "time_spent_on_fire",
        _("Gold Medals", ctx): "medals_gold",
        _("Silver Medals", ctx): "medals_sliver",
        _("Bronze Medals", ctx): "medals_bronze"
    }

    if h["stats"]["competitive"]:
        hero_playtime_comp = list(sorted(
            h["playtime"]["competitive"], key=h["playtime"]["competitive"].__getitem__, reverse=True
        ))
        for hero in hero_playtime_comp:
            if hero not in h["stats"]["competitive"]:
                break
            em = discord.Embed(color=random_color())
            if hero in name_dict:
                em.set_author(name=f"{name} - {name_dict[hero]} (Competitive)", icon_url=ctx.author.avatar_url)
            else:
                em.set_author(name=f"{name} - {hero.title()} (Competitive)", icon_url=ctx.author.avatar_url)

            avatar_url = getattr(emoji(ctx, hero), 'url', '')
            if avatar_url.startswith('http'):
                em.set_thumbnail(url=avatar_url)

            gen_comp_stats = h["stats"]["competitive"][hero]["general_stats"]
            for stat_name, stat in stats.items():
                if not gen_comp_stats.get(stat):
                    em.add_field(name=stat_name, value="None")
                elif stat_name == "K/D":
                    em.add_field(name=stat_name, value=gen_comp_stats[stat])
                elif stat_name == "Time Played":
                    if gen_comp_stats[stat] > 1:
                        em.add_field(name=stat_name, value=f"{round(gen_comp_stats[stat], 2)} hours")
                    else:
                        em.add_field(name=stat_name, value=f"{round(gen_comp_stats[stat]*60, 2)} minutes")
                elif stat_name == _("On Fire", ctx):
                    em.add_field(
                        name=stat_name,
                        value=f"{round(gen_comp_stats[stat]/gen_comp_stats['time_played']*100, 2)}% of the time"
                    )
                else:
                    em.add_field(name=stat_name, value=int(gen_comp_stats[stat]))
            if h['stats']['competitive'][hero]['hero_stats'] != {}:
                extra_stats = [f'**{x.replace("_", " ").title()}**: {y}' for x, y in h['stats']['competitive'][hero]['hero_stats'].items()]
                em.add_field(name="Extra Stats", value='\n'.join(extra_stats))
            embeds.append(em)

    hero_playtime_quick = list(sorted(
        h["playtime"]["quickplay"], key=h["playtime"]["quickplay"].__getitem__, reverse=True)
    )
    for hero in hero_playtime_quick:
        if hero not in h["stats"]["quickplay"]:
            break
        em = discord.Embed(color=random_color())
        if hero in name_dict:
            em.set_author(name=f"{name} - {name_dict[hero]} (Quickplay)", icon_url=ctx.author.avatar_url)
        else:
            em.set_author(name=f"{name} - {hero.title()} (Quickplay)", icon_url=ctx.author.avatar_url)

        avatar_url = getattr(emoji(ctx, hero), 'url', '')
        if avatar_url.startswith('http'):
            em.set_thumbnail(url=avatar_url)

        gen_quickplay_stats = h["stats"]["quickplay"][hero]["general_stats"]
        for stat_name, stat in stats.items():
            if not gen_quickplay_stats.get(stat):
                em.add_field(name=stat_name, value="None")
            elif stat_name == _("K/D", ctx):
                em.add_field(name=stat_name, value=gen_quickplay_stats[stat])
            elif stat_name == _("Time Played", ctx):
                if gen_quickplay_stats[stat] > 1:
                    em.add_field(name=stat_name, value=f"{round(gen_quickplay_stats[stat], 2)} hours")
                else:
                    em.add_field(name=stat_name, value=f"{round(gen_quickplay_stats[stat]*60, 2)} minutes")
            elif stat_name == _("On Fire", ctx):
                em.add_field(
                    name=stat_name,
                    value=f"{round(gen_quickplay_stats[stat]/gen_quickplay_stats['time_played']*100, 2)}% of the time"
                )
            else:
                em.add_field(name=stat_name, value=int(gen_quickplay_stats[stat]))
        if h['stats']['quickplay'][hero]['hero_stats'] != {}:
            extra_stats = [f'**{x.replace("_", " ").title()}**: {y}' for x, y in h['stats']['quickplay'][hero]['hero_stats'].items()]
            em.add_field(name=_("Extra Stats", ctx), value='\n'.join(extra_stats))
        embeds.append(em)
    return embeds
