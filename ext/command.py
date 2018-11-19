from discord.ext import commands

from locales.i18n import Translator

_ = Translator('Command Handler', __file__)


class StatsyCommand(commands.Command):

    def short_doc(self, ctx):
        """Overwrites default to use translations"""
        return _(super().short_doc)


class StatsyGroup(commands.Group):

    def short_doc(self, ctx):
        """Overwrites default to use translations"""
        return _(super().short_doc)

    def command(self, *args, **kwargs):
        """Overwrites GroupMixin.command to use StatsyCommand"""
        def decorator(func):
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


def command(**attrs):
    """Makes use of StatsyCommand"""
    return commands.command(cls=StatsyCommand, **attrs)


def group(**attrs):
    """Makes use of StatsyGroup"""
    return commands.command(cls=StatsyGroup, **attrs)


def cog(alias):
    """Creates a cog with support for aliases"""
    def decorator(cls):
        cls.alias = alias
        for name, method in cls.__dict__.items():
            if isinstance(method, (StatsyCommand, StatsyGroup)):
                if not method.parent:
                    method.name = alias + method.name
                    for n, i in enumerate(method.aliases):
                        method.aliases[n] = alias + i
        return cls
    return decorator
