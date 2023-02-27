import cat_win.cat as cat
import cat_win.util.ArgParser as ArgParser
from unittest.mock import patch
from unittest import TestCase
from io import StringIO
import os
# import sys
# sys.path.append('../cat_win')

test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path = os.path.join(test_file_dir, 'test.txt')
test_result_B = os.path.join(test_file_dir, 'full_test_result_B.txt')
test_result_C = os.path.join(test_file_dir, 'full_test_result_C.txt')
test_result_D = os.path.join(test_file_dir, 'full_test_result_D.txt')


class StdOutMock(StringIO):
    def reconfigure(self, encoding = None):
        return

    def fileno(self):
        return 0
    
# class StdInMock(DontReadFromInput):
class StdInMock:
    def reconfigure(self, encoding = None):
        return


@patch('cat_win.cat.sys.stdin', StdInMock())
class TestCatFull(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._CalculateLinePrefixSpacing.cache_clear()
        cat._CalculateLineLengthPrefixSpacing.cache_clear()
        ArgParser.FILE_ENCODING = 'utf-8'
        ArgParser.FILE_TRUNCATE = [None, None, None]
        for i in range(len(cat.holder.args_id)):
            cat.holder.args_id[i] = False
    
    # no files parsed
    @patch('cat_win.cat.sys.argv', ['<CAT>', '-ln', '--nc', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_A(self):
        expected_output = ''
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, '-ln', '--nc', '[::-2]', 'enc=utf8'])
    def test_cat_output_full_B(self):
        expected_output = ''
        with open(test_result_B, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc:UTF-8', test_file_path, '-ub', '[Sample,TEST]', '--nc', '-le'])
    def test_cat_output_full_C(self):
        expected_output = ''
        with open(test_result_C, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', 'enc=utf-8', test_file_path, 'trunc=2:6', '-n', '--reverse', '--nc', '-t'])
    def test_cat_output_full_D(self):
        expected_output = ''
        with open(test_result_D, 'r', encoding='utf-8') as output:
            expected_output = output.read()
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=cp1252', '--nc'])
    def test_cat_output_full_Cp1252(self):
        expected_output = ''
        with open(test_file_path, 'r', encoding='cp1252') as output:
            expected_output = output.read() + '\n'
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    @patch('cat_win.cat.sys.argv', ['<CAT>', test_file_path, 'enc=latin_1', '--nc'])
    def test_cat_output_full_Latin1(self):
        expected_output = ''
        with open(test_file_path, 'r', encoding='latin_1') as output:
            expected_output = output.read() + '\n'
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), expected_output)

# python -m unittest discover -s tests -p test*.py