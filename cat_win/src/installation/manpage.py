"""
manpage
"""

import os

from cat_win.src.const.argconstants import ALL_ARGS, SECTION_NAMES,VALUE_DESCRIPTIONS
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.iohelper import logger
from cat_win import __author__, __url__, __version__, __doc__


MAN_DIR = os.path.join(os.path.expanduser('~'), '.local', 'share', 'man', 'man1')


def _roff_escape(text: str) -> str:
    """
    Escape a string for use inside roff man source.

    Parameters:
    text (str):
        the raw string

    Returns:
    (str):
        the escaped string
    """
    if text.startswith('-') or text.startswith('\'') or \
            text.startswith('[') or text.startswith('&'):
        return '\\&' + text
    return text


def build_man() -> str:
    """
    render the roff man page. one page covers both entry points.

    Returns:
    (str):
        the man page source
    """
    lines = f".TH CATW 1 \"2026-10-11\" \"v{__version__}\" \"User Commands\"\n" \
            '.SH NAME\n' \
            f"catw \\- concatenate, inspect, transform and explore FILE(s), STREAM(s) and URL(s)\n" \
            '.SH SYNOPSIS\n' \
            '.B catw [\\fIOPTION\\fR]... [\\fIFILE\\fR]...\n\n' \
            'options may be combined with file arguments.\n' \
            '.SH DESCRIPTION\n' \
            '\\fBcatw\\fR concatenates \\fIFILE\\fR(s), \\fISTREAM\\fR(s) and \\fIURL\\fR(s) to standard output and can transform, search, summarize and visually render their contents.\n' \
            '.PP\n' \
            '\\fBcats\\fR is the interactive counterpart. It takes the same Options, but the input is manipulated in a REPL instead of being printed. It ignores all \\fIFILE\\fR(s)/\\fIURL\\fR(s) and some off the \\fIFILE\\FR related Options.\n' \
            '.SH OPTIONS\n'

    current_section = None
    for arg in ALL_ARGS:
        # if not arg.takes_value and arg.short_form.startswith('-'):
        #     continue
        if arg.arg_id < 0 and arg.metavar:
            continue
        # if '[' in arg.short_form:
        #     continue
        if arg.section != current_section:
            current_section = arg.section
            lines += f".SS {SECTION_NAMES.get(arg.section, 'Other')}\n"

        forms = [arg.short_form]
        if arg.long_form and arg.long_form not in forms:
            forms.append(arg.long_form)
        if not forms:
            continue
        value_taken = f"={arg.takes_value}" if arg.takes_value else ''
        label = ', '.join(_roff_escape(f)+value_taken for f in forms)
        lines += f".TP\n.B {label}\n.br\n{arg.arg_help.capitalize()}.\n"
        if arg.takes_value:
            lines += f".br\n{arg.takes_value}: {VALUE_DESCRIPTIONS[arg.takes_value][0]} {VALUE_DESCRIPTIONS[arg.takes_value][1]}\n"
    lines += '\n'

    lines += '.SH EXIT STATUS\n' \
             '.TP\n' \
             '.B 0\n' \
             'Success, including when a requested action completed.\n' \
             '.TP\n' \
             '.B >= 1\n' \
             'A requested action failed.\n' \
             '.SH ENVIRONMENT\n' \
             '.TP\n' \
             '.B CAT_WIN_CONFIG_DIR\n' \
             'Overrides the configuration directory, taking precedence over ' \
             '\\fBXDG_CONFIG_HOME\\fR and the OS default.\n' \
             '.TP\n' \
             '.B XDG_CONFIG_HOME\n' \
             'Base directory for configuration files on unix systems.\n' \
             '.SH FILES\n' \
             '.TP\n' \
             '.I $XDG_CONFIG_HOME/cat_win\n' \
             'Configuration directory.\n' \
             '.TP\n' \
             '.I $XDG_CONFIG_HOME/cat_win/cat.config\n' \
             'Configuration file for cat_win containing all the set (color) configurations.\n' \
             '.TP\n' \
             '.I $XDG_CONFIG_HOME/cat_win/viewstate_obj.bin\n' \
             'File containing the view state of the most recent cat_win curses application in order to restore it later.\n' \
             '.SH NOTES\n' \
             'This man page is maintained only fitfully; the full documentation is often more up-to-date.\n'\
             '.SH COPYRIGHT\n' \
             '.RE\n' \
             'This is free software licensed under the MIT license.\n.br\n' \
             f".BR catw ({__url__}/blob/main/LICENSE)\n\n" \
             '.TP\n' \
             'See the source for copying conditions.\n.br\n' \
             '.RE\n' \
             'There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n'\
             '.SH SEE ALSO\n' \
             'Full Documentation\n' \
             '.RS 2\n' \
             'A complete documentation is available at\n.br\n' \
             f".BR catw ({__url__}/blob/main/DOCUMENTATION.md)\n\n" \
             '.RE\n' \
             'Full Changelog\n' \
             '.RS 2\n' \
             'A complete changelog is available at\n.br\n' \
             f".BR catw({__url__}/blob/main/CHANGELOG.md)\n\n" \
             '.RE\n' \
             '.SH AUTHOR\n' \
             f"{__author__}"

    return lines


def install_hint():
    """
    explain how to install the generated man page.

    Returns:
    (str):
        a block of ready-to-run commands
    """
    return f"to install the man page, run:\n" \
           f"  mkdir -p {MAN_DIR}\n" \
           f"  catw --man > {os.path.join(MAN_DIR, 'catw.1')}\n\n" \
           f"if 'man catw' does not work, the directory is not on the man search path.\n" \
           f"add it to MANPATH in your shell profile:\n" \
           f"  export MANPATH=\"{os.path.dirname(MAN_DIR)}:$MANPATH\"\n\n" \
           f"to remove it again, run:\n" \
           f"  rm -f {os.path.join(MAN_DIR, 'catw.1')}\n\n" \
           f"verify with:\n" \
           f"  man catw\n"

def show_man() -> int:
    """
    print the man page to stdout and its install commands to stderr.

    Returns:
    (int):
        process exit code -- 0 on success, 1 on failure
    """
    if on_windows_os:
        logger(
            'man pages are a unix feature; nothing to do on windows.',
            priority=logger.INFO
        )
        return 0

    print(build_man(), end='')
    logger(install_hint(), priority=logger.INFO)
    return 0
