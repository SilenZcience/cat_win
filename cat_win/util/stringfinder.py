"""
stringfinder
"""

import re

from cat_win.const.colorconstants import CKW


class StringFinder:
    """
    defines a stringfinder
    """
    def __init__(self, literals: set = None, regex: set = None,
                 literals_ignore_case: bool = False, regex_ignore_case: bool = False) -> None:
        self.kw_literals = literals if literals is not None else {}
        self.kw_regex = regex if regex is not None else {}
        self.literals_ignore_case = literals_ignore_case
        self.regex_ignore_case = regex_ignore_case

    def _findliterals(self, sub: str, _s: str):
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
        if self.literals_ignore_case:
            sub, _s = sub.lower(), _s.lower()
        _l = len(sub)
        i = _s.find(sub)
        while i != -1:
            yield [i, i+_l]
            i = _s.find(sub, i+1)

    def _findregex(self, pattern: str, _s: str):
        """
        Generate lists containing the position of pattern in s.
        
        Parameters:
        pattern (str):
            the regex pattern to search for
        s (str):
            the string to search in
        
        Yields:
        (list):
            containing the start and end indeces like [start, end]
        """
        for match in re.finditer(fr'{pattern}', _s, re.IGNORECASE if self.regex_ignore_case else 0):
            yield list(match.span())

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

        for keyword in self.kw_literals:
            for _f in self._findliterals(keyword, line):
                found_position.append(_f[:])
                found_list.append((keyword, _f))
        # sort by start position (necessary for a deterministic output)
        found_list.sort(key = lambda x: x[1][0])

        for keyword in self.kw_regex:
            for _m in self._findregex(keyword, line):
                matched_position.append(_m[:])
                matched_list.append((keyword, _m))
        # sort by start position (necessary for a deterministic output)
        matched_list.sort(key = lambda x: x[1][0])

        return (self._merge_keyword_intervals(found_position, matched_position),
                found_list,
                matched_list)
