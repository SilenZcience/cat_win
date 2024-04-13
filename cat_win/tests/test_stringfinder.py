from unittest import TestCase

import re

from cat_win.util.service.stringfinder import StringFinder
# import sys
# sys.path.append('../cat_win')


class TestStringFinder(TestCase):
    def test_find_literals_true(self):
        string_finder = StringFinder(set(), set())
        _x = list(string_finder._findliterals('test', 'abctestdef', False))
        self.assertEqual(_x, [[3, 7]])

        _x = list(string_finder._findliterals('test', 'testabctestdetestf', False))
        self.assertEqual(_x, [[0, 4], [7, 11], [13, 17]])

        _x = list(string_finder._findliterals('', '', False))
        self.assertEqual(_x, [[0, 0]])

        _x = list(string_finder._findliterals('', 'x', False))
        self.assertEqual(_x, [[0, 0], [1, 1]])

    def test_find_literals_false(self):
        string_finder = StringFinder(set(), set())
        _x = list(string_finder._findliterals('a', '', False))
        self.assertEqual(_x, [])

        _x = list(string_finder._findliterals('test', 'tsetabctesdeestf', False))
        self.assertEqual(_x, [])

    def test_find_regex_true(self):
        string_finder = StringFinder(set(), set())
        _x = list(string_finder._findregex(re.compile(r"test", re.DOTALL | re.IGNORECASE), 'TeSt'))
        self.assertEqual(_x, [[0, 4]])

    def test_find_regex_false(self):
        string_finder = StringFinder(set(), set())
        _x = list(string_finder._findregex(re.compile(r"[A-Z]{1}[a-z]+\s?.*\.+\s", re.DOTALL), 'silas A. Kraume'))
        self.assertEqual(_x, [])
        _x = list(string_finder._findregex(re.compile(r"[0-9]{2}", re.DOTALL), '123'))
        self.assertEqual(_x, [[0, 2]])

        _x = list(string_finder._findregex(re.compile(r"[0-9]{2}", re.DOTALL), '1234'))
        self.assertEqual(_x, [[0, 2], [2, 4]])

        _x = list(string_finder._findregex(re.compile(r"[A-Z]{1}[a-z]*\s?.*\.+\s", re.DOTALL), 'Silas A. Kraume'))
        self.assertEqual(_x, [[0, 9]])

        _x = list(string_finder._findregex(re.compile(r"[A-Z]{1}[a-z]*\s?.*\.+\s", re.DOTALL), 'silas A. Kraume'))
        self.assertEqual(_x, [[6, 9]])

        _x = list(string_finder._findregex(re.compile(r"test", re.DOTALL), 'TeSt'))
        self.assertEqual(_x, [])

    def test_optimize_intervals(self):
        string_finder = StringFinder(set(), set())
        _x = string_finder._optimize_intervals([[1, 3], [3, 5]])
        self.assertEqual(_x, [[1, 5]])

        _x = string_finder._optimize_intervals([[1, 10], [5, 10]])
        self.assertEqual(_x, [[1, 10]])

        _x = string_finder._optimize_intervals([[1, 3], [2, 5], [6, 8]])
        self.assertEqual(_x, [[1, 5], [6, 8]])

        _x = string_finder._optimize_intervals([[1, 3], [-5, 0], [0, 2]])
        self.assertEqual(_x, [[-5, 3]])

    def test_optimize_intervals_empty(self):
        string_finder = StringFinder(set(), set())
        _x = string_finder._optimize_intervals([])
        self.assertEqual(_x, [])

    def test_find_keywords(self):
        string_finder = StringFinder(set([('Is', False),
                                          ('Test', False),
                                          ('Not', False)]),
                                     set([re.compile(r"[0-9]\!", re.DOTALL)]))
        line = 'ThisIsATest!1!'
        intervals, f_keywords, m_keywords = string_finder.find_keywords(line)

        self.assertCountEqual(intervals, [[14, 'reset_matched'], [12, 'matched_pattern'],
                                          [11, 'reset_found'], [7, 'found_keyword'],
                                          [6, 'reset_found'], [4, 'found_keyword']])
        self.assertCountEqual(f_keywords, [('Is', [4, 6]), ('Test', [7, 11])])
        self.assertCountEqual(m_keywords, [(r"[0-9]\!", [12, 14])])
