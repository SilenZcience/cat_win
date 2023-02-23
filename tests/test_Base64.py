from cat_win.util.Base64 import encodeBase64, decodeBase64
from unittest import TestCase
# import sys
# sys.path.append('../cat_win')


class TestBase64(TestCase):
    def test_encodeBase64(self):
        test_input = [('', 'Test'),
                      ('', '123404'),
                      ('', 'ÄÖÜ  TEST')]
        expected_output = [('', 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU')]
        self.assertEqual(encodeBase64(test_input), expected_output)

    def test_decodeBase64(self):
        test_input = [('', 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU')]
        expected_output = [('', 'Test'),
                           ('', '123404'),
                           ('', 'ÄÖÜ  TEST')]
        self.assertEqual(decodeBase64(test_input), expected_output)

    def test_decodeBase64_lineBreak(self):
        test_input = [('', 'VGVzdAoxMjM0MDQKw4'),
                      ('', 'TDlsOcICBURVNU')]
        expected_output = [('', 'Test'),
                           ('', '123404'),
                           ('', 'ÄÖÜ  TEST')]
        self.assertEqual(decodeBase64(test_input), expected_output)

# python -m unittest discover -s tests -p test*.py
