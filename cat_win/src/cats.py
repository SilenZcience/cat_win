"""
repl
"""

import os
import shlex
import sys
from time import monotonic

from cat_win import __project__, __url__, __version__
from cat_win.src.const.argconstants import ARGS_B64D, ARGS_CLIP, ARGS_ONELINE
from cat_win.src.const.colorconstants import CKW
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.processor.contentprocessor import edit_content
from cat_win.src.processor.lineprefixprocessor import (
    _calculate_line_length_prefix_spacing,
    _calculate_line_prefix_spacing
)
from cat_win.src.service.cbase64 import decode_base64
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.iohelper import IoHelper
from cat_win.src.service.querymanager import remove_ansi_codes_from_line


class ReplCommandHandler:
    """
    Handle !-prefixed commands inside the cats REPL.
    """

    def __init__(self, ctx, refresh_colors, show_unknown_args) -> None:
        self._session_start = monotonic()
        self._u_args = ctx.u_args
        self._arg_parser = ctx.arg_parser
        self._refresh_colors = refresh_colors
        self._show_unknown_args = show_unknown_args
        self.last_cmd = ''
        self.exit_repl = False

    def exec(self, cmd: str) -> bool:
        """
        Check whether cmd is a REPL command and execute it if so.

        Parameters:
        cmd (str):
            The command to check and execute.

        Returns:
        (bool):
            True if cmd was a REPL command and was executed, False otherwise.
        """
        if not cmd.startswith('!'):
            return False
        line_split = shlex.split(cmd[1:])
        self.last_cmd = line_split[0]
        method = getattr(self, '_command_' + self.last_cmd, self._command_unknown)
        method(line_split[1:])
        return True

    def _command_unknown(self, _) -> None:
        print(f"Command '!{self.last_cmd}' is unknown.")
        print(f"If you want to escape the command input, type: '\\!{self.last_cmd}'.")

    def _command_cat(self, _) -> None:
        elapsed = monotonic() - self._session_start
        hrs = int(elapsed / 3600)
        mins = int(elapsed % 3600 / 60)
        secs = int(elapsed % 60)
        art = " ,_     _\n |\\\\_,-~/\n / _  _ |    ,--.\n(  @  @ )   / ,-'\n \\  _T_/"
        art += "-._( (\n /         `. \\\n|         _  \\ |\n \\ \\ ,  /      |\n  || "
        art += f"|-_\\__   /\n ((_/`(____,-' Session time: {hrs:02d}:{mins:02d}:{secs:02d}s\a\n"
        print('\n'.join('\t\t\t' + c for c in art.split('\n')))

    def _command_help(self, _) -> None:
        _eof_char = 'Z' if on_windows_os else 'D'
        print(f"Type ^{_eof_char} (Ctrl + {_eof_char}) or '!exit' to exit.")
        print("Type '!add <OPTION>', '!del <OPTION>' to add/remove a specific parameter.")
        print("Type '!see', '!clear' to see/remove all active parameters.")
        print("Put a '\\' before a leading '!' to escape the command-input.")

    def _command_add(self, cmd: list) -> None:
        self._arg_parser.gen_arguments([''] + cmd)
        self._u_args.add_args(self._arg_parser.get_args())
        self._show_unknown_args()
        self._refresh_colors()
        added = [
            arg for _, arg in self._arg_parser.get_args()
        ] if self._arg_parser.get_args() else 'parameter(s)'
        print(f"successfully added {added}.")

    def _command_del(self, cmd: list) -> None:
        self._arg_parser.gen_arguments([''] + cmd, True)
        self._u_args.delete_args(self._arg_parser.get_args())
        self._refresh_colors()
        removed = [
            arg for _, arg in self._arg_parser.get_args()
        ] if self._arg_parser.get_args() else 'parameter(s)'
        print(f"successfully removed {removed}.")

    def _command_clear(self, _) -> None:
        self._arg_parser.reset_values()
        self._command_del([arg for _, arg in self._u_args])

    def _command_see(self, _) -> None:
        print(f"{'Active Args:': <12} {[arg for _, arg in self._u_args]}")
        if self._arg_parser.file_queries:
            print(f"{'Queries:':<12}", ','.join(
                ('str(' + ('CI' if c else 'CS') + '):' if isinstance(v, str) else '') + str(v)
                for v, c in self._arg_parser.file_queries
            ))
        if self._arg_parser.file_queries_replacement:
            print(f"{'Replacement:':<12} {repr(self._arg_parser.file_queries_replacement)}")

    def _command_exit(self, _) -> None:
        self.exit_repl = True


def repl_main(ctx, init_colors, show_unknown_args) -> None:
    """
    Run the cats REPL.

    Parameters:
    ctx (AppContext):
        The application context.
    init_colors (function):
        Function to initialize the REPL colors.
    show_unknown_args (function):
        Function to show the currently active unknown arguments.
    """
    repl_prefix = f"{ctx.color_dic[CKW.REPL_PREFIX]}>>> {ctx.color_dic[CKW.RESET_ALL]}"
    oneline = ctx.u_args[ARGS_ONELINE]

    def _refresh_repl_colors() -> None:
        init_colors()
        _calculate_line_prefix_spacing.cache_clear()
        _calculate_line_length_prefix_spacing.cache_clear()

    cmd = ReplCommandHandler(
        ctx=ctx,
        refresh_colors=_refresh_repl_colors,
        show_unknown_args=lambda: show_unknown_args(repl=True),
    )
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
            if ctx.u_args[ARGS_B64D]:
                stripped_line = decode_base64(stripped_line, True, ctx.arg_parser.file_encoding)
            stripped_line = stripped_line[:1].replace('\\', '') + stripped_line[1:]
            if stripped_line:
                ctx.content = ContentBuffer.from_lines([stripped_line])
                edit_content(ctx, -1, i - command_count)
                if ctx.u_args[ARGS_CLIP]:
                    Clipboard.put(remove_ansi_codes_from_line(Clipboard.clipboard))
                    Clipboard.clear()
        if not oneline:
            print(repl_prefix, end='', flush=True)
