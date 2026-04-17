"""
contentpreccesor
"""

import sys

from cat_win.src.const.argconstants import (
    ARGS_CCHARCOUNT,
    ARGS_CHECKSUM,
    ARGS_DATA,
    ARGS_DDIRECTORIES,
    ARGS_DIFF,
    ARGS_DOTFILES,
    ARGS_ECHO,
    ARGS_EDITOR,
    ARGS_FFILES,
    ARGS_HEX_EDITOR,
    ARGS_LESS,
    ARGS_ONELINE,
    ARGS_PLAIN_ONLY,
    ARGS_RAW,
    ARGS_RECONFIGURE,
    ARGS_RECONFIGURE_ERR,
    ARGS_RECONFIGURE_IN,
    ARGS_RECONFIGURE_OUT,
    ARGS_SSUM,
    ARGS_STDIN,
    ARGS_URI,
    ARGS_VISUALIZE_B,
    ARGS_VISUALIZE_D,
    ARGS_VISUALIZE_E,
    ARGS_VISUALIZE_H,
    ARGS_VISUALIZE_Z,
    ARGS_WWORDCOUNT
)
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor
from cat_win.src.processor.registerwrapper import (
    PRE_CONTENT_ACTIONS,
    register_pre
)
from cat_win.src.service.checksum import print_checksum
from cat_win.src.service.fileattributes import print_meta
from cat_win.src.service.helper.iohelper import IoHelper
from cat_win.src.service.more import More
from cat_win.src.service.summary import Summary
from cat_win.src.service.visualizer import Visualizer
from cat_win.src.web.urls import read_url


def _materialize_echo(ctx, tmp_file_helper) -> None:
    temp_file = IoHelper.write_file(
        tmp_file_helper.generate_temp_file_name(),
        ctx.echo_args,
        ctx.arg_parser.file_encoding,
    )
    ctx.known_files.append(temp_file)
    ctx.u_files.set_temp_file_echo(temp_file)


def _materialize_urls(ctx, tmp_file_helper) -> None:
    temp_files = {
        IoHelper.write_file(
            tmp_file_helper.generate_temp_file_name(),
            read_url(valid_url),
            ctx.arg_parser.file_encoding,
        ): valid_url
        for valid_url in ctx.valid_urls
    }
    ctx.known_files.extend(list(temp_files.keys()))
    ctx.u_files.set_temp_files_url(temp_files)


def _materialize_stdin(ctx, tmp_file_helper) -> None:
    is_raw = ctx.u_args[ARGS_RAW]
    piped_input = (b'' if is_raw else '').join(
        IoHelper.get_stdin_content(ctx.u_args[ARGS_ONELINE], is_raw)
    )
    temp_file = IoHelper.write_file(
        tmp_file_helper.generate_temp_file_name(),
        piped_input,
        ctx.arg_parser.file_encoding,
    )
    ctx.known_files.append(temp_file)
    ctx.u_files.set_temp_file_stdin(temp_file)
    ctx.unknown_files = IoHelper.write_files(
        ctx.unknown_files,
        piped_input,
        ctx.arg_parser.file_encoding,
    )


def _reconfigure_stream(stream, encoding: str) -> None:
    if stream and hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding=encoding)


def _reconfigure_streams(ctx) -> None:
    handlers = {
        ARGS_RECONFIGURE: lambda: (
            _reconfigure_stream(sys.stdin, ctx.arg_parser.file_encoding),
            _reconfigure_stream(sys.stdout, ctx.arg_parser.file_encoding),
        ),
        ARGS_RECONFIGURE_IN: lambda: _reconfigure_stream(sys.stdin, ctx.arg_parser.file_encoding),
        ARGS_RECONFIGURE_OUT: lambda: _reconfigure_stream(sys.stdout, ctx.arg_parser.file_encoding),
        ARGS_RECONFIGURE_ERR: lambda: _reconfigure_stream(sys.stderr, ctx.arg_parser.file_encoding),
    }
    for arg_id, handler in handlers.items():
        if ctx.u_args[arg_id]:
            handler()


def _resolve_unknown_files(ctx) -> None:
    if ctx.u_args[ARGS_STDIN]:
        return
    editor_first = ctx.u_args.find_first(ARGS_EDITOR, ARGS_HEX_EDITOR, True)
    hex_editor_first = ctx.u_args.find_first(ARGS_HEX_EDITOR, ARGS_EDITOR, True)
    if editor_first is not None or hex_editor_first is not None:
        return
    ctx.unknown_files = IoHelper.read_write_files_from_stdin(
        ctx.unknown_files,
        ctx.arg_parser.file_encoding,
        ctx.u_args[ARGS_ONELINE],
    )


def preprocess_context(ctx) -> None:
    """
    Parse CLI input and store all derived runtime values into AppContext.

    Parameters:
    ctx (AppContext):
        The application context to populate with parsed arguments, known files,
        unknown files, and valid URLs. This function updates the context in-place
        based on the command-line inputs and configuration.
    """
    args, unknown_args, echo_args = ctx.arg_parser.get_arguments(
        ctx.config.get_cmd()
    )
    ctx.args = args
    ctx.unknown_args = unknown_args
    ctx.echo_args = echo_args

    ctx.u_args.set_args(args)
    ctx.known_files = ctx.arg_parser.get_files(ctx.u_args[ARGS_DOTFILES])
    ctx.unknown_files, ctx.valid_urls = ctx.arg_parser.filter_urls(ctx.u_args[ARGS_URI])
    ctx.known_dirs = ctx.arg_parser.get_dirs()
    _reconfigure_streams(ctx)


def materialize_context_sources(ctx, tmp_file_helper) -> None:
    """
    Create temporary files from active content-source arguments.

    Parameters:
    ctx (AppContext):
        The application context
    tmp_file_helper (TempFileHelper):
        Helper for generating temporary file names and managing temp files.
    """
    handlers = {
        ARGS_ECHO: _materialize_echo,
        ARGS_URI: _materialize_urls,
        ARGS_STDIN: _materialize_stdin,
    }
    for arg_id, handler in handlers.items():
        if ctx.u_args[arg_id]:
            handler(ctx, tmp_file_helper)

    _resolve_unknown_files(ctx)


@register_pre(ARGS_EDITOR, ARGS_HEX_EDITOR)
def _open_editors(ctx) -> bool:
    if ctx.u_args.find_first(ARGS_EDITOR, ARGS_HEX_EDITOR, True) is not None:
        if not ctx.u_args[ARGS_STDIN] and ctx.unknown_files:
            with IoHelper.dup_stdstreams():
                Editor.open(
                    [(f, ctx.u_files.get_file_display_name(f)) for f in ctx.unknown_files],
                    ctx.u_args[ARGS_PLAIN_ONLY],
                )
        if ctx.known_files:
            with IoHelper.dup_stdstreams():
                Editor.open(
                    [(f, ctx.u_files.get_file_display_name(f)) for f in ctx.known_files],
                    ctx.u_args[ARGS_PLAIN_ONLY],
                )
        return bool(ctx.unknown_files or ctx.known_files)
    if ctx.u_args.find_first(ARGS_HEX_EDITOR, ARGS_EDITOR, True) is not None:
        if not ctx.u_args[ARGS_STDIN] and ctx.unknown_files:
            with IoHelper.dup_stdstreams():
                HexEditor.open(
                    [(f, ctx.u_files.get_file_display_name(f)) for f in ctx.unknown_files]
                )
        if ctx.known_files:
            with IoHelper.dup_stdstreams():
                HexEditor.open(
                    [(f, ctx.u_files.get_file_display_name(f)) for f in ctx.known_files]
                )
        return bool(ctx.unknown_files or ctx.known_files)
    return False


@register_pre(ARGS_DIFF)
def _open_diff_view(ctx) -> bool:
    if not ctx.known_files:
        return False
    with IoHelper.dup_stdstreams():
        DiffViewer.open(
            [(f, ctx.u_files.get_file_display_name(f)) for f in ctx.known_files]
        )
    return True


@register_pre(ARGS_FFILES, ARGS_DDIRECTORIES)
def _show_files_only(ctx) -> bool:
    if ctx.u_args[ARGS_FFILES]:
        Summary.show_files(ctx.u_files.files, ctx.u_args[ARGS_FFILES])
    if ctx.u_args[ARGS_DDIRECTORIES]:
        Summary.show_dirs(ctx.known_dirs)
    return True


@register_pre(ARGS_DATA, ARGS_CHECKSUM)
def _show_meta_and_checksum(ctx) -> bool:
    for file in ctx.u_files:
        if ctx.u_args[ARGS_DATA]:
            print_meta(file.path, ctx.color_dic)
        if ctx.u_args[ARGS_CHECKSUM]:
            print_checksum(file.path, ctx.color_dic)
    return True


@register_pre(
        (ARGS_VISUALIZE_B, 'ByteView'),
        (ARGS_VISUALIZE_Z, 'ZOrderCurveView'),
        (ARGS_VISUALIZE_H, 'HilbertCurveView'),
        (ARGS_VISUALIZE_E, 'ShannonEntropy'),
        (ARGS_VISUALIZE_D, 'DigraphDotPlotView'),
)
def _visualize_files(view_name: str):
    def _run(ctx) -> bool:
        Visualizer(
            [f.path for f in ctx.u_files],
            view_name, ctx.arg_parser.file_truncate
        ).visualize_files()
        return True
    return _run


register_pre(ARGS_LESS)
def _page_files_lazily(ctx) -> bool:
    for file in ctx.u_files:
        stepper = More()
        stepper.lazy_load_file(
            file.path,
            ctx.arg_parser.file_encoding,
            'ignore' if ctx.const_dic[DKW.IGNORE_UNKNOWN_BYTES] else 'replace',
        )
        try:
            stepper.step_through()
        except SystemExit:
            break
    return True


@register_pre(ARGS_SSUM)
def _show_sum_only(ctx) -> bool:
    Summary.show_sum(
        ctx.u_files.files,
        ctx.u_args[ARGS_SSUM],
        ctx.u_files.all_files_lines,
        ctx.u_files.all_line_number_place_holder,
    )
    return True


@register_pre(ARGS_WWORDCOUNT)
def _show_wordcount_only(ctx) -> bool:
    Summary.show_wordcount(ctx.u_files.files, ctx.arg_parser.file_encoding)
    return True


@register_pre(ARGS_CCHARCOUNT)
def _show_charcount_only(ctx) -> bool:
    Summary.show_charcount(ctx.u_files.files, ctx.arg_parser.file_encoding)
    return True


def run_pre_content_actions(ctx) -> bool:
    """
    Run pre-content actions that short-circuit before file-content editing.

    Parameters:
    ctx (AppContext):
        The application context.

    Returns:
    handled (bool):
        True if any pre-content action was executed, False otherwise.
    """
    handled = False
    executed_handlers = set()
    for arg_id, _ in ctx.u_args:
        handler = PRE_CONTENT_ACTIONS.get(arg_id)
        if handler is None or handler in executed_handlers:
            continue
        executed_handlers.add(handler)
        handled = handler(ctx) or handled
    return handled
