from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdInMock
from cat_win.util.StdInHelper import path_parts, getStdInContent


class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']
        
        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])
    
    @patch('cat_win.util.StdInHelper.stdin', StdInMock(f"hello\nworld"))
    def test_getStdInContent_oneline(self):
        self.assertEqual(''.join(getStdInContent(True)), 'hello')
        
    @patch('cat_win.util.StdInHelper.stdin', StdInMock(f"hello{chr(26)}\n"))
    def test_getStdInContent_oneline_eof(self):
        self.assertEqual(''.join(getStdInContent(True)), 'hello')
        
    @patch('cat_win.util.StdInHelper.stdin', StdInMock(f"hello\nworld"))
    def test_getStdInContent(self):
        self.assertEqual(''.join(getStdInContent(False)), 'hello\nworld\n')
        
    @patch('cat_win.util.StdInHelper.stdin', StdInMock(f"hello\nworld{chr(26)}\n"))
    def test_getStdInContent_eof(self):
        self.assertEqual(''.join(getStdInContent(False)), 'hello\nworld')