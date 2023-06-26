from unittest.mock import patch
from unittest import TestCase
import os

from cat_win import cat
from cat_win.tests.mocks.std import StdInMock, StdOutMock
from cat_win.util.argparser import ArgParser
from cat_win.util.holder import Holder
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_empty_path = os.path.join(test_file_dir, 'test_empty.txt')
test_peek       = os.path.join(test_file_dir, 'test_peek.txt')
test_result_B   = os.path.join(test_file_dir, 'full_test_result_B.txt')
test_result_C   = os.path.join(test_file_dir, 'full_test_result_C.txt')
test_result_D   = os.path.join(test_file_dir, 'full_test_result_D.txt')


@patch('cat_win.cat.sys.stdin', StdInMock())
class TestCatFull(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()
        cat.arg_parser = ArgParser()
        cat.holder = Holder()

    # no files parsed
    @patch('cat_win.cat.sys.argv', ['<CAT>', '-ln', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_a(self):
        expected_output = ''
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '-ln', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_b(self):
        expected_output = ''
        with open(test_result_B, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc:UTF-8', test_file_path, '-ub', '[Sample,TEST]', '-le'])
    def test_cat_output_full_c(self):
        expected_output = ''
        with open(test_result_C, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=utf-8', test_file_path, 'trunc=2:6', '-n', '--reverse', '-t'])
    def test_cat_output_full_d(self):
        expected_output = ''
        with open(test_result_D, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'trunc=0:0',])
    def test_cat_output_full_empty(self):
        expected_output = ''
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=cp1252'])
    def test_cat_output_full_cp1252(self):
        expected_output = ''
        with open(test_file_path, 'r', encoding='cp1252') as output:
            expected_output = output.read() + '\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=latin_1'])
    def test_cat_output_full_latin1(self):
        expected_output = ''
        with open(test_file_path, 'r', encoding='latin_1') as output:
            expected_output = output.read() + '\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=ple ', 'match=:'])
    def test_cat_output_full_find_found(self):
        expected_output = "Sample Text:\n--------------- Found [('ple ', [3, 7])] ---------------\n--------------- Matched [(':', [11, 12])] ---------------\n"
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=NOTINLINE'])
    def test_cat_output_full_find_not_found(self):
        expected_output = 'Sample Text:\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=Text', '--nk'])
    def test_cat_output_full_find_found_nokeyword(self):
        expected_output = ''
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=utf-8', 'find=Text', '--grep'])
    def test_cat_output_full_find_found_grep(self):
        expected_output = 'Sample Text:\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_peek, 'enc=utf-8', '--peek'])
    def test_cat_output_full_peek(self):
        expected_output = """1
2
3
4
5
           •
          (11)
           •
6
7
8
9
10
"""
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=utf-8', '--eval', '--dec', '-E', '5 + 5 * 5 // 2 - 3'])
    def test_cat_output_full_eval(self):
        expected_output = '14 {Hexadecimal: 0xe; Binary: 0b1110}\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

# python -m unittest discover -s cat_win.tests -p test*.py
