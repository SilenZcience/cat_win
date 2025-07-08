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
import shlex
import sys

from cat_win.src.argparser import ArgParser
from cat_win.src.const.argconstants import *
from cat_win.src.const.colorconstants import CKW, CVis
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.const.regex import ANSI_CSI_RE
from cat_win.src.domain.arguments import Arguments
from cat_win.src.domain.files import Files
from cat_win.src.persistence.cconfig import CConfig
from cat_win.src.persistence.config import Config
from cat_win.src.service.helper.archiveviewer import display_archive
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.iohelper import IoHelper, err_print
from cat_win.src.service.helper.levenshtein import calculate_suggestions
from cat_win.src.service.helper.progressbar import PBar
from cat_win.src.service.helper.tmpfilehelper import TmpFileHelper
try:
    from cat_win.src.service.helper.utility import comp_eval, comp_conv
except SyntaxError: # in case of Python 3.7
    from cat_win.src.service.helper.utilityold import comp_eval, comp_conv
from cat_win.src.service.cbase64 import encode_base64, decode_base64
from cat_win.src.service.checksum import print_checksum
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.converter import Converter
from cat_win.src.service.editor import Editor
from cat_win.src.service.fileattributes import get_file_size, get_file_mtime, print_meta
from cat_win.src.service.fileattributes import _convert_size
from cat_win.src.service.formatter import Formatter
from cat_win.src.service.hexeditor import HexEditor
from cat_win.src.service.more import More
from cat_win.src.service.rawviewer import SPECIAL_CHARS, get_raw_view_lines_gen
from cat_win.src.service.stringfinder import StringFinder
from cat_win.src.service.strings import get_strings
from cat_win.src.service.summary import Summary
from cat_win.src.service.visualizer import Visualizer
from cat_win.src.web.updatechecker import print_update_information
from cat_win.src.web.urls import read_url
from cat_win import __project__, __version__, __sysversion__, __author__, __url__


coloramaInit(strip=False)
working_dir = os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir, os.pardir))

file_uri_prefix = 'file://' + '/' * on_windows_os

cconfig = CConfig(working_dir)
config = Config(working_dir)

default_color_dic, color_dic, const_dic = None, None, None

arg_parser, u_args, u_files, converter, = None, None, None, None


def setup():
    """
    setup the global variables.
    """
    global default_color_dic, color_dic, const_dic
    global arg_parser, converter, u_files, u_args

    default_color_dic = cconfig.load_config()
    color_dic = default_color_dic.copy()
    const_dic = config.load_config()

    arg_parser = ArgParser(const_dic[DKW.DEFAULT_FILE_ENCODING],
                           const_dic[DKW.UNICODE_ESCAPED_ECHO],
                           const_dic[DKW.UNICODE_ESCAPED_FIND],
                           const_dic[DKW.UNICODE_ESCAPED_REPLACE])
    u_args = Arguments()
    u_files = Files()
    converter = Converter()


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
        if u_args[ARGS_DEBUG]:
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


def _show_help(repl: bool = False) -> None:
    """
    Show the Help message and exit.
    """
    if repl:
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
            if arg.show_arg and (not repl or arg.show_arg_on_repl):
                arg_descriptor = f'{arg.short_form}, {arg.long_form}'
                if len(arg_descriptor) > 35:
                    arg_descriptor = arg_descriptor[:31] + '...'
                help_message += f"\t{arg_descriptor: <35}{arg.arg_help}\n"
                relevant_section = True
        help_message += '\n' * relevant_section
    help_message += f"\t{'-R, --R<stream>': <35}"
    help_message += 'reconfigure the std-stream(s) with the parsed encoding\n'
    help_message += "\t<stream> == 'in'/'out'/'err' (default is stdin & stdout)\n"
    help_message += '\n'
    help_message += f"\t{'enc=X, enc:X'    : <35}set file encoding to X (default is utf-8)\n"
    help_message += f"\t{'find=X, find:X'  : <35}find/query a substring X in the given files\n"
    help_message += f"\t{'match=X, match:X': <35}find/query a pattern X in the given files\n"
    help_message += f"\t{'replace=X, replace:X': <35}replace queried substring(s)/pattern(s) in the given files\n"
    if not repl:
        help_message += f"\t{'trunc=X:Y, trunc:X:Y': <35}"
        help_message += 'truncate file to lines X and Y (python-like)\n'
    help_message += '\n'
    help_message += f"\t{'[a,b]': <35}replace a with b in every line\n"
    help_message += f"\t{'[a:b:c]': <35}python-like string indexing syntax (line by line)\n"
    help_message += '\n'
    help_message += 'Examples:\n'
    if repl:
        help_message += '\tcats --ln --dec\n'
        help_message += '\t> >>> 12345\n'
        help_message += '\t1) [53] 12345 {Hexadecimal: 0x3039; Binary: 0b11000000111001}\n'
        help_message += '\t> >>> !help\n'
        help_message += '\t> ...\n'
    else:
        help_message += f"\t{'catw f g -r' : <35}"
        help_message += "Output g's contents in reverse order, then f's content in reverse order\n"
        help_message += f"\t{'catw f g -ne': <35}"
        help_message += "Output f's, then g's content, "
        help_message += 'while numerating and showing the end of lines\n'
        help_message += f"\t{'catw f trunc=a:b:c': <35}"
        help_message += "Output f's content starting at line a, ending at line b, stepping c\n"
    help_message += '\n'
    help_message += 'Documentation:\n'
    help_message += f"\t{__url__}/blob/main/DOCUMENTATION.md"
    try:
        (More(help_message.splitlines())).step_through()
    finally:
        print_update_information(__project__, __version__, color_dic)


def _show_version(repl: bool = False) -> None:
    """
    Show the Version message and exit.
    """
    cat_version = f"{__project__} "
    if repl:
        cat_version += 'REPL '
    cat_version += f"{__version__} - from {working_dir}\n"
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
    print_update_information(__project__, __version__, color_dic)


def _show_debug(args: list, unknown_args: list, known_files: list, unknown_files: list,
                echo_args: str, known_dirs: list, valid_urls: list) -> None:
    """
    Print all neccassary debug information
    """
    err_print(color_dic[CKW.MESSAGE_INFORMATION], end='')
    err_print('================================================ '
        'DEBUG ================================================')
    err_print('sys_args:', sys.argv)
    err_print('args: ', end='')
    err_print([(arg[0], arg[1], u_args[arg[0]]) for arg in args])
    err_print('unknown_args: ', end='')
    err_print(unknown_args)
    err_print('known_files: ', end='')
    err_print(list(map(str, known_files)))
    err_print('unknown_files: ', end='')
    err_print(list(map(str, unknown_files)))
    err_print('echo_args: ', end='')
    err_print(repr(echo_args))
    err_print('known_directories: ', end='')
    err_print(list(map(str, known_dirs)))
    err_print('valid_urls: ', end='')
    err_print(valid_urls)
    err_print('file encoding: ', end='')
    err_print(arg_parser.file_encoding)
    err_print('search queries: ', end='')
    err_print(','.join(
        ('str(' + ('CI' if c else 'CS') + '):' if isinstance(v, str) else 're:') + str(v)
        for v, c in arg_parser.file_queries
    ))
    err_print('replace queries: ', end='')
    err_print(repr(arg_parser.file_queries_replacement))
    err_print('truncate file: ', end='')
    err_print(arg_parser.file_truncate)
    err_print('replace mapping: ', end='')
    err_print(arg_parser.file_replace_mapping)
    err_print('==================================================='
              '====================================================', end='')
    err_print(color_dic[CKW.RESET_ALL])


def _print_meta_and_checksum(show_meta: bool, show_checksum: bool) -> None:
    """
    calls _print_meta() and _print_checksum() on every file.

    Parameters:
    show_meta (bool):
        decides if the metadata of the files should be displayed
    show_checksum (bool):
        decides if the checksum of the files should be displayed
    """
    for file in u_files:
        if show_meta:
            print_meta(file.path, os.path.join(working_dir, 'res', 'signatures.json'),
                       [color_dic[CKW.RESET_ALL],
                        color_dic[CKW.ATTRIB],
                        color_dic[CKW.ATTRIB_POSITIVE],
                        color_dic[CKW.ATTRIB_NEGATIVE]])
        if show_checksum:
            print_checksum(file.path, color_dic[CKW.CHECKSUM], color_dic[CKW.RESET_ALL])

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
    line_prefix = ' ' * (u_files.all_line_number_place_holder - line_char_length)

    if file_name_prefix:
        line_prefix = '%i' + line_prefix
    else:
        line_prefix += '%i)'

    if include_file_prefix and not file_name_prefix:
        file_prefix = (' ' * (u_files.file_number_place_holder - file_char_length)) + '%i.'
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
    if u_args[ARGS_FILE_PREFIX]:
        return _calculate_line_prefix_spacing(len(str(line_num)), True) % (line_num)
    if len(u_files) > 1:
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
    length_prefix = '[' + ' ' * (u_files.file_line_length_place_holder - line_char_length) + '%i]'
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
    if not u_args[ARGS_NOCOL] and isinstance(line, str):
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
    file = f"{file_uri_prefix * hyper}{u_files[file_index].displayname}"
    if hyper:
        file = file.replace('\\', '/')
    if not u_args[ARGS_NUMBER] or hyper:
        return f"{prefix}{color_dic[CKW.FILE_PREFIX]}{file}{color_dic[CKW.RESET_ALL]} "
    return f"{color_dic[CKW.FILE_PREFIX]}{file}{color_dic[CKW.RESET_ALL]}:{prefix}"


def print_file(content: list, stepper: More) -> bool:
    """
    print a file and possibly include the substrings and patterns to search for.

    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    stepper (More):
        the stepper to step through the file

    Returns:
    (bool):
        identifies if the given content parameter contained any
        queried keyword/pattern.
    """
    if not content:
        return False
    if not any([arg_parser.file_queries, u_args[ARGS_GREP], u_args[ARGS_GREP_ONLY]]):
        if u_args[ARGS_MORE]:
            stepper.add_lines([prefix + line for prefix, line in content])
            return False
        print(*[prefix + line for prefix, line in content], sep='\n')
        return False

    string_finder = StringFinder(arg_parser.file_queries)

    contains_queried = False
    if arg_parser.file_queries and arg_parser.file_queries_replacement:
        for line_prefix, line in content:
            cleaned_line = remove_ansi_codes_from_line(line)
            for query, ignore_case in arg_parser.file_queries:
                contains_queried = True
                if isinstance(query, str):
                    for f_s, f_e in string_finder.find_literals(query, cleaned_line, ignore_case):
                        cleaned_line = (
                            cleaned_line[:f_s] + \
                                color_dic[CKW.REPLACE] + \
                                    arg_parser.file_queries_replacement + \
                                        color_dic[CKW.RESET_ALL] + \
                                            cleaned_line[f_e:]
                        )
                else:
                    cleaned_line = query.sub(
                        color_dic[CKW.REPLACE] + \
                            arg_parser.file_queries_replacement + \
                                color_dic[CKW.RESET_ALL],
                                cleaned_line
                    )
            if u_args[ARGS_MORE]:
                stepper.add_line(line_prefix + cleaned_line)
            else:
                print(line_prefix + cleaned_line)
        return contains_queried

    for line_prefix, line in content:
        cleaned_line = remove_ansi_codes_from_line(line)
        intervals, f_keywords, m_keywords = string_finder.find_keywords(cleaned_line)

        # used for marking the file when displaying applied files
        contains_queried |= bool(intervals)

        # this has priority over the other arguments
        if u_args[ARGS_GREP_ONLY]:
            if intervals:
                fm_substrings = [(pos[0], f"{color_dic[CKW.FOUND]}" + \
                    f"{line[pos[0]:pos[1]]}{color_dic[CKW.RESET_FOUND]}")
                                 for _, pos in f_keywords]
                fm_substrings+= [(pos[0], f"{color_dic[CKW.MATCHED]}" + \
                    f"{line[pos[0]:pos[1]]}{color_dic[CKW.RESET_MATCHED]}")
                                 for _, pos in m_keywords]
                fm_substrings.sort(key=lambda x:x[0])
                grepped_line = f"{line_prefix}{','.join(sub for _, sub in fm_substrings)}"
                if u_args[ARGS_MORE]:
                    stepper.add_line(grepped_line)
                    continue
                print(grepped_line)
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
            if not u_args[ARGS_GREP]:
                if u_args[ARGS_MORE]:
                    stepper.add_line(line_prefix + line)
                    continue
                print(line_prefix + line)
            continue

        if u_args[ARGS_NOKEYWORD]:
            continue

        if not u_args[ARGS_NOCOL]:
            for kw_pos, kw_code in intervals:
                cleaned_line = cleaned_line[:kw_pos] + color_dic[kw_code] + cleaned_line[kw_pos:]

        if u_args[ARGS_MORE]:
            stepper.add_line(line_prefix + cleaned_line)
        else:
            print(line_prefix + cleaned_line)

        if u_args[ARGS_GREP] or u_args[ARGS_NOBREAK]:
            continue

        found_sth = False
        if f_keywords:
            found_message = f"{color_dic[CKW.FOUND_MESSAGE]}---------- Found:   ("
            found_message+= ') ('.join(
                [f"'{kw}' {pos_s}-{pos_e}" for kw, (pos_s, pos_e) in f_keywords]
            )
            found_message+= f") ----------{color_dic[CKW.RESET_ALL]}"
            if u_args[ARGS_MORE]:
                stepper.add_line(found_message)
            else:
                print(found_message)
            found_sth = True
        if m_keywords:
            matched_message = f"{color_dic[CKW.MATCHED_MESSAGE]}---------- Matched: ("
            matched_message+= ') ('.join(
                [f"'{kw}' {pos_s}-{pos_e}" for kw, (pos_s, pos_e) in m_keywords]
            )
            matched_message+= f") ----------{color_dic[CKW.RESET_ALL]}"
            if u_args[ARGS_MORE]:
                stepper.add_line(matched_message)
            else:
                print(matched_message)
            found_sth = True

        if found_sth and not u_args[ARGS_MORE]:
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
    if not excluded_by_peek or len(content) <= const_dic[DKW.PEEK_SIZE]:
        return
    if any([u_args[ARGS_GREP],
            u_args[ARGS_GREP_ONLY],
            u_args[ARGS_NOKEYWORD],
            u_args[ARGS_MORE]]):
        return
    _print_excluded_by_peek(len(remove_ansi_codes_from_line(content[0][0])),
                            excluded_by_peek + 2*const_dic[DKW.PEEK_SIZE] - len(content))


def edit_raw_content(content: bytes, file_index: int = 0) -> None:
    """
    write raw binary

    Parameters:
    content (bytes):
        the raw content of a binary file
    file_index (int):
        the index of the u_files.files list, pointing to the file that
        is currently being processed. a negative value can be used for
        the repl mode
    """
    if u_args[ARGS_STRINGS]:
        return edit_content([('', content)], file_index)
    if u_args[ARGS_B64E]:
        content = encode_base64(content, True)
        if u_args[ARGS_CLIP]:
            Clipboard.clipboard += content
        return print(content)
    sys.stdout.buffer.write(content)

def edit_content(content: list, file_index: int = 0, line_offset: int = 0) -> None:
    """
    apply all parameters to a string (file Content).

    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    file_index (int):
        the index of the u_files.files list, pointing to the file that
        is currently being processed. a negative value can be used for
        the repl mode
    line_offset (int):
        the offset for counting the line numbers (used in the repl)
    """
    if not (
        content or
        os.isatty(sys.stdout.fileno()) or
        file_index < 0 or
        u_files.is_temp_file(file_index)
    ):
        # if the content of the file is empty, we check if maybe the file is its own pipe-target.
        # in this case the stdout cannot be atty.
        # also the repl would not produce this problem.
        # also the temp-files (stdin, echo, url, ...) are (most likely) safe.
        # an indicator would be if the file has just been modified to be empty (by the shell).
        # checking if the file is an _unknown_file is not valid, because by using '--stdin'
        # the stdin will be used to write the file
        file_mtime = get_file_mtime(u_files[file_index].path)
        date_nowtime = datetime.timestamp(datetime.now())
        if abs(date_nowtime - file_mtime) < 0.5:
            err_print(f"{color_dic[CKW.MESSAGE_WARNING]}Warning: It looks like you are " + \
                f"trying to pipe a file into itself.{color_dic[CKW.RESET_ALL]}")
            err_print(f"{color_dic[CKW.MESSAGE_WARNING]}In this case you might have lost " + \
                f"all data.{color_dic[CKW.RESET_ALL]}")
        # in any case we have nothing to do and can return
        return

    if u_args[ARGS_STRINGS]:
        content = get_strings(content,
                              const_dic[DKW.STRINGS_MIN_SEQUENCE_LENGTH],
                              const_dic[DKW.STRINGS_DELIMETER])

    if u_args[ARGS_SPECIFIC_FORMATS]:
        content = Formatter.format(content)

    excluded_by_peek = 0

    if u_args[ARGS_NUMBER]:
        content = [(_get_line_prefix(j+line_offset, file_index+1), c[1])
                   for j, c in enumerate(content, start=1)]

    content = content[slice(*arg_parser.file_truncate)]

    if u_args[ARGS_PEEK] and len(content) > 2*const_dic[DKW.PEEK_SIZE]:
        excluded_by_peek = len(content) - 2*const_dic[DKW.PEEK_SIZE]
        content = content[:const_dic[DKW.PEEK_SIZE]] + content[-const_dic[DKW.PEEK_SIZE]:]

    for arg, param in u_args:
        if arg == ARGS_CUT:
            slice_evals = [None, None, None]
            for i, p_split in enumerate(param[1:-1].split(':')):
                try:
                    slice_evals[i] = int(eval(p_split, {"__builtins__": {}}))
                except (SyntaxError, NameError, ValueError, ArithmeticError):
                    pass
            content = [(prefix, line[slice_evals[0]:slice_evals[1]:slice_evals[2]])
                        for prefix, line in content]

    for arg, param in u_args:
        if arg == ARGS_ENDS:
            emarker = color_dic[CKW.ENDS]+const_dic[DKW.END_MARKER_SYMBOL]+color_dic[CKW.RESET_ALL]
            content = [(prefix, line + emarker) for prefix, line in content]
        elif arg == ARGS_SQUEEZE:
            content = [list(group)[0] for _, group in groupby(content, lambda x: x[1])]
        elif arg == ARGS_REVERSE:
            content.reverse()
        elif arg == ARGS_SORT:
            content.sort(key = lambda l: l[1].casefold())
        elif arg == ARGS_SSORT:
            content.sort(key = lambda l: len(l[1]))
        elif arg == ARGS_BLANK:
            content = [c for c in content if c[1].strip(
                None if const_dic[DKW.BLANK_REMOVE_WS_LINES] else ''
            )]
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
            replace_this, replace_with = arg_parser.file_replace_mapping[param]
            content = [(prefix, line.replace(replace_this, f"{color_dic[CKW.REPLACE]}" + \
                f"{replace_with}{color_dic[CKW.RESET_ALL]}"))
                        for prefix, line in content]
        elif arg == ARGS_CHR:
            for c_id, char, _, possible in SPECIAL_CHARS:
                if not possible:
                    continue
                content = [
                    (prefix, line.replace(
                        chr(c_id), f"{color_dic[CKW.CHARS]}^{char}{color_dic[CKW.RESET_ALL]}"
                    ))
                    for prefix, line in content
                ]

    if u_args[ARGS_LLENGTH]:
        content = [(_get_line_length_prefix(prefix, line), line) for prefix, line in content]
    if u_args[ARGS_FILE_PREFIX]:
        content = [(_get_file_prefix(prefix, file_index), line) for prefix, line in content]
    elif u_args[ARGS_FFILE_PREFIX]:
        content = [(_get_file_prefix(prefix, file_index, hyper=True), line)
                   for prefix, line in content]
    if u_args[ARGS_B64E]:
        content = encode_base64('\n'.join(''.join(x) for x in content), True,
                                arg_parser.file_encoding)
        content = [('', content)]

    stepper = More()
    found_queried = print_file(content[:len(content)//2], stepper)
    if file_index >= 0:
        u_files[file_index].set_contains_queried(found_queried)
    print_excluded_by_peek(content, excluded_by_peek)
    found_queried = print_file(content[len(content)//2:], stepper)
    if file_index >= 0:
        u_files[file_index].set_contains_queried(found_queried)

    if u_args[ARGS_MORE]:
        stepper.step_through(u_args[ARGS_STDIN])

    if u_args[ARGS_CLIP]:
        Clipboard.clipboard += '\n'.join(prefix + line for prefix, line in content)


def edit_file(file_index: int = 0) -> None:
    """
    apply all parameters to a file.

    Parameters:
    file_index (int):
        the index regarding which file is currently being edited
    """
    if u_args[ARGS_RAW]:
        raw_content = IoHelper.read_file(u_files[file_index].path, True)
        edit_raw_content(raw_content, file_index)
        return
    content = []
    file_size = -1 if (
        u_files[file_index].file_size < const_dic[DKW.LARGE_FILE_SIZE]//len(u_files)
    ) else u_files[file_index].file_size
    try:
        file_content = IoHelper.read_file(
            u_files[file_index].path,
            file_encoding=arg_parser.file_encoding,
            file_length=file_size
        )
        # splitlines() gives a slight inaccuracy, because
        # it also splits on other bytes than \r and \n ...
        # the alternative would be worse: split('\n') would increase the linecount each
        # time catw touches a file.
        if not os.isatty(sys.stdout.fileno()) and const_dic[DKW.STRIP_COLOR_ON_PIPE]:
            file_content = remove_ansi_codes_from_line(file_content)
        content = [('', line) for line in file_content.splitlines()]
    except PermissionError:
        err_print(f"Permission denied! Skipping {u_files[file_index].displayname} ...")
        return
    except (BlockingIOError, FileNotFoundError):
        err_print('Resource blocked/unavailable! Skipping ' + \
            f"{u_files[file_index].displayname} ...")
        return
    except (OSError, UnicodeError):
        u_files[file_index].set_plaintext(plain=False)
        if u_args[ARGS_PLAIN_ONLY]:
            return
        if display_archive(u_files[file_index].path, _convert_size):
            return
        try:
            file_content = IoHelper.read_file(
                u_files[file_index].path,
                file_encoding=arg_parser.file_encoding,
                errors='ignore' if const_dic[DKW.IGNORE_UNKNOWN_BYTES] else 'replace',
                file_length=file_size
            )
            if not os.isatty(sys.stdout.fileno()) and const_dic[DKW.STRIP_COLOR_ON_PIPE]:
                file_content = remove_ansi_codes_from_line(file_content)
            content = [('', line) for line in file_content.splitlines()]
        except OSError:
            err_print('Operation failed! Try using the enc=X parameter.')
            return

    edit_content(content, file_index)


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
    skipped = 0

    print(u_files[file_index].displayname, ':', sep='')
    raw_gen = get_raw_view_lines_gen(u_files[file_index].path, mode,
                                     [color_dic[CKW.RAWVIEWER], color_dic[CKW.RESET_ALL]],
                                     arg_parser.file_encoding,
                                     slice(*arg_parser.file_truncate))
    print(next(raw_gen)) # the header will always be available
    for line in raw_gen:
        skipped += 1
        if u_args[ARGS_PEEK] and skipped > const_dic[DKW.PEEK_SIZE]:
            queue.append(line)
            if len(queue) > const_dic[DKW.PEEK_SIZE]:
                queue = queue[1:]
            continue
        print(line)
    if queue:
        if skipped > (2*const_dic[DKW.PEEK_SIZE]):
            _print_excluded_by_peek(21, skipped-2*const_dic[DKW.PEEK_SIZE])
        print('\n'.join(queue))
    print()


def edit_files() -> None:
    """
    manage the calls to edit_file() for each file.
    """
    start = len(u_files)-1 if u_args[ARGS_REVERSE] else 0
    end = -1 if u_args[ARGS_REVERSE] else len(u_files)

    raw_view_mode = u_args.find_first(ARGS_HEXVIEW, ARGS_BINVIEW)
    if raw_view_mode is not None:
        raw_view_mode = (
            'b' if raw_view_mode[0] == ARGS_BINVIEW else
            'X' if raw_view_mode[1].isupper() else 'x'
        )

    for i in range(start, end, -1 if u_args[ARGS_REVERSE] else 1):
        if raw_view_mode is None:
            edit_file(i)
        else:
            print_raw_view(i, raw_view_mode)
    if u_args[ARGS_FILES] or u_args[ARGS_DIRECTORIES]:
        print()
        if u_args[ARGS_FILES]:
            Summary.show_files(u_files.files, u_args[ARGS_FFILES])
        if u_args[ARGS_DIRECTORIES]:
            Summary.show_dirs(arg_parser.get_dirs())
    if u_args[ARGS_SUM]:
        print()
        Summary.show_sum(u_files.files, u_args[ARGS_SSUM], u_files.all_files_lines,
                         u_files.all_line_number_place_holder)
    if u_args[ARGS_WORDCOUNT]:
        print()
        Summary.show_wordcount(u_files.files, arg_parser.file_encoding)
    if u_args[ARGS_CHARCOUNT]:
        print()
        Summary.show_charcount(u_files.files, arg_parser.file_encoding)
    if u_args[ARGS_CLIP]:
        Clipboard.put(remove_ansi_codes_from_line(Clipboard.clipboard))


def decode_files_base64(tmp_file_helper: TmpFileHelper) -> None:
    """
    decode all files from base64 and save to temporary file.

    Parameters:
    tmp_file_helper (TmpFileHelper):
        the TmpFileHelper to keep track of the used tmp files
    """
    for i, file in enumerate(u_files):
        try:
            tmp_file_path = tmp_file_helper.generate_temp_file_name()
            f_read_content = IoHelper.read_file(file.path, file_encoding=arg_parser.file_encoding,
                                                errors='replace')
            if u_args[ARGS_RAW]:
                IoHelper.write_file(tmp_file_path,
                                    decode_base64(f_read_content))
            else:
                IoHelper.write_file(tmp_file_path,
                                    decode_base64(f_read_content, True, arg_parser.file_encoding),
                                    arg_parser.file_encoding)
            u_files[i].path = tmp_file_path
        except (OSError, UnicodeError):
            err_print(f"Base64 decoding failed for file: {file.displayname}")


def show_unknown_args_suggestions(repl: bool = False) -> list:
    """
    display the unknown arguments passed in aswell as their suggestions
    if possible

    Parameters:
    repl (bool):
        indicates whether or not the repl has been used

    Returns:
    arg_suggestions (list):
        the list generated by calculate_suggestion()
    """

    if repl:
        arg_options = [(arg.short_form, arg.long_form)
                       for arg in ALL_ARGS if arg.show_arg_on_repl]
    else:
        arg_options = [(arg.short_form, arg.long_form)
                       for arg in ALL_ARGS]
    arg_suggestions = calculate_suggestions(arg_parser._unknown_args, arg_options)
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

    if u_args[ARGS_NOCOL] or sys.stdout.closed or \
        (not os.isatty(sys.stdout.fileno()) and const_dic[DKW.STRIP_COLOR_ON_PIPE]):
        color_dic = dict.fromkeys(color_dic, '')
        CVis.remove_colors()
    else:
        color_dic = default_color_dic.copy()

    converter.set_params(u_args[ARGS_DEBUG],
                         [color_dic[CKW.EVALUATION],
                          color_dic[CKW.CONVERSION],
                          color_dic[CKW.RESET_ALL]])


def init(repl: bool = False) -> tuple:
    """
    initiate the code by calling the argparser and handling the default
    parameters: -h, -v, -d, --config.

    Parameters:
    repl (bool):
        indicates if the repl entry point was used, and the stdin will therefor
        be used by default

    Returns:
    (tuple):
        contains (known_files, unknown_files, echo_args, valid_urls) from the argparser
    """
    setup()

    # read parameter-args
    args, _, echo_args = arg_parser.get_arguments(config.get_args(sys.argv[:]))

    u_args.set_args(args)

    known_files = arg_parser.get_files(u_args[ARGS_DOTFILES])
    unknown_files, valid_urls = arg_parser.filter_urls(u_args[ARGS_URI])

    if u_args[ARGS_RECONFIGURE] or u_args[ARGS_RECONFIGURE_IN]:
        sys.stdin.reconfigure(encoding=arg_parser.file_encoding)
    if u_args[ARGS_RECONFIGURE] or u_args[ARGS_RECONFIGURE_OUT]:
        sys.stdout.reconfigure(encoding=arg_parser.file_encoding)
    if u_args[ARGS_RECONFIGURE_ERR]:
        sys.stderr.reconfigure(encoding=arg_parser.file_encoding)

    init_colors()

    arg_suggestions = show_unknown_args_suggestions(repl)

    # check for special cases
    if u_args[ARGS_DEBUG]:
        _show_debug(
            u_args.args, arg_suggestions, known_files,
            unknown_files, echo_args, arg_parser.get_dirs(), valid_urls
        )
    if (len(known_files) + len(unknown_files) + len(u_args) == 0 and not repl) or \
        u_args[ARGS_HELP]:
        _show_help(repl)
        sys.exit(0)
    if u_args[ARGS_VERSION]:
        _show_version(repl)
        sys.exit(0)
    if u_args[ARGS_CONFIG_REMOVE]:
        config.remove_config()
        sys.exit(0)
    if u_args[ARGS_CONFIG_FLUSH]:
        config.reset_config()
        sys.exit(0)
    if u_args[ARGS_CCONFIG_FLUSH]:
        cconfig.reset_config()
        sys.exit(0)
    if u_args[ARGS_CONFIG]:
        config.save_config()
        sys.exit(0)
    if u_args[ARGS_CCONFIG]:
        cconfig.save_config()
        sys.exit(0)

    Editor.set_indentation(const_dic[DKW.EDITOR_INDENTATION], const_dic[DKW.EDITOR_AUTO_INDENT])
    Editor.set_flags(u_args[ARGS_STDIN] and on_windows_os, u_args[ARGS_DEBUG],
                     const_dic[DKW.UNICODE_ESCAPED_EDITOR_SEARCH],
                     const_dic[DKW.UNICODE_ESCAPED_EDITOR_REPLACE],
                     arg_parser.file_encoding)
    HexEditor.set_flags(u_args[ARGS_STDIN] and on_windows_os, u_args[ARGS_DEBUG],
                        const_dic[DKW.UNICODE_ESCAPED_EDITOR_SEARCH],
                        const_dic[DKW.UNICODE_ESCAPED_EDITOR_INSERT],
                        const_dic[DKW.HEX_EDITOR_COLUMNS])
    More.set_flags(const_dic[DKW.MORE_STEP_LENGTH])
    Visualizer.set_flags(u_args[ARGS_DEBUG])
    Summary.set_flags(const_dic[DKW.SUMMARY_UNIQUE_ELEMENTS])
    Summary.set_colors(color_dic[CKW.SUMMARY], color_dic[CKW.RESET_ALL])
    PBar.set_colors(color_dic[CKW.PROGRESSBAR_DONE], color_dic[CKW.PROGRESSBAR_MISSING],
                    color_dic[CKW.RESET_ALL])

    return (known_files, unknown_files, echo_args, valid_urls)


def handle_args(tmp_file_helper: TmpFileHelper) -> None:
    """
    init, handle args, print

    Parameters:
    tmp_file_helper (TmpFileHelper):
        the temporary file helper to stdin, echo etc. ...
    """
    piped_input = temp_file = ''
    known_files, unknown_files, echo_args, valid_urls = init(repl=False)

    if u_args[ARGS_ECHO]:
        temp_file = IoHelper.write_file(tmp_file_helper.generate_temp_file_name(), echo_args,
                                        arg_parser.file_encoding)
        known_files.append(temp_file)
        u_files.set_temp_file_echo(temp_file)
    if u_args[ARGS_URI]:
        # the dictionary should contain an entry for each valid_url, since
        # generated temp-files are unique
        temp_files = dict([
            (IoHelper.write_file(tmp_file_helper.generate_temp_file_name(), read_url(valid_url),
                                 arg_parser.file_encoding), valid_url)
            for valid_url in valid_urls
        ])
        known_files.extend(list(temp_files.keys()))
        u_files.set_temp_files_url(temp_files)
    if u_args[ARGS_STDIN]:
        piped_input = (b'' if u_args[ARGS_RAW] else '').join(
            IoHelper.get_stdin_content(
                u_args[ARGS_ONELINE],
                u_args[ARGS_RAW]
            )
        )
        temp_file = IoHelper.write_file(tmp_file_helper.generate_temp_file_name(), piped_input,
                                        arg_parser.file_encoding)
        known_files.append(temp_file)
        u_files.set_temp_file_stdin(temp_file)
        unknown_files = IoHelper.write_files(
            unknown_files, piped_input, arg_parser.file_encoding
        )
    elif u_args.find_first(ARGS_EDITOR, ARGS_HEX_EDITOR, True) is not None:
        unknown_files = [file for file in unknown_files if Editor.open(
            file, u_files.get_file_display_name(file), u_args[ARGS_PLAIN_ONLY]
        )]
    elif u_args.find_first(ARGS_HEX_EDITOR, ARGS_EDITOR, True) is not None:
        unknown_files = [file for file in unknown_files if HexEditor.open(
            file, u_files.get_file_display_name(file)
        )]
    else:
        unknown_files = IoHelper.read_write_files_from_stdin(
            unknown_files, arg_parser.file_encoding, u_args[ARGS_ONELINE]
        )

    if u_args.find_first(ARGS_EDITOR, ARGS_HEX_EDITOR, True) is not None:
        with IoHelper.dup_stdin(u_args[ARGS_STDIN]):
            for file in known_files:
                Editor.open(file, u_files.get_file_display_name(file), u_args[ARGS_PLAIN_ONLY])
    elif u_args.find_first(ARGS_HEX_EDITOR, ARGS_EDITOR, True) is not None:
        with IoHelper.dup_stdin(u_args[ARGS_STDIN]):
            for file in known_files:
                HexEditor.open(file, u_files.get_file_display_name(file))

    # fill holder object with neccessary values
    u_files.set_files([*known_files, *unknown_files])
    # -------------- do not use known_files and unknown_files anymore --------------

    if u_args[ARGS_FFILES] or u_args[ARGS_DDIRECTORIES]:
        if u_args[ARGS_FFILES]:
            Summary.show_files(u_files.files, u_args[ARGS_FFILES])
        if u_args[ARGS_DDIRECTORIES]:
            Summary.show_dirs(arg_parser.get_dirs())
        return

    if len(u_files) == 0:
        return

    if u_args[ARGS_DATA] or u_args[ARGS_CHECKSUM]:
        _print_meta_and_checksum(u_args[ARGS_DATA], u_args[ARGS_CHECKSUM])
        return

    if u_args[ARGS_VISUALIZE_B]:
        vis = Visualizer([f.path for f in u_files], 'ByteView', arg_parser.file_truncate)
        vis.visualize_files()
        return
    if u_args[ARGS_VISUALIZE_Z]:
        vis = Visualizer([f.path for f in u_files], 'ZOrderCurveView', arg_parser.file_truncate)
        vis.visualize_files()
        return
    if u_args[ARGS_VISUALIZE_H]:
        vis = Visualizer([f.path for f in u_files], 'HilbertCurveView', arg_parser.file_truncate)
        vis.visualize_files()
        return
    if u_args[ARGS_VISUALIZE_E]:
        vis = Visualizer([f.path for f in u_files], 'ShannonEntropy', arg_parser.file_truncate)
        vis.visualize_files()
        return
    if u_args[ARGS_VISUALIZE_D]:
        vis = Visualizer([f.path for f in u_files], 'DigraphDotPlotView', arg_parser.file_truncate)
        vis.visualize_files()
        return

    if u_args[ARGS_LESS]:
        for file in u_files:
            stepper = More()
            stepper.lazy_load_file(file.path, arg_parser.file_encoding,
                                   'ignore' if const_dic[DKW.IGNORE_UNKNOWN_BYTES] else 'replace')
            try:
                stepper.step_through(u_args[ARGS_STDIN])
            except SystemExit:
                break
        return

    file_size_sum = 0
    for file in u_files:
        file.set_file_size(get_file_size(file.path))
        file_size_sum += file.file_size
    if file_size_sum >= const_dic[DKW.LARGE_FILE_SIZE]:
        err_print(color_dic[CKW.MESSAGE_IMPORTANT], end='')
        err_print('An exceedingly large amount of data is being loaded. ', end='')
        err_print('This may require a lot of time and resources.', end='')
        err_print(color_dic[CKW.RESET_ALL])

    if u_args[ARGS_B64D]:
        decode_files_base64(tmp_file_helper)
    u_files.generate_values(
        u_args[ARGS_SUM] or u_args[ARGS_SSUM] or u_args[ARGS_NUMBER],
        u_args[ARGS_LLENGTH]
    )

    if u_args[ARGS_SSUM]:
        Summary.show_sum(u_files.files, u_args[ARGS_SSUM], u_files.all_files_lines,
                         u_files.all_line_number_place_holder)
        return
    if u_args[ARGS_WWORDCOUNT]:
        Summary.show_wordcount(u_files.files, arg_parser.file_encoding)
        return
    if u_args[ARGS_CCHARCOUNT]:
        Summary.show_charcount(u_files.files, arg_parser.file_encoding)
        return

    edit_files()  # print the cat-output


def cleanup(tmp_file_helper: TmpFileHelper) -> None:
    """
    clean up everything

    Parameters:
    tmp_file_helper (TmpFileHelper):
        the temporary file helper to clean up the files
    """
    if u_args[ARGS_DEBUG]:
        err_print(color_dic[CKW.MESSAGE_INFORMATION], end='')
        err_print('================================================ '
            'DEBUG ================================================')
        caches = [
            remove_ansi_codes_from_line,
            _calculate_line_prefix_spacing,
            _calculate_line_length_prefix_spacing,
            u_files._get_file_lines_sum_,
            u_files._calc_max_line_length_,
            Visualizer.get_color_byte_view,
            Visualizer.get_color_entropy,
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
        if u_args[ARGS_DEBUG]:
            err_print('Cleaning', tmp_file)
        try:
            os.remove(tmp_file)
        except OSError as exc:
            if u_args[ARGS_DEBUG]:
                err_print(type(exc).__name__, tmp_file)
    if u_args[ARGS_DEBUG]:
        err_print('==================================================='
            '====================================================', end='')
        err_print(color_dic[CKW.RESET_ALL])


def main():
    """
    main function
    """
    tmp_file_helper = TmpFileHelper()
    handle_args(tmp_file_helper)
    cleanup(tmp_file_helper)


def repl_main():
    """
    run the repl.
    """
    init(True)

    command_prefix = '!'
    repl_prefix = f"{color_dic[CKW.REPL_PREFIX]}>>> {color_dic[CKW.RESET_ALL]}"
    eof_control_char = 'Z' if on_windows_os else 'D'
    oneline = u_args[ARGS_ONELINE]
    repl_session_time_start = monotonic()

    class CmdExec:
        """
        handle repl commands.
        """
        def __init__(self) -> None:
            self.exit_repl = False
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
            check if a repl line is an executable command,
            executes it if it is.

            Parameters:
            cmd (str):
                the line entered in the cat repl

            Returns:
            (bool):
                indicates if a valid command has been found
                and executed
            """
            if not cmd.startswith(command_prefix):
                return False
            line_split = shlex.split(cmd[1:])
            self.last_cmd = line_split[0]
            method = getattr(self, '_command_' + self.last_cmd, self._command_unknown)
            method(line_split[1:])
            return True

        def _command_unknown(self, _) -> None:
            print("Command '!", self.last_cmd, "' is unknown.", sep='')
            print("If you want to escape the command input, type: '\\!",
                  self.last_cmd, "'.", sep='')

        def _command_cat(self, _) -> None:
            repl_session_time = monotonic()-repl_session_time_start
            hrs, mins, secs = (int(repl_session_time/3600),
                               int(repl_session_time%3600/60),
                               int(repl_session_time%60))
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
            u_args.add_args(arg_parser.get_args())
            show_unknown_args_suggestions(repl=True)
            self.exec_colors()
            _added= [arg for _, arg in arg_parser.get_args()] \
                if arg_parser.get_args() else 'parameter(s)'
            print(f"successfully added {_added}.")

        def _command_del(self, cmd: list) -> None:
            arg_parser.gen_arguments([''] + cmd, True)
            u_args.delete_args(arg_parser.get_args())
            self.exec_colors()
            _removed = [arg for _, arg in arg_parser.get_args()] \
                if arg_parser.get_args() else 'parameter(s)'
            print(f"successfully removed {_removed}.")

        def _command_clear(self, _) -> None:
            arg_parser.reset_values()
            self._command_del([arg for _, arg in u_args])

        def _command_see(self, _) -> None:
            print(f"{'Active Args:': <12} {[arg for _, arg in u_args]}")
            if arg_parser.file_queries:
                print(f"{'Queries:':<12}", ','.join(
                    ('str(' + ('CI' if c else 'CS') + '):' if isinstance(v, str) else '') + str(v)
                    for v, c in arg_parser.file_queries
                ))
            if arg_parser.file_queries_replacement:
                print(f"{'Replacement:':<12} {repr(arg_parser.file_queries_replacement)}")

        def _command_exit(self, _) -> None:
            self.exit_repl = True


    cmd = CmdExec()
    command_count = 0

    print(__project__, 'v' + __version__, 'REPL', '(' + __url__ + ')', end=' - ')
    print("Use 'catw' to handle files.")
    print("Type '!help' for more information.")

    print(repl_prefix, end='', flush=True)
    for i, line in enumerate(IoHelper.get_stdin_content(oneline)):
        stripped_line = line.rstrip('\r\n')
        if not os.isatty(sys.stdin.fileno()):
            print(stripped_line)
        if cmd.exec(stripped_line):
            command_count += 1
            if cmd.exit_repl:
                break
        else:
            if u_args[ARGS_B64D]:
                stripped_line = decode_base64(stripped_line, True, arg_parser.file_encoding)
            stripped_line = stripped_line[:1].replace('\\', '') + stripped_line[1:]
            if stripped_line:
                edit_content([('', stripped_line)], -1, i-command_count)
                if u_args[ARGS_CLIP]:
                    Clipboard.put(remove_ansi_codes_from_line(Clipboard.clipboard))
                    Clipboard.clear()
        if not oneline:
            print(repl_prefix, end='', flush=True)


if __name__ == '__main__':
    main()
