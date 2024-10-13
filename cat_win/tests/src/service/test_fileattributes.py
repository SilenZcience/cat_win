from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.cat import on_windows_os
from cat_win.src.service.fileattributes import _convert_size, get_file_meta_data, get_file_size, print_meta, Signatures
# import sys
# sys.path.append('../cat_win')
res_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'res')
signatures_path = os.path.abspath(os.path.join(res_dir, 'signatures.json'))
test_zip_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resources')
test_zip_file_path  = os.path.abspath(os.path.join(test_zip_file_dir, 'test.zip'))
test_tar_file_path  = os.path.abspath(os.path.join(test_zip_file_dir, 'test.tar.gz'))


class TestSignatures(TestCase):
    def test_read_signature_failed(self):
        self.assertEqual(Signatures.read_signature('', __file__), 'lookup failed!')
        self.assertEqual(Signatures.read_signature(signatures_path, ''), 'lookup failed!')

    def test_read_signatures_empty(self):
        self.assertEqual(Signatures.read_signature(signatures_path, __file__), '-')

    def test_read_signatures(self):
        self.assertEqual(Signatures.read_signature(signatures_path, test_zip_file_path), 'application/x-zip-compressed(zip)')
        self.assertEqual(Signatures.read_signature(signatures_path, test_tar_file_path), 'application/x-gzip(gz) [application/gzip(tgz)]')


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
        meta_data = get_file_meta_data(__file__, '', on_windows_os)
        self.assertIn('Signature:', meta_data)
        self.assertIn('Size:', meta_data)
        self.assertIn('ATime:', meta_data)
        self.assertIn('MTime:', meta_data)
        self.assertIn('CTime:', meta_data)
        if '+' in meta_data:
            if on_windows_os:
                self.assertIn('Archive', meta_data)
                self.assertIn('System', meta_data)
                self.assertIn('Hidden', meta_data)
                self.assertIn('Readonly', meta_data)
                self.assertIn('Indexed', meta_data)
                self.assertIn('Compressed', meta_data)
                self.assertIn('Encrypted', meta_data)
            else:
                self.assertNotIn('Archive', meta_data)
                self.assertNotIn('System', meta_data)
                self.assertNotIn('Hidden', meta_data)
                self.assertNotIn('Readonly', meta_data)
                self.assertNotIn('Indexed', meta_data)
                self.assertNotIn('Compressed', meta_data)
                self.assertNotIn('Encrypted', meta_data)

        meta_data = get_file_meta_data(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|', '', False)
        self.assertEqual(meta_data, '')

    def test_get_file_size(self):
        self.assertGreater(get_file_size(__file__), 0)
        self.assertEqual(get_file_size(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_print_meta(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            print_meta(__file__, '', on_windows_os, ['A', 'B', 'C', 'D'])
            self.assertIn('Signature:', fake_out.getvalue())
            self.assertIn('Size:', fake_out.getvalue())
            self.assertIn('ATime:', fake_out.getvalue())
            self.assertIn('MTime:', fake_out.getvalue())
            self.assertIn('CTime:', fake_out.getvalue())
