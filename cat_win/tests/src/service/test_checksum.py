from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.service.checksum import get_checksum_from_file, print_checksum
# import sys
# sys.path.append('../cat_win')


test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')


class TestChecksum(TestCase):
    maxDiff = None

    def test_checksum(self):
        expected_output = ''
        expected_output += '\tCRC32:   C7222F64\n'
        expected_output += '\tMD5:     0f85f8d2b6783c06d40755ab54906862\n'
        expected_output += '\tSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934\n'
        expected_output += '\tSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3'
        expected_output += 'ed314dea394cafdfd1749f\n'
        expected_output += '\tSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490'
        expected_output += 'b48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3c'
        expected_output += 'c49bd82ce9e8527412ce2cc8355a391a1\n'
        self.assertEqual(get_checksum_from_file(test_file_path), expected_output)

    def test_checksum_colored(self):
        expected_output = ''
        expected_output += '\tXCRC32:   C7222F64Y\n'
        expected_output += '\tXMD5:     0f85f8d2b6783c06d40755ab54906862Y\n'
        expected_output += '\tXSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934Y\n'
        expected_output += '\tXSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3e'
        expected_output += 'd314dea394cafdfd1749fY\n'
        expected_output += '\tXSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490b'
        expected_output += '48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3cc49'
        expected_output += 'bd82ce9e8527412ce2cc8355a391a1Y\n'
        self.assertEqual(get_checksum_from_file(test_file_path, ['X', 'Y']), expected_output)

    def test_checksum_invalid_file(self):
        self.assertIn(get_checksum_from_file('randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), ['FileNotFoundError', 'OSError'])

    def test_print_checksum(self):
        expected_output = f"XChecksum of '{test_file_path}':Y\n"
        expected_output += '\tXCRC32:   C7222F64Y\n'
        expected_output += '\tXMD5:     0f85f8d2b6783c06d40755ab54906862Y\n'
        expected_output += '\tXSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934Y\n'
        expected_output += '\tXSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3e'
        expected_output += 'd314dea394cafdfd1749fY\n'
        expected_output += '\tXSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490b'
        expected_output += '48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3cc49'
        expected_output += 'bd82ce9e8527412ce2cc8355a391a1Y\n\n'
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            print_checksum(test_file_path, 'X', 'Y')
            self.assertEqual(fake_out.getvalue(), expected_output)
