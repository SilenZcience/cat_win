from glob import iglob
from re import match
from os.path import isfile, realpath, isdir
from cat_win.const.ArgConstants import *


FILE_ENCODING = 'utf-8'
FILE_SEARCH = []
FILE_MATCH = []
FILE_TRUNCATE = [None, None, None]


def __addArgument__(args: list, unknown_args: list, known_files: list, unknown_files: list, param: str) -> None:
    # 'enc' + ('=' or ':') + FILE_ENCODING
    if match(r"\Aenc[\=\:].+\Z", param):
        global FILE_ENCODING
        FILE_ENCODING = param[4:]
        return
    # 'match' + ('=' or ':') + FILE_MATCH
    elif match(r"\Amatch[\=\:].+\Z", param):
        global FILE_MATCH
        FILE_MATCH.append(fr'{param[6:]}')
        return
    # 'find' + ('=' or ':') + FILE_SEARCH
    elif match(r"\Afind[\=\:].+\Z", param):
        global FILE_SEARCH
        FILE_SEARCH.append(param[5:])
        return
    # 'trunc' + ('=' or ':') + FILE_TRUNCATE[0] + ':' + FILE_TRUNCATE[1] + ':' + FILE_TRUNCATE[2]
    elif match(r"\Atrunc[\=\:][0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\Z", param):
        param = param[6:].split(':')
        global FILE_TRUNCATE
        FILE_TRUNCATE[0] = None if param[0] == '' else (
            0 if param[0] == '0' else int(eval(param[0]))-1)
        FILE_TRUNCATE[1] = None if param[1] == '' else int(eval(param[1]))
        if len(param) == 3:
            FILE_TRUNCATE[2] = None if param[2] == '' else int(eval(param[2]))
        return
    # '[' + ARGS_CUT + ']'
    elif match(r"\A\[[0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\]\Z", param):
        args.append((ARGS_CUT, param))
        return
    # '[' + ARGS_REPLACE + ']'
    elif match(r"\A\[.+\,.+\]\Z", param):
        args.append((ARGS_REPLACE, param))
        return

    # default parameters
    for x in ALL_ARGS:
        if x.shortForm == param or x.longForm == param:
            args.append((x.id, param))
            return

    possible_path = realpath(param)
    if match(r".*\*+.*", param):
        for filename in iglob(param, recursive=True):
            if isfile(filename):
                known_files.append(realpath(filename))
    elif isdir(possible_path):
        for filename in iglob(possible_path + '**/**', recursive=True):
            if isfile(filename):
                known_files.append(realpath(filename))
    elif isfile(possible_path):
        known_files.append(possible_path)
    elif len(param) > 2 and param[0] == '-' and param[1] != '-':
        for i in range(1, len(param)):
            __addArgument__(args, unknown_args, known_files, unknown_files, '-' + param[i])
    elif match(r"\A[^-]+.*\Z", param):
        unknown_files.append(realpath(param))
    else:
        unknown_args.append(param)


def getArguments(argv: list) -> tuple:
    """
    Read all args to either a valid parameter,
    a known file or an unknown file.
    Return a tuple containing these three lists.
    """
    inputArgs = argv[1:]
    args = []
    unknown_args = []
    known_files = []
    unknown_files = []

    for arg in inputArgs:
        __addArgument__(args, unknown_args, known_files, unknown_files, arg)

    return (args, unknown_args, known_files, unknown_files)
