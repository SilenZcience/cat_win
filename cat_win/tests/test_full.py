from unittest.mock import patch
from unittest import TestCase
import os

from cat_win import cat
from cat_win.tests.mocks.std import StdInMock, StdOutMock, StdOutMockIsAtty
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
test_eval       = os.path.join(test_file_dir, 'full_test_eval.txt')


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

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', 'enc:UTF-8', test_file_path, '-ub', '[Sample,TEST]', '-le'])
    def test_cat_output_full_c(self):
        expected_output = ''
        with open(test_result_C, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', 'enc=utf-8', test_file_path, 'trunc=1:6', '-n', '--reverse', '--chr'])
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

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=ple ', 'match=:'])
    def test_cat_output_full_find_found(self):
        expected_output = "Sample Text:\n--------------- Found [('ple ', [3, 7])] ------"
        expected_output += "---------\n--------------- Matched [(':', [11, 12])] ---------------\n"
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=NOTINLINE'])
    def test_cat_output_full_find_not_found(self):
        expected_output = 'Sample Text:\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', test_file_path, 'enc=utf-8', 'trunc=0:1', 'find=Text', '--nk'])
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
        expected_output = """\
1
2
3
4
5
           :
          (11)
           :
6
7
8
9
10
"""
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=utf-8', '--eval', '--dec', test_eval])
    def test_cat_output_full_eval(self):
        expected_output = '14 [Bin: 0b1110, Oct: 0o16, Hex: 0xe]\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, test_empty_path, test_peek, '-F'])
    def test_cat_output_full_show_files(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertIn(test_file_path, fake_out.getvalue())
            self.assertIn(test_empty_path, fake_out.getvalue())
            self.assertIn(test_peek, fake_out.getvalue())

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, test_empty_path, test_peek, '-S'])
    def test_cat_output_full_show_count(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertIn(test_file_path, fake_out.getvalue())
            self.assertIn(test_empty_path, fake_out.getvalue())
            self.assertIn(test_peek, fake_out.getvalue())

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '-W'])
    def test_cat_output_full_show_wordcount(self):
        contains = """:: 5
is: 4
Line: 3
This: 3
a: 3
!: 2
-: 2
Duplicate: 2
<: 1
>: 1
Ary: 1
Character: 1
Chars: 1
Empty: 1
N: 1
Sample: 1
Special: 1
Summation: 1
Tab: 1
Text: 1
The: 1
These: 1
are: 1
following: 1
äöüÄÖÜ: 1
∑: 1"""
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertIn(contains, fake_out.getvalue())

    @patch('cat_win.cat.sys.argv',
           ['<CAT>', test_file_path, 'trunc=0:0', '--UNIQUE', '--b64', '-?'])
    def test_cat_output_suggestions(self):
        with patch('cat_win.cat.sys.stderr', new=StdOutMockIsAtty()) as fake_out:
            cat.main()
            self.assertIn("Unknown argument: '--UNIQUE'", fake_out.getvalue())
            self.assertIn("Did you mean --unique", fake_out.getvalue())
            self.assertIn("Unknown argument: '--b64'", fake_out.getvalue())
            self.assertIn("Did you mean --b64d or --b64e", fake_out.getvalue())
            self.assertIn("Unknown argument: '-?'", fake_out.getvalue())

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '--GREP', 'find=T'])
    def test_cat_output_grep_upper(self):
        expected_output = 'T\nT,T\nT\nT\nT\nT\n'
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(expected_output, fake_out.getvalue())

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '--sort'])
    def test_cat_output_sort(self):
        expected_output = """\

N-Ary Summation: ∑
Sample Text:
The following Line is Empty:
These are Special Chars: äöüÄÖÜ
This is a Tab-Character: >\t<
This Line is a Duplicate!
This Line is a Duplicate!
"""
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(expected_output, fake_out.getvalue())

    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '--peek', '--hexview'])
    def test_cat_output_raw(self):
        expected_output = """\
Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text                   
00000000 53 61 6d 70 6c 65 20 54 65 78 74 3a 0d 0a 54 68 # S a m p l e   T e x t : ␍ ␤ T h
00000010 69 73 20 69 73 20 61 20 54 61 62 2d 43 68 61 72 # i s   i s   a   T a b - C h a r
00000020 61 63 74 65 72 3a 20 3e 09 3c 0d 0a 54 68 65 73 # a c t e r :   > ␉ < ␍ ␤ T h e s
00000030 65 20 61 72 65 20 53 70 65 63 69 61 6c 20 43 68 # e   a r e   S p e c i a l   C h
00000040 61 72 73 3a 20 c3 a4 c3 b6 c3 bc c3 84 c3 96 c3 # a r s :   · · · · · · · · · · ·
                                :
                               (2)
                                :
00000070 6c 6f 77 69 6e 67 20 4c 69 6e 65 20 69 73 20 45 # l o w i n g   L i n e   i s   E
00000080 6d 70 74 79 3a 0d 0a 0d 0a 54 68 69 73 20 4c 69 # m p t y : ␍ ␤ ␍ ␤ T h i s   L i
00000090 6e 65 20 69 73 20 61 20 44 75 70 6c 69 63 61 74 # n e   i s   a   D u p l i c a t
000000A0 65 21 0d 0a 54 68 69 73 20 4c 69 6e 65 20 69 73 # e ! ␍ ␤ T h i s   L i n e   i s
000000B0 20 61 20 44 75 70 6c 69 63 61 74 65 21          #   a   D u p l i c a t e !

"""
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(expected_output, '\n'.join(fake_out.getvalue().split('\n')[1:]))

# python -m unittest discover -s cat_win.tests -p test*.py
