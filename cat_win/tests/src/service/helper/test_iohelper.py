from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.tests.mocks.std import StdInMock
from cat_win.src.service.helper.iohelper import IoHelper, path_parts


test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')

stdin_mock = StdInMock()


@patch('sys.stdin', stdin_mock)
class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']

        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])

    def test_get_newline(self):
        self.assertEqual(IoHelper.get_newline(test_file_path), '\r\n')
        self.assertEqual(IoHelper.get_newline(test_file_path_empty), '\n')
        self.assertEqual(IoHelper.get_newline(test_file_path_oneline), '\n')

    def test_get_stdin_content_oneline(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(IoHelper.get_stdin_content(True)), 'hello')

    def test_get_stdin_content_oneline_eof(self):
        stdin_mock.set_content(f"hello{chr(26)}\n")
        self.assertEqual(''.join(IoHelper.get_stdin_content(True)), 'hello')

    def test_get_stdin_content(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(IoHelper.get_stdin_content(False)), 'hello\nworld\n')

    def test_get_stdin_content_eof(self):
        stdin_mock.set_content(f"hello\nworld{chr(26)}\n")
        self.assertEqual(''.join(IoHelper.get_stdin_content(False)), 'hello\nworld')
