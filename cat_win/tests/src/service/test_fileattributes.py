from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.service.fileattributes import _convert_size, get_file_meta_data, get_file_size, print_meta
# import sys
# sys.path.append('../cat_win')


class TestFileAttributes(TestCase):
    def test__convert_size_zero(self):
        self.assertEqual(_convert_size(0), '0  B')

    def test__convert_size_edge_kb(self):
        self.assertEqual(_convert_size(1023), '1023.0  B')

    def test__convert_size_kb_exact(self):
        self.assertEqual(_convert_size(1024), '1.0 KB')

    def test__convert_size_kb(self):
        self.assertEqual(_convert_size(1836), '1.79 KB')

    def test__convert_size_round_kb(self):
        self.assertEqual(_convert_size(2044), '2.0 KB')

    def test__convert_size_tb(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024), '1.0 TB')

    def test__convert_size_uneven_tb(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024 * 2.3), '2.3 TB')

    def test__convert_size_yb(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024), '1.0 YB')

    def test__convert_size_edge_yb(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024 * 1023.99),
                         '1023.99 YB')

    def test__convert_size_out_of_range(self):
        self.assertEqual(_convert_size(1024*1024*1024*1024*1024*1024*1024*1024*1024), '1.0 ?')

    def test_get_file_meta_data(self):
        meta_data = get_file_meta_data(__file__, '', False)
        self.assertIn('Signature:', meta_data)
        self.assertIn('Size:', meta_data)
        self.assertIn('ATime:', meta_data)
        self.assertIn('MTime:', meta_data)
        self.assertIn('CTime:', meta_data)

        meta_data = get_file_meta_data(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|', '', False)
        self.assertEqual(meta_data, '')

    def test_get_file_size(self):
        self.assertGreater(get_file_size(__file__), 0)
        self.assertEqual(get_file_size(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_print_meta(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            print_meta(__file__, '', False, ['A', 'B', 'C', 'D'])
            self.assertIn('Signature:', fake_out.getvalue())
            self.assertIn('Size:', fake_out.getvalue())
            self.assertIn('ATime:', fake_out.getvalue())
            self.assertIn('MTime:', fake_out.getvalue())
            self.assertIn('CTime:', fake_out.getvalue())
