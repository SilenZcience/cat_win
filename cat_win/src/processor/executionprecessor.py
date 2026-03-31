"""
executionpreprocessor

Handles startup and control arguments that short-circuit normal execution
before the content pipeline begins.
"""
from datetime import datetime
from itertools import groupby
import os
import sys

from cat_win.src.const.argconstants import (
    ARGS_CCONFIG,
    ARGS_CCONFIG_FLUSH,
    ARGS_CONFIG,
    ARGS_CONFIG_FLUSH,
    ARGS_CONFIG_REMOVE,
    ARGS_HELP,
    ARGS_VERSION,
    ARGS_DEBUG,
    ALL_ARGS
)
from cat_win.src.processor.registerwrapper import STARTUP_ACTIONS, register_startup
from cat_win.src.service.fileattributes import get_file_ctime
from cat_win.src.service.more import More
from cat_win.src.service.helper.iohelper import logger
from cat_win.src.web.updatechecker import print_update_information
from cat_win import __project__, __version__, __sysversion__, __author__, __url__


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
        print_update_information(__project__, __version__)


def _show_version(ctx, repl: bool = False) -> None:
    """
    Show the Version message and exit.
    """
    cat_version = f"{__project__} "
    if repl:
        cat_version += 'REPL '
    cat_version += f"{__version__} - from {ctx.working_dir}\n"
    version_message = '\n'
    version_message += '-' * len(cat_version) + '\n'
    version_message += cat_version
    version_message += '-' * len(cat_version) + '\n'
    version_message += '\n'
    version_message += f"Built with: \tPython {__sysversion__}\n"  # sys.version
    try:
        time_stamp = datetime.fromtimestamp(get_file_ctime(os.path.realpath(__file__)))
        version_message += f"Install time: \t{time_stamp}\n"
    except OSError: # fails on pyinstaller executable
        version_message += 'Install time: \t-\n'
    version_message += f"Author: \t{__author__}\n"
    print(version_message)
    print_update_information(__project__, __version__)


def _show_debug(ctx, unknown_args: list) -> None:
    """
    Print all necessary debug information.
    """
    logger('================================================ '
        'DEBUG ================================================', priority=logger.DEBUG)
    logger('sys_args:', sys.argv, priority=logger.DEBUG)
    logger('args: ', end='', priority=logger.DEBUG)
    logger(
        [(arg[0], arg[1], ctx.u_args[arg[0]]) for arg in ctx.u_args.args],
        priority=logger.DEBUG
    )
    logger('unknown_args: ', end='', priority=logger.DEBUG)
    logger(unknown_args, priority=logger.DEBUG)
    logger('known_files: ', end='', priority=logger.DEBUG)
    logger(list(map(str, ctx.known_files)), priority=logger.DEBUG)
    logger('unknown_files: ', end='', priority=logger.DEBUG)
    logger(list(map(str, ctx.unknown_files)), priority=logger.DEBUG)
    logger('echo_args: ', end='', priority=logger.DEBUG)
    logger(repr(ctx.echo_args), priority=logger.DEBUG)
    logger('known_directories: ', end='', priority=logger.DEBUG)
    logger(list(map(str, ctx.known_dirs)), priority=logger.DEBUG)
    logger('valid_urls: ', end='', priority=logger.DEBUG)
    logger(ctx.valid_urls, priority=logger.DEBUG)
    logger('file encoding: ', end='', priority=logger.DEBUG)
    logger(ctx.arg_parser.file_encoding, priority=logger.DEBUG)
    logger('search queries: ', end='', priority=logger.DEBUG)
    logger(','.join(
        ('str(' + ('CI' if c else 'CS') + '):' if isinstance(v, str) else '') + str(v)
        for v, c in ctx.arg_parser.file_queries
    ), priority=logger.DEBUG)
    logger('replace queries: ', end='', priority=logger.DEBUG)
    logger(repr(ctx.arg_parser.file_queries_replacement), priority=logger.DEBUG)
    logger('truncate file: ', end='', priority=logger.DEBUG)
    logger(ctx.arg_parser.file_truncate, priority=logger.DEBUG)
    logger('==================================================='
              '====================================================', priority=logger.DEBUG)

@register_startup(ARGS_CONFIG_REMOVE)
def _remove_config(ctx) -> None:
    ctx.config.remove_config()

@register_startup(ARGS_CONFIG_FLUSH)
def _reset_config(ctx) -> None:
    ctx.config.reset_config()

@register_startup(ARGS_CCONFIG_FLUSH)
def _reset_color_config(ctx) -> None:
    ctx.cconfig.reset_config()

@register_startup(ARGS_CONFIG)
def _save_config(ctx) -> None:
    ctx.config.save_config()

@register_startup(ARGS_CCONFIG)
def _save_color_config(ctx) -> None:
    ctx.cconfig.save_config()


def run_startup_actions(
        ctx, repl: bool, arg_suggestions: list
) -> None:
    """Handle startup actions like help/version/config before the main pipeline."""
    if ctx.u_args[ARGS_DEBUG]:
        _show_debug(ctx, arg_suggestions)

    if (
        len(ctx.known_files) + len(ctx.unknown_files) + len(ctx.u_args) == 0 and not repl
    ) or ctx.u_args[ARGS_HELP]:
        _show_help(repl)
        raise SystemExit(0)

    if ctx.u_args[ARGS_VERSION]:
        _show_version(ctx, repl)
        raise SystemExit(0)

    for arg_id, _ in ctx.u_args:
        handler = STARTUP_ACTIONS.get(arg_id)
        if handler is None:
            continue
        handler(ctx)
        raise SystemExit(0)
