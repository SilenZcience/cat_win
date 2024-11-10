"""
stringfinder
"""

from cat_win.src.const.colorconstants import CKW


class StringFinder:
    """
    defines a stringfinder
    """
    def __init__(self, queries: set = None) -> None:
        self.kw_queries = queries

    def find_literals(self, sub: str, _s: str, ignore_case: bool):
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

    def find_regex(self, pattern, _s: str):
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
                for _f in self.find_literals(query, line, ignore_case):
                    found_position.append(_f[:])
                    found_list.append((query, _f))
            else:
                for _m in self.find_regex(query, line):
                    matched_position.append(_m[:])
                    matched_list.append((query.pattern, _m))
        # sort by start position (necessary for a deterministic output)
        found_list.sort(key = lambda x: x[1][0])
        matched_list.sort(key = lambda x: x[1][0])

        return (self._merge_keyword_intervals(found_position, matched_position),
                found_list,
                matched_list)
