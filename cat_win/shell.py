from sys import exit as sysexit


try:
    from cat_win import cat
except KeyboardInterrupt:
    sysexit(1)
except Exception as e:
    print('an error occured while loading the module:')
    print(e)
    sysexit(1)

def entry_point():
    cat.shell_main()

if __name__ == '__main__':
    entry_point()
