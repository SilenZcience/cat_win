from cat_win.util.StringFinder import StringFinder
from unittest import TestCase
# import sys
# sys.path.append('../cat_win')


class TestConverter(TestCase):
    def test_findliterals_True(self):
        stringFinder = StringFinder([], [])
        x = [x for x in stringFinder._findliterals('test', 'abctestdef')]
        self.assertEqual(x, [[3, 7]])
        
        x = [x for x in stringFinder._findliterals('test', 'testabctestdetestf')]
        self.assertEqual(x, [[0, 4], [7, 11], [13, 17]])
        
        x = [x for x in stringFinder._findliterals('', '')]
        self.assertEqual(x, [[0, 0]])
        
        x = [x for x in stringFinder._findliterals('', 'x')]
        self.assertEqual(x, [[0, 0], [1, 1]])
        
    def test_findLiterals_False(self):
        stringFinder = StringFinder([], [])
        x = [x for x in stringFinder._findliterals('a', '')]
        self.assertEqual(x, [])
        
        x = [x for x in stringFinder._findliterals('test', 'tsetabctesdeestf')]
        self.assertEqual(x, [])
        
    def test_findRegex_True(self):
        stringFinder = StringFinder([], [])
        x = [x for x in stringFinder._findregex(r"[0-9]{2}", '123')]
        self.assertEqual(x, [[0, 2]])
        
        x = [x for x in stringFinder._findregex(r"[0-9]{2}", '1234')]
        self.assertEqual(x, [[0, 2], [2, 4]])
        
        x = [x for x in stringFinder._findregex(r"[A-Z]{1}[a-z]*\s?.*\.+\s", 'Silas A. Kraume')]
        self.assertEqual(x, [[0, 9]])
        
        x = [x for x in stringFinder._findregex(r"[A-Z]{1}[a-z]*\s?.*\.+\s", 'silas A. Kraume')]
        self.assertEqual(x, [[6, 9]])
        
    def test_findRegex_False(self):
        stringFinder = StringFinder([], [])
        x = [x for x in stringFinder._findregex(r"[A-Z]{1}[a-z]+\s?.*\.+\s", 'silas A. Kraume')]
        self.assertEqual(x, [])
        
    def test_optimizeIntervals(self):
        stringFinder = StringFinder([], [])
        x = stringFinder._optimizeIntervals([[1, 3], [3, 5]])
        self.assertEqual(x, [[1, 5]])
        
        x = stringFinder._optimizeIntervals([[1, 10], [5, 10]])
        self.assertEqual(x, [[1, 10]])
        
        x = stringFinder._optimizeIntervals([[1, 3], [2, 5], [6, 8]])
        self.assertEqual(x, [[1, 5], [6, 8]])
        
        x = stringFinder._optimizeIntervals([[1, 3], [-5, 0], [0, 2]])
        self.assertEqual(x, [[-5, 3]])
        
    def test_optimizeIntervals_empty(self):
        stringFinder = StringFinder([], [])
        x = stringFinder._optimizeIntervals([])
        self.assertEqual(x, [])
        
    def test_findKeywords(self):
        stringFinder = StringFinder(['Is', 'Test', 'Not'], [r"[0-9]\!"])
        line = 'ThisIsATest!1!'
        intervals, fKeyWords, mKeywords = stringFinder.findKeywords(line)
        
        self.assertCountEqual(intervals, [[14, 'reset_matched'], [12, 'matched_pattern'], [11, 'reset_found'], [7, 'found_keyword'], [6, 'reset_found'], [4, 'found_keyword']])
        self.assertEqual(fKeyWords, [('Is', [4, 6]), ('Test', [7, 11])])
        self.assertEqual(mKeywords, [(r"[0-9]\!", [12, 14])])