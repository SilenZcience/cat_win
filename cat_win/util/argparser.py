"""
argparser
"""

import glob
import os
import re

from cat_win.const.argconstants import ALL_ARGS, ARGS_CUT, ARGS_REPLACE, ARGS_ECHO


IS_FILE, IS_DIR, IS_PATTERN = range(0, 3)


def levenshtein(str_a: str, str_b: str) -> float:
    """
    Calculate the levenshtein distance (similarity) between
    two strings and return the result as a percentage value.
    char case is ignored such that uppercase letters match their
    lowercase counterparts perfectly.
    
    Parameters:
    str_a (str):
        the first string to compare
    str_b (str):
        the second string to compare
        
    Returns:
    (float):
        the similarity of the two strings as a percentage between 0.0 and 100.0
    """
    str_a, str_b = str_a.lstrip('-'), str_b.lstrip('-')
    len_a, len_b = len(str_a), len(str_b)
    max_len = max(len_a, len_b)
    if len_a*len_b == 0:
        return (100 if max_len == 0 else (1 - (len_a+len_b)/max_len) * 100)

    d_arr = [[i] + ([0] * len_b) for i in range(len_a+1)]
    d_arr[0] = list(range(len_b+1))

    for i in range(1, len_a+1):
        str_a_i = str_a[i-1:i]

        for j in range(1, len_b+1):
            str_b_j = str_b[j-1:j]

            d_arr[i][j] = min(d_arr[i-1][j]+1,
                              d_arr[i][j-1]+1,
                              d_arr[i-1][j-1]+int(str_a_i.lower() != str_b_j.lower()))

    return (1 - d_arr[len_a][len_b]/max_len) * 100


class ArgParser:
    """
    defines the ArgParser
    """
    SIMILARITY_LIMIT = 50.0

    def __init__(self, default_file_encoding: str = 'utf-8') -> None:
        self.default_file_encoding: str = default_file_encoding
        self.file_encoding: str = ''
        self._clear_values()
        self.reset_values()

    def _clear_values(self) -> None:
        """
        The here defined variables may NOT be accessed from the outside.
        """
        self._args = []
        self._unknown_args = []
        self._known_files = []
        self._unknown_files = []
        self._echo_args = []

        self._known_file_structures = []
        self._known_directories = []

    def reset_values(self) -> None:
        """
        The here defined variables may be accessed from the outside.
        """
        self.file_encoding = self.default_file_encoding
        self.file_search = set()
        self.file_match = set()
        self.file_truncate = [None, None, None]

    def get_args(self) -> list:
        """
        getter of self._args
        
        Returns:
        self._args (list)
            the list of args
        """
        return self._args

    def get_dirs(self) -> list:
        """
        getter of self._known_directories
        
        Returns:
        self._known_directories (list)
            the list of directories
        """
        return self._known_directories

    def check_unknown_args(self, shell_arg: bool = False) -> list:
        """
        Calculate the suggestions for each unknown argument passed in
        using the levenshtein distance to all known/possible arguments
        
        Parameters:
        shell_arg (bool):
            indicates whether of not the shell has been used
            
        Returns:
        possible_arg_replacements (list):
            a list of the structure [(arg1, [suggestions]), (arg2, [suggestions]), ...]
        """
        possible_arg_replacements = []

        for u_arg in self._unknown_args:
            possible_arg_replacement = (u_arg, [])
            for arg in ALL_ARGS:
                if shell_arg and not arg.show_arg_on_shell:
                    continue
                leven_short = levenshtein(arg.short_form, u_arg)
                leven_long = levenshtein(arg.long_form, u_arg)
# print(leven_short.__round__(3), leven_long.__round__(3),
#       max(leven_short, leven_long).__round__(3), u_arg, arg.long_form, sep="\t") # DEBUG
                if max(leven_short, leven_long) > self.SIMILARITY_LIMIT:
                    if leven_short > leven_long:
                        possible_arg_replacement[1].append((arg.short_form, leven_short))
                    else:
                        possible_arg_replacement[1].append((arg.long_form, leven_long))
            possible_arg_replacements.append(possible_arg_replacement)

        return possible_arg_replacements

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
        (args, unknown_args, unknown_files, echo_args) (tuple):
            contains the paramater in a sorted manner
        """
        self.gen_arguments(argv, delete)
        return (self._args, self._unknown_args, self._unknown_files, self._echo_args)

    def get_files(self, dot_files: bool = False) -> list:
        """
        Collect all files from the given patterns or directories
        provided as an argument.
        
        Parameters:
        dot_files (bool):
            indicates if dotfiles should be included.
        
        Returns:
        self._known_files (list):
            a list containing all found files
        """
        if dot_files:
            # since py3.11 iglob supports queries for hidden,
            # we want compatibility for more versions ...
            glob._ishidden = lambda _: False
        for struct_type, structure in self._known_file_structures:
            if struct_type == IS_FILE:
                self._known_files.append(structure)
            elif struct_type == IS_DIR:
                for filename in glob.iglob(structure):
                    if os.path.isfile(filename):
                        self._known_files.append(os.path.realpath(filename))
                    else:
                        self._known_directories.append(filename)
            elif struct_type == IS_PATTERN:
                for _filename in glob.iglob(structure, recursive=True):
                    filename = os.path.realpath(_filename)
                    if os.path.isfile(filename):
                        self._known_files.append(os.path.realpath(filename))
                    else:
                        self._known_directories.append(filename)

        return self._known_files

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
        if re.match(r"\Aenc[\=\:].+\Z", param, re.IGNORECASE):
            self.file_encoding = param[4:]
            return False
        # 'match' + ('=' or ':') + file_match
        if re.match(r"\Amatch[\=\:].+\Z", param, re.IGNORECASE):
            if delete:
                self.file_match.discard(param[6:])
                return False
            self.file_match.add(fr'{param[6:]}')
            return False
        # 'find' + ('=' or ':') + file_search
        if re.match(r"\Afind[\=\:].+\Z", param, re.IGNORECASE):
            if delete:
                self.file_search.discard(param[5:])
                return False
            self.file_search.add(param[5:])
            return False
        # 'trunc' + ('='/':') + file_truncate[0] +':'+ file_truncate[1] [+ ':' + file_truncate[2]]
        if re.match(r"\Atrunc[\=\:][0-9\(\)\+\-\*\/]*\:[0-9\(\)\+\-\*\/]*\:?[0-9\(\)\+\-\*\/]*\Z",
                    param, re.IGNORECASE):
            for i, p_split in enumerate(param[6:].split(':')):
                try:
                    self.file_truncate[i] = int(eval(p_split))
                except (SyntaxError, NameError, ValueError, ArithmeticError):
                    self.file_truncate[i] = None
            return False
        # '[' + ARGS_CUT + ']'
        if re.match(r"\A\[[0-9\(\)\+\-\*\/]*\:[0-9\(\)\+\-\*\/]*\:?[0-9\(\)\+\-\*\/]*\]\Z", param):
            self._args.append((ARGS_CUT, param))
            return False
        # '[' + ARGS_REPLACE_THIS + ',' + ARGS_REPLACE_WITH + ']' (escape chars with '\')
        if re.match(r"\A\[(?:.*[^\\])?(?:\\\\)*,(?:.*[^\\])?(?:\\\\)*\]\Z", param):
            self._args.append((ARGS_REPLACE, param))
            return False

        # default parameters
        for arg in ALL_ARGS:
            if param in (arg.short_form, arg.long_form):
                self._args.append((arg.arg_id, param))
                if arg.arg_id == ARGS_ECHO:
                    return True
                return False
        possible_path = os.path.realpath(param)
        if os.path.isfile(possible_path):
            self._known_file_structures.append((IS_FILE, possible_path))
        elif os.path.isdir(possible_path):
            self._known_file_structures.append((IS_DIR, possible_path + '/**'))
        elif '*' in param:
            # matches file-patterns, not directories (e.g. *.txt)
            self._known_file_structures.append((IS_PATTERN, param))
        elif len(param) > 2 and param[0] == '-' != param[1]:
            for i in range(1, len(param)):
                if self._add_argument('-' + param[i], delete):
                    return True
        # out of bound is not possible, in case of length 0 param, possible_path would have
        # become the working-path and therefor handled the param as a directory
        elif param[0] != '-':
            self._unknown_files.append(param)
        else:
            self._unknown_args.append(param)
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
        """
        input_args = argv[1:]
        self._clear_values()

        echo_call = False
        for arg in input_args:
            if echo_call:
                self._echo_args.append(arg)
                continue
            echo_call = self._add_argument(arg, delete)
