from unittest import TestCase
from unittest.mock import patch

from cat_win.util.StdInHelper import path_parts, getStdInContent

class StdInMockIter:
    def __init__(self, mock: object) -> None:
        self.input_value = mock.input_value
        self.splitted_input_value = self.input_value.split('\n')
        self.index = -1
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.index < len(self.splitted_input_value)-1:
            self.index += 1
            return self.splitted_input_value[self.index] + '\n'
        raise StopIteration

class StdInMock:
    def __init__(self, input_value: str) -> None:
        self.input_value = input_value
    
    def readline(self) -> str:
        return self.input_value.split('\n')[0] + '\n'
    
    def __iter__(self):
        return StdInMockIter(self)

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