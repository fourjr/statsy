import subprocess
import sys
import os

TO_TRANSLATE = ['../cogs/' + i for i in os.listdir('../cogs') if i.endswith('.py')] +\
               ['../ext/' + i for i in os.listdir('../ext') if i.endswith('.py')] +\
               ['../statsbot.py']

code = f'"{sys.executable}" pygettext.py {" ".join(TO_TRANSLATE)} -p pot'

print(code)

subprocess.run(code)
