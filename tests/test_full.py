from cat_win.cat import main
from unittest.mock import patch
from unittest import TestCase
from io import StringIO
from _pytest.capture import DontReadFromInput
import os
# import sys
# sys.path.append("../cat_win")


test_file_dir = os.path.dirname(__file__) + '/texts/'
test_file_path = test_file_dir + "test.txt"


class StdOutMock(StringIO):
    def reconfigure(self, encoding = None):
        return

    def fileno(self):
        return 0
    
class StdInMock(DontReadFromInput):
    def reconfigure(self, encoding = None):
        return


@patch('cat_win.cat.sys.stdin', StdInMock())
class TestCat(TestCase):
    maxDiff = None

    # no files parsed
    @patch('cat_win.cat.sys.argv', ['<CAT>', '-xn', '-col', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_A(self):
        expected_output = ''
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '-xn', '-col', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_B(self):
        expected_output = ''
        with open(test_file_dir + 'full_test_result_B.txt', 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=ansi', test_file_path, '-sb', '[Sample,TEST]', '-col', '-xle'])
    def test_cat_output_full_C(self):
        expected_output = ''
        with open(test_file_dir + 'full_test_result_C.txt', 'r', encoding='ansi') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=utf-8', test_file_path, 'trunc=2:6', '-n', '--reverse', '-col', '-t'])
    def test_cat_output_full_D(self):
        expected_output = ''
        with open(test_file_dir + 'full_test_result_D.txt', 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            main()
            self.assertEqual(fake_out.getvalue(), expected_output)
# python -m unittest discover -s tests -p test*.py