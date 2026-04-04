"""
contentprocessor

Handles the per-line transformation pipeline and file-content editing.
All mutable state is received through an AppContext so this module has no
module-level side effects and does not import cat.py.
"""

from datetime import datetime
import os
import sys

from cat_win.src.const.argconstants import (
    ARGS_B64E,
    ARGS_BLANK,
    ARGS_CHR,
    ARGS_CLIP,
    ARGS_CUT,
    ARGS_DEC,
    ARGS_ENDS,
    ARGS_EOL,
    ARGS_EVAL,
    ARGS_FILE_PREFIX,
    ARGS_FFILE_PREFIX,
    ARGS_HEX,
    ARGS_LLENGTH,
    ARGS_MORE,
    ARGS_NUMBER,
    ARGS_OCT,
    ARGS_BIN,
    ARGS_PEEK,
    ARGS_REPLACE,
    ARGS_REVERSE,
    ARGS_SORT,
    ARGS_SPECIFIC_FORMATS,
    ARGS_SQUEEZE,
    ARGS_SSORT,
    ARGS_STDIN,
    ARGS_STRINGS,
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.processor.lineprefixprocessor import (
    get_file_prefix,
    get_line_length_prefix,
    get_line_prefix,
)
from cat_win.src.processor.outputprocessor import print_file
from cat_win.src.processor.registerwrapper import PRO_CONTENT_ACTIONS, register_pro
from cat_win.src.service.cbase64 import encode_base64
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.fileattributes import get_file_mtime
from cat_win.src.service.formatter import Formatter
from cat_win.src.service.more import More
from cat_win.src.service.querymanager import (
    remove_ansi_codes_from_line,
    replace_queries_in_line,
    _map_display_pos,
    _build_ansi_restore
)
from cat_win.src.service.rawviewer import SPECIAL_CHARS
from cat_win.src.service.strings import get_strings
from cat_win.src.service.helper.iohelper import logger
try:
    from cat_win.src.service.helper.utility import comp_eval, comp_conv
except SyntaxError:
    from cat_win.src.service.helper.utilityold import comp_eval, comp_conv


def _ansi_aware_slice_line(param: tuple, reset_all: str):
    """Create a line-slicer that cuts by plain-text positions and preserves ANSI state."""
    slice_obj = slice(*param)

    def _slice_line(line: str) -> str: # TODO: what about negative step in slice?
        plain_line = remove_ansi_codes_from_line(line)
        start, stop, step = slice_obj.indices(len(plain_line))
        selected_positions = list(range(start, stop, step))
        if not selected_positions:
            return ''

        ansi_restore, _ = _build_ansi_restore(reset_all, line)

        # Handles all slice steps (including step=1) without leaking ANSI state
        # from skipped plain-text positions.
        parts = []
        previous_state = None

        for plain_pos in selected_positions:
            active_state = ansi_restore.get(plain_pos, '')
            if active_state != previous_state:
                if active_state:
                    parts.append(active_state)
                elif previous_state:
                    parts.append(reset_all)
                previous_state = active_state

            display_start = _map_display_pos(line, plain_pos)
            parts.append(line[display_start])

        tail_state = ansi_restore.get(selected_positions[-1] + 1, '')
        if tail_state:
            parts.append(reset_all)

        return ''.join(parts)

    return _slice_line


@register_pro(ARGS_CUT)
def _apply_cut(param: tuple, ctx) -> None:
    """Slice each line (prefix unchanged). Operates in-place on ctx.content."""
    slice_line = _ansi_aware_slice_line(param, ctx.color_dic[CKW.RESET_ALL])
    ctx.content.lines[:] = [
        slice_line(line) for line in ctx.content.lines
    ]


@register_pro(ARGS_ENDS)
def _apply_ends(_param, ctx) -> None:
    """Append end marker to each suffix. Operates in-place on ctx.content."""
    emarker = (
        ctx.color_dic[CKW.ENDS]
        + ctx.const_dic[DKW.END_MARKER_SYMBOL]
        + ctx.color_dic[CKW.RESET_ALL]
    )
    ctx.content.suffixes[:] = [suffix + emarker for suffix in ctx.content.suffixes]



@register_pro(ARGS_CHR)
def _apply_chr(_param, ctx) -> None:
    """Replace special characters with visual markers. Operates in-place on ctx.content."""
    for c_id, char, _, possible in SPECIAL_CHARS:
        if not possible:
            continue
        marker = f"{ctx.color_dic[CKW.CHARS]}^{char}{ctx.color_dic[CKW.RESET_ALL]}"
        ctx.content.lines[:] = [
            line.replace(chr(c_id), marker) for line in ctx.content.lines
        ]


@register_pro(ARGS_SQUEEZE)
def _apply_squeeze(_param, ctx) -> None:
    """Collapse consecutive duplicate lines and annotate run-count in suffix."""
    new_lines = []
    new_prefixes = []
    new_suffixes = []
    dup_counter = []

    for line, prefix, suffix in ctx.content:
        if not new_lines or new_lines[-1] != line:
            new_lines.append(line)
            new_prefixes.append(prefix)
            new_suffixes.append(suffix)
            dup_counter.append(0)
            continue
        dup_counter[-1] += 1

    ctx.content.lines[:] = new_lines
    ctx.content.prefixes[:] = new_prefixes
    if ctx.const_dic[DKW.SQUEEZE_COLLAPSE_SUFFIXES]:
        ctx.content.suffixes[:] = [
            suffix + (
                f" {ctx.color_dic[CKW.SQUEEZE]}[x{count+1}]{ctx.color_dic[CKW.RESET_ALL]}"
            ) * bool(count)
            for suffix, count in zip(new_suffixes, dup_counter)
        ]
    else:
        ctx.content.suffixes[:] = new_suffixes


@register_pro(ARGS_REVERSE)
def _apply_reverse(_param, ctx) -> None:
    """Reverse content. Operates in-place on ctx.content."""
    ctx.content.reverse()


@register_pro(ARGS_SORT)
def _apply_sort_alpha(_param, ctx) -> None:
    """Sort lines alphabetically. Operates in-place on ctx.content."""
    ctx.content.sort(key=lambda l: l[0].casefold())


@register_pro(ARGS_SSORT)
def _apply_sort_length(_param, ctx) -> None:
    """Sort lines by length. Operates in-place on ctx.content."""
    ctx.content.sort(key=lambda l: len(l[0]))


@register_pro(ARGS_BLANK)
def _apply_blank(_param, ctx) -> None:
    """Remove blank lines. Operates in-place on ctx.content."""
    strip_obj = None if ctx.const_dic[DKW.BLANK_REMOVE_WS_LINES] else ''
    ctx.content.filter(
        lambda line, _, __: line.strip(strip_obj)
    )


@register_pro(ARGS_EVAL)
def _apply_eval(param: str, ctx) -> None:
    """Evaluate lines. Modifies ctx.content in-place."""
    ctx.content = comp_eval(ctx.content, param, remove_ansi_codes_from_line)


@register_pro(ARGS_HEX, ARGS_DEC, ARGS_OCT, ARGS_BIN)
def _apply_convert(param: str, ctx) -> None:
    """Convert lines. Modifies ctx.content in-place."""
    ctx.content = comp_conv(ctx.content, param, remove_ansi_codes_from_line)


@register_pro(ARGS_REPLACE)
def _apply_replace(param: tuple, ctx) -> None:
    """Replace text in lines. Operates in-place on ctx.content."""
    replace_this, replace_with = param
    ctx.content.lines[:] = [
        replace_queries_in_line(
            line,
            [(replace_this, False)],
            [replace_with],
            ctx.color_dic
        )[0] for line in ctx.content.lines
    ]


def _apply_eol_suffixes(ctx) -> None:
    """Build ContentBuffer rows as (line, prefix, suffix) with EOL markers in suffix."""
    ctx.content.suffixes[:] = [
        ctx.color_dic[CKW.CHARS] + (
            '<CRLF>' if line.endswith('\r\n') else
            '<LF>'   if line.endswith('\n') else
            '<CR>'   if line.endswith('\r') else
            '<EOF-noeol>'
        ) + ctx.color_dic[CKW.RESET_ALL]
        for line in ctx.content.lines
    ]
    ctx.content.lines[:] = [
        line.rstrip('\n\r') for line in ctx.content.lines
    ]


def edit_raw_content(raw_content: bytes, file_index: int, ctx) -> None:
    """Write raw binary content, honouring --strings and --b64e."""
    if ctx.u_args[ARGS_STRINGS]:
        ctx.content = ContentBuffer.from_lines([raw_content])
        edit_content(file_index, 0, ctx)
        return
    if ctx.u_args[ARGS_B64E]:
        encoded = encode_base64(raw_content, True)
        if ctx.u_args[ARGS_CLIP]:
            Clipboard.clipboard += encoded
        print(encoded)
        return
    sys.stdout.buffer.write(raw_content)


def edit_content(file_index: int, line_offset: int, ctx) -> None:
    """
    Apply all active transformation parameters to ctx.content and print it.

    Parameters:
    file_index (int):
        index into ctx.u_files; negative values indicate the REPL
    line_offset (int):
        line-number offset when running in REPL mode
    ctx (AppContext):
        the current invocation context (ctx.content must be pre-populated)
    """
    if not (
        ctx.content or
        os.isatty(sys.stdout.fileno()) or
        file_index < 0 or
        ctx.u_files.is_temp_file(file_index)
    ):
        # if the content of the file is empty, we check if maybe the file is its own pipe-target.
        # in this case the stdout cannot be atty.
        # also the repl would not produce this problem.
        # also the temp-files (stdin, echo, url, ...) are (most likely) safe.
        # an indicator would be if the file has just been modified to be empty (by the shell).
        # checking if the file is an _unknown_file is not valid, because by using '--stdin'
        # the stdin will be used to write the file
        file_mtime = get_file_mtime(ctx.u_files[file_index].path)
        if abs(datetime.timestamp(datetime.now()) - file_mtime) < 0.5:
            logger(
                'Warning: It looks like you are trying to pipe a file into itself.',
                priority=logger.WARNING
            )
            logger('In this case you might have lost all data.', priority=logger.WARNING)
        return


    if ctx.u_args[ARGS_STRINGS]:
        ctx.content = get_strings(
            ctx.content,
            ctx.const_dic[DKW.STRINGS_MIN_SEQUENCE_LENGTH],
            ctx.const_dic[DKW.STRINGS_DELIMETER],
        )
    elif ctx.u_args[ARGS_EOL]:
        _apply_eol_suffixes(ctx)

    if ctx.u_args[ARGS_SPECIFIC_FORMATS]:
        ctx.content = Formatter.format(ctx.content)

    if ctx.u_args[ARGS_NUMBER]:
        ctx.content.prefixes[:] = [
            get_line_prefix(ctx, i, file_index + 1) for i in range(
                1 + line_offset,
                len(ctx.content) + 1 + line_offset
            )
        ]

    start, stop, step = ctx.arg_parser.file_truncate
    if start is not None or stop is not None or step is not None:
        slice_obj = slice(start, stop, step)
        ctx.content = ctx.content[slice_obj]

    excluded_by_peek = 0
    if ctx.u_args[ARGS_PEEK] and len(ctx.content) > 2 * ctx.const_dic[DKW.PEEK_SIZE]:
        excluded_by_peek = len(ctx.content) - 2 * ctx.const_dic[DKW.PEEK_SIZE]
        peek_size = ctx.const_dic[DKW.PEEK_SIZE]
        ctx.content = ctx.content[:peek_size] + ctx.content[-peek_size:]

    for arg, param in ctx.u_args:
        handler = PRO_CONTENT_ACTIONS.get(arg)
        if handler is not None:
            handler(param, ctx)

    if ctx.u_args[ARGS_LLENGTH]:
        ctx.content.prefixes[:] = [
            get_line_length_prefix(ctx, prefix, line) for line, prefix, _ in ctx.content
        ]

    if ctx.u_args[ARGS_FILE_PREFIX]:
        ctx.content.prefixes[:] = [
            get_file_prefix(ctx, prefix, file_index) for prefix in ctx.content.prefixes
        ]
    elif ctx.u_args[ARGS_FFILE_PREFIX]:
        ctx.content.prefixes[:] = [
            get_file_prefix(ctx, prefix, file_index, hyper=True) for prefix in ctx.content.prefixes
        ]

    if ctx.u_args[ARGS_B64E]:
        encoded = encode_base64(
            '\n'.join(prefix + line + suffix for line, prefix, suffix in ctx.content),
            True,
            ctx.arg_parser.file_encoding,
        )
        ctx.content = ContentBuffer.from_lines([encoded])

    stepper = More()
    found_queried = print_file(ctx, stepper, excluded_by_peek)
    if file_index >= 0:
        ctx.u_files[file_index].set_contains_queried(found_queried)

    if ctx.u_args[ARGS_MORE]:
        stepper.step_through()

    if ctx.u_args[ARGS_CLIP]:
        Clipboard.clipboard += '\n'.join(
            prefix + line + suffix for line, prefix, suffix in ctx.content
        )
