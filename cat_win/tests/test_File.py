from unittest import TestCase

from cat_win.util.File import File
# import sys
# sys.path.append('../cat_win')


class TestFile(TestCase):
    def test_file_default(self):
        file = File('TestPath', 'TestName')
        
        self.assertEqual(file.containsQueried, False)
        self.assertEqual(file.path, 'TestPath')
        self.assertEqual(file.displayname, 'TestName')
        
    def test_file_queried(self):
        file = File('TestPath', 'TestName')
        self.assertEqual(file.containsQueried, False)
        
        file.setContainsQueried(False)
        self.assertEqual(file.containsQueried, False)
        
        file.setContainsQueried(True)
        self.assertEqual(file.containsQueried, True)
        
        file.setContainsQueried(False)
        self.assertEqual(file.containsQueried, True)

# python -m unittest discover -s tests -p test*.py
