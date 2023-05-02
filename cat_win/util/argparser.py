from glob import iglob
from os.path import isfile, realpath, isdir
from re import match

from cat_win.const.argconstants import ALL_ARGS, ARGS_CUT, ARGS_REPLACE, ARGS_ECHO


class ArgParser:
    def __init__(self) -> None:
        self.file_encoding: str = 'utf-8'
        self.file_search = set()
        self.file_match = set()
        self.file_truncate = [None, None, None]
        self.args = []
        self.unknown_args = []
        self.known_files = []
        self.unknown_files = []
        self.echo_args = []

    def get_arguments(self, argv: list, delete: bool = False) -> tuple:
        """
        Read all args to either a valid parameter, an invalid parameter,
        a known file, an unknown file, or an echo parameter to print out.
        
        Parameters:
        argv (list):
            the entire sys.argv list
        delete (bool):
            indicates if a parameter should be deleted or added. Needed for
            the shell when changing file_search, file_match
        
        Returns:
        (args, unknown_args, known_files, unknown_files, echo_args) (tuple):
            contains the paramater in a sorted manner
        """
        self.gen_arguments(argv, delete)
        return (self.args, self.unknown_args, self.known_files, self.unknown_files, self.echo_args)

    def _add_argument(self, param: str, delete: bool = False) -> bool:
        """
        sorts an argument to either list option, by appending to it.
        
        Parameters:
        param (str):
            the current parameter
        delete (bool):
            indicates if a parameter should be deleted or added. Needed for
            the shell when changing file_search, file_match
            
        Returns:
        (bool):
            True if -E has been called, meaning every following parameter
            should simply be printed to stdout.
        """
        # 'enc' + ('=' or ':') + file_encoding
        if match(r"\Aenc[\=\:].+\Z", param):
            self.file_encoding = param[4:]
            return False
        # 'match' + ('=' or ':') + file_match
        if match(r"\Amatch[\=\:].+\Z", param):
            if delete:
                self.file_match.discard(param[6:])
                return False
            self.file_match.add(fr'{param[6:]}')
            return False
        # 'find' + ('=' or ':') + file_search
        if match(r"\Afind[\=\:].+\Z", param):
            if delete:
                self.file_search.discard(param[5:])
                return False
            self.file_search.add(param[5:])
            return False
        # 'trunc' + ('=' or ':') + file_truncate[0] + ':' + file_truncate[1] + ':' + file_truncate[2]
        if match(r"\Atrunc[\=\:][0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\Z", param):
            param_split = param[6:].split(':')
            self.file_truncate[0] = None if param_split[0] == '' else (
                0 if param_split[0] == '0' else int(eval(param_split[0]))-1)
            self.file_truncate[1] = None if param_split[1] == '' else int(eval(param_split[1]))
            if len(param_split) == 3:
                self.file_truncate[2] = None if param_split[2] == '' else int(eval(param_split[2]))
            return False
        # '[' + ARGS_CUT + ']'
        if match(r"\A\[[0-9()+\-*\/]*\:[0-9()+\-*\/]*\:?[0-9()+\-*\/]*\]\Z", param):
            self.args.append((ARGS_CUT, param))
            return False
        # '[' + ARGS_REPLACE + ']'
        if match(r"\A\[.+\,.+\]\Z", param):
            self.args.append((ARGS_REPLACE, param))
            return False

        # default parameters
        for arg in ALL_ARGS:
            if param in (arg.short_form, arg.long_form):
                self.args.append((arg.arg_id, param))
                if arg.arg_id == ARGS_ECHO:
                    return True
                return False

        possible_path = realpath(param)
        if match(r".*\*+.*", param):
            for filename in iglob(param, recursive=True):
                if isfile(filename):
                    self.known_files.append(realpath(filename))
        elif isdir(possible_path):
            for filename in iglob(possible_path + '**/**', recursive=True):
                if isfile(filename):
                    self.known_files.append(realpath(filename))
        elif isfile(possible_path):
            self.known_files.append(possible_path)
        elif len(param) > 2 and param[0] == '-' and param[1] != '-':
            for i in range(1, len(param)):
                if self._add_argument('-' + param[i], delete):
                    return True
        elif match(r"\A[^-]+.*\Z", param):
            self.unknown_files.append(realpath(param))
        else:
            self.unknown_args.append(param)
        return False


    def gen_arguments(self, argv: list, delete: bool = False) -> None:
        """
        Read all args to either a valid parameter, an invalid parameter,
        a known file, an unknown file, or an echo parameter to print out.
        
        Parameters:
        argv (list):
            the entire sys.argv list
        delete (bool):
            indicates if a parameter should be deleted or added. Needed for
            the shell when changing file_search, file_match
        
        Returns:
        (args, unknown_args, known_files, unknown_files, echo_args) (tuple):
            contains the paramater in a sorted manner
        """
        input_args = argv[1:]
        self.args = []
        self.unknown_args = []
        self.known_files = []
        self.unknown_files = []
        self.echo_args = []

        echo_call = False

        for arg in input_args:
            if echo_call:
                self.echo_args.append(arg)
                continue
            echo_call = self._add_argument(arg, delete)
