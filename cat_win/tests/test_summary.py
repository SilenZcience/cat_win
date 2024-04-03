from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.tests.mocks.std import StdOutMock
from cat_win.util.helper.file import File
from cat_win.util.service.summary import Summary

test_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'test.txt')


class TestSummary(TestCase):
    def test_show_dirs(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_dirs(['dirA', 'dirB'])
            self.assertIn('dirA', fake_out.getvalue())
            self.assertIn('dirB', fake_out.getvalue())

    def test_show_dirs_empty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_dirs([])
            self.assertEqual('No directores have been found!\n', fake_out.getvalue())

    def test_show_sum(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_sum(False, None, None, 15)
            self.assertEqual(fake_out.getvalue(), "Lines (Sum): 15\n")

    def test_show_sum_detailed(self):
        output = r"""File LineCount
test 111

Lines (Sum): 11
"""
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Summary.show_sum(True, {'test': 111}, 0, 11)
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

    def test_show_charcount(self):
        output = r"""
' ': 23
i: 15
a: 13
e: 13
s: 9
'\n': 7
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
