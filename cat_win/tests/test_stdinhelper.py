from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdInMock
from cat_win.util.stdinhelper import path_parts, get_stdin_content


class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']

        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])

    @patch('cat_win.util.stdinhelper.stdin', StdInMock('hello\nworld'))
    def test_get_stdin_content_oneline(self):
        self.assertEqual(''.join(get_stdin_content(True)), 'hello')

    @patch('cat_win.util.stdinhelper.stdin', StdInMock(f"hello{chr(26)}\n"))
    def test_get_stdin_content_oneline_eof(self):
        self.assertEqual(''.join(get_stdin_content(True)), 'hello')

    @patch('cat_win.util.stdinhelper.stdin', StdInMock('hello\nworld'))
    def test_get_stdin_content(self):
        self.assertEqual(''.join(get_stdin_content(False)), 'hello\nworld\n')

    @patch('cat_win.util.stdinhelper.stdin', StdInMock(f"hello\nworld{chr(26)}\n"))
    def test_get_stdin_content_eof(self):
        self.assertEqual(''.join(get_stdin_content(False)), 'hello\nworld')
