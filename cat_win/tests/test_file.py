from unittest import TestCase

from cat_win.util.helper.file import File
# import sys
# sys.path.append('../cat_win')


class TestFile(TestCase):
    def test_file_default(self):
        file = File('TestPath', 'TestName')

        self.assertEqual(file.contains_queried, False)
        self.assertEqual(file.path, 'TestPath')
        self.assertEqual(file.displayname, 'TestName')

    def test_file_queried(self):
        file = File('TestPath', 'TestName')
        self.assertEqual(file.contains_queried, False)

        file.set_contains_queried(False)
        self.assertEqual(file.contains_queried, False)

        file.set_contains_queried(True)
        self.assertEqual(file.contains_queried, True)

        file.set_contains_queried(False)
        self.assertEqual(file.contains_queried, True)

    def test_file_plaintext(self):
        file = File('testPath', 'testName')
        self.assertEqual(file.plaintext, True)

        file.set_plaintext(False)
        self.assertEqual(file.plaintext, False)
