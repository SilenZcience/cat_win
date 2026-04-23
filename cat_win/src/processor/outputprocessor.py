"""
outputprocessor
"""

from collections import deque

from cat_win.src.const.argconstants import (
    ARGS_GREP,
    ARGS_GREP_ONLY,
    ARGS_MORE,
    ARGS_NOBREAK,
    ARGS_NOCOL,
    ARGS_NOKEYWORD,
    ARGS_PEEK
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.service.helper.iohelper import IoHelper
from cat_win.src.service.querymanager import (
    QueryManager,
    _build_ansi_restore,
    _map_display_pos,
    remove_ansi_codes_from_line,
    replace_queries_in_line
)
from cat_win.src.service.rawviewer import get_raw_view_lines_gen


def _print_excluded_by_peek(prefix_len: int, excluded_by_peek: int, color_dic: dict) -> None:
    """
    Print a visual separator conveying how many lines were hidden by --peek.

    Parameters:
    prefix_len (int):
        approximate character-width of the line prefix (used for indentation)
    excluded_by_peek (int):
        number of lines that were hidden
    color_dic (dict):
        color dictionary containing all configured ANSI color values
    """
    excluded_by_peek_length = (len(str(excluded_by_peek)) - 1) // 2
    excluded_by_peek_indent = ' ' * (prefix_len - excluded_by_peek_length + 10)
    excluded_by_peek_indent_add = ' ' * excluded_by_peek_length
    excluded_by_peek_parting = f"{excluded_by_peek_indent}{excluded_by_peek_indent_add} "
    excluded_by_peek_parting += f"{color_dic[CKW.NUMBER]}:{color_dic[CKW.RESET_ALL]}"
    print(excluded_by_peek_parting)
    print(f"{excluded_by_peek_indent}{color_dic[CKW.NUMBER]}", end='')
    print(f"({excluded_by_peek}){color_dic[CKW.RESET_ALL]}")
    print(excluded_by_peek_parting)


def print_excluded_by_peek(ctx, excluded_by_peek: int) -> None:
    """
    Conditionally print the peek-exclusion separator.

    Parameters:
    ctx (AppContext):
        the app context
    excluded_by_peek (int):
        originally excluded line count
    """

    if not excluded_by_peek or len(ctx.content) <= ctx.const_dic[DKW.PEEK_SIZE]:
        return
    if any([
        ctx.u_args[ARGS_GREP],
        ctx.u_args[ARGS_GREP_ONLY],
        ctx.u_args[ARGS_NOKEYWORD],
        ctx.u_args[ARGS_MORE],
    ]):
        return

    _print_excluded_by_peek(
        len(remove_ansi_codes_from_line(ctx.content[0][1])),
        excluded_by_peek + 2 * ctx.const_dic[DKW.PEEK_SIZE] - len(ctx.content),
        ctx.color_dic
    )


def print_raw_view(ctx, file_index: int, mode: str) -> None:
    """
    Print a hex or binary byte-view of one file.

    Parameters:
    ctx (AppContext):
        the app context
    file_index (int):
        index of the file to print in ctx.u_files
    mode (str):
        either 'x', 'X' for hexadecimal (lower- or upper case letters),
        or 'b' for binary
    """
    queue = []
    skipped = 0

    print(ctx.u_files[file_index].displayname, ':', sep='')
    raw_gen = get_raw_view_lines_gen(ctx, file_index, mode)
    print(next(raw_gen))  # header is always available
    for line in raw_gen:
        skipped += 1
        if ctx.u_args[ARGS_PEEK] and skipped > ctx.const_dic[DKW.PEEK_SIZE]:
            queue.append(line)
            if len(queue) > ctx.const_dic[DKW.PEEK_SIZE]:
                queue = queue[1:]
            continue
        print(line)
    if queue:
        if skipped > 2 * ctx.const_dic[DKW.PEEK_SIZE]:
            _print_excluded_by_peek(
                21,
                skipped - 2 * ctx.const_dic[DKW.PEEK_SIZE],
                ctx.color_dic
            )
        print('\n'.join(queue))
    print()


def print_file(ctx, stepper, excluded_by_peek: int) -> bool:
    """
    Print a file, applying search/replace/grep filtering and keyword highlighting.

    Parameters:
    ctx (AppContext):
        the app context
    stepper:
        More instance for paged output
    excluded_by_peek (int):
        lines excluded by --peek

    Returns:
    (bool):
        True if any queried keyword/pattern was found in the content
    """
    content = ctx.content
    if not content:
        return False

    u_args = ctx.u_args
    arg_parser = ctx.arg_parser
    const_dic = ctx.const_dic
    color_dic = ctx.color_dic

    reset_all = color_dic[CKW.RESET_ALL]
    content_len = len(content) // 2


    if not any([arg_parser.file_queries, u_args[ARGS_GREP], u_args[ARGS_GREP_ONLY]]):
        if u_args[ARGS_MORE]:
            if content_len:
                stepper.add_lines([
                    prefix + line + suffix
                    for line, prefix, suffix in content[:content_len]
                ])
            print_excluded_by_peek(ctx, excluded_by_peek)
            stepper.add_lines([
                prefix + line + suffix
                for line, prefix, suffix in content[content_len:]
            ])
            return False
        if content_len:
            print(*[
                prefix + line + suffix
                for line, prefix, suffix in content[:content_len]
            ], sep='\n')
        print_excluded_by_peek(ctx, excluded_by_peek)
        print(*[
            prefix + line + suffix
            for line, prefix, suffix in content[content_len:]
        ], sep='\n')
        return False


    string_finder = QueryManager(arg_parser.file_queries[len(arg_parser.file_queries_replacement):])

    contains_queried = False
    last_grep_line = -const_dic[DKW.GREP_CONTEXT_LINES] - 1
    grep_context_dq = deque(maxlen=const_dic[DKW.GREP_CONTEXT_LINES])

    for c_idx, (line, line_prefix, line_suffix) in enumerate(content):
        if c_idx == content_len:
            print_excluded_by_peek(ctx, excluded_by_peek)

        # Apply find-and-replace queries
        display_line, plain_line = replace_queries_in_line(
            line,
            arg_parser.file_queries,
            arg_parser.file_queries_replacement,
            color_dic
        )

        intervals, f_keywords, m_keywords = string_finder.find_keywords(plain_line)

        # Track whether any queried keyword appeared (used to mark files)
        contains_queried |= bool(intervals)

        # --grep-only: emit only the matched substrings, one line per match
        if u_args[ARGS_GREP_ONLY]:
            if intervals:
                fm_substrings = [
                    (pos[0], f"{color_dic[CKW.FOUND]}{plain_line[pos[0]:pos[1]]}{color_dic[CKW.RESET_FOUND]}")
                    for _, pos in f_keywords
                ]
                fm_substrings += [
                    (pos[0], f"{color_dic[CKW.MATCHED]}{plain_line[pos[0]:pos[1]]}{color_dic[CKW.RESET_MATCHED]}")
                    for _, pos in m_keywords
                ]
                fm_substrings.sort(key=lambda x: x[0])
                grepped_line = f"{line_prefix}{const_dic[DKW.GREP_QUERY_SEPARATOR].join(sub for _, sub in fm_substrings)}"
                if u_args[ARGS_MORE]:
                    stepper.add_line(grepped_line)
                    continue
                print(grepped_line)
            continue

        # intervals | grep | nokeyword -> print?
        #     0     |  0   |     0     ->   1
        #     0     |  0   |     1     ->   1
        #     0     |  1   |     0     ->   0
        #     0     |  1   |     1     ->   0
        #     1     |  0   |     0     ->   1
        #     1     |  0   |     1     ->   0
        #     1     |  1   |     0     ->   1
        #     1     |  1   |     1     ->   0
        if not intervals:
            if not u_args[ARGS_GREP] or c_idx - last_grep_line <= const_dic[DKW.GREP_CONTEXT_LINES]:
                if u_args[ARGS_MORE]:
                    stepper.add_line(line_prefix + display_line + line_suffix)
                    continue
                print(line_prefix + display_line + line_suffix)
            elif u_args[ARGS_GREP]:
                grep_context_dq.append(line_prefix + display_line + line_suffix)
            continue

        for grep_line in grep_context_dq:
            if u_args[ARGS_MORE]:
                stepper.add_line(grep_line)
            else:
                print(grep_line)
        grep_context_dq.clear()
        last_grep_line = c_idx

        if u_args[ARGS_NOKEYWORD]:
            continue

        if not u_args[ARGS_NOCOL]:
            # Pre-scan display_line to know:
            #   - active ANSI state at each plain position (restore after CLOSE)
            #   - positions where RESET_ALL occurred (re-inject colour inside span)
            ansi_restore, ansi_set = _build_ansi_restore(reset_all, display_line)
            found_closes = (pos for pos, code in intervals if code == CKW.RESET_FOUND)
            matched_closes = (pos for pos, code in intervals if code == CKW.RESET_MATCHED)
            span_end = {}
            for pos, code in intervals:
                if code == CKW.FOUND:
                    span_end[(pos, code)] = next(found_closes)
                elif code == CKW.MATCHED:
                    span_end[(pos, code)] = next(matched_closes)
            for kw_pos, kw_code in intervals:
                mapped = _map_display_pos(display_line, kw_pos)
                if kw_code in (CKW.FOUND, CKW.MATCHED):
                    # Re-inject open colour before any char inside the span that
                    # was preceded by an ANSI code, so the keyword colour wins.
                    close_pos = span_end[(kw_pos, kw_code)]
                    for r in sorted(
                        [r for r in ansi_set if kw_pos < r < close_pos], reverse=True
                    ):
                        r_mapped = _map_display_pos(display_line, r)
                        display_line = (
                            display_line[:r_mapped] + color_dic[kw_code] + display_line[r_mapped:]
                        )
                    display_line = display_line[:mapped] + color_dic[kw_code] + display_line[mapped:]
                else:
                    restore = ansi_restore.get(kw_pos, '')
                    display_line = (
                        display_line[:mapped] + color_dic[kw_code] + restore + display_line[mapped:]
                    )

        if u_args[ARGS_MORE]:
            stepper.add_line(line_prefix + display_line + line_suffix)
        else:
            print(line_prefix + display_line + line_suffix)

        if u_args[ARGS_GREP] or u_args[ARGS_NOBREAK]:
            continue

        found_sth = False
        if f_keywords:
            found_message = f"{color_dic[CKW.FOUND_MESSAGE]}---------- Found:   ("
            found_message += ') ('.join(
                [f"'{kw}' {pos_s}-{pos_e}" for kw, (pos_s, pos_e) in f_keywords]
            )
            found_message += f") ----------{reset_all}"
            if u_args[ARGS_MORE]:
                stepper.add_line(found_message)
            else:
                print(found_message)
            found_sth = True
        if m_keywords:
            matched_message = f"{color_dic[CKW.MATCHED_MESSAGE]}---------- Matched: ("
            matched_message += ') ('.join(
                [f"'{kw}' {pos_s}-{pos_e}" for kw, (pos_s, pos_e) in m_keywords]
            )
            matched_message += f") ----------{reset_all}"
            if u_args[ARGS_MORE]:
                stepper.add_line(matched_message)
            else:
                print(matched_message)
            found_sth = True

        if found_sth and not u_args[ARGS_MORE]:
            with IoHelper.dup_stdstreams():
                try:
                    # fails when using --stdin mode because stdin sends EOF without
                    # prompting the user → dup stdin guards against that
                    input()
                except (EOFError, UnicodeDecodeError):
                    pass

    return contains_queried
