from cat_win.util.FileAttributes import _convert_size
from unittest import TestCase
import os
# import sys
# sys.path.append('../cat_win')


class TestConverter(TestCase):
    def test__convert_size_zero(self):
        self.assertEqual(_convert_size(0), '0 B')
        
    def test__convert_size_EdgeKB(self):
        self.assertEqual(_convert_size(1023), '1023.0 B')
    
    def test__convert_size_KB(self):
        self.assertEqual(_convert_size(1024), '1.0 KB')
        
    def test__convert_size_KB(self):
        self.assertEqual(_convert_size(1836), '1.79 KB')
        
    def test__convert_size_RoundKB(self):
        self.assertEqual(_convert_size(2044), '2.0 KB')
        
    def test__convert_size_TB(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024), '1.0 TB')
        
    def test__convert_size_UnevenTB(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024 * 2.3), '2.3 TB')
        
    def test__convert_size_YB(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024), '1.0 YB')
        
    def test__convert_size_EdgeYB(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024 * 1023.99), '1023.99 YB')
        
    def test__convert_size_OutOfRange(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024*1024), '1.0 ?')
