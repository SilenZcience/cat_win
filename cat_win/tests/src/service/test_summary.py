from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.src.const.colorconstants import CKW
from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.domain.file import File
from cat_win.src.service.summary import Summary, _unique_list

test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')


class TestSummary(TestCase):
    def test__unique_list(self):
        self.assertListEqual(_unique_list([1, 2, 3, 1, 2, 3]), [1, 2, 3])
        self.assertListEqual(_unique_list([1, 3, 3, 3, 2, 3]), [1, 3, 2])
        self.assertListEqual(_unique_list([]), [])
        self.assertListEqual(_unique_list([1]), [1])
        self.assertListEqual(_unique_list([5, 1]), [5, 1])

    def test_show_files_empty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_files([], False)
            self.assertEqual('No files have been found!\n', fake_out.getvalue())

    def test_show_dirs(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_dirs(['dirA', 'dirB', 'dirB'])
            self.assertIn('dirA', fake_out.getvalue())
            self.assertIn('dirB', fake_out.getvalue())
            self.assertEqual(fake_out.getvalue().count('dirB'), 2)

    @patch('cat_win.src.service.summary.Summary.unique', True)
    def test_show_dirs_unique(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_dirs(['dirA', 'dirB', 'dirB'])
            self.assertIn('dirA', fake_out.getvalue())
            self.assertIn('dirB', fake_out.getvalue())
            self.assertEqual(fake_out.getvalue().count('dirB'), 1)

    def test_show_dirs_empty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_dirs([])
            self.assertEqual('No directores have been found!\n', fake_out.getvalue())

    def test_show_sum(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_sum([File('1', '1'), File('2', '2')], False,
                             {'1': 8, '2': 7}, 0)
            self.assertEqual(fake_out.getvalue(), "Lines (Sum): 15\n")

    def test_show_sum_detailed(self):
        output = r"""File LineCount
test 111
test 111

Lines (Sum): 222
"""
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_sum([File('test', ''), File('test', '')], True, {'test': 111}, 0)
            self.assertEqual(fake_out.getvalue(), output)

    @patch('cat_win.src.service.summary.Summary.unique', True)
    def test_show_sum_detailed_unique(self):
        output = r"""File LineCount
test 111

Lines (Sum): 111
"""
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_sum([File('test', ''), File('test', '')], True, {'test': 111}, 0)
            self.assertEqual(fake_out.getvalue(), output)

    def test_show_wordcount(self):
        output = r"""
:: 5
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
∑: 1
"""
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_wordcount([File(test_file_path, '')], 'utf-8')
            self.assertIn(output, fake_out.getvalue())

    def test_show_wordcount_empty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_wordcount([], 'utf-8')
            self.assertEqual('The word count could not be calculated.\n', fake_out.getvalue())

    def test_show_charcount(self):
        output = r"""
' ': 23
i: 15
a: 13
e: 13
s: 9
'\n': 7
'\r': 7
T: 7
h: 7
l: 6
t: 6
:: 5
n: 5
p: 5
r: 5
c: 4
m: 4
L: 3
S: 3
o: 3
u: 3
!: 2
-: 2
C: 2
D: 2
y: 2
'\t': 1
<: 1
>: 1
A: 1
E: 1
N: 1
b: 1
f: 1
g: 1
w: 1
x: 1
Ä: 1
Ö: 1
Ü: 1
ä: 1
ö: 1
ü: 1
∑: 1
"""
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_charcount([File(test_file_path, '')], 'utf-8')
            self.assertIn(output, fake_out.getvalue())

    def test_show_charcount_empty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_charcount([], 'utf-8')
            self.assertEqual('The char count could not be calculated.\n', fake_out.getvalue())

    @patch('cat_win.src.service.summary.Summary.unique', True)
    @patch('cat_win.src.service.summary.get_file_size', lambda *_: 10)
    @patch('cat_win.src.service.summary._convert_size', lambda v: f'{v}B')
    def test_show_files_non_empty_unique(self):
        file_a = File('a.txt', 'A')
        file_b = File('b.bin', 'B')
        file_b.set_plaintext(False)
        file_b.set_contains_queried(True)
        file_b.set_file_size(3)

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_files([file_a, file_b, file_b], True)
            output = fake_out.getvalue()
            self.assertIn('found FILE(s):', output)
            self.assertIn('  A', output)
            self.assertIn('-*B', output)
            self.assertIn('Sum:        13B', output)
            self.assertIn('Amount:\t2', output)
            self.assertEqual(file_a.file_size, 10)

    @patch('cat_win.src.service.summary.Summary.unique', True)
    @patch('cat_win.src.service.summary.IoHelper.read_file', lambda *_args, **_kwargs: 'alpha beta alpha')
    def test_show_wordcount_unique_files(self):
        dup_file = File('same.txt', 'same-display')

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_wordcount([dup_file, dup_file], 'utf-8')
            output = fake_out.getvalue()
            self.assertIn('The word count includes the following files:', output)
            self.assertEqual(output.count('same-display'), 1)

    @patch('cat_win.src.service.summary.IoHelper.read_file')
    def test_show_wordcount_ignores_read_errors(self, mock_read_file):
        def _read(path, **_kwargs):
            if str(path) == 'bad.txt':
                raise OSError('cannot read')
            return 'ok ok'

        mock_read_file.side_effect = _read
        bad_file = File('bad.txt', 'bad-display')
        good_file = File('good.txt', 'good-display')

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_wordcount([bad_file, good_file], 'utf-8')
            output = fake_out.getvalue()
            self.assertIn('The word count includes the following files:', output)
            self.assertIn('good-display', output)
            self.assertNotIn('bad-display', output)

    @patch('cat_win.src.service.summary.Summary.unique', True)
    @patch('cat_win.src.service.summary.IoHelper.read_file')
    def test_show_charcount_unique_and_ignores_read_errors(self, mock_read_file):
        def _read(path, **_kwargs):
            if str(path) == 'bad-char.txt':
                raise UnicodeError('decode fail')
            return 'aa'

        mock_read_file.side_effect = _read
        bad_file = File('bad-char.txt', 'bad-char-display')
        good_file = File('good-char.txt', 'good-char-display')

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_charcount([good_file, good_file, bad_file], 'utf-8')
            output = fake_out.getvalue()
            self.assertIn('The char count includes the following files:', output)
            self.assertEqual(output.count('good-char-display'), 1)
            self.assertNotIn('bad-char-display', output)

    def test_set_flags(self):
        backup = Summary.unique
        Summary.set_flags(True)
        self.assertTrue(Summary.unique)
        Summary.set_flags(False)
        self.assertFalse(Summary.unique)
        Summary.set_flags(backup)

    def test_set_colors(self):
        backup_color = Summary.COLOR
        backup_color_reset = Summary.COLOR_RESET
        color_dic = {
            CKW.SUMMARY: 'red',
            CKW.RESET_ALL: 'reset'
        }
        Summary.set_colors(color_dic)
        self.assertEqual(Summary.COLOR, 'red')
        self.assertEqual(Summary.COLOR_RESET, 'reset')
        color_dic = {
            CKW.SUMMARY: backup_color,
            CKW.RESET_ALL: backup_color_reset
        }
        Summary.set_colors(color_dic)
