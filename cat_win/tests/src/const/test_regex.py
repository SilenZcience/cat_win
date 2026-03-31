from unittest import TestCase

from cat_win.src.const.regex import *


class TestRegex(TestCase):
    def test_compile_re_case(self):
        pattern = r'\d+'
        regex = compile_re(pattern, False)
        self.assertIsNotNone(regex)
        self.assertEqual(regex.pattern, pattern)
        self.assertNotEqual(regex.flags & re.IGNORECASE, re.IGNORECASE)

    def test_compile_re_nocase(self):
        pattern = r'\d+'
        regex = compile_re(pattern, True)
        self.assertIsNotNone(regex)
        self.assertEqual(regex.pattern, pattern)
        self.assertEqual(regex.flags & re.IGNORECASE, re.IGNORECASE)
