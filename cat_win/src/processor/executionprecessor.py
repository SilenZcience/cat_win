"""
executionpreprocessor
"""
import os
import sys
from datetime import datetime
from itertools import groupby

from cat_win import (
    __author__,
    __project__,
    __sysversion__,
    __url__,
    __version__,
    __doc__
)
from cat_win.src.const.argconstants import (
    ALL_ARGS,
    ARGS_CCONFIG,
    ARGS_CCONFIG_FLUSH,
    ARGS_CONFIG,
    ARGS_CONFIG_FLUSH,
    ARGS_CONFIG_REMOVE,
    ARGS_COMPLETION,
    ARGS_DEBUG,
    ARGS_HELP,
    ARGS_MAN,
    ARGS_SUDO_ALLOW,
    ARGS_VERSION,
    SECTION_NAMES,
    VALUE_DESCRIPTIONS
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.escapecodes import (
    GRAPHIC_BOLD,
    GRAPHIC_ITALIC,
    GRAPHIC_RESET,
    GRAPHIC_UNDERLINE,
)
from cat_win.src.const.regex import RE_ANSI_CSI
from cat_win.src.installation.completion import show_completion
from cat_win.src.installation.manpage import show_man
from cat_win.src.installation.sudoshim import show_shim
from cat_win.src.processor.registerwrapper import (
    STARTUP_ACTIONS,
    register_startup
)
from cat_win.src.service.fileattributes import get_file_ctime
from cat_win.src.service.helper.iohelper import logger
from cat_win.src.service.more import More
from cat_win.src.service.querymanager import remove_ansi_codes_from_line
from cat_win.src.web.updatechecker import print_update_information


def _show_help(ctx, repl: bool = False) -> None:
    """
    Show the Help message and exit.

    Parameters:
    ctx (AppContext):
        The current invocation context, holding the active color dictionary.
    repl (bool):
        Whether the help message is for the REPL or not. Defaults to False.
    """
    COLUMN = 35

    colors = ctx.color_dic
    reset = colors[CKW.RESET_ALL] or GRAPHIC_RESET
    bold_cyan = GRAPHIC_BOLD + colors['cyan']
    italic_yellow = GRAPHIC_ITALIC + colors['yellow']

    def colored(text: str, style: str) -> str:
        return f"{style}{text}{reset}"

    def pad(text: str, width: int) -> str:
        return text + ' ' * max(0, width - len(remove_ansi_codes_from_line(text)))

    def fit(text: str, width: int) -> str:
        if len(remove_ansi_codes_from_line(text)) <= width:
            return text
        kept = []
        count = 0
        pos = 0
        while pos < len(text) and count < width-3:
            ansi = RE_ANSI_CSI.match(text, pos)
            if ansi:
                kept.append(ansi.group())
                pos = ansi.end()
                continue
            kept.append(text[pos])
            pos += 1
            count += 1
        # keep escape codes that immediately close the last copied style
        while pos < len(text):
            ansi = RE_ANSI_CSI.match(text, pos)
            if not ansi:
                break
            kept.append(ansi.group())
            pos = ansi.end()
        return ''.join(kept) + '...'

    help_message = colored(f"{__project__} v{__version__} -- {__doc__}", bold_cyan) + '\n'
    if repl:
        help_message += 'Interactively manipulate standard input.\n\n'
    else:
        help_message += 'concatenate, inspect, transform and explore FILE(s) from the terminal.\n\n'

    help_message += colored('Usage', bold_cyan) + '\n'
    if repl:
        help_message += (
            f"{GRAPHIC_UNDERLINE}{colored('cats', colors['green'])} "
            f"{colored('[OPTION]...', colors['magenta'])}\n\n"
        )
    else:
        help_message += (
            f"{GRAPHIC_UNDERLINE}{colored('catw', colors['green'])} "
            f"{colored('[FILE]...', colors['magenta'])} "
            f"{colored('[OPTION]...', colors['magenta'])}\n"
        )
        help_message += 'options may be combined with file arguments.\n\n'

    for section_id, group in groupby(ALL_ARGS, lambda arg: arg.section):
        if section_id < 0:
            continue

        entries = []
        values_taken = []
        for arg in group:
            if not arg.show_arg or (repl and not arg.show_arg_on_repl):
                continue

            # a '--' short form is itself a long-style option and gets the
            # metavar too, e.g. '--vis<CURVE>, --visualize<CURVE>'
            magenta = colors['magenta']
            name_parts = [(arg.short_form, italic_yellow)]
            if arg.takes_value:
                name_parts.append((f"[={arg.takes_value}]", magenta))
            if arg.metavar and (arg.short_form.startswith('--') or not arg.long_form):
                name_parts.append((f"<{arg.metavar}>", magenta))
            if arg.long_form:
                name_parts.append((f", {arg.long_form}", italic_yellow))
                if arg.takes_value:
                    name_parts.append((f"[={arg.takes_value}]", magenta))
                if arg.metavar:
                    name_parts.append((f"<{arg.metavar}>", magenta))
            # merge adjacent parts of the same style, so a plain run is colored
            # once and the yellow is restored after every magenta placeholder
            name = ''.join(
                colored(''.join(text for text, _ in part), style)
                for style, part in groupby(name_parts, key=lambda p: p[1])
            )
            name = fit(name, COLUMN - 2)
            if not name.endswith(reset):
                name += reset

            entries.append(f"\t{pad(name, COLUMN)}{arg.arg_help}\n")
            value_taken = arg.takes_value or arg.metavar
            if value_taken:
                values_taken.append(value_taken)

        if not entries:
            continue

        help_message += colored(SECTION_NAMES[section_id], bold_cyan) + '\n'
        help_message += ''.join(entries)
        for value_taken in values_taken:
            value_desc = ' '.join(map(str, VALUE_DESCRIPTIONS[value_taken]))
            help_message += f"\t{pad(colored(value_taken, colors['magenta']), COLUMN)}{value_desc}\n"
        help_message += '\n'

    help_message += '\n'
    help_message += colored('Examples', bold_cyan) + '\n'
    if repl:
        repl_examples = [
            'cats --ln --dec',
            '> >>> 12345',
            '1) [53] 12345 {Hexadecimal: 0x3039; Binary: 0b11000000111001}',
            '> >>> !help',
            '> ...',
        ]
        help_message += ''.join(f"\t{colored(line, colors['green'])}\n" for line in repl_examples)
    else:
        examples = [
            ('catw f g -r', "Output g's contents in reverse order, then f's content in reverse order"),
            ('catw f g -r -ne', 'Output f\'s, then g\'s content, while numerating and showing the end of lines'),
            ('catw f trunc=a:b:c', "Output f's content starting at line a, ending at line b, stepping c"),
        ]
        help_message += ''.join(
            f"\t{pad(colored(command, colors['green']), COLUMN)}{description}\n"
            for command, description in examples
        )
    help_message += '\n'
    help_message += colored('Documentation', bold_cyan) + '\n'
    help_message += f"\t{__url__}/blob/main/DOCUMENTATION.md"

    try:
        More(help_message.splitlines()).step_through()
    finally:
        print_update_information(__project__, __version__)


def _show_version(repl: bool = False) -> None:
    """
    Show the Version message and exit.

    Parameters:
    repl (bool):
        Whether to show REPL-specific version information. Defaults to False.
    """
    cat_version = f"{__project__} "
    if repl:
        cat_version += 'REPL '
    working_dir = os.path.abspath(
        os.path.join(
            os.path.realpath(__file__),
            os.pardir,
            os.pardir,
            os.pardir,
        )
    )
    cat_version += f"{__version__} - from {working_dir}\n"
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

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    unknown_args (list):
        A list of unknown arguments that were not parsed successfully.
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

@register_startup(ARGS_MAN)
def _show_man(ctx) -> None:
    raise SystemExit(show_man())

@register_startup(ARGS_COMPLETION)
def _show_completion(ctx) -> None:
    raise SystemExit(show_completion(ctx.u_args.find_arg_value(ARGS_COMPLETION)))

@register_startup(ARGS_SUDO_ALLOW)
def _show_sudoshim(ctx) -> None:
    raise SystemExit(show_shim(ctx.u_args.find_arg_value(ARGS_SUDO_ALLOW)))

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
    """
    Handle startup actions like help/version/config before the main pipeline.

    Parameters:
    ctx (AppContext).
        The current invocation context, containing parsed arguments and other state.
    repl (bool):
        Whether the current execution is in REPL mode or not.
    arg_suggestions (list):
        A list of argument suggestions for the user, used in debug output.
    """
    if ctx.u_args[ARGS_DEBUG]:
        _show_debug(ctx, arg_suggestions)

    if (
        len(ctx.known_files) + len(ctx.unknown_files) + len(ctx.u_args) == 0 and not repl
    ) or ctx.u_args[ARGS_HELP]:
        _show_help(ctx, repl)
        raise SystemExit(0)

    if ctx.u_args[ARGS_VERSION]:
        _show_version(repl)
        raise SystemExit(0)

    for arg_id, _ in ctx.u_args:
        handler = STARTUP_ACTIONS.get(arg_id)
        if handler is None:
            continue
        handler(ctx)
        raise SystemExit(0)
