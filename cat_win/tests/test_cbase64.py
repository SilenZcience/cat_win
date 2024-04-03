from unittest import TestCase

from cat_win.util.service.cbase64 import encode_base64, decode_base64
# import sys
# sys.path.append('../cat_win')


class TestBase64(TestCase):
    def test_encode_base64(self):
        test_input = [('', 'Test'),
                      ('', '123404'),
                      ('', 'ÄÖÜ  TEST')]
        expected_output = [('', 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU')]
        self.assertEqual(encode_base64(test_input), expected_output)

    def test_decode_base64(self):
        test_input = [('', 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU')]
        expected_output = [('', 'Test'),
                           ('', '123404'),
                           ('', 'ÄÖÜ  TEST')]
        self.assertEqual(decode_base64(test_input), expected_output)

    def test_decode_base64_linebreak(self):
        test_input = [('', 'VGVzdAoxMjM0MDQKw4'),
                      ('', 'TDlsOcICBURVNU')]
        expected_output = [('', 'Test'),
                           ('', '123404'),
                           ('', 'ÄÖÜ  TEST')]
        self.assertEqual(decode_base64(test_input), expected_output)
