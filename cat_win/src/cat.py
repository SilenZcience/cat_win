"""
cat
"""

try:
    from colorama import init as coloramaInit
except ImportError:
    nop = lambda *_, **__: None; coloramaInit = nop
from contextlib import contextmanager
import os
import sys

from cat_win.src.const.argconstants import (
    ALL_ARGS,
    ARGS_DEBUG,
    ARGS_DEBUG_LOG,
    ARGS_NOCOL,
    ARGS_WATCH,
    ARGS_STDIN,
    ARGS_B64D,
    ARGS_SUM,
    ARGS_SSUM,
    ARGS_NUMBER,
    ARGS_LLENGTH
)
from cat_win.src.const.colorconstants import CKW, CVis
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor
from cat_win.src.domain.appcontext import AppContext
from cat_win.src.processor.contentprecessor import (
    preprocess_context,
    materialize_context_sources,
    run_pre_content_actions,
)
from cat_win.src.processor.contentpostessor import finalize_context, run_post_content_actions
from cat_win.src.processor.executionprecessor import run_startup_actions
from cat_win.src.processor.fileprocessor import (
    decode_files_base64 as _fp_decode_files_base64,
    edit_files as _fp_edit_files,
)
from cat_win.src.service.converter import Converter
from cat_win.src.service.fileattributes import get_file_size, Signatures
from cat_win.src.service.more import More
from cat_win.src.service.summary import Summary
from cat_win.src.service.visualizer import Visualizer
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.iohelper import logger
from cat_win.src.service.helper.levenshtein import calculate_suggestions
from cat_win.src.service.helper.progressbar import PBar
from cat_win.src.service.helper.tmpfilehelper import TmpFileHelper
from cat_win.src import cats as repl_module
from cat_win import __url__


coloramaInit(strip=False)

_ctx = AppContext()



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
        logger(_ctx.color_dic.get(CKW.RESET_ALL, ''))
        if _ctx.u_args and _ctx.u_args[ARGS_DEBUG]:
            debug_hook(exception_type, exception, traceback)
            return
        logger(
            f"\n{exception_type.__name__}{':' * bool(str(exception))} {exception}",
            priority=logger.ERROR
        )
        if exception_type != KeyboardInterrupt:
            logger(
                'If this Exception is unexpected, please raise an official Issue at:',
                priority=logger.WARNING
            )
            logger(f"{__url__}/issues", priority=logger.WARNING)
        sys.exit(0)
    except BrokenPipeError: # we only used stderr in the try-block, so it has to be the broken pipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stderr.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE
    except (Exception, KeyboardInterrupt):
        debug_hook(exception_type, exception, traceback)
sys.excepthook = exception_handler




def show_unknown_args_suggestions(repl: bool = False) -> list:
    """
    Display unknown arguments and return Levenshtein-based suggestions.

    Parameters:
    repl (bool):
        True when invoked from the REPL entry point, which may filter which args to suggest.

    Returns:
    arg_suggestions (list):
        List of tuples containing unknown arguments and their suggested replacements.
    """
    if repl:
        arg_options = [
            (arg.short_form, arg.long_form)
            for arg in ALL_ARGS if arg.show_arg_on_repl and arg.arg_id >= 0
        ]
    else:
        arg_options = [(arg.short_form, arg.long_form) for arg in ALL_ARGS if arg.arg_id >= 0]
    arg_suggestions = calculate_suggestions(_ctx.arg_parser._unknown_args, arg_options)
    for u_arg, arg_replacement in arg_suggestions:
        logger(f"Unknown argument: '{u_arg}'", priority=logger.WARNING)
        if arg_replacement:
            arg_replacement = [arg_r[0] for arg_r in arg_replacement]
            logger(f"\tDid you mean {' or '.join(arg_replacement)}", priority=logger.WARNING)
    return arg_suggestions


def init_colors() -> None:
    """
    Set the active color dictionary based on output-mode flags.
    """
    if _ctx.u_args[ARGS_NOCOL] or sys.stdout.closed or \
        (not os.isatty(sys.stdout.fileno()) and _ctx.const_dic[DKW.STRIP_COLOR_ON_PIPE]):
        _ctx.color_dic = dict.fromkeys(_ctx.color_dic, '')
        CVis.remove_colors()
    else:
        _ctx.color_dic = _ctx.default_color_dic.copy()
    if _ctx.u_args[ARGS_NOCOL] or _ctx.u_args[ARGS_DEBUG_LOG] or sys.stderr.closed or \
        (not os.isatty(sys.stderr.fileno()) and _ctx.const_dic[DKW.STRIP_COLOR_ON_PIPE]):
        logger.clear_colors()
    else:
        logger.set_colors(_ctx.default_color_dic)


def init(repl: bool = False) -> None:
    """
    Parse arguments, configure subsystems, and handle early-exit flags.

    Parameters:
    repl (bool):
        True when invoked from the REPL entry point.
    """
    _ctx.init()

    preprocess_context(_ctx)

    logger.set_log_to_file(_ctx.u_args[ARGS_DEBUG_LOG])
    logger.set_level(logger.DEBUG if _ctx.u_args[ARGS_DEBUG] else logger.INFO)

    init_colors()

    arg_suggestions = show_unknown_args_suggestions(repl)

    run_startup_actions(
        _ctx,
        repl,
        arg_suggestions,
    )

    DiffViewer.set_flags(
        _ctx.u_args[ARGS_DEBUG],
        _ctx.u_args[ARGS_WATCH],
        _ctx.arg_parser.file_encoding,
    )
    Editor.set_indentation(
        _ctx.const_dic[DKW.EDITOR_INDENTATION],
        _ctx.const_dic[DKW.EDITOR_AUTO_INDENT],
    )
    Editor.set_flags(
        _ctx.u_args[ARGS_STDIN] and on_windows_os,
        _ctx.u_args[ARGS_DEBUG],
        _ctx.const_dic[DKW.UNICODE_ESCAPED_EDITOR_SEARCH],
        _ctx.const_dic[DKW.UNICODE_ESCAPED_EDITOR_REPLACE],
        _ctx.arg_parser.file_encoding,
    )
    HexEditor.set_flags(
        _ctx.u_args[ARGS_STDIN] and on_windows_os,
        _ctx.u_args[ARGS_DEBUG],
        _ctx.const_dic[DKW.UNICODE_ESCAPED_EDITOR_SEARCH],
        _ctx.const_dic[DKW.UNICODE_ESCAPED_EDITOR_INSERT],
        _ctx.const_dic[DKW.HEX_EDITOR_COLUMNS],
    )
    More.set_flags(
        _ctx.const_dic[DKW.MORE_STEP_LENGTH],
    )
    More.set_colors(_ctx.color_dic)
    Visualizer.set_flags(
        _ctx.u_args[ARGS_DEBUG],
    )
    Summary.set_flags(
        _ctx.const_dic[DKW.SUMMARY_UNIQUE_ELEMENTS],
    )
    Summary.set_colors(_ctx.color_dic)
    PBar.set_colors(_ctx.color_dic)
    Converter.set_flags(
        _ctx.u_args[ARGS_DEBUG],
    )
    Converter.set_colors(_ctx.color_dic)


def handle_args(tmp_file_helper: TmpFileHelper) -> None:
    """
    Parse args, build the file list, and trigger output.

    Parameters:
    tmp_file_helper (TmpFileHelper):
        manages temporary files created for stdin, echo, and URLs
    """
    init(repl=False)

    if len(sys.argv) == 2 and sys.argv[1] == 'fg': # TODO: this is weird, but proof-of-concept
        from cat_win.src.persistence.viewstate import load_view_state
        view_obj = load_view_state()
        if view_obj is None:
            return
        type(view_obj).open(view_obj.files, fg_state = view_obj)
        return

    materialize_context_sources(_ctx, tmp_file_helper)

    _ctx.u_files.set_files([*_ctx.known_files, *_ctx.unknown_files])

    file_size_sum = 0
    for file in _ctx.u_files:
        file.set_file_size(get_file_size(file.path))
        file_size_sum += file.file_size
    if file_size_sum >= _ctx.const_dic[DKW.LARGE_FILE_SIZE]:
        logger(
            'An exceedingly large amount of data is being loaded. ', end='',
            priority=logger.WARNING
        )
        logger('This may require a lot of time and resources.', priority=logger.WARNING)

    if _ctx.u_args[ARGS_B64D]:
        _fp_decode_files_base64(_ctx, tmp_file_helper)

    if len(_ctx.u_files):
        _ctx.u_files.generate_values(
            _ctx.u_args[ARGS_SUM] or _ctx.u_args[ARGS_SSUM] or _ctx.u_args[ARGS_NUMBER],
            _ctx.u_args[ARGS_LLENGTH],
        )

    if run_pre_content_actions(_ctx) or len(_ctx.u_files) == 0:
        return

    _fp_edit_files(_ctx)
    run_post_content_actions(_ctx)


@contextmanager
def managed_tmp_file_helper():
    """
    Create and clean up temporary files for one command execution.
    """
    tmp_file_helper = TmpFileHelper()
    try:
        yield tmp_file_helper
    finally:
        finalize_context(_ctx, tmp_file_helper)


def main() -> None:
    """
    Entry point for the catw command.
    """
    with managed_tmp_file_helper() as tmp_file_helper:
        handle_args(tmp_file_helper)


def repl_main() -> None:
    """
    Entry point for the REPL.
    """
    with managed_tmp_file_helper():
        init(repl=True)
        repl_module.repl_main(
            _ctx,
            init_colors,
            show_unknown_args_suggestions,
        )


if __name__ == '__main__':
    main()
