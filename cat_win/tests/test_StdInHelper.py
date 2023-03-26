from cat_win.util.StdInHelper import path_parts
from unittest import TestCase


class TestStdInHelper(TestCase):
    def test_path_parts(self):
        expected_output = ['C:/', 'a', 'b', 'c', 'd.txt']
        
        self.assertListEqual(path_parts('C:/a/b/c/d.txt'), expected_output)