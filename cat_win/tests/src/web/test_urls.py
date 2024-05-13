from unittest import TestCase
from unittest.mock import patch
import io
import random

from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.src.web.urls import is_valid_uri, sep_valid_urls, read_url

class TestUrls(TestCase):
    @patch('urllib.parse.urlparse', ErrorDefGen.get_def(ValueError()))
    def test_is_valid_uri_valueerror(self):
        self.assertEqual(is_valid_uri('invalid uri'), False)

    def test_is_valid_uri_false(self):
        self.assertEqual(is_valid_uri('invalid uri'), False)

    def test_sep_valid_urls(self):
        random.seed(1)
        valid_expected = [
            'https://google.com',
            'https://www.google.com',
            'https://github.com/SilenZcience/cat_win',
            'github.com/SilenZcience/cat_win',
            'ftp://netloc.net/test_url;param=1?query#fragment',
            ]
        invalid_expected = [
            'testURI',
            'testURI.x',
            'ftp:///test_url;param=1?query#fragment',
            'https://www google.com',
            ]
        test_input = valid_expected+invalid_expected
        random.shuffle(test_input)
        valid_output, invalid_output = sep_valid_urls(test_input)
        self.assertCountEqual(valid_expected, valid_output)
        self.assertCountEqual(invalid_expected, invalid_output)

    @patch('urllib.request.urlopen', new=lambda *args, **kwars: io.StringIO('test'))
    def test_read_url(self):
        self.assertEqual(read_url('invalid uri', False), 'test')

    @patch('urllib.request.urlopen', ErrorDefGen.get_def(ValueError()))
    def test_read_url_valueerror(self):
        expected_output = b'Error at opening the following url:\nhttps://invalid uri'
        self.assertEqual(read_url('invalid uri', False), expected_output)

    @patch('urllib.request.urlopen', ErrorDefGen.get_def(OSError()))
    def test_read_url_oserror(self):
        expected_output = b'Error at opening the following url:\ninvalid uri'
        self.assertEqual(read_url('invalid uri', False), expected_output)
