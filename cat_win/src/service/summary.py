"""
summary
"""

from collections import Counter
from itertools import groupby

from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.regex import RE_TOKENIZER
from cat_win.src.service.fileattributes import (
    _convert_size,
    get_dir_size,
    get_file_size
)
from cat_win.src.service.helper.iohelper import IoHelper


def _unique_list(_l: list) -> list:
    """
    Returns a list of unique elements from the input list.
    Keeps the order.

    Parameters:
    _l (list):
        the list to filter for unique elements

    Returns:
    unique_elements (list):
        a list of unique elements from the input list
    """
    unique_elements = []
    for _i in _l:
        if _i in unique_elements:
            continue
        unique_elements.append(_i)
    return unique_elements

class Summary:
    """
    collection of static summaries.
    """
    COLOR: str       = ''
    COLOR_RESET: str = ''

    unique: bool = False

    @staticmethod
    def set_flags(unique: bool) -> None:
        """
        setup the flags to use in the summaries.

        Parameters:
        unique (bool):
            indicates if the listed summary should only display the elements once
        """
        Summary.unique = unique

    @staticmethod
    def set_colors(color_dic: dict) -> None:
        """
        setup the colors to use in the summaries.

        Parameters:
        color_dic (dict):
            color dictionary containing all configured ANSI color values
        """
        Summary.COLOR       = color_dic[CKW.SUMMARY]
        Summary.COLOR_RESET = color_dic[CKW.RESET_ALL]


    @staticmethod
    def show_files(files: list, detailed: bool) -> None:
        """
        displays u_files.files including their size and calculates
        their size sum.

        Parameters:
        detailed (bool):
            indicates if the detailed summary should be displayed.
        files (list):
            the fies to summarize.
        """
        if not files:
            print(Summary.COLOR, end='')
            print('No files have been found!', end='')
            print(Summary.COLOR_RESET)
            return
        if Summary.unique:
            files = _unique_list(files)

        file_sizes = []
        msg = 'found' if detailed else 'applied'
        print(Summary.COLOR, end='')
        print(f"{msg} FILE(s):", end='')
        print(Summary.COLOR_RESET)
        for file in files:
            if file.file_size == -1:
                file.set_file_size(get_file_size(file.path))
            file_sizes.append(file.file_size)
            print(f"     {Summary.COLOR}" + \
                f"{str(_convert_size(file.file_size)).rjust(10)}", end='')
            prefix = ' ' if file.plaintext        else '-'
            prefix+= '*' if file.contains_queried else ' '
            print(f"{prefix}{file.displayname}{Summary.COLOR_RESET}")
        print(Summary.COLOR, end='')
        print(f"Sum: {str(_convert_size(sum(file_sizes))).rjust(10)}", end='')
        print(Summary.COLOR_RESET)
        print(Summary.COLOR, end='')
        print(f"Amount:\t{len(files)}", end='')
        print(Summary.COLOR_RESET)

    @staticmethod
    def show_dirs(known_directories: list) -> None:
        """
        displays all found directoies.

        known_directories (list):
            the directories to display
        """
        if not known_directories:
            print(Summary.COLOR, end='')
            print('No directores have been found!', end='')
            print(Summary.COLOR_RESET)
            return
        if Summary.unique:
            known_directories = _unique_list(known_directories)

        dir_sizes = []
        print(Summary.COLOR, end='')
        print('found DIR(s):', end='')
        print(Summary.COLOR_RESET)
        for directory in known_directories:
            dir_sizes.append(get_dir_size(directory))
            print(f"     {Summary.COLOR}" + \
                f"{str(_convert_size(dir_sizes[-1]).rjust(10))}", end='')
            print(f"  {directory}{Summary.COLOR_RESET}")
        print(Summary.COLOR, end='')
        print(f"Sum: {str(_convert_size(sum(dir_sizes))).rjust(10)}", end='')
        print(Summary.COLOR_RESET)
        print(Summary.COLOR, end='')
        print(f"Amount:\t{len(known_directories)}", end='')
        print(Summary.COLOR_RESET)

    @staticmethod
    def show_sum(files: list, detailed: bool, all_files_lines: dict,
                 all_line_number_place_holder: int) -> None:
        """
        display the line sum of each file individually if
        detailed is specified.
        display the line sum of all files.

        files (list):
            the fies to summarize.
        detailed (bool):
            indicates if the detailed summary should be displayed.
        all_files_lines (dict):
            the sum of lines for each file individually (see files)
        all_line_number_place_holder (int):
            the amount of chars neccessary to display the last line (breaks on base64 decoding)
            (see files)
        """
        if Summary.unique:
            files = _unique_list(files)

        if files and detailed:
            longest_file_name = max(map(len, all_files_lines.keys())) + 1
            print(f"{Summary.COLOR}{'File': <{longest_file_name}}{Summary.COLOR_RESET}"
                f"{Summary.COLOR}LineCount{Summary.COLOR_RESET}")
            for file in files:
                file_path = str(file.path)
                print(f"{Summary.COLOR}{file_path: <{longest_file_name}}" + \
                    f"{all_files_lines[file_path]: >{all_line_number_place_holder}}" + \
                        f"{Summary.COLOR_RESET}")
            print()

        print(f"{Summary.COLOR}Lines (Sum): " + \
            f"{sum(all_files_lines[str(f.path)] for f in files)}{Summary.COLOR_RESET}")

    @staticmethod
    def show_wordcount(files: list, file_encoding: str) -> None:
        """
        summarize how often each word/token is used in the specifed files.

        Parameters:
        files (list):
            the fies to summarize.
        file_encoding (str):
            the encoding to use when opening the files
        """
        if Summary.unique:
            files = _unique_list(files)

        word_count = Counter()
        used_files = []

        for hfile in files:
            try:
                f_content = IoHelper.read_file(hfile.path, file_encoding=file_encoding,
                                               errors='replace')
                word_count.update(RE_TOKENIZER.findall(f_content))
                used_files.append(hfile.displayname)
            except (OSError, UnicodeError):
                pass
        if not used_files:
            print(Summary.COLOR, end='')
            print('The word count could not be calculated.', end='')
            print(Summary.COLOR_RESET)
            return

        print(Summary.COLOR, end='')
        print('The word count includes the following files:', end='')
        print(Summary.COLOR_RESET, end='\n\t')
        print('\n\t'.join(map(
            lambda f: f"{Summary.COLOR}{f}{Summary.COLOR_RESET}", used_files
        )))

        for _, group in groupby(word_count.most_common(), lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_word_count = map(
                lambda x: f"{Summary.COLOR}{x[0]}{Summary.COLOR_RESET}: "
                f"{Summary.COLOR}{x[1]}{Summary.COLOR_RESET}",
                sorted_group
            )
            print('\n' + '\n'.join(formatted_word_count), end='')
        print(Summary.COLOR_RESET)

    @staticmethod
    def show_charcount(files: list, file_encoding: str) -> None:
        """
        summarize how often each character is used in the specifed files.

        Parameters:
        files (list):
            the fies to summarize.
        file_encoding (str):
            the encoding to use when opening the files
        """
        if Summary.unique:
            files = _unique_list(files)

        char_count = Counter()
        used_files = []

        for hfile in files:
            try:
                f_content = IoHelper.read_file(hfile.path, file_encoding=file_encoding,
                                               errors='replace')
                char_count.update(f_content)
                used_files.append(hfile.displayname)
            except (OSError, UnicodeError):
                pass
        if not used_files:
            print(Summary.COLOR, end='')
            print('The char count could not be calculated.', end='')
            print(Summary.COLOR_RESET)
            return

        print(Summary.COLOR, end='')
        print('The char count includes the following files:', end='')
        print(Summary.COLOR_RESET, end='\n\t')
        print('\n\t'.join(map(
            lambda f: f"{Summary.COLOR}{f}{Summary.COLOR_RESET}", used_files
        )))

        for _, group in groupby(char_count.most_common(), lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_char_count = map(
                lambda x: f"{Summary.COLOR}{repr(x[0]) if x[0].isspace() else x[0]}"
                f"{Summary.COLOR_RESET}: {Summary.COLOR}{x[1]}{Summary.COLOR_RESET}",
                sorted_group
            )
            print('\n' + '\n'.join(formatted_char_count), end='')
        print(Summary.COLOR_RESET)
