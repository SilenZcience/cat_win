from functools import lru_cache
from heapq import nlargest

from cat_win.const.argconstants import HIGHEST_ARG_ID, ARGS_NOCOL, ARGS_LLENGTH, ARGS_NUMBER, \
    ARGS_REVERSE, ARGS_B64D, ARGS_B64E, ARGS_COUNT, ARGS_CCOUNT, DIFFERENTIABLE_ARGS
from cat_win.util.cbase64 import _decode_base64
from cat_win.util.file import File


def reduce_list(args: list) -> list:
    """
    remove duplicate args regardless if shortform or
    longform has been used, an exception exists for those
    args that contain different information per parameter.
    
    Parameters:
    args (list):
        the entire list of args, containing possible duplicates
        
    Returns:
    new_args (list):
        the args-list without duplicates
    """
    new_args = []
    temp_args_id = []

    for arg in args:
        id, _ = arg
        # it can make sense to have the exact same parameter twice, even if it does
        # the same information, therefor we do not test for the param here.
        if id in DIFFERENTIABLE_ARGS:
            new_args.append(arg)
        elif id not in temp_args_id:
            temp_args_id.append(id)
            new_args.append(arg)

    return new_args

def diff_list(args: list, to_remove: list) -> list:
    """
    subtract args in to_remove from args in args regardless
    if shortform or longform has been used, an exception exists for those
    args that contain different information per parameter.
    
    Parameters:
    args (list):
        the entire list of args
    to_remove (list):
        the list of args to subtract from the args list
        
    Returns:
    new_args (list):
        the args-list without duplicates
    """
    new_args = []
    temp_args_id = [id for id, _ in to_remove]
    temp_args = [arg for arg in to_remove if arg[0] in DIFFERENTIABLE_ARGS]

    for arg in args:
        id, _ = arg
        if id not in temp_args_id or id in DIFFERENTIABLE_ARGS:
            new_args.append(arg)

    for arg in temp_args:
        try:
            new_args.remove(arg)
        except ValueError:
            pass

    return new_args

class Holder():
    def __init__(self) -> None:
        self.files: list = []  # all files, including tmp-file from stdin
        self._inner_files: list = []
        self.args: list = []  # list of all used parameters: format [[id, param]]
        self.args_id: list = [False] * (HIGHEST_ARG_ID + 1)
        self.temp_file_stdin = None  # if stdin is used, this temp_file will contain the stdin-input
        self.temp_file_echo = None  # if ARGS_ECHO is used, this temp_file will contain the following parameters
        self.temp_file_urls = []
        self.reversed = False

        # the amount of chars neccessary to display the last file
        self.file_number_place_holder = 0
        # the sum of all lines of all files
        self.all_files_lines_sum = 0
        # the sum of lines for each file individually
        self.all_files_lines = {}
        # the amount of chars neccessary to display the last line (breaks on base64 decoding)
        self.all_line_number_place_holder = 0
        # the amount of chars neccessary to display the longest line within all files (breaks on base64 decoding)
        self.file_line_length_place_holder = 0

        self.clip_board = ''

    def _get_file_display_name(self, file: str) -> str:
        """
        return the display name of a file. Expects self.temp_file_stdin
        and self.temp_file_echo to be set already.
        
        Parameters_
        file (str):
            a path of a file
            
        Returns:
        (str):
            the display name for the file. Either the path itself
            or a special identifier von stdin or echo inputs
        """
        if file == self.temp_file_stdin:
            return '<STDIN>'
        if file == self.temp_file_echo:
            return '<ECHO>'
        if file in self.temp_file_urls:
            return '<URL>'
        return file

    def set_files(self, files: list) -> None:
        self.files = [File(path, self._get_file_display_name(path)) for path in files]
        self._inner_files = files[:]

    def set_args(self, args: list) -> None:
        self.args = reduce_list(args)
        for arg_id, _ in self.args:
            self.args_id[arg_id] = True
        if self.args_id[ARGS_B64E]:
            self.args_id[ARGS_NOCOL] = True
        self.reversed = self.args_id[ARGS_REVERSE]

    def add_args(self, args: list) -> None:
        self.args_id = [False] * (HIGHEST_ARG_ID + 1)
        self.set_args(self.args + args)

    def delete_args(self, args: list) -> None:
        self.args_id = [False] * (HIGHEST_ARG_ID + 1)
        self.set_args(diff_list(self.args, args))

    def set_temp_file_stdin(self, file: str) -> None:
        self.temp_file_stdin = file

    def set_temp_file_echo(self, file: str) -> None:
        self.temp_file_echo = file

    def set_temp_files_url(self, files: list) -> None:
        self.temp_file_urls = files

    def __calc_file_number_place_holder__(self) -> None:
        self.file_number_place_holder = len(str(len(self.files)))

    def __count_generator__(self, reader):
        """
        Parameters:
        reader (method):
            the method to read from
        
        Yields:
        byt (bytes):
            the bytes in chunks read from the reader
        """
        byt = reader(1024 * 1024)
        while byt:
            yield byt
            byt = reader(1024 * 1024)

    @lru_cache(maxsize=10)
    def __get_file_lines_sum__(self, file: str) -> int:
        try:
            with open(file, 'rb') as raw_f:
                c_generator = self.__count_generator__(raw_f.raw.read)
                lines_sum = sum(buffer.count(b'\n') for buffer in c_generator) + 1
            return lines_sum
        except OSError:
            return 0

    def __calc_place_holder__(self) -> None:
        file_lines = []
        for file in self._inner_files:
            file_line_sum = self.__get_file_lines_sum__(file)
            file_lines.append(file_line_sum)
            self.all_files_lines[file] = file_line_sum
        self.all_files_lines_sum = sum(file_lines)
        self.all_line_number_place_holder = len(str(max(file_lines)))

    @lru_cache(maxsize=10)
    def __calc_max_line_length__(self, file: str) -> int:
        """
        Calculate self.file_line_length_place_holder for a single file.
        
        Parameters:
        file (str):
            a string representation of a file (-path)
            
        Returns:
        (int):
            the length of the placeholder to represent
            the longest line within the file
        """
        heap = []
        lines = []
        try:
            with open(file, 'rb') as raw_f:
                lines = raw_f.readlines()
        except OSError:
            return 0
        heap = nlargest(1, lines, len)
        if len(heap) == 0:
            return 0
        # also check the longest line against the last line because
        # the lines still contain (\r)\n, except the last line does not
        longest_line_len = len(heap[0][:-1].rstrip(b'\n').rstrip(b'\r'))
        last_line_len = len(lines[-1].rstrip(b'\n').rstrip(b'\r'))

        return len(str(max(longest_line_len, last_line_len)))

    def __calc_file_line_length_place_holder__(self) -> None:
        self.file_line_length_place_holder = max(self.__calc_max_line_length__(file)
                                             for file in self._inner_files)

    def set_decoding_temp_files(self, temp_files: list) -> None:
        self._inner_files = temp_files[:]

    def generate_values(self, encoding: str) -> None:
        self.__calc_file_number_place_holder__()
        if self.args_id[ARGS_B64D]:
            for i, file in enumerate(self.files):
                try:
                    with open(file.path, 'rb') as raw_f_read:
                        with open(self._inner_files[i], 'wb') as raw_f_write:
                            raw_f_write.write(_decode_base64(raw_f_read.read().decode(encoding)))
                except OSError:
                    pass
        if self.args_id[ARGS_COUNT] or self.args_id[ARGS_CCOUNT] or self.args_id[ARGS_NUMBER]:
            self.__calc_place_holder__()
        if self.args_id[ARGS_LLENGTH]:
            self.__calc_file_line_length_place_holder__()
