import discord


async def format_profile(ctx, profile):
    return discord.Embed(title=str(profile))
    # TODO: Make embeds better.