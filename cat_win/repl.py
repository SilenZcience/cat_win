"""
repl
"""

import sys


try:
    from cat_win.src import cat
except KeyboardInterrupt:
    sys.exit(1)
except Exception as exc:
    print('an error occured while loading the module:', file=sys.stderr)
    print(exc, file=sys.stderr)
    sys.exit(1)

def entry_point():
    """
    run the repl.
    """
    cat.repl_main()

if __name__ == '__main__':
    entry_point()
