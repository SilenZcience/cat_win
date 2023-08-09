from os.path import isfile, realpath, isdir
from re import match, IGNORECASE
import glob

from cat_win.const.argconstants import ALL_ARGS, ARGS_CUT, ARGS_REPLACE, ARGS_ECHO


DEFAULT_FILE_ENCODING = 'utf-8'


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
    a, b = len(str_a), len(str_b)
    max_len = max(a, b)
    if a*b == 0:
        return (100 if max_len == 0 else (1 - (a+b)/max_len) * 100)

    d = [[i] + ([0] * b) for i in range(a+1)]
    d[0] = list(range(b+1))
    
    for i in range(1, a+1):
        str_a_i = str_a[i-1:i]

        for j in range(1, b+1):
            str_b_j = str_b[j-1:j]

            d[i][j] = min(d[i-1][j]+1,
                          d[i][j-1]+1,
                          d[i-1][j-1]+int(str_a_i.lower() != str_b_j.lower()))

    return (1 - d[a][b]/max_len) * 100


class ArgParser:
    SIMILARITY_LIMIT = 50.0

    def __init__(self) -> None:
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

        self._known_files_patterns = []       

    def reset_values(self) -> None:
        """
        The here defined variables may be accessed from the outside.
        """
        self.file_encoding: str = DEFAULT_FILE_ENCODING
        self.file_search = set()
        self.file_match = set()
        self.file_truncate = [None, None, None]

    def get_args(self) -> list:
        return self._args

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

    def get_files(self, hidden: bool = False) -> list:
        """
        Collect all files from the given patterns or directories
        provided as an argument.
        
        Parameters:
        hidden (bool):
            indicates if hidden files (and dotfiles) should
            be included.
        
        Returns:
        self._known_files (list):
            a list containing all found files
        """
        if hidden:
            glob._ishidden = lambda _: False
        for pattern in self._known_files_patterns:
            for filename in glob.iglob(pattern, recursive=True):
                if isfile(filename):
                    self._known_files.append(realpath(filename))

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
        if match(r"\Aenc[\=\:].+\Z", param, IGNORECASE):
            self.file_encoding = param[4:]
            return False
        # 'match' + ('=' or ':') + file_match
        if match(r"\Amatch[\=\:].+\Z", param, IGNORECASE):
            if delete:
                self.file_match.discard(param[6:])
                return False
            self.file_match.add(fr'{param[6:]}')
            return False
        # 'find' + ('=' or ':') + file_search
        if match(r"\Afind[\=\:].+\Z", param, IGNORECASE):
            if delete:
                self.file_search.discard(param[5:])
                return False
            self.file_search.add(param[5:])
            return False
        # 'trunc' + ('=' or ':') + file_truncate[0] + ':' + file_truncate[1] [+ ':' + file_truncate[2]]
        if match(r"\Atrunc[\=\:][0-9\(\)\+\-\*\/]*\:[0-9\(\)\+\-\*\/]*\:?[0-9\(\)\+\-\*\/]*\Z", param, IGNORECASE):
            for i, p_split in enumerate(param[6:].split(':')):
                try:
                    self.file_truncate[i] = int(eval(p_split))
                except:
                    self.file_truncate[i] = None
            return False
        # '[' + ARGS_CUT + ']'
        if match(r"\A\[[0-9\(\)\+\-\*\/]*\:[0-9\(\)\+\-\*\/]*\:?[0-9\(\)\+\-\*\/]*\]\Z", param):
            self._args.append((ARGS_CUT, param))
            return False
        # '[' + ARGS_REPLACE_THIS + ',' + ARGS_REPLACE_WITH + ']' (escape chars with '\')
        if match(r"\A\[(?:.*[^\\])?(?:\\\\)*,(?:.*[^\\])?(?:\\\\)*\]\Z", param):
            self._args.append((ARGS_REPLACE, param))
            return False

        # default parameters
        for arg in ALL_ARGS:
            if param in (arg.short_form, arg.long_form):
                self._args.append((arg.arg_id, param))
                if arg.arg_id == ARGS_ECHO:
                    return True
                return False

        possible_path = realpath(param)
        if '*' in param:
            self._known_files_patterns.append(param)
        elif isdir(possible_path):
            self._known_files_patterns.append(possible_path + '/**')
        elif isfile(possible_path):
            self._known_files.append(possible_path)
        elif len(param) > 2 and param[0] == '-' and param[1] != '-':
            for i in range(1, len(param)):
                if self._add_argument('-' + param[i], delete):
                    return True
        elif match(r"\A[^-].*\Z", param):
            self._unknown_files.append(realpath(param))
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
