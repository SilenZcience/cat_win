from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdInMock
from cat_win.util.helper.stdinhelper import path_parts, get_stdin_content


stdin_mock = StdInMock()


@patch('sys.stdin', stdin_mock)
class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']

        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])

    def test_get_stdin_content_oneline(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(get_stdin_content(True)), 'hello')

    def test_get_stdin_content_oneline_eof(self):
        stdin_mock.set_content(f"hello{chr(26)}\n")
        self.assertEqual(''.join(get_stdin_content(True)), 'hello')

    def test_get_stdin_content(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(get_stdin_content(False)), 'hello\nworld\n')

    def test_get_stdin_content_eof(self):
        stdin_mock.set_content(f"hello\nworld{chr(26)}\n")
        self.assertEqual(''.join(get_stdin_content(False)), 'hello\nworld')
