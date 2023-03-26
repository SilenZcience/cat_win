from cat_win.util.StdInHelper import path_parts
from unittest import TestCase


class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']
        
        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])