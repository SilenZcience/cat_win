try:
    from colorama import init as coloramaInit
except ImportError:
    nop = lambda *_, **__: None; coloramaInit = nop
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from platform import system
from re import sub as resub
import os
import sys

from cat_win.const.argconstants import *
from cat_win.const.colorconstants import CKW
from cat_win.persistence.config import Config
from cat_win.util.argparser import ArgParser
from cat_win.util.cbase64 import decode_base64, encode_base64
from cat_win.util.checksum import get_checksum_from_file
from cat_win.util.converter import Converter
try:
    from cat_win.util.utility import comp_eval, comp_conv, split_replace
except SyntaxError: # in case of Python 3.7
    from cat_win.util.utilityold import comp_eval, comp_conv, split_replace
from cat_win.util.fileattributes import get_file_meta_data, get_file_size, _convert_size
from cat_win.util.holder import Holder
from cat_win.util.rawviewer import get_raw_view_lines_gen
from cat_win.util.stringfinder import StringFinder
from cat_win.util.tmpfilehelper import TmpFileHelper
from cat_win.util import stdinhelper
from cat_win.web.updatechecker import print_update_information
from cat_win import __project__, __version__, __sysversion__, __author__, __url__


working_dir = os.path.dirname(os.path.realpath(__file__))

coloramaInit()
config = Config(working_dir)

default_color_dic = config.load_config()
color_dic = default_color_dic.copy()

arg_parser = ArgParser()
converter = Converter()
holder = Holder()
tmp_file_helper = TmpFileHelper()

on_windows_os = system() == 'Windows'

LARGE_FILE_SIZE = 1024 * 1024 * 100  # 100 Megabytes


def exception_handler(exception_type: type, exception, traceback, debug_hook=sys.excepthook) -> None:
    try:
        print(color_dic[CKW.RESET_ALL])
        if holder.args_id[ARGS_DEBUG]:
            debug_hook(exception_type, exception, traceback)
            return
        print(f"\n{exception_type.__name__}{':' * bool(str(exception))} {exception}")
        if exception_type != KeyboardInterrupt:
            print('If this Exception is unexpected, please raise an official Issue at:')
            print(f"{__url__}/issues")
    except Exception:
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
    for arg in ALL_ARGS:
        if arg.show_arg and (not shell or arg.show_arg_on_shell):
            help_message += f"\t{f'{arg.short_form}, {arg.long_form}': <25}{arg.arg_help}\n"
    help_message += '\n'
    help_message += f"\t{'-R, --R<stream>': <25}reconfigure the std-stream(s) with the parsed encoding\n"
    help_message += "\t<stream> == 'in'/'out'/'err' (default is stdin & stdout)\n"
    help_message += '\n'
    help_message += f"\t{'enc=X, enc:X'    : <25}set file encoding to X (default is utf-8)\n"
    help_message += f"\t{'find=X, find:X'  : <25}find/query a substring X in the given files\n"
    help_message += f"\t{'match=X, match:X': <25}find/query a pattern X in the given files\n"
    if not shell:
        help_message += f"\t{'trunc=X:Y, trunc:X:Y': <25}truncate file to lines x and y (python-like)\n"
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
        help_message += f"\t{'catw f g -r' : <25}Output g's contents in reverse order, then f's content in reverse order\n"
        help_message += f"\t{'catw f g -ne': <25}Output f's, then g's content, while numerating and showing the end of lines\n"
        help_message += f"\t{'catw f trunc=a:b:c': <25}Output f's content starting at line a, ending at line b, stepping c\n"
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
        version_message += f"Install time: \t{datetime.fromtimestamp(os.path.getctime(os.path.realpath(__file__)))}\n"
    except OSError: # fails on pyinstaller executable
        version_message += 'Install time: \t-\n'
    version_message += f"Author: \t{__author__}\n"
    print(version_message)
    print_update_information(__project__, __version__, color_dic, on_windows_os)


def _show_debug(args: list, unknown_args: list, known_files: list, unknown_files: list,
                echo_args: list) -> None:
    """
    Print all neccassary debug information
    """
    print('==================================== DEBUG ====================================')
    print('args: ', end='')
    print([(arg[0], arg[1], holder.args_id[arg[0]]) for arg in args])
    print('unknown_args: ', end='')
    print(unknown_args)
    print('known_files: ', end='')
    print(known_files)
    print('unknown_files: ', end='')
    print(unknown_files)
    print('echo_args: ', end='')
    print(echo_args)
    print('file encoding: ', end='')
    print(arg_parser.file_encoding)
    print('search keyword(s): ', end='')
    print(arg_parser.file_search)
    print('search match(es): ', end='')
    print(arg_parser.file_match)
    print('truncate file: ', end='')
    print(arg_parser.file_truncate)
    print('===============================================================================')


def _show_count() -> None:
    """
    display the line sum of each file individually if
    ARGS_CCOUNT is specified.
    display the line sum of all files.
    """
    if holder.args_id[ARGS_CCOUNT]:
        longest_file_name = max(map(len, holder.all_files_lines.keys())) + 1
        print(f"{color_dic[CKW.COUNT_AND_FILES]}{'File': <{longest_file_name}}LineCount{color_dic[CKW.RESET_ALL]}")
        for file in holder.all_files_lines:
            print(f"{color_dic[CKW.COUNT_AND_FILES]}{file: <{longest_file_name}}{holder.all_files_lines[file]: >{holder.all_line_number_place_holder}}{color_dic[CKW.RESET_ALL]}")
        print('')
    print(f"{color_dic[CKW.COUNT_AND_FILES]}Lines (Sum): {holder.all_files_lines_sum}{color_dic[CKW.RESET_ALL]}")


def _show_files() -> None:
    """
    displays holder.files including their size and calculates
    their size sum.
    """
    if len(holder.files) == 0:
        return
    file_sizes = []
    msg = 'found' if holder.args_id[ARGS_FFILES] else 'applied'
    print(color_dic[CKW.COUNT_AND_FILES], end='')
    print(f"{msg} FILE(s):", end='')
    print(color_dic[CKW.RESET_ALL])
    for file in holder.files:
        if file.file_size == -1:
            file.set_file_size(get_file_size(file.path))
        file_sizes.append(file.file_size)
        print(f"\t{color_dic[CKW.COUNT_AND_FILES]}{_convert_size(file.file_size): <10}", end='')
        print(f"{'*' if file.contains_queried else ' '}{file.displayname}{color_dic[CKW.RESET_ALL]}")
    print(color_dic[CKW.COUNT_AND_FILES], end='')
    print(f"Sum:\t{_convert_size(sum(file_sizes))}", end='')
    print(color_dic[CKW.RESET_ALL])
    print(color_dic[CKW.COUNT_AND_FILES], end='')
    print(f"Amount:\t{len(holder.files)}", end='')
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
    return resub(r'\x1b\[[0-9\;]*m', '', line)


# def removeAnsiCodes(content: list) -> list:
#     return [(remove_ansi_codes_from_line(prefix), remove_ansi_codes_from_line(line)) for prefix, line in content]


@lru_cache(maxsize=None)
def _calculate_line_prefix_spacing(line_char_length: int, include_file_prefix: bool = False,
                                   file_char_length: int = 0) -> str:
    """
    calculate a string template for the line prefix.
    
    Parameters:
    line_char_length (int):
        the length of the line number
    include_file_prefix (bool):
        should the file be included in the prefix
    file_char_length (int):
        the length of the file number
    
    Returns:
    (str):
        a non-finished but correctly formatted string template to insert line number
        and file index into
    """
    line_prefix = (' ' * (holder.all_line_number_place_holder - line_char_length)) + '%i)'

    if include_file_prefix:
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
    if len(holder.files) > 1:
        return _calculate_line_prefix_spacing(len(str(line_num)), True, len(str(index))) % (index, line_num)
    return _calculate_line_prefix_spacing(len(str(line_num))) % (line_num)


@lru_cache(maxsize=None)
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
    if not (arg_parser.file_search or arg_parser.file_match):
        print(*[prefix + line for prefix, line in content], sep='\n')
        return False

    contains_queried = False
    string_finder = StringFinder(arg_parser.file_search, arg_parser.file_match)

    for line_prefix, line in content:
        cleaned_line = remove_ansi_codes_from_line(line)
        intervals, f_keywords, m_keywords = string_finder.find_keywords(cleaned_line)

        if holder.args_id[ARGS_GREP_ONLY]:
            if f_keywords or m_keywords:
                fm_substrings = [line[pos[0]:pos[1]] for _, pos in f_keywords + m_keywords]
                print(','.join(fm_substrings))
            continue

        if len(f_keywords + m_keywords) == 0:
            if not holder.args_id[ARGS_GREP]:
                print(line_prefix + line)
            continue

        contains_queried = True
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
                # fails when using -i mode, because the stdin will send en EOF char
                # to input without prompting the user
                input()
            except (EOFError, UnicodeDecodeError):
                pass

    return contains_queried


def print_excluded_by_peek(content: list, excluded_by_peek: int) -> None:
    """
    print a paragraph about how many lines have been excluded.
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    excluded_by_peek (int):
        the amount of lines that have been excluded
    """
    if not excluded_by_peek or len(content) <= 5:
        return
    excluded_by_peek = excluded_by_peek + 10 - len(content)
    prefix = content[0][0]
    prefix = prefix.replace(color_dic[CKW.NUMBER], '')
    prefix = prefix.replace(color_dic[CKW.LINE_LENGTH], '')
    prefix = prefix.replace(color_dic[CKW.RESET_ALL], '')
    excluded_by_peek_length = (len(str(excluded_by_peek))-1)//2
    excluded_by_peek_indent = ' ' * (len(prefix) - excluded_by_peek_length + 10)
    excluded_by_peek_indent_add = ' ' * excluded_by_peek_length
    print(color_dic[CKW.NUMBER], end='')
    print(excluded_by_peek_indent, excluded_by_peek_indent_add, ' •', sep='')
    print(excluded_by_peek_indent, '(', excluded_by_peek, ')', sep='')
    print(excluded_by_peek_indent, excluded_by_peek_indent_add, ' •', sep='', end='')
    print(color_dic[CKW.RESET_ALL])


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
    """
    excluded_by_peek = 0

    if not show_bytecode and holder.args_id[ARGS_B64D]:
        content = decode_base64(content, arg_parser.file_encoding)

    if holder.args_id[ARGS_NUMBER]:
        content = [(_get_line_prefix(j+line_offset, file_index+1), c[1])
                   for j, c in enumerate(content, start=1)]
    content = content[arg_parser.file_truncate[0]:arg_parser.file_truncate[1]:arg_parser.file_truncate[2]]
    if holder.args_id[ARGS_PEEK] and len(content) > 10:
        excluded_by_peek = len(content) - 10
        content = content[:5] + content[-5:]

    if not show_bytecode:
        for arg, param in holder.args:
            if arg == ARGS_CUT:
                try:
                    content = [(prefix, eval(repr(line) + param))
                                for prefix, line in content]
                except Exception:
                    print('Error at operation: ', param)
                    return

        for arg, param in holder.args:
            if arg == ARGS_ENDS:
                content = [(prefix, f"{line}{color_dic[CKW.ENDS]}${color_dic[CKW.RESET_ALL]}")
                           for prefix, line in content]
            elif arg == ARGS_TABS:
                content = [(prefix, line.replace('\t', f"{color_dic[CKW.TABS]}^I{color_dic[CKW.RESET_ALL]}"))
                           for prefix, line in content]
            elif arg == ARGS_SQUEEZE:
                content = [list(group)[0] for _, group in groupby(content, lambda x: x[1])]
            elif arg == ARGS_REVERSE:
                content.reverse()
            elif arg == ARGS_SORT:
                content.sort(key = lambda l: l[1])
            elif arg == ARGS_BLANK:
                content = [c for c in content if c[1]]
            elif arg == ARGS_EVAL:
                content = comp_eval(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_DEC:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_HEX:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_BIN:
                content = comp_conv(converter, content, param, remove_ansi_codes_from_line)
            elif arg == ARGS_REPLACE:
                replace_values = split_replace(param)
                content = [(prefix, line.replace(replace_values[0], f"{color_dic[CKW.REPLACE]}{replace_values[1]}{color_dic[CKW.RESET_ALL]}"))
                           for prefix, line  in content]
            elif arg == ARGS_EOF:
                content = [(prefix, line.replace(chr(26), f"{color_dic[CKW.REPLACE]}^EOF{color_dic[CKW.RESET_ALL]}"))
                           for prefix, line in content]

    if holder.args_id[ARGS_LLENGTH]:
        content = [(_get_line_length_prefix(c[0], c[1]), c[1]) for c in content]
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
            holder.clip_board += '\n'.join([prefix + line for prefix, line in content])


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
            content = [('', line) for line in file.read().splitlines()]
    except Exception as exc:
        print('Failed to open:', holder.files[file_index].displayname)
        try:
            enter_char = '⏎'
            try:
                if len(enter_char.encode(arg_parser.file_encoding)) != 3:
                    raise UnicodeEncodeError('', '', -1, -1, '') from exc
            except UnicodeEncodeError:
                enter_char = 'ENTER'
            print(f"Do you want to open the file as a binary, without parameters? [Y/{enter_char}]:", end='')
            inp = input()
            if not os.isatty(sys.stdin.fileno()):
                print('') # if the input is piped, we add the linefeed char manually
            if inp and 'Y' not in inp.upper():
                print('Aborting...')
                return
        except EOFError:
            pass
        except UnicodeError:
            print(f"Input is not recognized in the given encoding: {arg_parser.file_encoding}")
            print('Aborting...')
            return
        try:
            with open(holder.files[file_index].path, 'rb') as raw_f:
                # in binary splitlines() is our only option
                content = [('', repr(line)[2:-1]) for line in raw_f.read().splitlines()]
            show_bytecode = True
        except Exception:
            print('Operation failed! Try using the enc=X parameter.')
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
            error_msg += "ClipBoardError: You can use either 'pyperclip3', 'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
            error_msg += "Try to install a different one using 'python -m pip install ...'"
        else:
            error_msg = '\n'
            error_msg += "ImportError: You need either 'pyperclip3', 'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
            error_msg += "Should you have any problem with either module, try to install a different one using 'python -m pip install ...'"
        print(error_msg)
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
    print(holder.files[file_index].displayname, ':', sep='')
    for line in get_raw_view_lines_gen(holder.files[file_index].path, mode, \
        [color_dic[CKW.RAWVIEWER], color_dic[CKW.RESET_ALL]], arg_parser.file_encoding):
        print(line)
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
    if holder.args_id[ARGS_COUNT]:
        print('')
        _show_count()
    if holder.args_id[ARGS_FILES]:
        print('')
        _show_files()
    if holder.args_id[ARGS_CLIP]:
        copy_to_clipboard(remove_ansi_codes_from_line(holder.clip_board))


def init_colors() -> None:
    """
    set the color dictionary to be used. either empty for no colors
    or the default color dictionary.
    """
    # do not use colors if requested, or output will be piped anyways
    global color_dic
    if holder.args_id[ARGS_NOCOL] or (not sys.stdout.isatty() or sys.stdout.closed):
        color_dic = dict.fromkeys(color_dic, '')
    else:
        color_dic = default_color_dic.copy()

    converter.set_params(holder.args_id[ARGS_DEBUG],
                         [color_dic[CKW.EVALUATION], color_dic[CKW.CONVERSION], color_dic[CKW.RESET_ALL]])


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
        contains (known_files, unknown_files, echo_args) from the argparser
    """
    # read parameter-args
    args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(sys.argv)

    holder.set_args(args)

    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_IN]:
        sys.stdin.reconfigure(encoding=arg_parser.file_encoding)
    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_OUT]:
        sys.stdout.reconfigure(encoding=arg_parser.file_encoding)
    if holder.args_id[ARGS_RECONFIGURE_ERR]:
        sys.stderr.reconfigure(encoding=arg_parser.file_encoding)

    init_colors()

    # check for special cases
    if holder.args_id[ARGS_DEBUG]:
        _show_debug(holder.args, unknown_args, known_files, unknown_files, echo_args)
    if (len(known_files) + len(unknown_files) + len(holder.args) == 0 and not shell) or \
        holder.args_id[ARGS_HELP]:
        _show_help(shell)
        sys.exit(0)
    if holder.args_id[ARGS_VERSION]:
        _show_version()
        sys.exit(0)
    if holder.args_id[ARGS_CONFIG]:
        config.save_config()
        sys.exit(0)

    return (known_files, unknown_files, echo_args)


def main():
    piped_input = temp_file = ''
    known_files, unknown_files, echo_args = init(False)

    if holder.args_id[ARGS_ECHO]:
        temp_file = stdinhelper.write_temp(' '.join(echo_args), \
            tmp_file_helper.generate_temp_file_name(), arg_parser.file_encoding)
        known_files.append(temp_file)
        holder.set_temp_file_echo(temp_file)
    if holder.args_id[ARGS_INTERACTIVE]:
        piped_input = ''.join(stdinhelper.get_stdin_content(holder.args_id[ARGS_ONELINE]))
        temp_file = stdinhelper.write_temp(piped_input, tmp_file_helper.generate_temp_file_name(), \
            arg_parser.file_encoding)
        known_files.append(temp_file)
        unknown_files = stdinhelper.write_files(unknown_files, piped_input, arg_parser.file_encoding)
        holder.set_temp_file_stdin(temp_file)
    else:
        unknown_files = stdinhelper.read_write_files_from_stdin(
            unknown_files, arg_parser.file_encoding, on_windows_os, holder.args_id[ARGS_ONELINE])

    if len(known_files) + len(unknown_files) == 0:
        return

    # fill holder object with neccessary values
    holder.set_files([*known_files, *unknown_files])

    if holder.args_id[ARGS_FFILES]:
        _show_files()
        return
    if holder.args_id[ARGS_DATA] or holder.args_id[ARGS_CHECKSUM]:
        _print_meta_and_checksum(holder.args_id[ARGS_DATA], holder.args_id[ARGS_CHECKSUM])
        return

    file_size_sum = 0
    for file in holder.files:
        file.set_file_size(get_file_size(file.path))
        file_size_sum += file.file_size
        if file_size_sum >= LARGE_FILE_SIZE:
            if (sys.stdout.isatty() and not sys.stdout.closed):
                print(color_dic[CKW.MESSAGE_IMPORTANT], end='')
                print('Some files are exceedingly large and may require a lot of time and resources.', end='')
                print(color_dic[CKW.RESET_ALL])
            break

    if holder.args_id[ARGS_B64D]:
        holder.set_decoding_temp_files([tmp_file_helper.generate_temp_file_name() for _ in holder.files])
    holder.generate_values(arg_parser.file_encoding)

    if holder.args_id[ARGS_CCOUNT]:
        _show_count()
        return

    try:
        edit_files()  # print the cat-output
    except IOError: # catch broken-pipe error
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE

    # clean-up
    if holder.args_id[ARGS_DEBUG] and tmp_file_helper.tmp_count:
        print('==================================== DEBUG ====================================')
    for tmp_file in tmp_file_helper.get_generated_temp_files():
        if holder.args_id[ARGS_DEBUG]:
            print('Cleaning', tmp_file)
        try:
            os.remove(tmp_file)
        except FileNotFoundError:
            if holder.args_id[ARGS_DEBUG]:
                print('FileNotFoundError', tmp_file)
        except PermissionError:
            if holder.args_id[ARGS_DEBUG]:
                print('PermissionError', tmp_file)
    if holder.args_id[ARGS_DEBUG] and tmp_file_helper.tmp_count:
        print('===============================================================================')


def shell_main():
    init(True)

    command_prefix = '!'
    shell_prefix = '>>> '
    eof_control_char = 'Z' if on_windows_os else 'D'
    oneline = holder.args_id[ARGS_ONELINE]

    class CmdExec:
        def __init__(self) -> None:
            self.exit_shell = False
            self.last_cmd = ''

        def exec_colors(self) -> None:
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
            print("If you want to escape the command input, type: '\\!", self.last_cmd, "'.", sep='')

        def _command_cat(self, _) -> None:
            cat = " ,_     _\n |\\\\_,-~/\n / _  _ |    ,--.\n(  @  @ )   / ,-'\n \\  _T_/"
            cat += "-._( (\n /         `. \\\n|         _  \\ |\n \\ \\ ,  /      |\n  || |-_\\__   /\n ((_/`(____,-'\n"
            print('\n'.join(['\t\t\t' + c for c in cat.split('\n')]))

        def _command_help(self, _) -> None:
            print(f"Type ^{eof_control_char} (Ctrl + {eof_control_char}) or '!exit' to exit.")
            print("Type '!add <OPTION>', '!del <OPTION>' to add/remove a specific parameter.")
            print("Type '!see', '!clear' to see/remove all active parameters.")
            print("Put a '\\' before a leading '!' to escape the command-input.")

        def _command_add(self, cmd: list) -> None:
            arg_parser.gen_arguments([''] + cmd)
            holder.add_args(arg_parser._args)
            self.exec_colors()
            print(f"successfully added {[arg for _, arg in arg_parser._args] if arg_parser._args else 'parameters'}.")

        def _command_del(self, cmd: list) -> None:
            arg_parser.gen_arguments([''] + cmd, True)
            holder.delete_args(arg_parser._args)
            self.exec_colors()
            print(f"successfully removed {[arg for _, arg in arg_parser._args] if arg_parser._args else 'parameters'}.")
            
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
                    copy_function = copy_to_clipboard(remove_ansi_codes_from_line(holder.clip_board), copy_function)
                    holder.clip_board = ''
        if not oneline:
            print(shell_prefix, end='', flush=True)


if __name__ == '__main__':
    main()
