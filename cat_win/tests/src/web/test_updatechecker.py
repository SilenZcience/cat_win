from unittest import TestCase
from unittest.mock import patch
import io

from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.src.web import updatechecker
# import sys
# sys.path.append('../cat_win')


class TestUpdateChecker(TestCase):
    def test_get_stable_package_version_error(self):
        with patch('urllib.request.urlopen', ErrorDefGen.get_def(ValueError())):
            self.assertEqual(updatechecker.get_stable_package_version('cat_win'), '0.0.0')
        with patch('urllib.request.urlopen', ErrorDefGen.get_def(OSError())):
            self.assertEqual(updatechecker.get_stable_package_version('cat_win'), '0.0.0')
        with patch('urllib.request.urlopen', lambda *args, **kwargs: io.StringIO('{"wrong":{"values":"1.4.5"}}')):
            self.assertEqual(updatechecker.get_stable_package_version('cat_win'), '0.0.0')

    @patch('urllib.request.urlopen', lambda *args, **kwargs: io.StringIO('{"info":{"version":"1.4.5"}}'))
    def test_get_stable_package_version(self):
        self.assertEqual(updatechecker.get_stable_package_version('cat_win'), '1.4.5')

    def test_get_latest_package_version_error(self):
        with patch('urllib.request.urlopen', ErrorDefGen.get_def(ValueError())):
            self.assertEqual(updatechecker.get_latest_package_version('cat_win'), '0.0.0')
        with patch('urllib.request.urlopen', ErrorDefGen.get_def(OSError())):
            self.assertEqual(updatechecker.get_latest_package_version('cat_win'), '0.0.0')
        with patch('urllib.request.urlopen', lambda *args, **kwargs: io.StringIO('{"wrong":{"values":"1.4.5"}}')):
            self.assertEqual(updatechecker.get_latest_package_version('cat_win'), '0.0.0')
        with patch('urllib.request.urlopen', lambda *args, **kwargs: io.StringIO('{"releases":{}}')):
            self.assertEqual(updatechecker.get_latest_package_version('cat_win'), '0.0.0')

    @patch('urllib.request.urlopen', lambda *args, **kwargs: io.StringIO('{"releases":{"1.4.5": [{"upload_time": "2022-10-09T15:49:40"}], "1.4.0": [{"upload_time": "2022-10-09T15:49:41"}]}}'))
    def test_get_latest_package_version(self):
        self.assertEqual(updatechecker.get_latest_package_version('cat_win'), '1.4.0')

    def test_only_numeric(self):
        self.assertEqual(updatechecker.only_numeric('1nh589h15io125b085218'), 158915125085218)
        self.assertEqual(updatechecker.only_numeric('1nh'), 1)
        self.assertEqual(updatechecker.only_numeric('123'), 123)
        self.assertEqual(updatechecker.only_numeric('abc'), 0)

    def test_gen_version_tuples(self):
        self.assertEqual(updatechecker.gen_version_tuples('1.0.33.0', '1.1.0a'),
                         (('01', '00', '33', '00'), ('01', '01', '0a', '00')))
        self.assertEqual(updatechecker.gen_version_tuples('1.2.3', '1.2.3.4.5'),
                         (('1', '2', '3', '0', '0'), ('1', '2', '3', '4', '5')))
        self.assertEqual(updatechecker.gen_version_tuples('1.12345', '1.2'),
                         (('00001', '12345'), ('00001', '00002')))

    def test_version_comparison_up_to_date(self):
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.0.9'), 0)
        self.assertEqual(updatechecker.new_version_available('1.0.9b', '1.0.9a'), 0)
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.0.09'), 0)
        self.assertEqual(updatechecker.new_version_available('1.10.9', 'v1.10.9'), 0)
        self.assertEqual(updatechecker.new_version_available('1.7a.9', '1.7a.9'), 0)
        self.assertEqual(updatechecker.new_version_available('09.0.8b', '9.0.08b'), 0)
        self.assertEqual(updatechecker.new_version_available('v7b.4', '07b.04.00'), 0)
        self.assertEqual(updatechecker.new_version_available('9', '9.0.0'), 0)

    def test_version_comparison_stable_release(self):
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.0.10'), 1)
        self.assertEqual(updatechecker.new_version_available('1.0.15', 'v1.0.016'), 1)
        self.assertEqual(updatechecker.new_version_available('1.0.12', '1.000.020'), 1)
        self.assertEqual(updatechecker.new_version_available('v1.0.0', 'v01.00.01'), 1)
        self.assertEqual(updatechecker.new_version_available('2.1.5a', '2.1.6'), 1)
        self.assertEqual(updatechecker.new_version_available('2.1.6a', '2.1.6'), 1)
        self.assertEqual(updatechecker.new_version_available('v2.1b.5a', '2.1b.051'), 1)

    def test_version_comparison_pre_release(self):
        self.assertEqual(updatechecker.new_version_available('v1.0.9a', '1.0.9b'), 2)
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.0.19b'), 2)
        self.assertEqual(updatechecker.new_version_available('1.0.9', 'v1.0.10b'), 2)
        self.assertEqual(updatechecker.new_version_available('2.1.5a', '2.1.5b'), 2)

    def test_version_comparison_stable_release_unsafe(self):
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.01.10'), -1)
        self.assertEqual(updatechecker.new_version_available('1.0.15', '1.1.9'), -1)
        self.assertEqual(updatechecker.new_version_available('1.0.9', 'v2.0.9'), -1)
        self.assertEqual(updatechecker.new_version_available('1.0.12', '1.001.0'), -1)
        self.assertEqual(updatechecker.new_version_available('1.10a.0', '1.10.0'), -1)
        self.assertEqual(updatechecker.new_version_available('v1.0.0', 'v01.001.01'), -1)
        self.assertEqual(updatechecker.new_version_available('2.1.5a', '2.2.5'), -1)

    def test_version_comparison_pre_release_unsafe(self):
        self.assertEqual(updatechecker.new_version_available('v1.0.9', '2a.0.9a'), -2)
        self.assertEqual(updatechecker.new_version_available('1.0.9', '1.1a.9'), -2)
        self.assertEqual(updatechecker.new_version_available('1a.0.9', '1.0a.9'), -2)
        self.assertEqual(updatechecker.new_version_available('0.0.9', 'v1a.0.9'), -2)
        self.assertEqual(updatechecker.new_version_available('1.0.9', '2b.0.10b'), -2)
        self.assertEqual(updatechecker.new_version_available('v1.0.9', '1.1b.10a'), -2)
        self.assertEqual(updatechecker.new_version_available('2.1.5a', '2.2a.5'), -2)
        self.assertEqual(updatechecker.new_version_available('2.1.5', '2.2.0a'), -2)

    def test_version_availability_current_is_newest(self):
        self.assertEqual(updatechecker.new_version_available('v1.1.9', '1.0.9a'), 0)
