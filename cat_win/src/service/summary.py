"""
summary
"""

from collections import Counter
from itertools import groupby

from cat_win.src.const.regex import TOKENIZER
from cat_win.src.service.fileattributes import get_file_size, get_dir_size, _convert_size
from cat_win.src.service.helper.iohelper import IoHelper


class Summary:
    """
    collection of static summaries.
    """
    color: str = ''
    color_reset: str = ''
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
    def set_colors(color: str, color_reset: str) -> None:
        """
        setup the colors to use in the summaries.

        Parameters:
        color (str):
            the color to use (ansi escape)
        color_reset (str)
            the ansi esacpe to reset the color
        """
        Summary.color = color
        Summary.color_reset = color_reset


    @staticmethod
    def _unique_list(_l: list) -> list:
        unique_elements = []
        for _i in _l:
            if _i in unique_elements:
                continue
            unique_elements.append(_i)
        return unique_elements

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
            print(Summary.color, end='')
            print('No files have been found!', end='')
            print(Summary.color_reset)
            return
        if Summary.unique:
            files = Summary._unique_list(files)

        file_sizes = []
        msg = 'found' if detailed else 'applied'
        print(Summary.color, end='')
        print(f"{msg} FILE(s):", end='')
        print(Summary.color_reset)
        for file in files:
            if file.file_size == -1:
                file.set_file_size(get_file_size(file.path))
            file_sizes.append(file.file_size)
            print(f"     {Summary.color}" + \
                f"{str(_convert_size(file.file_size)).rjust(10)}", end='')
            prefix = ' ' if file.plaintext        else '-'
            prefix+= '*' if file.contains_queried else ' '
            print(f"{prefix}{file.displayname}{Summary.color_reset}")
        print(Summary.color, end='')
        print(f"Sum: {str(_convert_size(sum(file_sizes))).rjust(10)}", end='')
        print(Summary.color_reset)
        print(Summary.color, end='')
        print(f"Amount:\t{len(files)}", end='')
        print(Summary.color_reset)

    @staticmethod
    def show_dirs(known_directories: list) -> None:
        """
        displays all found directoies.

        known_directories (list):
            the directories to display
        """
        if not known_directories:
            print(Summary.color, end='')
            print('No directores have been found!', end='')
            print(Summary.color_reset)
            return
        if Summary.unique:
            known_directories = Summary._unique_list(known_directories)

        dir_sizes = []
        print(Summary.color, end='')
        print('found DIR(s):', end='')
        print(Summary.color_reset)
        for directory in known_directories:
            dir_sizes.append(get_dir_size(directory))
            print(f"     {Summary.color}" + \
                f"{str(_convert_size(dir_sizes[-1]).rjust(10))}", end='')
            print(f"  {directory}{Summary.color_reset}")
        print(Summary.color, end='')
        print(f"Sum: {str(_convert_size(sum(dir_sizes))).rjust(10)}", end='')
        print(Summary.color_reset)
        print(Summary.color, end='')
        print(f"Amount:\t{len(known_directories)}", end='')
        print(Summary.color_reset)

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
            files = Summary._unique_list(files)

        if detailed:
            longest_file_name = max(map(len, all_files_lines.keys())) + 1
            print(f"{Summary.color}{'File': <{longest_file_name}}{Summary.color_reset}"
                f"{Summary.color}LineCount{Summary.color_reset}")
            for file in files:
                file_path = str(file.path)
                print(f"{Summary.color}{file_path: <{longest_file_name}}" + \
                    f"{all_files_lines[file_path]: >{all_line_number_place_holder}}" + \
                        f"{Summary.color_reset}")
            print()

        print(f"{Summary.color}Lines (Sum): " + \
            f"{sum(all_files_lines[str(f.path)] for f in files)}{Summary.color_reset}")

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
            files = Summary._unique_list(files)

        word_count = Counter()
        used_files = []

        for hfile in files:
            try:
                f_content = IoHelper.read_file(hfile.path, file_encoding=file_encoding,
                                               errors='replace')
                word_count.update(TOKENIZER.findall(f_content))
                used_files.append(hfile.displayname)
            except (OSError, UnicodeError):
                pass
        if not used_files:
            print(Summary.color, end='')
            print('The word count could not be calculated.', end='')
            print(Summary.color_reset)
            return

        print(Summary.color, end='')
        print('The word count includes the following files:', end='')
        print(Summary.color_reset, end='\n\t')
        print('\n\t'.join(map(
            lambda f: f"{Summary.color}{f}{Summary.color_reset}", used_files
        )))

        for _, group in groupby(word_count.most_common(), lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_word_count = map(
                lambda x: f"{Summary.color}{x[0]}{Summary.color_reset}: "
                f"{Summary.color}{x[1]}{Summary.color_reset}",
                sorted_group
            )
            print('\n' + '\n'.join(formatted_word_count), end='')
        print(Summary.color_reset)

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
            files = Summary._unique_list(files)

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
            print(Summary.color, end='')
            print('The char count could not be calculated.', end='')
            print(Summary.color_reset)
            return

        print(Summary.color, end='')
        print('The char count includes the following files:', end='')
        print(Summary.color_reset, end='\n\t')
        print('\n\t'.join(map(
            lambda f: f"{Summary.color}{f}{Summary.color_reset}", used_files
        )))

        for _, group in groupby(char_count.most_common(), lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_char_count = map(
                lambda x: f"{Summary.color}{repr(x[0]) if x[0].isspace() else x[0]}"
                f"{Summary.color_reset}: {Summary.color}{x[1]}{Summary.color_reset}",
                sorted_group
            )
            print('\n' + '\n'.join(formatted_char_count), end='')
        print(Summary.color_reset)
