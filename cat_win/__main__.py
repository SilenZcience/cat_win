from sys import exit

try:
    import cat_win.cat as cat
except KeyboardInterrupt:
    exit(1)
except:
    print("an error occured while loading the module")
    exit(1)


if __name__ == '__main__':
    cat.main()