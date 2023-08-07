from sys import exit as sysexit, stderr


try:
    from cat_win import cat
except KeyboardInterrupt:
    sysexit(1)
except Exception as e:
    print('an error occured while loading the module:', file=stderr)
    print(e, file=stderr)
    sysexit(1)

def shell_entry_point():
    cat.shell_main()

def entry_point():
    cat.main()

if __name__ == '__main__':
    entry_point()
