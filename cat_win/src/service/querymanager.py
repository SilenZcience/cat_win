"""
stringfinder
"""

from functools import lru_cache

from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.regex import RE_ANSI_CSI


@lru_cache(maxsize=256)
def remove_ansi_codes_from_line(line: str) -> str:
    """Return *line* with all ANSI CSI escape sequences stripped."""
    return RE_ANSI_CSI.sub('', line)


def _map_display_pos(display_str: str, plain_pos: int) -> int:
    """
    Map a character position in the ANSI-stripped version of *display_str*
    to the corresponding position in *display_str* itself.

    ANSI escape sequences are skipped first; the plain-character count is
    incremented only for non-escape bytes.
    """
    plain_count = 0
    i = 0
    while i < len(display_str):
        ansi_m = RE_ANSI_CSI.match(display_str, i)
        if ansi_m:
            i = ansi_m.end()
            continue
        if plain_count == plain_pos:
            return i
        plain_count += 1
        i += 1
    return i

def _build_ansi_restore(reset_all: str, display_str: str) -> tuple:
    """
    Scan *display_str* and return:
      - a dict mapping each plain-text character index to the string of ANSI
        codes that are active just before that character (used to re-emit lost
        colours after a close keyword marker).
      - a set of plain-text positions preceded by at least one ANSI code
        (used to re-inject the open keyword colour after any ANSI override
        inside a keyword span, so the keyword colour always wins).

    Parameters:
    reset_all (str):
        the ANSI escape sequence that resets all SGR attributes
    display_str (str):
        the line text to scan
    """
    restore = {}
    active = []
    ansi_set = set()
    had_ansi = False
    pc = 0
    i = 0
    while i < len(display_str):
        ansi_m = RE_ANSI_CSI.match(display_str, i)
        if ansi_m:
            code = ansi_m.group(0)
            if code == reset_all:
                active = []
            else:
                active.append(code)
            had_ansi = True
            i = ansi_m.end()
        else:
            if had_ansi:
                ansi_set.add(pc)
                had_ansi = False
            restore[pc] = ''.join(active)
            pc += 1
            i += 1
    restore[pc] = ''.join(active)  # state at end of string
    return restore, ansi_set

def find_literals(sub: str, _s: str, ignore_case: bool):
    """
    Generate lists containing the position of sub in s.

    Parameters:
    sub (str):
        the substring to search for
    s (str):
        the string to search in

    Yields:
    (list):
        containing the start and end indeces like [start, end]
    """
    if ignore_case:
        sub, _s = sub.lower(), _s.lower()
    _l = len(sub)
    i = _s.find(sub)
    while i != -1:
        yield [i, i+_l]
        i = _s.find(sub, i+1)

def find_regex(pattern, _s: str):
    """
    Generate lists containing the position of pattern in s.

    Parameters:
    pattern (re_pattern):
        the regex pattern to search for
    s (str):
        the string to search in

    Yields:
    (list):
        containing the start and end indeces like [start, end]
    """
    for _match in pattern.finditer(_s):
        yield list(_match.span())

def replace_queries_in_line(
        line: str, queries: list, replacements: list, color_dic: dict
) -> str:
    """
    Replace all occurences of the queries in line with the replace color.

    Parameters:
    line (str):
        the string in which to search for all occurences of
        self.kw_literals and self.kw_regex
    queries (set):
        the set of queries to search for
    color_dic (dict):
        color dictionary containing all configured ANSI color values

    Returns:
    (tuple):
        containing the new replaced line with color codes and plain
    """
    plain_line = remove_ansi_codes_from_line(line)
    display_line = line

    for q_idx, replacement in enumerate(replacements):
        query, ignore_case = queries[q_idx]
        ansi_restore, _ = _build_ansi_restore(color_dic[CKW.RESET_ALL], display_line)
        if isinstance(query, str):
            matches = list(find_literals(query, plain_line, ignore_case))
            disp_pos = [
                (_map_display_pos(display_line, f_s), _map_display_pos(display_line, f_e))
                for f_s, f_e in matches
            ]
            for (f_s, f_e), (d_s, d_e) in reversed(list(zip(matches, disp_pos))):
                plain_line = plain_line[:f_s] + replacement + plain_line[f_e:]
                display_line = (
                    display_line[:d_s]
                    + color_dic[CKW.REPLACE] + replacement + color_dic[CKW.RESET_ALL]
                    + ansi_restore.get(f_e, '')
                    + display_line[d_e:]
                )
        else:
            matches = list(query.finditer(plain_line))
            disp_pos = [
                (_map_display_pos(display_line, m.start()), _map_display_pos(display_line, m.end()))
                for m in matches
            ]
            for m, (d_s, d_e) in reversed(list(zip(matches, disp_pos))):
                repl = m.expand(replacement)
                plain_line = plain_line[:m.start()] + repl + plain_line[m.end():]
                display_line = (
                    display_line[:d_s]
                    + color_dic[CKW.REPLACE] + repl + color_dic[CKW.RESET_ALL]
                    + ansi_restore.get(m.end(), '')
                    + display_line[d_e:]
                )
    return display_line, plain_line

class QueryManager:
    """
    defines a stringfinder
    """
    def __init__(self, queries: set = None) -> None:
        self.kw_queries = queries

    def _optimize_intervals(self, intervals: list) -> list:
        """
        optimize/shorten/merge overlapping intervalls for partially
        color encoded lines. Needed when multiple
        search-keywords apply to the same line.

        Parameters:
        intervals (list):
            the intervals to optimize like [[start, end], ...]

        Returns:
        stack (list)
            the optimized intervals
        """
        if not intervals:
            return []
        intervals.sort()
        stack = []
        stack.append(intervals[0])
        for interval in intervals:
            if stack[-1][0] <= interval[0] <= stack[-1][-1]:
                stack[-1][-1] = max(stack[-1][-1], interval[-1])
            else:
                stack.append(interval)
        return stack

    def _merge_keyword_intervals(self, f_list: list, m_mist: list) -> list:
        f_list = self._optimize_intervals(f_list)
        m_mist = self._optimize_intervals(m_mist)
        kw_list = []
        for _f in f_list:
            kw_list.append([_f[0], CKW.FOUND])
            kw_list.append([_f[1], CKW.RESET_FOUND])
        for _m in m_mist:
            kw_list.append([_m[0], CKW.MATCHED])
            kw_list.append([_m[1], CKW.RESET_MATCHED])
        kw_list.sort(reverse=True)
        return kw_list

    def find_keywords(self, line: str) -> tuple:
        """
        calculate the positions for ANSI-ColorCodes.

        Parameters:
        line (str):
            the string in which to search for all occurences of
            self.kw_literals and self.kw_regex

        Returns:
        (tuple):
            containing three lists:
                the index positions of all intervals
                the found substrings
                the matched patterns
        """
        found_list = []
        found_position = []
        matched_list = []
        matched_position = []

        for query, ignore_case in self.kw_queries:
            if isinstance(query, str):
                for _f in find_literals(query, line, ignore_case):
                    found_position.append(_f[:])
                    found_list.append((query, _f))
            else:
                for _m in find_regex(query, line):
                    matched_position.append(_m[:])
                    matched_list.append((query.pattern, _m))
        # sort by start position (necessary for a deterministic output)
        found_list.sort(key = lambda x: x[1][0])
        matched_list.sort(key = lambda x: x[1][0])

        return (
            self._merge_keyword_intervals(found_position, matched_position),
            found_list,
            matched_list
        )
