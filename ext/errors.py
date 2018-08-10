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
