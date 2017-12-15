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
    name_dict = {
        "torbjorn": "Torbjörn",
        "dva": "D.Va",
        "soldier76":
        "Soldier: 76",
        "lucio": "Lúcio",
        "mccree": "McCree"
        }
    stats = {
        "Time Played": "time_played",
        "Kills": "eliminations",
        "K/D": "eliminations_per_life",
        "Best Kill Streak": "kill_streak_best",
        "Total Damage": "all_damage_done",
        "Hero Damage": "hero_damage_done",
        "On Fire": "time_spent_on_fire",
        "Gold Medals": "medals_gold",
        "Silver Medals": "medals_sliver",
        "Bronze Medals": "medals_bronze"
        }
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
                elif stat_name == "On Fire":
                    em.add_field(name=stat_name, value=f"{round(gen_comp_stats[stat]/gen_comp_stats['time_played']*100, 2)}% of the time")
                else:
                    em.add_field(name=stat_name, value=int(gen_comp_stats[stat]))
            if h['stats']['competitive'][hero]['hero_stats'] != {}:
                em.add_field(name="Extra Stats", value='\n'.join(['**' + stat_name.replace('_', ' ').title() + '**: ' + str(int(stat)) for stat_name, stat in h['stats']['competitive'][hero]['hero_stats'].items()]))
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
        for stat_name, stat in stats.items():
            if not gen_quickplay_stats.get(stat):
                em.add_field(name=stat_name, value="None")
            elif stat_name == "K/D":
                em.add_field(name=stat_name, value=gen_quickplay_stats[stat])
            elif stat_name == "Time Played":
                if gen_quickplay_stats[stat] > 1:
                    em.add_field(name=stat_name, value=f"{round(gen_quickplay_stats[stat], 2)} hours")
                else:
                    em.add_field(name=stat_name, value=f"{round(gen_quickplay_stats[stat]*60, 2)} minutes")
            elif stat_name == "On Fire":
                em.add_field(name=stat_name, value=f"{round(gen_quickplay_stats[stat]/gen_quickplay_stats['time_played']*100, 2)}% of the time")
            else:
                em.add_field(name=stat_name, value=int(gen_quickplay_stats[stat]))
        if h['stats']['quickplay'][hero]['hero_stats'] != {}:
            em.add_field(name="Extra Stats", value='\n'.join(['**' + stat_name.replace('_', ' ').title() + '**: ' + str(int(stat)) for stat_name, stat in h['stats']['quickplay'][hero]['hero_stats'].items()]))
        embeds.append(em)
    return embeds
