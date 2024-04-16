from unittest.mock import patch
from unittest import TestCase
import os

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.service.helper.zipviewer import display_zip
# import sys
# sys.path.append('../cat_win')
test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_zip_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'resources')
test_zip_file_path  = os.path.abspath(os.path.join(test_zip_file_dir, 'test.zip'))


class TestZipviewer(TestCase):
    maxDiff = None

    def test_display_zip_bad_file(self):
        self.assertEqual(display_zip('', lambda x: x), False)
        self.assertEqual(display_zip(test_file_path, lambda x: x), False)

    @patch('sys.stderr', new=StdOutMock())
    def test_display_zip(self):
        self.assertEqual(display_zip(test_zip_file_path, lambda x: x), True)

    def test_display_zip_output(self):
        expected_output = f"The file '{test_zip_file_path}' has been detected to be a zip-file. "
        expected_output += 'The archive contains the following files:\n'
        expected_output += 'FileName       FileSize CompressedFileSize\n'
        expected_output += 'test.txt            189                145\n'
        expected_output += 'test_empty.txt        0                  0\n'
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            display_zip(test_zip_file_path, lambda x: x)
            self.assertEqual(fake_out.getvalue(), expected_output)
