from unittest import TestCase
import os

from cat_win.util.checksum import get_checksum_from_file
# import sys
# sys.path.append('../cat_win')


test_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'test.txt')


class TestChecksum(TestCase):
    def test_checksum(self):
        expected_output = ''
        expected_output += '\tCRC32:   C7222F64\n'
        expected_output += '\tMD5:     0f85f8d2b6783c06d40755ab54906862\n'
        expected_output += '\tSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934\n'
        expected_output += '\tSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3ed314dea394cafdfd1749f\n'
        expected_output += '\tSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490b48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3cc49bd82ce9e8527412ce2cc8355a391a1\n'
        self.assertEqual(get_checksum_from_file(test_file_path), expected_output)

    def test_checksum_colored(self):
        expected_output = ''
        expected_output += '\tXCRC32:   C7222F64Y\n'
        expected_output += '\tXMD5:     0f85f8d2b6783c06d40755ab54906862Y\n'
        expected_output += '\tXSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934Y\n'
        expected_output += '\tXSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3ed314dea394cafdfd1749fY\n'
        expected_output += '\tXSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490b48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3cc49bd82ce9e8527412ce2cc8355a391a1Y\n'
        self.assertEqual(get_checksum_from_file(test_file_path, ['X', 'Y']), expected_output)

# python -m unittest discover -s tests -p test*.py
