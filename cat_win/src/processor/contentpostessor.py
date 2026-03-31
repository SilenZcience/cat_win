"""
contentposteccor

Post-processing stage for after-display actions, cleanup, and diagnostics.
"""

import os

from cat_win.src.const.argconstants import (
    ARGS_CHARCOUNT,
    ARGS_CLIP,
    ARGS_DIRECTORIES,
    ARGS_FFILES,
    ARGS_FILES,
    ARGS_SSUM,
    ARGS_SUM,
    ARGS_WORDCOUNT,
    ARGS_DEBUG,
)
from cat_win.src.curses.helper.diffviewerhelper import is_special_character
from cat_win.src.processor.lineprefixprocessor import (
    _calculate_line_prefix_spacing,
    _calculate_line_length_prefix_spacing,
)
from cat_win.src.processor.registerwrapper import POST_CONTENT_ACTIONS, register_post
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.querymanager import remove_ansi_codes_from_line
from cat_win.src.service.summary import Summary
from cat_win.src.service.visualizer import Visualizer
from cat_win.src.service.helper.iohelper import logger


def _print_cache_debug_info(ctx) -> None:
    logger(
        '================================================ DEBUG ================================================',
        priority=logger.DEBUG,
    )
    caches = [
        remove_ansi_codes_from_line,
        _calculate_line_prefix_spacing,
        _calculate_line_length_prefix_spacing,
        ctx.u_files._get_file_lines_sum_,
        ctx.u_files._calc_max_line_length_,
        Visualizer.get_color_byte_view,
        Visualizer.get_color_entropy,
        is_special_character,
    ]
    caches_info = [
        (
            cache.__name__,
            str(cache.cache_info().hits),
            str(cache.cache_info().misses),
            str(cache.cache_info().maxsize),
            str(cache.cache_info().currsize),
        )
        for cache in caches
    ]
    max_val = [max(len(_c) for _c in c_info) + 1 for c_info in zip(*caches_info)]
    for name, hits, misses, maxsize, currsize in caches_info:
        cache_info  = f"def:{name.ljust(max_val[0])}"
        cache_info += f"hits:{hits.ljust(max_val[1])}"
        cache_info += f"misses:{misses.ljust(max_val[2])}"
        cache_info += f"maxsize:{maxsize.ljust(max_val[3])}"
        cache_info += f"currsize:{currsize.ljust(max_val[4])}"
        cache_info += f"full:{100 * int(currsize) / int(maxsize):6.2f}%"
        logger(cache_info, priority=logger.DEBUG)


def _cleanup_temp_files(tmp_file_helper) -> None:
    for tmp_file in tmp_file_helper.get_generated_temp_files():
        logger('Cleaning', tmp_file, priority=logger.DEBUG)
        try:
            os.remove(tmp_file)
        except OSError as exc:
            logger(type(exc).__name__, tmp_file, priority=logger.ERROR)


@register_post(ARGS_FILES, ARGS_DIRECTORIES)
def _show_files_and_directories(ctx) -> None:
    print()
    if ctx.u_args[ARGS_FILES]:
        Summary.show_files(ctx.u_files.files, ctx.u_args[ARGS_FFILES])
    if ctx.u_args[ARGS_DIRECTORIES]:
        Summary.show_dirs(ctx.known_dirs)


@register_post(ARGS_SUM)
def _show_sum(ctx) -> None:
    print()
    Summary.show_sum(
        ctx.u_files.files,
        ctx.u_args[ARGS_SSUM],
        ctx.u_files.all_files_lines,
        ctx.u_files.all_line_number_place_holder,
    )


@register_post(ARGS_WORDCOUNT)
def _show_wordcount(ctx) -> None:
    print()
    Summary.show_wordcount(ctx.u_files.files, ctx.arg_parser.file_encoding)


@register_post(ARGS_CHARCOUNT)
def _show_charcount(ctx) -> None:
    print()
    Summary.show_charcount(ctx.u_files.files, ctx.arg_parser.file_encoding)


@register_post(ARGS_CLIP)
def _copy_to_clipboard(_ctx) -> None:
    Clipboard.put(remove_ansi_codes_from_line(Clipboard.clipboard))


def run_post_content_actions(ctx) -> None:
    """Run actions that are intended to happen after file-content display."""
    executed_handlers = set()
    for arg_id, _ in ctx.u_args:
        handler = POST_CONTENT_ACTIONS.get(arg_id)
        if handler is None or handler in executed_handlers:
            continue
        executed_handlers.add(handler)
        handler(ctx)


def finalize_context(ctx, tmp_file_helper) -> None:
    """Run post-processing actions based on active arguments."""
    if ctx.u_args[ARGS_DEBUG]:
        _print_cache_debug_info(ctx)

    _cleanup_temp_files(tmp_file_helper)

    logger(
        '=======================================================================================================',
        priority=logger.DEBUG,
    )
    logger.close()
