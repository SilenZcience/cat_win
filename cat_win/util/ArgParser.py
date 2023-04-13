from glob import iglob
from os.path import isfile, realpath, isdir
from re import match

from cat_win.const.ArgConstants import *


FILE_ENCODING: str = 'utf-8'
FILE_SEARCH = []
FILE_MATCH = []
FILE_TRUNCATE = [None, None, None]


def __addArgument__(args: list, unknown_args: list, known_files: list, unknown_files: list, param: str) -> bool:
    """
    sorts an argument to either list option, by appending to it.
    
    Parameters:
    args (list):
        all known parameters
    unknown_args (list):
        all unknown parameters
    known_files (list):
        all known files
    unknown_files (list)
        all unknown files
    param (str):
        the current parameter
        
    Returns:
    (bool):
        True if -E has been called, meaning every following parameter
        should simply be printed to stdout.
    """
    # 'enc' + ('=' or ':') + FILE_ENCODING
    if match(r"\Aenc[\=\:].+\Z", param):
        global FILE_ENCODING
        FILE_ENCODING = param[4:]
        return False
    # 'match' + ('=' or ':') + FILE_MATCH
    elif match(r"\Amatch[\=\:].+\Z", param):
        global FILE_MATCH
        FILE_MATCH.append(fr'{param[6:]}')
        return False
    # 'find' + ('=' or ':') + FILE_SEARCH
    elif match(r"\Afind[\=\:].+\Z", param):
        global FILE_SEARCH
        FILE_SEARCH.append(param[5:])
        return False
    # 'trunc' + ('=' or ':') + FILE_TRUNCATE[0] + ':' + FILE_TRUNCATE[1] + ':' + FILE_TRUNCATE[2]
    elif match(r"\Atrunc[\=\:][0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\Z", param):
        paramSplit = param[6:].split(':')
        global FILE_TRUNCATE
        FILE_TRUNCATE[0] = None if paramSplit[0] == '' else (
            0 if paramSplit[0] == '0' else int(eval(paramSplit[0]))-1)
        FILE_TRUNCATE[1] = None if paramSplit[1] == '' else int(eval(paramSplit[1]))
        if len(paramSplit) == 3:
            FILE_TRUNCATE[2] = None if paramSplit[2] == '' else int(eval(paramSplit[2]))
        return False
    # '[' + ARGS_CUT + ']'
    elif match(r"\A\[[0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\]\Z", param):
        args.append((ARGS_CUT, param))
        return False
    # '[' + ARGS_REPLACE + ']'
    elif match(r"\A\[.+\,.+\]\Z", param):
        args.append((ARGS_REPLACE, param))
        return False

    # default parameters
    for x in ALL_ARGS:
        if x.shortForm == param or x.longForm == param:
            args.append((x.id, param))
            if x.id == ARGS_ECHO:
                return True
            return False

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
            if __addArgument__(args, unknown_args, known_files, unknown_files, '-' + param[i]):
                return True
    elif match(r"\A[^-]+.*\Z", param):
        unknown_files.append(realpath(param))
    else:
        unknown_args.append(param)
    return False


def getArguments(argv: list) -> tuple:
    """
    Read all args to either a valid parameter, an invalid parameter,
    a known file, an unknown file, or an echo parameter to print out.
    
    Parameters:
    argv (list):
        the entire sys.argv list
    
    Returns:
    (args, unknown_args, known_files, unknown_files, echo_args) (tuple):
        contains the paramater in a sorted manner
    """
    inputArgs = argv[1:]
    args = []
    unknown_args = []
    known_files = []
    unknown_files = []
    echo_args = []

    echoCall = False
    

    for arg in inputArgs:
        if echoCall:
            echo_args.append(arg)
            continue
        echoCall = __addArgument__(args, unknown_args, known_files, unknown_files, arg)

    return (args, unknown_args, known_files, unknown_files, echo_args)
