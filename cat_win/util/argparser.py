from glob import iglob
from os.path import isfile, realpath, isdir
from re import match

from cat_win.const.argconstants import ALL_ARGS, ARGS_CUT, ARGS_REPLACE, ARGS_ECHO


FILE_ENCODING: str = 'utf-8'
FILE_SEARCH = set()
FILE_MATCH  = set()
FILE_TRUNCATE = [None, None, None]


def _add_argument(args: list, unknown_args: list, known_files: list, unknown_files: list,
                  param: str, delete: bool = False) -> bool:
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
    delete (bool):
        indicates if a parameter should be deleted or added. Needed for
        the shell when changing FILE_SEARCH, FILE_MATCH
        
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
    if match(r"\Amatch[\=\:].+\Z", param):
        global FILE_MATCH
        if delete:
            FILE_MATCH.discard(param[6:])
            return False
        FILE_MATCH.add(fr'{param[6:]}')
        return False
    # 'find' + ('=' or ':') + FILE_SEARCH
    if match(r"\Afind[\=\:].+\Z", param):
        global FILE_SEARCH
        if delete:
            FILE_SEARCH.discard(param[5:])
            return False
        FILE_SEARCH.add(param[5:])
        return False
    # 'trunc' + ('=' or ':') + FILE_TRUNCATE[0] + ':' + FILE_TRUNCATE[1] + ':' + FILE_TRUNCATE[2]
    if match(r"\Atrunc[\=\:][0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\Z", param):
        param_split = param[6:].split(':')
        global FILE_TRUNCATE
        FILE_TRUNCATE[0] = None if param_split[0] == '' else (
            0 if param_split[0] == '0' else int(eval(param_split[0]))-1)
        FILE_TRUNCATE[1] = None if param_split[1] == '' else int(eval(param_split[1]))
        if len(param_split) == 3:
            FILE_TRUNCATE[2] = None if param_split[2] == '' else int(eval(param_split[2]))
        return False
    # '[' + ARGS_CUT + ']'
    if match(r"\A\[[0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\]\Z", param):
        args.append((ARGS_CUT, param))
        return False
    # '[' + ARGS_REPLACE + ']'
    if match(r"\A\[.+\,.+\]\Z", param):
        args.append((ARGS_REPLACE, param))
        return False

    # default parameters
    for arg in ALL_ARGS:
        if param in (arg.short_form, arg.long_form):
            args.append((arg.arg_id, param))
            if arg.arg_id == ARGS_ECHO:
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
            if _add_argument(args, unknown_args, known_files, unknown_files, '-' + param[i]):
                return True
    elif match(r"\A[^-]+.*\Z", param):
        unknown_files.append(realpath(param))
    else:
        unknown_args.append(param)
    return False


def get_arguments(argv: list, delete: bool = False) -> tuple:
    """
    Read all args to either a valid parameter, an invalid parameter,
    a known file, an unknown file, or an echo parameter to print out.
    
    Parameters:
    argv (list):
        the entire sys.argv list
    delete (bool):
        indicates if a parameter should be deleted or added. Needed for
        the shell when changing FILE_SEARCH, FILE_MATCH
    
    Returns:
    (args, unknown_args, known_files, unknown_files, echo_args) (tuple):
        contains the paramater in a sorted manner
    """
    input_args = argv[1:]
    args = []
    unknown_args = []
    known_files = []
    unknown_files = []
    echo_args = []

    echo_call = False

    for arg in input_args:
        if echo_call:
            echo_args.append(arg)
            continue
        echo_call = _add_argument(args, unknown_args, known_files, unknown_files, arg, delete)

    return (args, unknown_args, known_files, unknown_files, echo_args)
