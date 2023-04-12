from sys import exit

try:
    import cat_win.cat as cat
except KeyboardInterrupt:
    exit(1)
except Exception as e:
    print('an error occured while loading the module:')
    print(e)
    exit(1)

def shell_entry_point():
    cat.shell_main()

def entry_point():
    cat.main()

if __name__ == '__main__':
    entry_point()