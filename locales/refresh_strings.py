import subprocess
import sys
import os

TO_TRANSLATE = ['../cogs/' + i for i in os.listdir('../cogs') if i.endswith('.py')] +\
               ['../ext/' + i for i in os.listdir('../ext') if i.endswith('.py')] +\
               ['../statsbot.py']

old_text = {}

for file in TO_TRANSLATE:
    with open(file, 'r+') as f:
        old_text[file] = f.read()
        f.write(f.read().replace(', ctx', ''))

code = f'"{sys.executable}" pygettext.py {" ".join(TO_TRANSLATE)} -p pot'

subprocess.run(code)

for file in TO_TRANSLATE:
    with open(file, 'w') as f:
        f.write(old_text[file])
