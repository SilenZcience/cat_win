"""
lineprefixprocessor
"""

from functools import lru_cache

from cat_win.src.const.argconstants import (
    ARGS_FILE_PREFIX,
    ARGS_NOCOL,
    ARGS_NUMBER
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.querymanager import remove_ansi_codes_from_line

FILE_URI_PREFIX = 'file://' + '/' * on_windows_os


@lru_cache()
def _calculate_line_prefix_spacing(
    line_char_length: int,
    max_line_ph: int,
    file_num_ph: int,
    number_color: str,
    reset_color: str,
    file_name_prefix: bool = False,
    include_file_prefix: bool = False,
    file_char_length: int = 0,
) -> str:
    """
    Return a %-format template for a line-number prefix.

    All parameters that affect the output are explicit so the lru_cache
    key fully determines the result (no hidden global reads).

    Parameters:
    line_char_length (int):
        digit-width of the line number
    max_line_ph (int):
        u_files.all_line_number_place_holder
    file_num_ph (int):
        u_files.file_number_place_holder  (pass 0 when unused)
    number_color (str):
        color_dic[CKW.NUMBER]
    reset_color (str):
        color_dic[CKW.RESET_ALL]
    file_name_prefix (bool):
        include full file path instead of a numeric index
    include_file_prefix (bool):
        include a numeric file index in the prefix
    file_char_length (int):
        digit-width of the file index

    Returns:
    (str):
        A format string for the line prefix, with placeholders for the file index
        and line number as needed.
    """
    line_prefix = ' ' * (max_line_ph - line_char_length)

    if file_name_prefix:
        line_prefix = '%i' + line_prefix
    else:
        line_prefix += '%i)'

    if include_file_prefix and not file_name_prefix:
        file_prefix = (' ' * (file_num_ph - file_char_length)) + '%i.'
        return number_color + file_prefix + line_prefix + reset_color + ' '

    return number_color + line_prefix + reset_color + ' '


@lru_cache()
def _calculate_line_length_prefix_spacing(
    line_char_length: int,
    max_ll_ph: int,
    ll_color: str,
    reset_color: str,
) -> str:
    """
    Return a %-format template for a line-length prefix.

    All parameters that affect the output are explicit so the lru_cache
    key fully determines the result (no hidden global reads).

    Parameters:
    line_char_length (int):
        digit-width of the line-length value
    max_ll_ph (int):
        u_files.file_line_length_place_holder
    ll_color (str):
        color_dic[CKW.LINE_LENGTH]
    reset_color (str):
        color_dic[CKW.RESET_ALL]

    Returns:
    (str):
        A format string for the line-length prefix, with a placeholder for the
        line length.
    """
    length_prefix = '[' + ' ' * (max_ll_ph - line_char_length) + '%i]'
    return '%s' + ll_color + length_prefix + reset_color + ' '



def get_line_prefix(ctx, line_num: int, index: int) -> str:
    """
    Return the formatted line-number prefix for line_num / file index.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    line_num (int):
        The line number for which to generate the prefix.
    index (int):
        The index of the file in ctx.u_files for which to generate the prefix.

    Returns:
    (str):
        The formatted line-number prefix for the given line number and file index.
    """
    num_color = ctx.color_dic[CKW.NUMBER]
    reset = ctx.color_dic[CKW.RESET_ALL]
    if ctx.u_args[ARGS_FILE_PREFIX]:
        return _calculate_line_prefix_spacing(
            len(str(line_num)),
            ctx.u_files.all_line_number_place_holder, 0,
            num_color, reset,
            file_name_prefix=True,
        ) % line_num
    if len(ctx.u_files) > 1:
        return _calculate_line_prefix_spacing(
            len(str(line_num)),
            ctx.u_files.all_line_number_place_holder,
            ctx.u_files.file_number_place_holder,
            num_color, reset,
            include_file_prefix=True,
            file_char_length=len(str(index)),
        ) % (index, line_num)
    return _calculate_line_prefix_spacing(
        len(str(line_num)),
        ctx.u_files.all_line_number_place_holder, 0,
        num_color, reset,
    ) % line_num


def get_line_length_prefix(ctx, prefix: str, line) -> str:
    """
    Return prefix extended with the line-length annotation.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    prefix (str):
        The existing line prefix to extend with the line-length annotation.
    line (str or bytes):
        The line for which to calculate the length annotation.  Can be a string

    Returns:
    (str):
        The input prefix extended with the line-length annotation.
    """
    if not ctx.u_args[ARGS_NOCOL] and isinstance(line, str):
        line = remove_ansi_codes_from_line(line)
    return _calculate_line_length_prefix_spacing(
        len(str(len(line))),
        ctx.u_files.file_line_length_place_holder,
        ctx.color_dic[CKW.LINE_LENGTH],
        ctx.color_dic[CKW.RESET_ALL],
    ) % (prefix, len(line))


def get_file_prefix(ctx, prefix: str, file_index: int, hyper: bool = False) -> str:
    """
    Return prefix extended with the filename annotation.

    Parameters:
    ctx (AppContext):
        The current invocation context, containing parsed arguments and other state.
    prefix (str):
        The existing line prefix to extend with the filename annotation.
    file_index (int):
        The index of the file in ctx.u_files for which to generate the prefix.
    hyper (bool):
         Whether to format the file prefix as a hyperlink (using the file URI scheme).
          If True, the file path will be formatted as a hyperlink and backslashes will
          be replaced with forward slashes for compatibility with the file URI scheme.

    Returns:
    (str):
        The input prefix extended with the filename annotation, formatted as a hyperlink
        if hyper is True.
    """
    if file_index < 0:
        return prefix
    file = f"{FILE_URI_PREFIX * hyper}{ctx.u_files[file_index].displayname}"
    if hyper:
        file = file.replace('\\', '/')
    if not ctx.u_args[ARGS_NUMBER] or hyper:
        return f"{prefix}{ctx.color_dic[CKW.FILE_PREFIX]}{file}{ctx.color_dic[CKW.RESET_ALL]} "
    return f"{ctx.color_dic[CKW.FILE_PREFIX]}{file}{ctx.color_dic[CKW.RESET_ALL]}:{prefix}"
