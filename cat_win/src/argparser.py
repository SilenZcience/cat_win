"""
argparser
"""

import glob
import os

from cat_win.src.const.argconstants import ALL_ARGS, ARGS_CUT, ARGS_REPLACE, ARGS_ECHO
from cat_win.src.const.regex import compile_re
from cat_win.src.const.regex import RE_ENCODING, RE_MATCH, RE_M_ATCH, RE_FIND, RE_F_IND
from cat_win.src.const.regex import RE_TRUNC, RE_CUT, RE_REPLACE, RE_REPLACE_COMMA

IS_FILE, IS_DIR, IS_DIR_CONTENT, IS_PATTERN = range(0, 4)


class ArgParser:
    """
    defines the ArgParser
    """
    def __init__(self, default_file_encoding: str = 'utf-8',
                 unicode_echo: bool = True,
                 unicode_find: bool = True,
                 unicode_replace: bool = True) -> None:
        self.default_file_encoding: str = default_file_encoding
        self.unicode_echo: bool = unicode_echo
        self.unicode_find = unicode_find
        self.unicode_replace = unicode_replace
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
        self.file_queries = []
        self.file_replace_mapping = {}
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

    def get_arguments(self, argv: list, delete: bool = False) -> tuple:
        """
        Read all args to either a valid parameter, an invalid parameter,
        a known file, an unknown file, or an echo parameter to print out.
        
        Parameters:
        argv (list):
            the entire sys.argv list
        delete (bool):
            indicates if a parameter should be deleted or added. Needed for
            the repl when changing file_queries
        
        Returns:
        (args, unknown_args, unknown_files, echo_args) (tuple):
            contains the paramater in a sorted manner
        """
        self.gen_arguments(argv, delete)
        echo_args = ' '.join(self._echo_args)
        if self.unicode_echo:
            try:
                echo_args = echo_args.encode(self.file_encoding).decode('unicode_escape').encode('latin-1').decode(self.file_encoding)
            except UnicodeError:
                pass
        return (self._args, self._unknown_args, self._unknown_files, echo_args)

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
                self._known_directories.append(structure)
            elif struct_type == IS_DIR_CONTENT:
                for filename in glob.iglob(structure):
                    if os.path.isfile(filename):
                        self._known_files.append(os.path.realpath(filename))
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
            the repl when changing file_queries
            
        Returns:
        (bool):
            True if -E has been called, meaning every following parameter
            should simply be printed to stdout.
        """
        # 'enc' + ('=' or ':') + file_encoding
        if RE_ENCODING.match(param):
            self.file_encoding = param[4:]
            return False
        # 'match' + ('=' or ':') + file_match
        if RE_MATCH.match(param) or RE_M_ATCH.match(param):
            p_length = 6 if RE_MATCH.match(param) else 2
            query_element = (compile_re(param[p_length:], param[:p_length].isupper()),
                             param[:p_length].isupper())
            if delete:
                if query_element in self.file_queries:
                    self.file_queries.remove(query_element)
                return False
            self.file_queries.append(query_element)
            return False
        # 'find' + ('=' or ':') + file_search
        if RE_FIND.match(param) or RE_F_IND.match(param):
            p_length = 5 if RE_FIND.match(param) else 2
            query = param[p_length:]
            try:
                if self.unicode_find:
                    query = query.encode().decode('unicode_escape').encode('latin-1').decode()
            except UnicodeError:
                pass
            query_element = (query, param[:p_length].isupper())
            if delete:
                self.file_queries.remove(query_element)
                return False
            self.file_queries.append(query_element)
            return False
        # 'trunc' + ('='/':') + file_truncate[0] +':'+ file_truncate[1] [+ ':' + file_truncate[2]]
        if RE_TRUNC.match(param):
            for i, p_split in enumerate(param[6:].split(':')):
                try:
                    self.file_truncate[i] = int(eval(p_split))
                except (SyntaxError, NameError, ValueError, ArithmeticError):
                    self.file_truncate[i] = None
            return False
        # '[' + ARGS_CUT + ']'
        if RE_CUT.match(param):
            self._args.append((ARGS_CUT, param))
            return False
        # '[' + ARGS_REPLACE_THIS + ',' + ARGS_REPLACE_WITH + ']' (escape chars with '\')
        if RE_REPLACE.match(param):
            re_match = RE_REPLACE.match(param)
            re_this = RE_REPLACE_COMMA.sub(r"\1,", re_match.group(1))
            re_with = RE_REPLACE_COMMA.sub(r"\1,", re_match.group(2))
            try:
                if self.unicode_replace:
                    re_this = re_this.encode().decode('unicode_escape').encode('latin-1').decode()
                    re_with = re_with.encode().decode('unicode_escape').encode('latin-1').decode()
            except UnicodeError:
                pass
            finally:
                self.file_replace_mapping[param] = (re_this, re_with)
            self._args.append((ARGS_REPLACE, param))
            return False

        # default parameters
        for arg in ALL_ARGS:
            if param in (arg.short_form, arg.long_form):
                self._args.append((arg.arg_id, param))
                return arg.arg_id == ARGS_ECHO
        possible_path = os.path.realpath(param)
        if os.path.isfile(possible_path):
            self._known_file_structures.append((IS_FILE, possible_path))
        elif os.path.isdir(possible_path):
            self._known_file_structures.append((IS_DIR, possible_path))
            self._known_file_structures.append((IS_DIR_CONTENT, possible_path + '/*'))
        elif '*' in param or '?' in param or '[' in param:
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
            the repl when changing file_queries
        """
        input_args = argv[1:]
        self._clear_values()

        echo_call = False
        for arg in input_args:
            if echo_call:
                self._echo_args.append(arg)
                continue
            echo_call = self._add_argument(arg, delete)
