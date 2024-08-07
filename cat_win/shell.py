"""
shell
"""

import sys


try:
    from cat_win.src import cat
except KeyboardInterrupt:
    sys.exit(1)
except Exception as e:
    print('an error occured while loading the module:', file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)

def entry_point():
    """
    run the shell.
    """
    cat.shell_main()

if __name__ == '__main__':
    entry_point()
