"""
cat
"""

try:
    from colorama import init as coloramaInit
except ImportError:
    nop = lambda *_, **__: None; coloramaInit = nop
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from time import monotonic
import os
import platform
import re
import sys

from cat_win.const.argconstants import ALL_ARGS, ARGS_EDITOR, ARGS_WORDCOUNT, ARGS_WWORDCOUNT
from cat_win.const.argconstants import ARGS_HELP, ARGS_NUMBER, ARGS_ENDS, ARGS_SQUEEZE
from cat_win.const.argconstants import ARGS_REVERSE, ARGS_SUM, ARGS_BLANK, ARGS_FILES
from cat_win.const.argconstants import ARGS_STDIN, ARGS_NOCOL, ARGS_BINVIEW, ARGS_FILE_PREFIX
from cat_win.const.argconstants import ARGS_CLIP, ARGS_CHECKSUM, ARGS_DEC, ARGS_HEX, ARGS_BIN
from cat_win.const.argconstants import ARGS_VERSION, ARGS_DEBUG, ARGS_CUT, ARGS_REPLACE, ARGS_DATA
from cat_win.const.argconstants import ARGS_CCONFIG, ARGS_LLENGTH, ARGS_ONELINE, ARGS_PEEK
from cat_win.const.argconstants import ARGS_CHR, ARGS_B64E, ARGS_B64D, ARGS_FFILES, ARGS_GREP
from cat_win.const.argconstants import ARGS_NOBREAK, ARGS_ECHO, ARGS_SSUM, ARGS_HEXVIEW
from cat_win.const.argconstants import ARGS_NOKEYWORD, ARGS_RECONFIGURE, ARGS_RECONFIGURE_IN
from cat_win.const.argconstants import ARGS_RECONFIGURE_OUT, ARGS_RECONFIGURE_ERR, ARGS_CONFIG
from cat_win.const.argconstants import ARGS_EVAL, ARGS_SORT, ARGS_GREP_ONLY, ARGS_PLAIN_ONLY
from cat_win.const.argconstants import ARGS_FFILE_PREFIX, ARGS_DOTFILES, ARGS_OCT, ARGS_URI
from cat_win.const.argconstants import ARGS_DIRECTORIES, ARGS_DDIRECTORIES, ARGS_SPECIFIC_FORMATS
from cat_win.const.argconstants import ARGS_CHARCOUNT, ARGS_CCHARCOUNT, ARGS_STRINGS
from cat_win.const.colorconstants import CKW
from cat_win.const.defaultconstants import DKW
from cat_win.persistence.cconfig import CConfig
from cat_win.persistence.config import Config
from cat_win.util.argparser import ArgParser
from cat_win.util.cbase64 import decode_base64, encode_base64
from cat_win.util.checksum import get_checksum_from_file
from cat_win.util.converter import Converter
from cat_win.util.editor import Editor
from cat_win.util.fileattributes import get_file_meta_data, get_file_size, get_file_mtime
from cat_win.util.fileattributes import _convert_size
from cat_win.util.formatter import Formatter
from cat_win.util.holder import Holder
from cat_win.util.rawviewer import SPECIAL_CHARS, get_raw_view_lines_gen
from cat_win.util.stringfinder import StringFinder
from cat_win.util.strings import get_strings
from cat_win.util.tmpfilehelper import TmpFileHelper
from cat_win.util.urls import sep_valid_urls, read_url
try:
    from cat_win.util.utility import comp_eval, comp_conv, split_replace
except SyntaxError: # in case of Python 3.7
    from cat_win.util.utilityold import comp_eval, comp_conv, split_replace
from cat_win.util import stdinhelper
from cat_win.util.zipviewer import display_zip
from cat_win.web.updatechecker import print_update_information
from cat_win import __project__, __version__, __sysversion__, __author__, __url__


coloramaInit(strip=False)
working_dir = os.path.dirname(os.path.realpath(__file__))

cconfig = CConfig(working_dir)
config = Config(working_dir)

default_color_dic = cconfig.load_config()
color_dic = default_color_dic.copy()
const_dic = config.load_config()

arg_parser = ArgParser(const_dic[DKW.DEFAULT_FILE_ENCODING])
converter = Converter()
holder = Holder()
tmp_file_helper = TmpFileHelper()

on_windows_os = platform.system() == 'Windows'
file_uri_prefix = 'file://' + '/' * on_windows_os
ANSI_CSI_RE = re.compile(r'\001?\033\[(?:\d|;)*[a-zA-Z]\002?') # Control Sequence Introducer
# ANSI_OSC_RE = re.compile(r'\001?\033\]([^\a]*)(\a)\002?')          # Operating System Command

def err_print(*args, **kwargs):
    """
    print to stderr.
    """
    print(*args, file=sys.stderr, flush=True, **kwargs)


def exception_handler(exception_type: type, exception, traceback,
                      debug_hook=sys.excepthook) -> None:
    """
    custom exception handler.
    """
    # STATUS_PIPE_CLOSING can map to WinAPI EINVAL (errno: 22)
    if isinstance(exception, BrokenPipeError) or \
        isinstance(exception, OSError) and exception.errno == 22:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE
    try:
        err_print(color_dic[CKW.RESET_ALL])
        if holder.args_id[ARGS_DEBUG]:
            return debug_hook(exception_type, exception, traceback)
        err_print(f"\n{exception_type.__name__}{':' * bool(str(exception))} {exception}")
        if exception_type != KeyboardInterrupt:
            err_print('If this Exception is unexpected, please raise an official Issue at:')
            err_print(f"{__url__}/issues")
        sys.exit(0)
    except BrokenPipeError: # we only used stderr in the try-block, so it has to be the broken pipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stderr.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE
    except (Exception, KeyboardInterrupt):
        debug_hook(exception_type, exception, traceback)


sys.excepthook = exception_handler


def _show_help(shell: bool = False) -> None:
    """
    Show the Help message and exit.
    """
    if shell:
        help_message = 'Usage: cats [OPTION]...\n'
        help_message += 'Interactively manipulate standard input.\n\n'
    else:
        help_message = 'Usage: catw [FILE]... [OPTION]...\n'
        help_message += 'Concatenate FILE(s) to standard output.\n\n'
    for section_id, group in groupby(ALL_ARGS, lambda x: x.section):
        if section_id < 0:
            continue
        relevant_section = False
        for arg in group:
            if arg.show_arg and (not shell or arg.show_arg_on_shell):
                help_message += f"\t{f'{arg.short_form}, {arg.long_form}': <25}{arg.arg_help}\n"
                relevant_section = True
        help_message += '\n' * relevant_section
    help_message += f"\t{'-R, --R<stream>': <25}"
    help_message += 'reconfigure the std-stream(s) with the parsed encoding\n'
    help_message += "\t<stream> == 'in'/'out'/'err' (default is stdin & stdout)\n"
    help_message += '\n'
    help_message += f"\t{'enc=X, enc:X'    : <25}set file encoding to X (default is utf-8)\n"
    help_message += f"\t{'find=X, find:X'  : <25}find/query a substring X in the given files\n"
    help_message += f"\t{'match=X, match:X': <25}find/query a pattern X in the given files\n"
    if not shell:
        help_message += f"\t{'trunc=X:Y, trunc:X:Y': <25}"
        help_message += 'truncate file to lines x and y (python-like)\n'
    help_message += '\n'
    help_message += f"\t{'[a,b]': <25}replace a with b in every line (escape chars with '\\')\n"
    help_message += f"\t{'[a:b:c]': <25}python-like string indexing syntax (line by line)\n"
    help_message += '\n'
    help_message += 'Examples:\n'
    if shell:
        help_message += '\tcats --ln --dec\n'
        help_message += '\t> >>> 12345\n'
        help_message += '\t1) [53] 12345 {Hexadecimal: 0x3039; Binary: 0b11000000111001}\n'
        help_message += '\t> >>> !help\n'
        help_message += '\t> ...\n'
    else:
        help_message += f"\t{'catw f g -r' : <25}"
        help_message += "Output g's contents in reverse order, then f's content in reverse order\n"
        help_message += f"\t{'catw f g -ne': <25}"
        help_message += "Output f's, then g's content, "
        help_message += 'while numerating and showing the end of lines\n'
        help_message += f"\t{'catw f trunc=a:b:c': <25}"
        help_message += "Output f's content starting at line a, ending at line b, stepping c\n"
    print(help_message)
    print_update_information(__project__, __version__, color_dic, on_windows_os)


def _show_version() -> None:
    """
    Show the Version message and exit.
    """
    cat_version = f"Catw {__version__} - from {working_dir}\n"
    version_message = '\n'
    version_message += '-' * len(cat_version) + '\n'
    version_message += cat_version
    version_message += '-' * len(cat_version) + '\n'
    version_message += '\n'
    version_message += f"Built with: \tPython {__sysversion__}\n"  # sys.version
    try:
        time_stamp = datetime.fromtimestamp(os.path.getctime(os.path.realpath(__file__)))
        version_message += f"Install time: \t{time_stamp}\n"
    except OSError: # fails on pyinstaller executable
        version_message += 'Install time: \t-\n'
    version_message += f"Author: \t{__author__}\n"
    print(version_message)
    print_update_information(__project__, __version__, color_dic, on_windows_os)


def _show_debug(args: list, unknown_args: list, known_files: list, unknown_files: list,
                echo_args: list, valid_urls: list) -> None:
    """
    Print all neccassary debug information
    """
    err_print('================================================ ' + \
        'DEBUG ================================================')
    err_print('sys_args:', sys.argv)
    err_print('args: ', end='')
    err_print([(arg[0], arg[1], holder.args_id[arg[0]]) for arg in args])
    err_print('unknown_args: ', end='')
    err_print(unknown_args)
    err_print('known_files: ', end='')
    err_print(known_files)
    err_print('unknown_files: ', end='')
    err_print(unknown_files)
    err_print('echo_args: ', end='')
    err_print(echo_args)
    err_print('valid_urls: ', end='')
    err_print(valid_urls)
    err_print('file encoding: ', end='')
    err_print(arg_parser.file_encoding)
    err_print('search keyword(s): ', end='')
    err_print(arg_parser.file_search)
    err_print('search match(es): ', end='')
    err_print(arg_parser.file_match)
    err_print('truncate file: ', end='')
    err_print(arg_parser.file_truncate)
    err_print('===================================================' + \
              '====================================================')


def _show_wordcount() -> None:
    word_count = {}
    used_files = []

    for hfile in holder.files:
        try:
            with open(hfile.path, 'r', encoding=arg_parser.file_encoding) as file:
                for token in re.findall(r'\w+|[^\s\w]', file.read()):
                    word_count[token] = word_count.get(token, 0)+1
            used_files.append(hfile.displayname)
        except (OSError, UnicodeError):
            pass

    print(color_dic[CKW.SUMMARY], end='')
    print('The word count includes the following files:', end='')
    print(color_dic[CKW.RESET_ALL], end='\n\t')
    print('\n\t'.join(map(
        lambda f: f"{color_dic[CKW.SUMMARY]}{f}{color_dic[CKW.RESET_ALL]}", used_files
        )))
    sorted_word_count = sorted(word_count.items(), key=lambda token: token[1], reverse=True)
    format_delimeter = f"{color_dic[CKW.RESET_ALL]}:{color_dic[CKW.SUMMARY]} "
    for _, group in groupby(sorted_word_count, lambda token: token[1]):
        sorted_group = sorted(group, key=lambda token: token[0])
        formatted_word_count = map(
            lambda x: f"{color_dic[CKW.SUMMARY]}{x[0]}"
            f"{format_delimeter}{x[1]}{color_dic[CKW.RESET_ALL]}",
            sorted_group
            )
        print('\n' + '\n'.join(formatted_word_count), end='')
    print(color_dic[CKW.RESET_ALL])


def _show_charcount() -> None:
    char_count = {}
    used_files = []

    for hfile in holder.files:
        try:
            with open(hfile.path, 'r', encoding=arg_parser.file_encoding) as file:
                for char in list(file.read()):
                    char_count[char] = char_count.get(char, 0)+1
            used_files.append(hfile.displayname)
        except (OSError, UnicodeError):
            pass

    print(color_dic[CKW.SUMMARY], end='')
    print('The char count includes the following files:', end='')
    print(color_dic[CKW.RESET_ALL], end='\n\t')
    print('\n\t'.join(map(
        lambda f: f"{color_dic[CKW.SUMMARY]}{f}{color_dic[CKW.RESET_ALL]}", used_files
        )))
    sorted_char_count = sorted(char_count.items(), key=lambda token: token[1], reverse=True)
    format_delimeter = f"{color_dic[CKW.RESET_ALL]}:{color_dic[CKW.SUMMARY]} "
    for _, group in groupby(sorted_char_count, lambda token: token[1]):
        sorted_group = sorted(group, key=lambda token: token[0])
        formatted_char_count = map(
            lambda x: f"{color_dic[CKW.SUMMARY]}{repr(x[0]) if x[0].isspace() else x[0]}"
            f"{format_delimeter}{x[1]}{color_dic[CKW.RESET_ALL]}",
            sorted_group
            )
        print('\n' + '\n'.join(formatted_char_count), end='')
    print(color_dic[CKW.RESET_ALL])


def _show_sum() -> None:
    """
    display the line sum of each file individually if
    ARGS_SSUM is specified.
    display the line sum of all files.
    """
    if holder.args_id[ARGS_SSUM]:
        longest_file_name = max(map(len, holder.all_files_lines.keys())) + 1
        print(f"{color_dic[CKW.SUMMARY]}{'File': <{longest_file_name}}{color_dic[CKW.RESET_ALL]}"
            f"{color_dic[CKW.SUMMARY]}LineCount{color_dic[CKW.RESET_ALL]}")
        for file, _ in holder.all_files_lines.items():
            print(f"{color_dic[CKW.SUMMARY]}{file: <{longest_file_name}}" + \
                f"{holder.all_files_lines[file]: >{holder.all_line_number_place_holder}}" + \
                    f"{color_dic[CKW.RESET_ALL]}")
        print('')
    print(f"{color_dic[CKW.SUMMARY]}Lines (Sum): " + \
        f"{holder.all_files_lines_sum}{color_dic[CKW.RESET_ALL]}")


def _show_files() -> None:
    """
    displays holder.files including their size and calculates
    their size sum.
    """
    if len(holder.files) == 0:
        return
    file_sizes = []
    msg = 'found' if holder.args_id[ARGS_FFILES] else 'applied'
    print(color_dic[CKW.SUMMARY], end='')
    print(f"{msg} FILE(s):", end='')
    print(color_dic[CKW.RESET_ALL])
    for file in holder.files:
        if file.file_size == -1:
            file.set_file_size(get_file_size(file.path))
        file_sizes.append(file.file_size)
        print(f"     {color_dic[CKW.SUMMARY]}" + \
            f"{str(_convert_size(file.file_size)).rjust(9)}", end='')
        prefix = ' ' if file.plaintext        else '-'
        prefix+= '*' if file.contains_queried else ' '
        print(f"{prefix}{file.displayname}{color_dic[CKW.RESET_ALL]}")
    print(color_dic[CKW.SUMMARY], end='')
    print(f"Sum: {str(_convert_size(sum(file_sizes))).rjust(9)}", end='')
    print(color_dic[CKW.RESET_ALL])
    print(color_dic[CKW.SUMMARY], end='')
    print(f"Amount:\t{len(holder.files)}", end='')
    print(color_dic[CKW.RESET_ALL])


def _show_dirs():
    known_directories = arg_parser.get_dirs()
    if len(known_directories) == 0:
        print(color_dic[CKW.SUMMARY], end='')
        print('No directores have been found!', end='')
        print(color_dic[CKW.RESET_ALL])
        return
    print(color_dic[CKW.SUMMARY], end='')
    print('found DIR(s):', end='')
    print(color_dic[CKW.RESET_ALL])
    for directory in known_directories:
        print(f"     {color_dic[CKW.SUMMARY]}" + \
            f"{directory}{color_dic[CKW.RESET_ALL]}")
    print(color_dic[CKW.SUMMARY], end='')
    print(f"Amount:\t{len(known_directories)}", end='')
    print(color_dic[CKW.RESET_ALL])


def _print_meta(file: str) -> None:
    """
    print the information retrieved by get_file_meta_data()
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    """
    meta_data = get_file_meta_data(file, on_windows_os,
                               [color_dic[CKW.RESET_ALL],
                               color_dic[CKW.ATTRIB],
                               color_dic[CKW.ATTRIB_POSITIVE],
                               color_dic[CKW.ATTRIB_NEGATIVE]])
    print(meta_data)


def _print_checksum(file: str) -> None:
    """
    print the information retrieved by get_checksum_from_file()
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    """
    print(f"{color_dic[CKW.CHECKSUM]}Checksum of '{file}':{color_dic[CKW.RESET_ALL]}")
    print(get_checksum_from_file(file, [color_dic[CKW.CHECKSUM], color_dic[CKW.RESET_ALL]]))


def _print_meta_and_checksum(show_meta: bool, show_checksum: bool) -> None:
    """
    calls _print_meta() and _print_checksum() on every file.
    
    Parameters:
    show_meta (bool):
        decides if the metadata of the files should be displayed
    show_checksum (bool):
        decides if the checksum of the files should be displayed
    """
    for file in holder.files:
        if show_meta:
            _print_meta(file.path)
        if show_checksum:
            _print_checksum(file.path)

@lru_cache(maxsize=250)
def remove_ansi_codes_from_line(line: str) -> str:
    """
    Parameters:
    line (str):
        the string to clean ANSI-Colorcodes from
        
    Returns:
    (str):
        the cleaned string
    """
    # version 1: efficiency is about the same, and does not have any dependency
    # however it is not as safe in case of unusual/broken escape sequences.
    # while (codePosStart := line.find(ESC_CODE)) != -1:
    #     codePosEnd = line[codePosStart:].find('m')
    #     # here should be checks like 'codePosEnd' != -1 and
    #     # 'codePosEnd' <= 5 to make sure we found a valid EscapeSequence
    #     # for a better performance let's assume all EscapeSequences are valid...
    #     line = line[:codePosStart] + line[codePosStart+codePosEnd+1:]
    # return line
    # version 2:
    return ANSI_CSI_RE.sub('', line)


# def removeAnsiCodes(content: list) -> list:
#     return [(remove_ansi_codes_from_line(prefix),
#                   remove_ansi_codes_from_line(line)) for prefix, line in content]


@lru_cache()
def _calculate_line_prefix_spacing(line_char_length: int, file_name_prefix: bool = False,
                                   include_file_prefix: bool = False,
                                   file_char_length: int = 0) -> str:
    """
    calculate a string template for the line prefix.
    
    Parameters:
    line_char_length (int):
        the length of the line number
    file_name_prefix (bool):
        will the full file path be included in the prefix
    include_file_prefix (bool):
        should the file be included in the prefix
    file_char_length (int):
        the length of the file number
    
    Returns:
    (str):
        a non-finished but correctly formatted string template to insert line number
        and file index into
    """
    line_prefix = ' ' * (holder.all_line_number_place_holder - line_char_length)

    if file_name_prefix:
        line_prefix = '%i' + line_prefix
    else:
        line_prefix += '%i)'

    if include_file_prefix and not file_name_prefix:
        file_prefix = (' ' * (holder.file_number_place_holder - file_char_length)) + '%i.'
        return color_dic[CKW.NUMBER] + file_prefix + line_prefix + color_dic[CKW.RESET_ALL] + ' '

    return color_dic[CKW.NUMBER] + line_prefix + color_dic[CKW.RESET_ALL] + ' '


def _get_line_prefix(line_num: int, index: int) -> str:
    """
    calculates the line prefix in regard to the line number and file count.
    
    Parameters:
    line_num (int):
        the current number identifying the line
    index (int):
        the current number identifying the file
    
    Returns:
    (str):
        the new line prefix including the line number.
    """
    if holder.args_id[ARGS_FILE_PREFIX]:
        return _calculate_line_prefix_spacing(len(str(line_num)), True) % (line_num)
    if len(holder.files) > 1:
        return _calculate_line_prefix_spacing(len(str(line_num)), False, True,
                                              len(str(index))) % (index, line_num)
    return _calculate_line_prefix_spacing(len(str(line_num))) % (line_num)


@lru_cache()
def _calculate_line_length_prefix_spacing(line_char_length: int) -> str:
    """
    calculate a string template for the line prefix.
    
    Parameters:
    line_char_length (int):
        the length of the line
    
    Returns:
    (str):
        a non-finished but correctly formatted string template to insert line length into
    """
    length_prefix = '[' + ' ' * (holder.file_line_length_place_holder - line_char_length) + '%i]'
    return '%s' + color_dic[CKW.LINE_LENGTH] + length_prefix + color_dic[CKW.RESET_ALL] + ' '


def _get_line_length_prefix(prefix: str, line) -> str:
    """
    calculates the line prefix in regard to the line length.
    
    Parameters:
    prefix (str):
        the current prefix to append to
    line (str|byte):
        a representation of the current line
    
    Returns:
    (str):
        the new line prefix including the line length.
    """
    if not holder.args_id[ARGS_NOCOL] and isinstance(line, str):
        line = remove_ansi_codes_from_line(line)
    return _calculate_line_length_prefix_spacing(len(str(len(line)))) % (prefix, len(line))


def _get_file_prefix(prefix: str, file_index: int, hyper: bool = False) -> str:
    """
    append the file to the line prefix.
    
    Parameters:
    prefix (str):
        the current prefix to append to
    file_index (int):
        the index of the current file
    hyper (bool):
        if True the filename will include the file-protocol prefix.
        (this will make the file a link, which are clickable in some terminals)
    
    Returns:
    (str):
        the new line prefix including the file.
    """
    if file_index < 0:
        return prefix
    file = file_uri_prefix * hyper + holder.files[file_index].displayname
    if hyper:
        file = file.replace('\\', '/')
    if not holder.args_id[ARGS_NUMBER] or hyper:
        return f"{prefix}{color_dic[CKW.FILE_PREFIX]}{file}{color_dic[CKW.RESET_ALL]} "
    return f"{color_dic[CKW.FILE_PREFIX]}{file}{color_dic[CKW.RESET_ALL]}:{prefix}"


def print_file(content: list) -> bool:
    """
    print a file and possibly include the substrings and patterns to search for.
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
        
    Returns:
    (bool):
        identifies if the given content parameter contained any
        queried keyword/pattern.
    """
    if not content:
        return False
    if not any([arg_parser.file_search, arg_parser.file_match,
                holder.args_id[ARGS_GREP], holder.args_id[ARGS_GREP_ONLY]]):
        print(*[prefix + line for prefix, line in content], sep='\n')
        return False

    contains_queried = False
    string_finder = StringFinder(arg_parser.file_search,
                                 arg_parser.file_match,
                                 arg_parser.file_search_ignore_case,
                                 arg_parser.file_match_ignore_case)

    for line_prefix, line in content:
        cleaned_line = remove_ansi_codes_from_line(line)
        intervals, f_keywords, m_keywords = string_finder.find_keywords(cleaned_line)

        # used for marking the file when displaying applied files
        contains_queried |= bool(intervals)

        # this has priority over the other arguments
        if holder.args_id[ARGS_GREP_ONLY]:
            if intervals:
                fm_substrings = [(pos[0], f"{color_dic[CKW.FOUND]}" + \
                    f"{line[pos[0]:pos[1]]}{color_dic[CKW.RESET_FOUND]}") 
                                 for _, pos in f_keywords]
                fm_substrings+= [(pos[0], f"{color_dic[CKW.MATCHED]}" + \
                    f"{line[pos[0]:pos[1]]}{color_dic[CKW.RESET_MATCHED]}")
                                 for _, pos in m_keywords]
                fm_substrings.sort(key=lambda x:x[0])
                print(f"{line_prefix}{','.join(sub for _, sub in fm_substrings)}")
            continue

        # when bool(intervals) == True -> found keyword or matched pattern!
        # intervals | grep | nokeyword -> print?
        #     0     |  0   |     0     ->   1
        #     0     |  0   |     1     ->   1
        #     0     |  1   |     0     ->   0
        #     0     |  1   |     1     ->   0
        #     1     |  0   |     0     ->   1
        #     1     |  0   |     1     ->   0
        #     1     |  1   |     0     ->   1
        #     1     |  1   |     1     ->   0
        if not intervals:
            if not holder.args_id[ARGS_GREP]:
                print(line_prefix + line)
            continue

        if holder.args_id[ARGS_NOKEYWORD]:
            continue

        if not holder.args_id[ARGS_NOCOL]:
            for kw_pos, kw_code in intervals:
                cleaned_line = cleaned_line[:kw_pos] + color_dic[kw_code] + cleaned_line[kw_pos:]

        print(line_prefix + cleaned_line)

        if holder.args_id[ARGS_GREP] or holder.args_id[ARGS_NOBREAK]:
            continue

        found_sth = False
        if f_keywords:
            print(color_dic[CKW.FOUND_MESSAGE], end='')
            print('--------------- Found', f_keywords, '---------------', end='')
            print(color_dic[CKW.RESET_ALL])
            found_sth = True
        if m_keywords:
            print(color_dic[CKW.MATCHED_MESSAGE], end='')
            print('--------------- Matched', m_keywords, '---------------', end='')
            print(color_dic[CKW.RESET_ALL])
            found_sth = True

        if found_sth:
            try:
                # fails when using --stdin mode, because the stdin will send en EOF char
                # to input without prompting the user
                input()
            except (EOFError, UnicodeDecodeError):
                pass

    return contains_queried


def _print_excluded_by_peek(prefix_len: int, excluded_by_peek: int) -> None:
    """
    print a paragraph about how many lines have been excluded.
    
    Parameters:
    prefix_len (int):
        the approximate length of the prefix
    excluded_by_peek (int):
        the amount of lines that have been excluded
    """
    excluded_by_peek_length = (len(str(excluded_by_peek))-1)//2
    excluded_by_peek_indent = ' ' * (prefix_len - excluded_by_peek_length + 10)
    excluded_by_peek_indent_add = ' ' * excluded_by_peek_length
    excluded_by_peek_parting = f"{excluded_by_peek_indent}{excluded_by_peek_indent_add} "
    excluded_by_peek_parting+= f"{color_dic[CKW.NUMBER]}:{color_dic[CKW.RESET_ALL]}"
    print(excluded_by_peek_parting)
    print(f"{excluded_by_peek_indent}{color_dic[CKW.NUMBER]}", end='')
    print(f"({excluded_by_peek}){color_dic[CKW.RESET_ALL]}")
    print(excluded_by_peek_parting)

def print_excluded_by_peek(content: list, excluded_by_peek: int) -> None:
    """
    print a paragraph about how many lines have been excluded,
    using the method _print_excluded_by_peek().
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    excluded_by_peek (int):
        the amount of lines that have been originally excluded
    """
    if not excluded_by_peek or len(content) <= 5:
        return
    if any([holder.args_id[ARGS_GREP],
            holder.args_id[ARGS_GREP_ONLY],
            holder.args_id[ARGS_NOKEYWORD]]):
        return
    _print_excluded_by_peek(len(remove_ansi_codes_from_line(content[0][0])),
                            excluded_by_peek + 10 - len(content))


def edit_content(content: list, show_bytecode: bool, file_index: int = 0,
                 line_offset: int = 0) -> None:
    """
    apply all parameters to a string (file Content).
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    show_bytecode (bool).
        indicates if the content lines are string or bytes
    file_index (int):
        the index of the holder.files list, pointing to the file that
        is currently being processed. a negative value can be used for
        the shell mode
    line_offset (int):
        the offset for counting the line numbers (used in the shell)
    """
    if holder.args_id[ARGS_STRINGS]:
        content = get_strings(content,
                              const_dic[DKW.STRINGS_MIN_SEQUENCE_LENGTH],
                              const_dic[DKW.STRINGS_DELIMETER])
    elif show_bytecode:
        if const_dic[DKW.BINARY_HEX_VIEW]:
            content = [(prefix, repr(line)[2:-1]) for prefix, line in content]
        else:
            content = [(prefix, ''.join(map(chr, line))) for prefix, line in content] 

    if holder.args_id[ARGS_SPECIFIC_FORMATS]:
        content = Formatter.format(content)

    if not (content or os.isatty(sys.stdout.fileno()) or file_index < 0):
        # if the content of the file is empty, we check if maybe the file is its own pipe-target.
        # an indicator would be if the file has just been modified to be empty (by the shell).
        # also the stdout cannot be atty.
        # checking if the file is an _unknown_file is not valid, because by using '--stdin'
        # the stdin will be used to write the file
        file_mtime = get_file_mtime(holder.files[file_index].path)
        date_nowtime = datetime.timestamp(datetime.now())
        if abs(date_nowtime - file_mtime) < 0.5:
            err_print(f"{color_dic[CKW.MESSAGE_WARNING]}Warning: It looks like you are " + \
                f"trying to pipe a file into itself.{color_dic[CKW.RESET_ALL]}")
            err_print(f"{color_dic[CKW.MESSAGE_WARNING]}In this case you might have lost " + \
                f"all data.{color_dic[CKW.RESET_ALL]}")
        # in any case we have nothing to do and can return
        return
    excluded_by_peek = 0

    if not show_bytecode and holder.args_id[ARGS_B64D]:
        content = decode_base64(content, arg_parser.file_encoding)

    if holder.args_id[ARGS_NUMBER]:
        content = [(_get_line_prefix(j+line_offset, file_index+1), c[1])
                   for j, c in enumerate(content, start=1)]
    content = content[
        arg_parser.file_truncate[0]:arg_parser.file_truncate[1]:arg_parser.file_truncate[2]
        ]
    if holder.args_id[ARGS_PEEK] and len(content) > 10:
        excluded_by_peek = len(content) - 10
        content = content[:5] + content[-5:]

    if not show_bytecode:
        for arg, param in holder.args:
            if arg == ARGS_CUT:
                slice_evals = [None, None, None]
                for i, p_split in enumerate(param[1:-1].split(':')):
                    try:
                        slice_evals[i] = int(eval(p_split))
                    except (SyntaxError, NameError, ValueError, ArithmeticError):
                        pass
                content = [(prefix, line[slice_evals[0]:slice_evals[1]:slice_evals[2]])
                            for prefix, line in content]

        for arg, param in holder.args:
            if arg == ARGS_ENDS:
                content = [(prefix, f"{line}{color_dic[CKW.ENDS]}${color_dic[CKW.RESET_ALL]}")
                           for prefix, line in content]
            elif arg == ARGS_SQUEEZE:
                content = [list(group)[0] for _, group in groupby(content, lambda x: x[1])]
            elif arg == ARGS_REVERSE:
                content.reverse()
            elif arg == ARGS_SORT:
                sort_method = len if param.isupper() else str.casefold
                content.sort(key = lambda l: sort_method(l[1]))
            elif arg == ARGS_BLANK:
                content = [c for c in content if c[1]]
            elif arg == ARGS_EVAL:
                content = comp_eval(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_HEX:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_DEC:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_OCT:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_BIN:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_REPLACE:
                replace_values = split_replace(param)
                content = [(prefix, line.replace(replace_values[0], f"{color_dic[CKW.REPLACE]}" + \
                    f"{replace_values[1]}{color_dic[CKW.RESET_ALL]}"))
                           for prefix, line in content]
            elif arg == ARGS_CHR:
                for c_id, char, _, possible in SPECIAL_CHARS:
                    if not possible:
                        continue
                    content = [(prefix, line.replace(
                        chr(c_id), f"{color_dic[CKW.CHARS]}^{char}{color_dic[CKW.RESET_ALL]}"
                        )) for prefix, line in content]

    if holder.args_id[ARGS_LLENGTH]:
        content = [(_get_line_length_prefix(prefix, line), line) for prefix, line in content]
    if holder.args_id[ARGS_FILE_PREFIX]:
        content = [(_get_file_prefix(prefix, file_index), line) for prefix, line in content]
    elif holder.args_id[ARGS_FFILE_PREFIX]:
        content = [(_get_file_prefix(prefix, file_index, hyper=True), line)
                   for prefix, line in content]
    if holder.args_id[ARGS_B64E]:
        content = encode_base64(content, arg_parser.file_encoding)

    found_queried = print_file(content[:len(content)//2])
    if file_index >= 0:
        holder.files[file_index].set_contains_queried(found_queried)
    print_excluded_by_peek(content, excluded_by_peek)
    found_queried = print_file(content[len(content)//2:])
    if file_index >= 0:
        holder.files[file_index].set_contains_queried(found_queried)

    if not show_bytecode:
        if holder.args_id[ARGS_CLIP]:
            holder.clip_board += '\n'.join(prefix + line for prefix, line in content)


def edit_file(file_index: int = 0) -> None:
    """
    apply all parameters to a file.
    
    Parameters:
    file_index (int):
        the index regarding which file is currently being edited
    """
    show_bytecode = False

    content = [('', '')]
    try:
        with open(holder.files[file_index].path, 'r', encoding=arg_parser.file_encoding) as file:
            # splitlines() gives a slight inaccuracy, in case the last line is empty.
            # the alternative would be worse: split('\n') would increase the linecount each
            # time catw touches a file.
            file_content = file.read()
            if not os.isatty(sys.stdout.fileno()) and const_dic[DKW.STRIP_COLOR_ON_PIPE]:
                file_content = remove_ansi_codes_from_line(file_content)
            content = [('', line) for line in file_content.splitlines()]
    except PermissionError:
        err_print(f"Permission denied! Skipping {holder.files[file_index].displayname} ...")
        return
    except (BlockingIOError, FileNotFoundError):
        err_print('Resource blocked/unavailable! Skipping ' + \
            f"{holder.files[file_index].displayname} ...")
        return
    except (OSError, UnicodeError) as exc:
        holder.files[file_index].set_plaintext(plain=False)
        if holder.args_id[ARGS_PLAIN_ONLY]:
            return
        if display_zip(holder.files[file_index].path, _convert_size):
            return
        if not holder.args_id[ARGS_STRINGS]:
            err_print('Failed to open:', holder.files[file_index].displayname)
            try:
                enter_char = '⏎'
                try:
                    # on e.g. utf-16 the encoded form would be 4 bytes and also
                    # raise an exception event, so the char could be displayed.
                    # but the stdout and terminal would need to be configured
                    # correctly ...
                    if len(enter_char.encode(arg_parser.file_encoding)) != 3:
                        raise UnicodeEncodeError('', '', -1, -1, '') from exc
                except UnicodeEncodeError:
                    enter_char = 'ENTER'
                err_print('Do you want to open the file as a binary, without parameters?')
                err_print(f"[Y/{enter_char}] Yes, Continue       [N] No, Abort :", end='')
                inp = 'Y' if holder.args_id[ARGS_NOBREAK] else input()
                if not (os.isatty(sys.stdin.fileno()) and os.isatty(sys.stdout.fileno()) and \
                    not holder.args_id[ARGS_NOBREAK]):
                    err_print('') # if the input or output is piped, we add a newline manually
                if inp and inp.upper() != 'Y':
                    err_print('Aborting...')
                    return
            except EOFError:
                # on eoferror it is safe to assume that the user did not press
                # enter, therefor we print a new line
                err_print('')
            except UnicodeError:
                err_print('')
                err_print('Input is not recognized in the given encoding: '
                          f"{arg_parser.file_encoding}")
                err_print('Aborting...')
                return
        try:
            with open(holder.files[file_index].path, 'rb') as raw_f:
                # in binary splitlines() is our only option
                content = [('', line) for line in raw_f.read().splitlines()]
            show_bytecode = True
        except OSError:
            err_print('Operation failed! Try using the enc=X parameter.')
            return

    edit_content(content, show_bytecode, file_index)


def _copy_to_clipboard(content: str, __dependency: int = 3,
                       __clip_board_error: bool = False) -> object:
    """
    copy a string to the clipboard, by recursively checking which module exists and could
    be used, this function should only be called by copy_to_clipboard()
    
    Parameters:
    content (str):
        the string to copy
    __dependency (int):
        do not change!
    __clip_board_error (bool):
        do not change!
        
    Returns:
    (function):
        the method used for copying to the clipboard
        (in case we want to use this function again without another import)
    """
    if __dependency == 0:
        if __clip_board_error:
            error_msg = '\n'
            error_msg += "ClipBoardError: You can use either 'pyperclip3', "
            error_msg += "'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
            error_msg += 'Try to install a different one using '
            error_msg += f"'{os.path.basename(sys.executable)} -m pip install ...'"
        else:
            error_msg = '\n'
            error_msg += "ImportError: You need either 'pyperclip3', 'pyperclip',"
            error_msg += "or 'pyclip' in order to use the '--clip' parameter.\n"
            error_msg += 'Should you have any problem with either module, try to install a diff'
            error_msg += f"erent one using '{os.path.basename(sys.executable)} -m pip install ...'"
        err_print(error_msg)
        return None
    try:
        if __dependency == 3:
            import pyperclip as pc
        elif __dependency == 2:
            import pyclip as pc
        elif __dependency == 1:
            import pyperclip3 as pc
        pc.copy(content)
        return pc.copy
    except ImportError:
        return _copy_to_clipboard(content, __dependency-1, False or __clip_board_error)
    except Exception:
        return _copy_to_clipboard(content, __dependency-1, True or __clip_board_error)


def copy_to_clipboard(content: str, copy_function: object = None) -> object:
    """
    entry point to recursive function _copy_to_clipboard()
    
    Parameters:
    content (str):
        the string to copy
    copy_function (function):
        the method to use for copying to the clipboard
        (in case such a method already exists we do not need to import any module (again))
        
    Returns:
    (function):
        the method used for copying to the clipboard
        (in case we want to use this function again without another import)
    """
    if copy_function is not None:
        copy_function(content)
        return copy_function
    return _copy_to_clipboard(content)


def print_raw_view(file_index: int = 0, mode: str = 'X') -> None:
    """
    print the raw byte representation of a file in hexadecimal or binary
    
    Parameters:
    file_index (int):
        the index regarding which file is currently being edited
    mode (str):
        either 'x', 'X' for hexadecimal (lower- or upper case letters),
        or 'b' for binary
    """
    queue = []
    skipped = -1

    print(holder.files[file_index].displayname, ':', sep='')
    raw_gen = get_raw_view_lines_gen(holder.files[file_index].path, mode,
                                     [color_dic[CKW.RAWVIEWER], color_dic[CKW.RESET_ALL]],
                                     arg_parser.file_encoding)
    print(next(raw_gen)) # the header will always be available
    for line in raw_gen:
        skipped += 1
        if holder.args_id[ARGS_PEEK] and skipped > 4:
            queue.append(line)
            if len(queue) > 5:
                queue = queue[1:]
            continue
        print(line)
    if queue:
        if skipped > 9:
            _print_excluded_by_peek(21, skipped-9)
        print('\n'.join(queue))
    print('')


def edit_files() -> None:
    """
    manage the calls to edit_file() for each file.
    """
    start = len(holder.files)-1 if holder.reversed else 0
    end = -1 if holder.reversed else len(holder.files)

    raw_view_mode = None
    if holder.args_id[ARGS_HEXVIEW] or holder.args_id[ARGS_BINVIEW]:
        for arg, param in holder.args:
            if arg == ARGS_HEXVIEW:
                raw_view_mode = 'X' if param.isupper() else 'x'
                break
            if arg == ARGS_BINVIEW:
                raw_view_mode = 'b'
                break

    for i in range(start, end, -1 if holder.reversed else 1):
        if raw_view_mode:
            print_raw_view(i, raw_view_mode)
        else:
            edit_file(i)
    if holder.args_id[ARGS_WORDCOUNT]:
        print('')
        _show_wordcount()
    if holder.args_id[ARGS_CHARCOUNT]:
        print('')
        _show_charcount()
    if holder.args_id[ARGS_SUM]:
        print('')
        _show_sum()
    if holder.args_id[ARGS_FILES]:
        print('')
        _show_files()
    if holder.args_id[ARGS_DIRECTORIES]:
        print('')
        _show_dirs()
    if holder.args_id[ARGS_CLIP]:
        copy_to_clipboard(remove_ansi_codes_from_line(holder.clip_board))


def show_unknown_args_suggestions(shell: bool = False) -> list:
    """
    display the unknown arguments passed in aswell as their suggestions
    if possible
    
    Parameters:
    shell (bool):
        indicates whether or not the shell has been used
        
    Returns:
    arg_suggestions (list):
        the list generated by check_unknown_args()
    """
    arg_suggestions = arg_parser.check_unknown_args(shell)
    for u_arg, arg_replacement in arg_suggestions:
        err_print(f"{color_dic[CKW.MESSAGE_IMPORTANT]}Unknown argument: " + \
            f"'{u_arg}'{color_dic[CKW.RESET_ALL]}")
        if arg_replacement:
            arg_replacement = [arg_r[0] for arg_r in arg_replacement]
            err_print(f"\t{color_dic[CKW.MESSAGE_IMPORTANT]}Did you mean " + \
                f"{' or '.join(arg_replacement)}{color_dic[CKW.RESET_ALL]}")
    return arg_suggestions


def init_colors() -> None:
    """
    set the color dictionary to be used. either empty for no colors
    or the default color dictionary.
    """
    # do not use colors if requested, or output will be piped anyways
    global color_dic

    if holder.args_id[ARGS_NOCOL] or sys.stdout.closed or \
        (not os.isatty(sys.stdout.fileno()) and const_dic[DKW.STRIP_COLOR_ON_PIPE]):
        color_dic = dict.fromkeys(color_dic, '')
    else:
        color_dic = default_color_dic.copy()

    converter.set_params(holder.args_id[ARGS_DEBUG],
                         [color_dic[CKW.EVALUATION],
                          color_dic[CKW.CONVERSION],
                          color_dic[CKW.RESET_ALL]])


def init(shell: bool = False) -> tuple:
    """
    initiate the code by calling the argparser and handling the default
    parameters: -h, -v, -d, --config.
    
    Parameters:
    shell (bool):
        indicates if the shell entry point was used, and the stdin will therefor
        be used by default
        
    Returns:
    (tuple):
        contains (known_files, unknown_files, echo_args, valid_urls) from the argparser
    """
    # read parameter-args
    args, _, unknown_files, echo_args = arg_parser.get_arguments(sys.argv + config.get_cmd())

    holder.set_args(args)

    known_files = arg_parser.get_files(holder.args_id[ARGS_DOTFILES])
    valid_urls = []
    if holder.args_id[ARGS_URI]:
        valid_urls, unknown_files = sep_valid_urls(unknown_files)

    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_IN]:
        sys.stdin.reconfigure(encoding=arg_parser.file_encoding)
    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_OUT]:
        sys.stdout.reconfigure(encoding=arg_parser.file_encoding)
    if holder.args_id[ARGS_RECONFIGURE_ERR]:
        sys.stderr.reconfigure(encoding=arg_parser.file_encoding)

    init_colors()

    arg_suggestions = show_unknown_args_suggestions(shell)

    # check for special cases
    if holder.args_id[ARGS_DEBUG]:
        _show_debug(holder.args, arg_suggestions, known_files, unknown_files, echo_args, valid_urls)
    if (len(known_files) + len(unknown_files) + len(holder.args) == 0 and not shell) or \
        holder.args_id[ARGS_HELP]:
        _show_help(shell)
        sys.exit(0)
    if holder.args_id[ARGS_VERSION]:
        _show_version()
        sys.exit(0)
    if holder.args_id[ARGS_CCONFIG]:
        cconfig.save_config()
        sys.exit(0)
    if holder.args_id[ARGS_CONFIG]:
        config.save_config()
        sys.exit(0)

    if holder.args_id[ARGS_ECHO]:
        echo_args = ' '.join(echo_args)
        for arg, param in holder.args:
            if arg == ARGS_ECHO:
                if param.isupper():
                    echo_args = echo_args.encode(arg_parser.file_encoding).decode('unicode_escape')
                break

    Editor.set_indentation(const_dic[DKW.EDITOR_INDENTATION], const_dic[DKW.EDITOR_AUTO_INDENT])
    Editor.set_flags(holder.args_id[ARGS_STDIN] and on_windows_os, holder.args_id[ARGS_DEBUG])

    return (known_files, unknown_files, echo_args, valid_urls)


def main():
    """
    main function
    """
    piped_input = temp_file = ''
    known_files, unknown_files, echo_args, valid_urls = init(shell=False)

    if holder.args_id[ARGS_ECHO]:
        temp_file = stdinhelper.write_file(echo_args, tmp_file_helper.generate_temp_file_name(),
                                           arg_parser.file_encoding)
        known_files.append(temp_file)
        holder.set_temp_file_echo(temp_file)
    if holder.args_id[ARGS_URI]:
        # the dictionary should contain an entry for each valid_url, since
        # generated temp-files are unique
        temp_files = dict([
            (stdinhelper.write_file(read_url(valid_url), tmp_file_helper.generate_temp_file_name(),
                                    arg_parser.file_encoding), valid_url)
            for valid_url in valid_urls])
        known_files.extend(list(temp_files.keys()))
        holder.set_temp_files_url(temp_files)
    if holder.args_id[ARGS_STDIN]:
        piped_input = ''.join(stdinhelper.get_stdin_content(holder.args_id[ARGS_ONELINE]))
        temp_file = stdinhelper.write_file(piped_input, tmp_file_helper.generate_temp_file_name(),
                                           arg_parser.file_encoding)
        known_files.append(temp_file)
        unknown_files = stdinhelper.write_files(unknown_files, piped_input,
                                                arg_parser.file_encoding)
        holder.set_temp_file_stdin(temp_file)
    elif holder.args_id[ARGS_EDITOR]:
        unknown_files = [file for file in unknown_files if Editor.open(
            file, holder.get_file_display_name(file), arg_parser.file_encoding,
            stdinhelper.write_file, on_windows_os, holder.args_id[ARGS_PLAIN_ONLY])]
    else:
        unknown_files = stdinhelper.read_write_files_from_stdin(
            unknown_files, arg_parser.file_encoding, on_windows_os,
            holder.args_id[ARGS_ONELINE])

    if holder.args_id[ARGS_EDITOR]:
        stdin_backup = os.dup(sys.stdin.fileno())
        if holder.args_id[ARGS_STDIN]:
            tty = os.open('CONIN$' if on_windows_os else '/dev/tty', os.O_RDONLY)
            os.dup2(tty, sys.stdin.fileno())
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') and on_windows_os:
                # for pyinstaller:
                import ctypes
# stdin, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
# None security, OPEN_EXISTING, 0 flags, None template
                conin_handle = ctypes.windll.kernel32.CreateFileW(
                    "CONIN$", 0x80000000, 3, None, 3, 0, None
                    ) # os.dup2 does not work on pyinstaller
                ctypes.windll.kernel32.SetStdHandle(-10, conin_handle) # -10 = stdin
        for file in known_files:
            Editor.open(file, holder.get_file_display_name(file), arg_parser.file_encoding,
                        stdinhelper.write_file, on_windows_os, holder.args_id[ARGS_PLAIN_ONLY])
        os.dup2(stdin_backup, sys.stdin.fileno())

    if len(known_files) + len(unknown_files) == 0:
        return

    # fill holder object with neccessary values
    holder.set_files([*known_files, *unknown_files])

    if holder.args_id[ARGS_FFILES]:
        _show_files()
        return
    if holder.args_id[ARGS_DDIRECTORIES]:
        _show_dirs()
        return
    if holder.args_id[ARGS_DATA] or holder.args_id[ARGS_CHECKSUM]:
        _print_meta_and_checksum(holder.args_id[ARGS_DATA], holder.args_id[ARGS_CHECKSUM])
        return

    file_size_sum = 0
    for file in holder.files:
        file.set_file_size(get_file_size(file.path))
        file_size_sum += file.file_size
        if file_size_sum >= const_dic[DKW.LARGE_FILE_SIZE]:
            err_print(color_dic[CKW.MESSAGE_IMPORTANT], end='')
            err_print('An exceedingly large amount of data is being loaded. ', end='')
            err_print('This may require a lot of time and resources.', end='')
            err_print(color_dic[CKW.RESET_ALL])
            break

    if holder.args_id[ARGS_B64D]:
        holder.set_decoding_temp_files(
            [tmp_file_helper.generate_temp_file_name() for _ in holder.files])
    holder.generate_values(arg_parser.file_encoding)

    if holder.args_id[ARGS_SSUM]:
        _show_sum()
        return
    if holder.args_id[ARGS_WWORDCOUNT]:
        _show_wordcount()
        return
    if holder.args_id[ARGS_CCHARCOUNT]:
        _show_charcount()
        return

    edit_files()  # print the cat-output

    # clean-up
    if holder.args_id[ARGS_DEBUG]:
        err_print('================================================ ' + \
            'DEBUG ================================================')
        caches = [
            remove_ansi_codes_from_line,
            _calculate_line_prefix_spacing,
            _calculate_line_length_prefix_spacing,
            holder.__get_file_lines_sum__,
            holder.__calc_max_line_length__,
            ]
        caches_info = [(cache.__name__,
                        str(cache.cache_info().hits),
                        str(cache.cache_info().misses),
                        str(cache.cache_info().maxsize),
                        str(cache.cache_info().currsize)) for cache in caches]
        max_val = [max(len(_c) for _c in c_info)+1 for c_info in zip(*caches_info)]
        for name, hits, misses, maxsize, currsize in caches_info:
            cache_info = f"def:{name.ljust(max_val[0])}"
            cache_info+= f"hits:{hits.ljust(max_val[1])}"
            cache_info+= f"misses:{misses.ljust(max_val[2])}"
            cache_info+= f"maxsize:{maxsize.ljust(max_val[3])}"
            cache_info+= f"currsize:{currsize.ljust(max_val[4])}"
            cache_info+= f"full:{100*int(currsize)/int(maxsize):6.2f}%"
            err_print(cache_info)
    for tmp_file in tmp_file_helper.get_generated_temp_files():
        if holder.args_id[ARGS_DEBUG]:
            err_print('Cleaning', tmp_file)
        try:
            os.remove(tmp_file)
        except (FileNotFoundError, PermissionError, OSError) as e:
            if holder.args_id[ARGS_DEBUG]:
                err_print(type(e).__name__, tmp_file)
    if holder.args_id[ARGS_DEBUG]:
        err_print('===================================================' + \
            '====================================================')


def shell_main():
    """
    run the shell.
    """
    init(True)

    command_prefix = '!'
    shell_prefix = '>>> '
    eof_control_char = 'Z' if on_windows_os else 'D'
    oneline = holder.args_id[ARGS_ONELINE]
    shell_session_time_start = monotonic()

    class CmdExec:
        """
        handle shell commands.
        """
        def __init__(self) -> None:
            self.exit_shell = False
            self.last_cmd = ''

        def exec_colors(self) -> None:
            """
            reset the colors cache and init colors.
            """
            init_colors()
            _calculate_line_prefix_spacing.cache_clear()
            _calculate_line_length_prefix_spacing.cache_clear()

        def exec(self, cmd: str) -> bool:
            """
            check if a shell line is an executable command,
            executes it if it is.
            
            Parameters:
            cmd (str):
                the line entered in the cat shell
                
            Returns:
            (bool):
                indicates if a valid command has been found
                and executed
            """
            if cmd[:1] != command_prefix:
                return False
            line_split = cmd[1:].split(' ')
            self.last_cmd = line_split[0]
            method = getattr(self, '_command_' + self.last_cmd, self._command_unknown)
            method(line_split[1:])
            return True

        def _command_unknown(self, _) -> None:
            print("Command '!", self.last_cmd, "' is unknown.", sep='')
            print("If you want to escape the command input, type: '\\!",
                  self.last_cmd, "'.", sep='')

        def _command_cat(self, _) -> None:
            shell_session_time = monotonic()-shell_session_time_start
            hrs, mins, secs = (int(shell_session_time/3600),
                               int(shell_session_time%3600/60),
                               int(shell_session_time%60))
            cat = " ,_     _\n |\\\\_,-~/\n / _  _ |    ,--.\n(  @  @ )   / ,-'\n \\  _T_/"
            cat += "-._( (\n /         `. \\\n|         _  \\ |\n \\ \\ ,  /      |\n  || "
            cat += f"|-_\\__   /\n ((_/`(____,-' Session time: {hrs:02d}:{mins:02d}:{secs:02d}s\a\n"
            print('\n'.join('\t\t\t' + c for c in cat.split('\n')))

        def _command_help(self, _) -> None:
            print(f"Type ^{eof_control_char} (Ctrl + {eof_control_char}) or '!exit' to exit.")
            print("Type '!add <OPTION>', '!del <OPTION>' to add/remove a specific parameter.")
            print("Type '!see', '!clear' to see/remove all active parameters.")
            print("Put a '\\' before a leading '!' to escape the command-input.")

        def _command_add(self, cmd: list) -> None:
            arg_parser.gen_arguments([''] + cmd)
            holder.add_args(arg_parser.get_args())
            show_unknown_args_suggestions(shell=True)
            self.exec_colors()
            _added= [arg for _, arg in arg_parser.get_args()] \
                if arg_parser.get_args() else 'parameter(s)'
            print(f"successfully added {_added}.")

        def _command_del(self, cmd: list) -> None:
            arg_parser.gen_arguments([''] + cmd, True)
            holder.delete_args(arg_parser.get_args())
            self.exec_colors()
            _removed = [arg for _, arg in arg_parser.get_args()] \
                if arg_parser.get_args() else 'parameter(s)'
            print(f"successfully removed {_removed}.")

        def _command_clear(self, _) -> None:
            arg_parser.reset_values()
            self._command_del([arg for _, arg in holder.args])

        def _command_see(self, _) -> None:
            print(f"{'Active Args:': <12} {[arg for _, arg in holder.args]}")
            if arg_parser.file_search:
                print(f"{'Literals:':<12} {arg_parser.file_search}")
            if arg_parser.file_match:
                print(f"{'Matches:': <12} {arg_parser.file_match}")

        def _command_exit(self, _) -> None:
            self.exit_shell = True


    cmd = CmdExec()
    command_count = 0
    copy_function = None

    print(__project__, 'v' + __version__, 'shell', '(' + __url__ + ')', end=' - ')
    print("Use 'catw' to handle files.")
    print("Type '!help' for more information.")

    print(shell_prefix, end='', flush=True)
    for i, line in enumerate(stdinhelper.get_stdin_content(oneline)):
        stripped_line = line.rstrip('\n')
        if cmd.exec(stripped_line):
            command_count += 1
            if cmd.exit_shell:
                break
        else:
            stripped_line = stripped_line[:1].replace('\\', '') + stripped_line[1:]
            if stripped_line:
                edit_content([('', stripped_line)], False, -1, i-command_count)
                if holder.args_id[ARGS_CLIP]:
                    copy_function = copy_to_clipboard(
                        remove_ansi_codes_from_line(holder.clip_board), copy_function)
                    holder.clip_board = ''
        if not oneline:
            print(shell_prefix, end='', flush=True)


if __name__ == '__main__':
    main()
