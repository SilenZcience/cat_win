from re import finditer
from cat_win.util.ColorConstants import C_KW


class StringFinder:
    kw_literals = []
    kw_regex = []

    def __init__(self, literals: list, regex: list) -> None:
        self.kw_literals = literals
        self.kw_regex = regex

    def _findliterals(self, sub: str, s: str) -> list:
        """
        Generate lists containing the start and end index
        of all found positions of substring 'sub'
        within string 's'.
        """
        l = len(sub)
        i = s.find(sub)
        while i != -1:
            yield [i, i+l]
            i = s.find(sub, i+1)

    def _findregex(self, pattern, s) -> list:
        """
        Generate lists containing the start and end index
        of all found positions of regex-match 'pattern'
        within string 's'.
        """
        for match in finditer(fr'{pattern}', s):
            yield list(match.span())

    def _optimizeIntervals(self, intervals: list) -> list:
        """\
            Merge overlapping intervalls for partially
            color encoded lines. Needed when multiple
            search-keywords apply to the same line.
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
        Takes a string and searches for all occurrences
        of self.kw_literals and self.kw_regex.
        Merges the Intervals to optimized/shortened Intervals.
        Returns a tuple containing the index positions of all intervals,
        and thee lists containing which elements have been found
        """
        found_list = []
        found_position = []
        matched_list = []
        matched_position = []

        for keyword in self.kw_literals:
            for f in self._findliterals(keyword, line):
                found_position.append(f)
                found_list.append((keyword, f))

        for keyword in self.kw_regex:
            for m in self._findregex(keyword, line):
                matched_position.append(m)
                matched_list.append((keyword, m))

        return (self._mergeKeywordIntervals(found_position, matched_position), found_list, matched_list)
