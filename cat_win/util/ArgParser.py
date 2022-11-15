from sys import argv
from glob import iglob
from re import match
from os.path import isfile, realpath, isdir
from cat_win.util.ArgConstants import *

FILE_ENCODING = None
FILE_SEARCH = []
RFILE_SEARCH = []
COLOR_ENCODING = False


def __addArgument__(args: list, known_files: list, unknown_files: list, param: str) -> None:
    if match(r"\Aenc\=.+\Z", param):
        global FILE_ENCODING
        FILE_ENCODING = param[4:]
        return
    elif match(r"\Amatch\=.+\Z", param):
        global RFILE_SEARCH
        RFILE_SEARCH.append(fr'{param[6:]}')
        return
    elif match(r"\Afind\=.+\Z", param):
        global FILE_SEARCH
        FILE_SEARCH.append(param[5:])
        return
    elif match(r"\A\[.*\:.*\]\Z", param):
        args.append([ARGS_CUT, param])
        return
    elif match(r"\A\[.+\;.+\]\Z", param):
        args.append([ARGS_REPLACE, param])
        return
    elif param in ["-col", "--color"]:
        global COLOR_ENCODING
        COLOR_ENCODING = True
        return

    for x in ALL_ARGS:
        if x.shortForm == param or x.longForm == param:
            args.append([x.id, param])
            return

    possible_path = realpath(param)
    if match(r"\*", param):
        for filename in iglob("./" + param, recursive=True):
            if isdir(filename):
                continue
            known_files.append(realpath(filename))
        return
    elif isdir(possible_path):
        for filename in iglob(possible_path + '**/**', recursive=True):
            if isdir(filename):
                continue
            known_files.append(realpath(filename))
        return
    elif isfile(possible_path):
        known_files.append(realpath(possible_path))
        return
    elif param[0] == "-" and len(param) > 2:
        for i in range(1, len(param)):
            __addArgument__(args, known_files, unknown_files, "-" + param[i])
    elif match(r"\A[^-]+\Z", param):
        unknown_files.append(realpath(param))


def getArguments():
    inputArgs = argv
    args = []
    known_files = []
    unknown_files = []
    
    for i in range(1, len(inputArgs)):
        __addArgument__(args, known_files, unknown_files, inputArgs[i])

    return (args, known_files, unknown_files)
