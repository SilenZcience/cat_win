"""
fileprocessor
"""

import os
import sys
from time import sleep

from cat_win.src.const.argconstants import (
    ARGS_BINVIEW,
    ARGS_DIFF,
    ARGS_EOL,
    ARGS_HEXVIEW,
    ARGS_PLAIN_ONLY,
    ARGS_RAW,
    ARGS_REVERSE,
    ARGS_WATCH
)
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.processor.contentprocessor import (
    edit_content,
    edit_raw_content
)
from cat_win.src.processor.outputprocessor import print_raw_view
from cat_win.src.service.cbase64 import decode_base64
from cat_win.src.service.fileattributes import _convert_size, get_file_mtime
from cat_win.src.service.helper.archiveviewer import display_archive
from cat_win.src.service.helper.iohelper import IoHelper, logger
from cat_win.src.service.querymanager import remove_ansi_codes_from_line


def edit_file(ctx, file_index: int) -> None:
    """
    Read and process one file, dispatching to the appropriate processor.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    file_index (int):
        The index of the file in ctx.u_files to process.
    """
    if ctx.u_args[ARGS_RAW]:
        raw_content = IoHelper.read_file(ctx.u_files[file_index].path, True)
        edit_raw_content(ctx, raw_content, file_index)
        return

    file_size = -1 if (
        ctx.u_files[file_index].file_size < ctx.const_dic[DKW.LARGE_FILE_SIZE]
    ) else ctx.u_files[file_index].file_size

    try:
        file_content = IoHelper.read_file(
            ctx.u_files[file_index].path,
            file_encoding=ctx.arg_parser.file_encoding,
            file_length=file_size,
        )
        if not os.isatty(sys.stdout.fileno()) and ctx.const_dic[DKW.STRIP_COLOR_ON_PIPE]:
            file_content = remove_ansi_codes_from_line(file_content)
        ctx.content = ContentBuffer.from_lines(
            file_content.splitlines(keepends=ctx.u_args[ARGS_EOL])
        )
    except PermissionError:
        logger(
            f"Permission denied! Skipping {ctx.u_files[file_index].displayname} ...",
            priority=logger.ERROR,
        )
        return
    except (BlockingIOError, FileNotFoundError):
        logger(
            f"Resource blocked/unavailable! Skipping {ctx.u_files[file_index].displayname} ...",
            priority=logger.ERROR,
        )
        return
    except (OSError, UnicodeError):
        ctx.u_files[file_index].set_plaintext(plain=False)
        if ctx.u_args[ARGS_PLAIN_ONLY]:
            return
        if display_archive(ctx.u_files[file_index].path, _convert_size):
            return
        try:
            file_content = IoHelper.read_file(
                ctx.u_files[file_index].path,
                file_encoding=ctx.arg_parser.file_encoding,
                errors='ignore' if ctx.const_dic[DKW.IGNORE_UNKNOWN_BYTES] else 'replace',
                file_length=file_size,
            )
            if not os.isatty(sys.stdout.fileno()) and ctx.const_dic[DKW.STRIP_COLOR_ON_PIPE]:
                file_content = remove_ansi_codes_from_line(file_content)
            ctx.content = ContentBuffer.from_lines(
                file_content.splitlines(keepends=ctx.u_args[ARGS_EOL])
            )
        except OSError:
            logger('Operation failed! Try using the enc=X parameter.', priority=logger.ERROR)
            return

    edit_content(ctx, file_index, 0)


def decode_files_base64(ctx, tmp_file_helper) -> None:
    """
    Decode every file in ctx.u_files from base64 into a temporary file.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    tmp_file_helper (TempFileHelper):
        A helper for generating temporary file paths.
    """
    for i, file in enumerate(ctx.u_files):
        try:
            tmp_file_path = tmp_file_helper.generate_temp_file_name()
            f_read_content = IoHelper.read_file(
                file.path,
                file_encoding=ctx.arg_parser.file_encoding,
                errors='replace',
            )
            if ctx.u_args[ARGS_RAW]:
                IoHelper.write_file(tmp_file_path, decode_base64(f_read_content))
            else:
                IoHelper.write_file(
                    tmp_file_path,
                    decode_base64(f_read_content, True, ctx.arg_parser.file_encoding),
                    ctx.arg_parser.file_encoding,
                )
            ctx.u_files[i].path = tmp_file_path
        except (OSError, UnicodeError):
            logger(
                f"Base64 decoding failed for file: {file.displayname}",
                priority=logger.ERROR,
            )


def edit_files(ctx) -> None:
    """
    Iterate over all files in ctx.u_files and process each one.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    """
    start = len(ctx.u_files) - 1 if ctx.u_args[ARGS_REVERSE] else 0
    end = -1 if ctx.u_args[ARGS_REVERSE] else len(ctx.u_files)
    step = -1 if ctx.u_args[ARGS_REVERSE] else 1

    raw_view_mode = ctx.u_args.find_first(ARGS_HEXVIEW, ARGS_BINVIEW)
    if raw_view_mode is not None:
        raw_view_mode = (
            'b' if raw_view_mode[0] == ARGS_BINVIEW else
            'X' if raw_view_mode[1].isupper() else 'x'
        )

    def _process(i: int) -> None:
        if raw_view_mode is None:
            edit_file(ctx, i)
        else:
            print_raw_view(ctx, i, raw_view_mode)

    for i in range(start, end, step):
        _process(i)

    if ctx.u_args[ARGS_WATCH] and not ctx.u_args[ARGS_DIFF]:
        mtimes = {f.path: get_file_mtime(f.path) for f in ctx.u_files}
        try:
            while True:
                sleep(2)
                for i in range(start, end, step):
                    if get_file_mtime(ctx.u_files[i].path) != mtimes[ctx.u_files[i].path]:
                        mtimes[ctx.u_files[i].path] = get_file_mtime(ctx.u_files[i].path)
                        logger(
                            f"File '{ctx.u_files[i].displayname}' has been modified. Reloading ...",
                            priority=logger.INFO,
                        )
                        _process(i)
        except KeyboardInterrupt:
            pass
