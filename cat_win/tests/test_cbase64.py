from unittest import TestCase

from cat_win.util.service.cbase64 import encode_base64, decode_base64
# import sys
# sys.path.append('../cat_win')


class TestBase64(TestCase):
    def test_encode_base64_string_to_string(self):
        test_input = 'Test\n123404\nÄÖÜ  TEST'
        expected_output = 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        self.assertEqual(encode_base64(test_input, True), expected_output)

    def test_encode_base64_string_to_bytes(self):
        test_input = 'Test\n123404\nÄÖÜ  TEST'
        expected_output = b'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        self.assertEqual(encode_base64(test_input), expected_output)

    def test_encode_base64_bytes_to_string(self):
        test_input = 'Test\n123404\nÄÖÜ  TEST'.encode()
        expected_output = 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        self.assertEqual(encode_base64(test_input, True), expected_output)

    def test_encode_base64_bytes_to_bytes(self):
        test_input = 'Test\n123404\nÄÖÜ  TEST'.encode()
        expected_output = b'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        self.assertEqual(encode_base64(test_input), expected_output)

    def test_decode_base64_string_to_string(self):
        test_input = 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        expected_output = 'Test\n123404\nÄÖÜ  TEST'
        self.assertEqual(decode_base64(test_input, True), expected_output)

    def test_decode_base64_string_to_bytes(self):
        test_input = 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        expected_output = 'Test\n123404\nÄÖÜ  TEST'.encode()
        self.assertEqual(decode_base64(test_input), expected_output)

    def test_decode_base64_string_to_bytes_ml(self):
        test_input = 'VGVzdAoxMjM0MDQKw4TDlsOcICBURVNU\nVGVzdAoxMjM0MDQKw4TDlsOcICBURVNU'
        expected_output = 'Test\n123404\nÄÖÜ  TESTTest\n123404\nÄÖÜ  TEST'.encode()
        self.assertEqual(decode_base64(test_input), expected_output)
