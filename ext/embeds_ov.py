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

async def format_profile(ctx, name, p, h):
    embeds = []
    if p["competitive"]:
        em = discord.Embed(color=random_color())
        try:
            em.set_thumbnail(url=p['competitive']['overall_stats']['avatar'])
        except:
            pass

        em.set_author(name=f"{name} - Competitive", icon_url=ctx.author.avatar_url)
        tier = p["competitive"]["overall_stats"]["tier"] or "none"

        embed_fields = [
            ('Level', p['competitive']['overall_stats']['prestige']*100+p['competitive']['overall_stats']['level'], True),
            ('Win-Loss-Draw', f"{p['competitive']['overall_stats']['wins']}-{p['competitive']['overall_stats']['losses']}-{p['competitive']['overall_stats']['ties']}", True),
            ('Games Played', p['competitive']['overall_stats']['games'], True),
            ('Win Rate', int(p['competitive']['overall_stats']["win_rate"]), True),
            ("Tier", tier.title(), True),
            ('Kills', int(p['competitive']['game_stats']["eliminations"]), True),
            ("Top Kills in a Game", int(p["competitive"]["game_stats"]["eliminations_most_in_game"]), True),
            ("Solo Kills", int(p["competitive"]["game_stats"]["solo_kills"]), True),
            ("Final Blows", int(p["competitive"]["game_stats"]["final_blows"]), True),
            ("Deaths", int(p["competitive"]["game_stats"]["deaths"]), True),
            ("K/D", p["competitive"]["game_stats"]["kpd"], True),
            ("Gold Medals", int(p["competitive"]["game_stats"]["medals_gold"]), True),
            ("Silver Medals", int(p["competitive"]["game_stats"]["medals_silver"]), True),
            ("Bronze Medals", int(p["competitive"]["game_stats"]["medals_bronze"]), True)
            ]

        for n, v, i in embed_fields:
            if v:
                em.add_field(name=n, value=v, inline=i)

        embeds.append(em)
    em = discord.Embed(color=random_color())

    try:
        em.set_thumbnail(url=p['quickplay']['overall_stats']['avatar'])
    except:
        pass

    em.set_author(name=f"{name} - Quickplay", icon_url=ctx.author.avatar_url)
    tier = p["quickplay"]["overall_stats"]["tier"] or "none"

    embed_fields = [
        ('Level', p['quickplay']['overall_stats']['prestige']*100+p['quickplay']['overall_stats']['level'], True),
        ('Wins', f"{p['quickplay']['overall_stats']['wins']}", True),
        ('Games Played', p['quickplay']['overall_stats']['games'], True),
        ("Tier", tier.title(), True),
        ("Kills", int(p["quickplay"]["game_stats"]["eliminations"]), True),
        ("Top Kills in a Game", int(p["quickplay"]["game_stats"]["eliminations_most_in_game"]), True),
        ("Solo Kills", int(p["quickplay"]["game_stats"]["solo_kills"]), True),
        ("Final Blows", int(p["quickplay"]["game_stats"]["final_blows"]), True),
        ("Deaths", int(p["quickplay"]["game_stats"]["deaths"]), True),
        ("K/D", p["quickplay"]["game_stats"]["kpd"], True),
        ("Gold Medals", int(p["quickplay"]["game_stats"]["medals_gold"]), True),
        ("Silver Medals", int(p["quickplay"]["game_stats"]["medals_silver"]), True),
        ("Bronze Medals", int(p["quickplay"]["game_stats"]["medals_bronze"]), True)
        ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    embeds.append(em)
    name_dict = {"torbjorn": "Torbjörn", "dva": "D.Va", "soldier76": "Soldier: 76", "lucio": "Lúcio"}
    if h["stats"]["competitive"]:
        hero_playtime_comp = list(sorted(h["playtime"]["competitive"], key=h["playtime"]["competitive"].__getitem__, reverse=True))
        for hero in hero_playtime_comp:
            if hero not in h["stats"]["competitive"]:
                break
            em = discord.Embed(color=random_color())
            if hero in name_dict:
                em.set_author(name=f"{name} - {name_dict[hero]} (Competitive)", icon_url=ctx.author.avatar_url)
            else:
                em.set_author(name=f"{name} - {hero.title()} (Competitive)", icon_url=ctx.author.avatar_url)
            em.set_thumbnail(url=emoji(ctx, hero).url)
            gen_comp_stats = h["stats"]["competitive"][hero]["general_stats"]
            em.add_field(name="Time Played", value=f'{gen_comp_stats["time_played"]} hours')
            em.add_field(name="Kills", value=int(gen_comp_stats["eliminations"]))
            em.add_field(name="Deaths", value=int(gen_comp_stats["deaths"]))
            em.add_field(name="K/D", value=gen_comp_stats["eliminations_per_life"])
            em.add_field(name="Best Kill Streak", value=int(gen_comp_stats["kill_streak_best"]))
            em.add_field(name="Total Damage", value=int(gen_comp_stats["all_damage_done"]))
            em.add_field(name="Hero Damage", value=int(gen_comp_stats["hero_damage_done"]))
            em.add_field(name="On Fire", value=f"{round(gen_quickplay_stats['time_spent_on_fire']/gen_quickplay_stats['time_played']*100}, 2)}%")
            for stat_name, stat in h["stats"]["competitive"][hero]["hero_stats"].items():
                em.add_field(name=stat_name.replace("_", " ").title(), value=int(stat))
            embeds.append(em)
            
    hero_playtime_quick = list(sorted(h["playtime"]["quickplay"], key=h["playtime"]["quickplay"].__getitem__, reverse=True))
    for hero in hero_playtime_quick:
        if hero not in h["stats"]["quickplay"]:
            break
        em = discord.Embed(color=random_color())
        if hero in name_dict:
            em.set_author(name=f"{name} - {name_dict[hero]} (Quickplay)", icon_url=ctx.author.avatar_url)
        else:
            em.set_author(name=f"{name} - {hero.title()} (Quickplay)", icon_url=ctx.author.avatar_url)
        em.set_thumbnail(url=emoji(ctx, hero).url)
        gen_quickplay_stats = h["stats"]["quickplay"][hero]["general_stats"]
        em.add_field(name="Time Played", value=f'{gen_quickplay_stats["time_played"]} hours')
        em.add_field(name="Kills", value=int(gen_quickplay_stats["eliminations"]))
        em.add_field(name="Deaths", value=int(gen_quickplay_stats["deaths"]))
        em.add_field(name="K/D", value=gen_quickplay_stats["eliminations_per_life"])
        em.add_field(name="Best Kill Streak", value=int(gen_quickplay_stats["kill_streak_best"]))
        em.add_field(name="Total Damage", value=int(gen_quickplay_stats["all_damage_done"]))
        em.add_field(name="Hero Damage", value=int(gen_quickplay_stats["hero_damage_done"]))
        em.add_field(name="On Fire", value=f"{round(gen_quickplay_stats['time_spent_on_fire']/gen_quickplay_stats['time_played']*100}, 2)}%")
        for stat_name, stat in h["stats"]["quickplay"][hero]["hero_stats"].items():
            em.add_field(name=stat_name.replace("_", " ").title(), value=int(stat))
        embeds.append(em)
    return embeds
