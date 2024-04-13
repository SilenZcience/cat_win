"""
summary
"""

from itertools import groupby

from cat_win.const.regex import TOKENIZER
from cat_win.util.service.fileattributes import get_file_size, _convert_size


class Summary:
    """
    collection of static summaries.
    """
    color: str = ''
    color_reset: str = ''


    @staticmethod
    def setup_colors(color: str, color_reset: str) -> None:
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
    def show_files(detailed: bool, files: list) -> None:
        """
        displays holder.files including their size and calculates
        their size sum.
        
        Parameters:
        detailed (bool):
            indicates if the detailed summary should be displayed.
        files (list):
            the fies to summarize.
        """
        if not files:
            return
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
                f"{str(_convert_size(file.file_size)).rjust(9)}", end='')
            prefix = ' ' if file.plaintext        else '-'
            prefix+= '*' if file.contains_queried else ' '
            print(f"{prefix}{file.displayname}{Summary.color_reset}")
        print(Summary.color, end='')
        print(f"Sum: {str(_convert_size(sum(file_sizes))).rjust(9)}", end='')
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
        print(Summary.color, end='')
        print('found DIR(s):', end='')
        print(Summary.color_reset)
        for directory in known_directories:
            print(f"     {Summary.color}" + \
                f"{directory}{Summary.color_reset}")
        print(Summary.color, end='')
        print(f"Amount:\t{len(known_directories)}", end='')
        print(Summary.color_reset)


    @staticmethod
    def show_sum(detailed: bool, all_files_lines: dict, all_line_number_place_holder: int,
                 all_files_lines_sum: int) -> None:
        """
        display the line sum of each file individually if
        detailed is specified.
        display the line sum of all files.

        detailed (bool):
            indicates if the detailed summary should be displayed.
        all_files_lines (dict):
            the sum of lines for each file individually (see holder)
        all_line_number_place_holder (int):
            the amount of chars neccessary to display the last line (breaks on base64 decoding)
            (see holder)
        all_files_lines_sum (int):
            the sum of all lines of all files (see holder)
        """
        if detailed:
            longest_file_name = max(map(len, all_files_lines.keys())) + 1
            print(f"{Summary.color}{'File': <{longest_file_name}}{Summary.color_reset}"
                f"{Summary.color}LineCount{Summary.color_reset}")
            for file, _ in all_files_lines.items():
                print(f"{Summary.color}{file: <{longest_file_name}}" + \
                    f"{all_files_lines[file]: >{all_line_number_place_holder}}" + \
                        f"{Summary.color_reset}")
            print()
        print(f"{Summary.color}Lines (Sum): " + \
            f"{all_files_lines_sum}{Summary.color_reset}")

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
        word_count = {}
        used_files = []

        for hfile in files:
            try:
                with open(hfile.path, 'r', encoding=file_encoding) as file:
                    for token in TOKENIZER.findall(file.read()):
                        word_count[token] = word_count.get(token, 0)+1
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
        sorted_word_count = sorted(word_count.items(), key=lambda token: token[1], reverse=True)
        format_delimeter = f"{Summary.color_reset}:{Summary.color} "
        for _, group in groupby(sorted_word_count, lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_word_count = map(
                lambda x: f"{Summary.color}{x[0]}"
                f"{format_delimeter}{x[1]}{Summary.color_reset}",
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
        char_count = {}
        used_files = []

        for hfile in files:
            try:
                with open(hfile.path, 'r', encoding=file_encoding) as file:
                    for char in list(file.read()):
                        char_count[char] = char_count.get(char, 0)+1
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
        sorted_char_count = sorted(char_count.items(), key=lambda token: token[1], reverse=True)
        format_delimeter = f"{Summary.color_reset}:{Summary.color} "
        for _, group in groupby(sorted_char_count, lambda token: token[1]):
            sorted_group = sorted(group, key=lambda token: token[0])
            formatted_char_count = map(
                lambda x: f"{Summary.color}{repr(x[0]) if x[0].isspace() else x[0]}"
                f"{format_delimeter}{x[1]}{Summary.color_reset}",
                sorted_group
                )
            print('\n' + '\n'.join(formatted_char_count), end='')
        print(Summary.color_reset)
