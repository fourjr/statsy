from discord.ext.commands.view import StringView


class CustomView(StringView):
    """Overwrites the default StringView for space insensitivity
    Original: https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/view.py
    """

    def get_word(self):
        pos = 0
        non_space = False
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if current.isspace():
                    if non_space:
                        break
                else:
                    non_space = True
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index:self.index + pos]
        self.index += pos
        return result.strip()
