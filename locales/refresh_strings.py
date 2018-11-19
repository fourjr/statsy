import os
import re
import subprocess
import sys

TO_TRANSLATE = ['../cogs/' + i for i in os.listdir('../cogs') if i.endswith('.py')] +\
               ['../statsbot.py']

old_text = {}


def nth_repl(string, sub, wanted, n):
    # https://stackoverflow.com/a/35091558
    where = [m.start() for m in re.finditer(sub, string)][n - 1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    newString = before + after
    return newString


for file in TO_TRANSLATE:
    with open(file, 'r+', encoding='utf8') as f:
        old_text[file] = f.read()
        f.seek(0)
        new_content = old_text[file]
        new_content_sl = new_content.splitlines()
        if file.startswith('../cogs/') or file.startswith('../statsbot.py'):
            # docstrings translation
            for n, i in enumerate(new_content_sl):
                if i.strip() == '"""':
                    pass  # new_content_sl[n] += ')'
                elif i.strip().startswith('"""'):
                    # if it is a docstring line
                    new_content_sl[n] = new_content_sl[n].replace('"""', '_("""', 1)
                    if not i.endswith('"""'):
                        new_content_sl[n] += '""")\n        """'
                    else:
                        new_content_sl[n] += ')'

        f.write('\n'.join(new_content_sl) + '\n')

        f.truncate()

code = f'"{sys.executable}" pygettext.py {" ".join(TO_TRANSLATE)} -p pot'

subprocess.run(code)

for file in TO_TRANSLATE:
    with open(file, 'w', encoding='utf8') as f:
        f.write(old_text[file])
