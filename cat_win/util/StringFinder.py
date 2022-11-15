from re import finditer


class StringFinder:
    kw_literals = []
    kw_regex = []

    def __init__(self, literals: list, regex: list):
        self.kw_literals = literals
        self.kw_regex = regex

    def _findliterals(self, sub, s):
        l = len(sub)
        i = s.find(sub)
        while i != -1:
            yield [i, i+l]
            i = s.find(sub, i+1)

    def _findregex(self, pattern, s):
        for match in finditer(fr'{pattern}', s):
            yield list(match.span())

    def _optimizeIntervals(self, intervals: list[list]) -> list[list]:
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

    def _mergeKeywordIntervals(self, fList: list[list], mList: list[list]) -> list[list]:
        fList = self._optimizeIntervals(fList)
        mList = self._optimizeIntervals(mList)
        kwList = []
        for f in fList:
            kwList.append([f[0], "found_keyword"])
            kwList.append([f[1], "found_reset"])
        for rf in mList:
            kwList.append([rf[0], "matched_keyword"])
            kwList.append([rf[1], "matched_reset"])
        kwList.sort(reverse=True)
        return kwList

    def findKeywords(self, line: str, color_encoded: bool):
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
