from re import finditer

from cat_win.const.ColorConstants import C_KW


class StringFinder:
    def __init__(self, literals: set, regex: set) -> None:
        self.kw_literals = literals
        self.kw_regex = regex

    def _findliterals(self, sub: str, s: str):
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
        l = len(sub)
        i = s.find(sub)
        while i != -1:
            yield [i, i+l]
            i = s.find(sub, i+1)

    def _findregex(self, pattern: str, s: str):
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
        for match in finditer(fr'{pattern}', s):
            yield list(match.span())

    def _optimizeIntervals(self, intervals: list) -> list:
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

    def _mergeKeywordIntervals(self, fList: list, mList: list) -> list:
        fList = self._optimizeIntervals(fList)
        mList = self._optimizeIntervals(mList)
        kwList = []
        for f in fList:
            kwList.append([f[0], C_KW.FOUND])
            kwList.append([f[1], C_KW.RESET_FOUND])
        for rf in mList:
            kwList.append([rf[0], C_KW.MATCHED])
            kwList.append([rf[1], C_KW.RESET_MATCHED])
        kwList.sort(reverse=True)
        return kwList

    def findKeywords(self, line: str) -> tuple:
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
            for f in self._findliterals(keyword, line):
                found_position.append(f[:])
                found_list.append((keyword, f))

        for keyword in self.kw_regex:
            for m in self._findregex(keyword, line):
                matched_position.append(m[:])
                matched_list.append((keyword, m))

        return (self._mergeKeywordIntervals(found_position, matched_position), found_list, matched_list)
