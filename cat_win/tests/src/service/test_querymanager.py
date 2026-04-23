from unittest import TestCase

import re

from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.querymanager import (
    QueryManager,
    remove_ansi_codes_from_line,
    _map_display_pos,
    _build_ansi_restore,
    find_literals,
    find_literals_no_overlap,
    find_regex,
    replace_queries_in_line
)
# import sys
# sys.path.append('../cat_win')


class TestQueryManager(TestCase):
    def test_remove_ansi_codes_from_line(self):
        line = '\x1b[31mRed\x1b[0m Text'
        self.assertEqual(remove_ansi_codes_from_line(line), 'Red Text')

    def test_map_display_pos(self):
        display = '\x1b[31mAB\x1b[0mC'
        self.assertEqual(_map_display_pos(display, 0), 5)
        self.assertEqual(_map_display_pos(display, 1), 6)
        self.assertEqual(_map_display_pos(display, 2), 11)
        # out-of-range plain index maps to end of display string
        self.assertEqual(_map_display_pos(display, 99), len(display))

    def test_build_ansi_restore(self):
        reset = '\x1b[0m'
        display = '\x1b[31mA\x1b[32mB\x1b[0mC'

        restore, ansi_set = _build_ansi_restore(reset, display)

        self.assertEqual(restore[0], '\x1b[31m')
        self.assertEqual(restore[1], '\x1b[31m\x1b[32m')
        self.assertEqual(restore[2], '')
        self.assertEqual(restore[3], '')
        self.assertSetEqual(ansi_set, {0, 1, 2})

    def test_find_literals_true(self):
        _x = list(find_literals('test', 'abctEStdef', True))
        self.assertListEqual(_x, [[3, 7]])

        _x = list(find_literals('TeSt', 'abctEstdef', True))
        self.assertListEqual(_x, [[3, 7]])

        _x = list(find_literals('tesT', 'testabctestdetestf', True))
        self.assertListEqual(_x, [[0, 4], [7, 11], [13, 17]])

        _x = list(find_literals('', '', True))
        self.assertListEqual(_x, [[0, 0]])

        _x = list(find_literals('', 'x', True))
        self.assertListEqual(_x, [[0, 0], [1, 1]])

        _x = list(find_literals('aa', 'aaaaa', False))
        self.assertListEqual(_x, [[0, 2], [1, 3], [2, 4], [3, 5]])

    def test_find_literals_false(self):
        _x = list(find_literals('a', '', False))
        self.assertListEqual(_x, [])

        _x = list(find_literals('TeSt', 'abctestdef', False))
        self.assertListEqual(_x, [])

        _x = list(find_literals('test', 'tsetabctesdeestf', False))
        self.assertListEqual(_x, [])

    def test_find_literals_no_overlap_true(self):
        _x = list(find_literals_no_overlap('test', 'abctEStdef', True))
        self.assertListEqual(_x, [[3, 7]])

        _x = list(find_literals_no_overlap('TeSt', 'abctEstdef', True))
        self.assertListEqual(_x, [[3, 7]])

        _x = list(find_literals_no_overlap('tesT', 'testabctestdetestf', True))
        self.assertListEqual(_x, [[0, 4], [7, 11], [13, 17]])

        _x = list(find_literals_no_overlap('', '', True))
        self.assertListEqual(_x, [[0, 0]])

        _x = list(find_literals_no_overlap('', 'x', True))
        self.assertListEqual(_x, [[0, 0], [1, 1]])

        _x = list(find_literals_no_overlap('aa', 'aaaaa', False))
        self.assertListEqual(_x, [[0, 2], [2, 4]])

    def test_find_literals_no_overlap_false(self):
        _x = list(find_literals_no_overlap('a', '', False))
        self.assertListEqual(_x, [])

        _x = list(find_literals_no_overlap('TeSt', 'abctestdef', False))
        self.assertListEqual(_x, [])

        _x = list(find_literals_no_overlap('test', 'tsetabctesdeestf', False))
        self.assertListEqual(_x, [])

    def test_find_regex_true(self):
        _x = list(find_regex(re.compile(r"test", re.DOTALL | re.IGNORECASE), 'TeSt'))
        self.assertListEqual(_x, [[0, 4]])

    def test_find_regex_false(self):
        _x = list(find_regex(re.compile(r"[A-Z]{1}[a-z]+\s?.*\.+\s", re.DOTALL), 'silas A. Kraume'))
        self.assertListEqual(_x, [])
        _x = list(find_regex(re.compile(r"[0-9]{2}", re.DOTALL), '123'))
        self.assertListEqual(_x, [[0, 2]])

        _x = list(find_regex(re.compile(r"[0-9]{2}", re.DOTALL), '1234'))
        self.assertListEqual(_x, [[0, 2], [2, 4]])

        _x = list(find_regex(re.compile(r"[A-Z]{1}[a-z]*\s?.*\.+\s", re.DOTALL), 'Silas A. Kraume'))
        self.assertListEqual(_x, [[0, 9]])

        _x = list(find_regex(re.compile(r"[A-Z]{1}[a-z]*\s?.*\.+\s", re.DOTALL), 'silas A. Kraume'))
        self.assertListEqual(_x, [[6, 9]])

        _x = list(find_regex(re.compile(r"test", re.DOTALL), 'TeSt'))
        self.assertListEqual(_x, [])

    def test_optimize_intervals(self):
        string_finder = QueryManager([])
        _x = string_finder._optimize_intervals([[1, 3], [3, 5]])
        self.assertListEqual(_x, [[1, 5]])

        _x = string_finder._optimize_intervals([[1, 10], [5, 10]])
        self.assertListEqual(_x, [[1, 10]])

        _x = string_finder._optimize_intervals([[1, 3], [2, 5], [6, 8]])
        self.assertListEqual(_x, [[1, 5], [6, 8]])

        _x = string_finder._optimize_intervals([[1, 3], [-5, 0], [0, 2]])
        self.assertListEqual(_x, [[-5, 3]])

    def test_optimize_intervals_empty(self):
        string_finder = QueryManager([])
        _x = string_finder._optimize_intervals([])
        self.assertListEqual(_x, [])

    def test_find_keywords(self):
        string_finder = QueryManager([('Is', False),
                                      ('Test', False),
                                      ('Not', False),
                                      (re.compile(r"[0-9]\!", re.DOTALL), False)])
        line = 'ThisIsATest!1!'
        intervals, f_keywords, m_keywords = string_finder.find_keywords(line)

        self.assertCountEqual(intervals, [[14, 'reset_matched'], [12, 'matched_pattern'],
                                          [11, 'reset_found'], [7, 'found_keyword'],
                                          [6, 'reset_found'], [4, 'found_keyword']])
        self.assertCountEqual(f_keywords, [('Is', [4, 6]), ('Test', [7, 11])])
        self.assertCountEqual(m_keywords, [(r"[0-9]\!", [12, 14])])

    def test_replace_queries_in_line_literal(self):
        color_dic = {
            CKW.REPLACE: '<R>',
            CKW.RESET_ALL: '</R>',
        }
        line = 'A \x1b[34mtest\x1b[0m B'

        display_line, plain_line = replace_queries_in_line(
            line,
            [('test', False)],
            ['done'],
            color_dic,
        )

        self.assertEqual(plain_line, 'A done B')
        self.assertIn('<R>done</R>', display_line)
        self.assertNotIn('test', plain_line)

    def test_replace_queries_in_line_regex(self):
        color_dic = {
            CKW.REPLACE: '<R>',
            CKW.RESET_ALL: '</R>',
        }

        display_line, plain_line = replace_queries_in_line(
            'abc123def',
            [(re.compile(r'(\d+)'), False)],
            [r'[\1]'],
            color_dic,
        )

        self.assertEqual(plain_line, 'abc[123]def')
        self.assertIn('<R>[123]</R>', display_line)
