"""
__main__
"""

import os
import platform
import sys

if (3,14) <= sys.version_info <= (3,15) and platform.system() == 'Windows':
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '_vendor')))

try:
    from cat_win.src import cat
except KeyboardInterrupt:
    sys.exit(1)
except Exception as exc:
    print('an error occured while loading the module:', file=sys.stderr)
    print(exc, file=sys.stderr)
    sys.exit(1)

def repl_entry_point():
    """
    run the repl.
    """
    cat.repl_main()

def entry_point():
    """
    run the main program.
    """
    cat.main()

if __name__ == '__main__':
    entry_point()
