from cat_win.util.checksum import getChecksumFromFile
from unittest.mock import patch
from unittest import TestCase
import os
import sys
sys.path.append("../cat_win")


script_dir = os.path.dirname(__file__)
test_file_dir = script_dir + "/test.txt"


class TestChecksum(TestCase):
    def test_checksum(self):
        expected_output = ""
        expected_output += "\tCRC23:   C7222F64\n"
        expected_output += "\tMD5:     0f85f8d2b6783c06d40755ab54906862\n"
        expected_output += "\tSHA1:    1c50f01c5be5fc4795817e14f5deccbd51bf0934\n"
        expected_output += "\tSHA256:  dfb46efd198ad4b1204308c2be1c5e0254effe0de3ed314dea394cafdfd1749f\n"
        expected_output += "\tSHA512:  bf35256e790288a6dbf93b7327e1f97840349e0490b48848273663d34ad493e73a325df6725d7b0d5eb680d751bfe3cc49bd82ce9e8527412ce2cc8355a391a1\n"
        self.assertEqual(getChecksumFromFile(test_file_dir), expected_output)

# python -m unittest discover -s tests -p test*.py
