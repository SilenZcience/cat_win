from unittest import TestCase

from cat_win.src.domain.file import File
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

    def test_file_filesize(self):
        file = File('testPath', 'testName')
        self.assertEqual(file.file_size, -1)

        file.set_file_size(1024)
        self.assertEqual(file.file_size, 1024)

    def test_file_hashable(self):
        file = File('testPath', 'testName')
        file2 = File('testPath', 'testName')
        self.assertSetEqual({file, file2}, {file2})

    def test_file_equality(self):
        file = File('testPath', 'testName')
        file2 = File('testPath', 'testName')
        self.assertEqual(file, file2)

        file = File('testPath1', 'testName')
        file2 = File('testPath2', 'testName')
        self.assertNotEqual(file, file2)
