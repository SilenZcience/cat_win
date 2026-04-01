from unittest import TestCase
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.fileattributes import _convert_size, get_file_meta_data, get_file_size, get_dir_size, get_file_mtime, get_file_ctime, print_meta, Signatures, read_attribs, get_libmagic_file
# import sys
# sys.path.append('../cat_win')
res_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'res')
signatures_path = os.path.abspath(os.path.join(res_dir, 'signatures.json'))
test_zip_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resources')
test_zip_file_path  = os.path.abspath(os.path.join(test_zip_file_dir, 'test.zip'))
test_tar_file_path  = os.path.abspath(os.path.join(test_zip_file_dir, 'test.tar.gz'))


class TestSignatures(TestCase):
    def test_read_signature_failed(self):
        with patch.object(Signatures, 'init'):
            Signatures.signatures = None
            self.assertEqual(Signatures.read_signature(__file__), 'lookup failed: Signatures not loaded')
        Signatures.init()
        self.assertEqual(Signatures.read_signature(''), "lookup failed: [Errno 2] No such file or directory: ''")

    def test_read_signatures_empty(self):
        Signatures.init()
        self.assertEqual(Signatures.read_signature(__file__), '-')

    def test_read_signatures(self):
        Signatures.init()
        self.assertEqual(Signatures.read_signature(test_zip_file_path), 'application/x-zip-compressed(zip) [aar(aar)]')
        self.assertEqual(Signatures.read_signature(test_tar_file_path), 'application/x-gzip(gz) [application/gzip(tgz);tar.gz(tar.gz)]')


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
        color_dic = {
            CKW.ATTRIB: '',
            CKW.ATTRIB_POSITIVE: '',
            CKW.ATTRIB_NEGATIVE: '',
            CKW.RESET_ALL: '',
        }
        meta_data = get_file_meta_data(__file__, color_dic)
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
                self.assertIn('-rw-rw-rw- (666)', meta_data)
                self.assertNotIn('rwx', meta_data)
            else:
                self.assertNotIn('Archive', meta_data)
                self.assertNotIn('System', meta_data)
                self.assertNotIn('Hidden', meta_data)
                self.assertNotIn('Readonly', meta_data)
                self.assertNotIn('Indexed', meta_data)
                self.assertNotIn('Compressed', meta_data)
                self.assertNotIn('Encrypted', meta_data)
                self.assertIn('rwx', meta_data)

        meta_data = get_file_meta_data(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|',
            color_dic
        )
        self.assertEqual(meta_data, '')

    def test_get_file_size(self):
        self.assertGreater(get_file_size(__file__), 0)
        self.assertEqual(get_file_size(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_get_dir_size(self):
        self.assertGreater(get_dir_size(os.path.dirname(__file__)), 180000)
        self.assertEqual(get_dir_size(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_get_file_mtime(self):
        self.assertGreater(get_file_mtime(__file__), 1500000000)
        self.assertEqual(get_file_mtime(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_get_file_ctime(self):
        self.assertGreater(get_file_ctime(__file__), 1500000000)
        self.assertEqual(get_file_ctime(
            'randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

    def test_print_meta(self):
        color_dic = {
            CKW.ATTRIB: 'A',
            CKW.ATTRIB_POSITIVE: 'B',
            CKW.ATTRIB_NEGATIVE: 'C',
            CKW.RESET_ALL: 'D',
        }
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with patch.object(Signatures, 'init'):
                Signatures.signatures = None
                print_meta(__file__, color_dic)
                self.assertIn('Signature:', fake_out.getvalue())
                self.assertIn('Size:', fake_out.getvalue())
                self.assertIn('AATime:', fake_out.getvalue())
                self.assertIn('AMTime:', fake_out.getvalue())
                self.assertIn('ACTime:', fake_out.getvalue())

    def test_get_libmagic_file_returncode_nonzero(self):
        """Test line 82: return '' when subprocess returncode != 0"""
        with patch('cat_win.src.service.fileattributes.which', return_value='/usr/bin/file'):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stdout = b''
                mock_run.return_value = mock_result
                result = get_libmagic_file('test.bin')
                self.assertEqual(result, '')

    def test_get_libmagic_file_initial_oserror(self):
        """Test OSError on initial file command execution"""
        with patch('cat_win.src.service.fileattributes.which', side_effect=['/usr/bin/file', '', '/usr/bin/git']):
            with patch('subprocess.run', side_effect=OSError('Command failed')):
                with patch('cat_win.src.service.fileattributes.Path') as mock_path:
                    root = MagicMock()
                    root.parents = [root]
                    root.parent = root
                    root.rglob.side_effect = [[], iter(['file'])]
                    mock_path.return_value.resolve.return_value = root
                    # mock_path.return_value.parent.rglob.return_value = iter(['file'])
                    # mock_path.return_value.parent.parent.rglob.return_value = iter(['file'])
                    result = get_libmagic_file('test.bin')
                    self.assertEqual(result, '')

    def test_get_libmagic_file_no_file_cmd(self):
        def which_side_effect(cmd):
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            result = get_libmagic_file('test.bin')
            self.assertEqual(result, '')

    def test_get_libmagic_file_git_cmd_not_found(self):
        """Test when git is not found"""
        def which_side_effect(cmd):
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            result = get_libmagic_file('test.bin')
            self.assertEqual(result, '')

    def test_get_libmagic_file_path_resolve_oserror(self):
        """Test line 138: OSError when resolving git path"""
        def which_side_effect(cmd):
            # None for file searches
            if 'file' in cmd.lower():
                return None
            # Return a git path
            if 'git' in cmd.lower():
                return '/usr/bin/git'
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            mock_path_instance = MagicMock()
            mock_path_instance.resolve.side_effect = OSError('Path error')

            with patch('cat_win.src.service.fileattributes.Path', return_value=mock_path_instance):
                result = get_libmagic_file('test.bin')
                self.assertEqual(result, '')

    def test_get_libmagic_file_rglob_oserror(self):
        """Test lines 156-168: OSError during rglob search"""
        def which_side_effect(cmd):
            if 'file' in cmd.lower():
                return None
            if 'git' in cmd.lower():
                return '/usr/bin/git'
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            mock_path_instance = MagicMock()
            mock_path_instance.parents = [MagicMock(), MagicMock()]
            mock_path_instance.parent.parent.rglob.side_effect = OSError('rglob failed')

            with patch('cat_win.src.service.fileattributes.Path', return_value=mock_path_instance):
                result = get_libmagic_file('test.bin')
                self.assertEqual(result, '')

    def test_get_libmagic_file_found_file_not_found(self):
        """Test line 174: return '' when file not found after rglob"""
        def which_side_effect(cmd):
            if 'file' in cmd.lower():
                return None
            if 'git' in cmd.lower():
                return '/usr/bin/git'
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            mock_path_instance = MagicMock()
            mock_path_instance.parents = [MagicMock(), MagicMock()]
            # Both rglob calls return empty (no file found)
            mock_path_instance.parent.parent.rglob.return_value = iter([])

            with patch('cat_win.src.service.fileattributes.Path', return_value=mock_path_instance):
                result = get_libmagic_file('test.bin')
                self.assertEqual(result, '')

    def test_get_libmagic_file_subprocess_oserror_check_true(self):
        """Test lines 178-179: OSError in subprocess.run with check=True"""
        def which_side_effect(cmd):
            if 'file' in cmd.lower():
                return None
            if 'git' in cmd.lower():
                return '/usr/bin/git'
            return None

        with patch('cat_win.src.service.fileattributes.which', side_effect=which_side_effect):
            mock_path = MagicMock()
            mock_path.parents = [MagicMock(), MagicMock()]

            # rglob finds file
            mock_found_file = MagicMock()
            mock_path.parent.parent.rglob.return_value = iter([mock_found_file])

            with patch('cat_win.src.service.fileattributes.Path', return_value=mock_path):
                with patch('cat_win.src.service.fileattributes.subprocess.run', side_effect=OSError('Subprocess failed')):
                    result = get_libmagic_file('test.bin')
                    self.assertEqual(result, '')

    def test_read_attribs_no_attribute(self):
        """Test lines 205-206: return [] when st_file_attributes doesn't exist"""
        with patch('os.stat') as mock_stat:
            mock_stat.return_value = MagicMock(spec=[])  # No st_file_attributes
            result = read_attribs('test.txt')
            self.assertEqual(result, [])

    def test_get_dir_size_oserror_on_scandir(self):
        """Test lines 247-248: OSError handling in get_dir_size"""
        with patch('os.scandir', side_effect=OSError('Directory error')):
            result = get_dir_size('nonexistent_dir')
            self.assertEqual(result, 0)

    def test_get_dir_size_oserror_on_entry_stat(self):
        """Test OSError when stat fails on entry"""
        mock_entry = MagicMock()
        mock_entry.is_file.return_value = True
        mock_entry.stat.side_effect = OSError('Stat failed')

        # Create a context manager mock
        context_manager = MagicMock()
        context_manager.__enter__.return_value = [mock_entry]
        context_manager.__exit__.return_value = None

        with patch('os.scandir', return_value=context_manager):
            result = get_dir_size('dir')
            self.assertEqual(result, 0)

    def test_get_file_meta_data_file_attributes_formatting(self):
        color_dic = {
            CKW.ATTRIB: 'C',
            CKW.ATTRIB_POSITIVE: 'P',
            CKW.ATTRIB_NEGATIVE: 'N',
            CKW.RESET_ALL: 'R',
        }

        # Test using a real file (avoiding complex mocking)
        result = get_file_meta_data(__file__, color_dic)
        # Verify basic structure is present
        self.assertIn('Signature:', result)
        self.assertIn('Size:', result)

    def test_get_file_meta_data_windows_no_attribs(self):
        """Test Windows path when no file attributes (lines 383-393)"""
        color_dic = {
            CKW.ATTRIB: '',
            CKW.ATTRIB_POSITIVE: '',
            CKW.ATTRIB_NEGATIVE: '',
            CKW.RESET_ALL: '',
        }

        with patch('os.stat') as mock_stat:
            mock_stat_result = MagicMock()
            from stat import S_IFREG
            mock_stat_result.st_mode = S_IFREG | 0o666
            mock_stat_result.st_size = 1024
            mock_stat_result.st_atime = 1500000000
            mock_stat_result.st_mtime = 1500000000
            mock_stat_result.st_ctime = 1500000000
            mock_stat.return_value = mock_stat_result

            with patch('cat_win.src.service.fileattributes.on_windows_os', True):
                with patch('cat_win.src.service.fileattributes.WinStreams') as mock_win:
                    mock_win.return_value.streams = []

                    with patch('cat_win.src.service.fileattributes.read_attribs', return_value=[]):
                        with patch('cat_win.src.service.fileattributes.Signatures.read_signature', return_value='-'):
                            with patch('cat_win.src.service.fileattributes.get_libmagic_file', return_value=''):
                                meta_data = get_file_meta_data('test.bin', color_dic)
                                self.assertNotIn('Alternate Data Streams', meta_data)

    def test_get_file_meta_data_windows_with_streams(self):
        """Test Windows path with alternate data streams (lines 383-385)"""
        color_dic = {
            CKW.ATTRIB: '',
            CKW.ATTRIB_POSITIVE: '',
            CKW.ATTRIB_NEGATIVE: '',
            CKW.RESET_ALL: '',
        }

        with patch('os.stat') as mock_stat:
            mock_stat_result = MagicMock()
            from stat import S_IFREG
            mock_stat_result.st_mode = S_IFREG | 0o666
            mock_stat_result.st_size = 1024
            mock_stat_result.st_atime = 1500000000
            mock_stat_result.st_mtime = 1500000000
            mock_stat_result.st_ctime = 1500000000
            mock_stat.return_value = mock_stat_result

            with patch('cat_win.src.service.fileattributes.on_windows_os', True):
                with patch('cat_win.src.service.fileattributes.WinStreams') as mock_win:
                    mock_win.return_value.streams = [':Zone.Identifier:$DATA', ':custom:$DATA']

                    with patch('cat_win.src.service.fileattributes.read_attribs', return_value=[]):
                        with patch('cat_win.src.service.fileattributes.Signatures.read_signature', return_value='-'):
                            with patch('cat_win.src.service.fileattributes.get_libmagic_file', return_value=''):
                                meta_data = get_file_meta_data('test.bin', color_dic)
                                self.assertIn('Alternate Data Streams', meta_data)
                                self.assertIn(':Zone.Identifier:$DATA', meta_data)

    def test_get_file_meta_data_windows_with_attributes(self):
        """Test Windows path with file attributes (lines 391-393)"""
        color_dic = {
            CKW.ATTRIB: 'A',
            CKW.ATTRIB_POSITIVE: 'P',
            CKW.ATTRIB_NEGATIVE: 'N',
            CKW.RESET_ALL: 'R',
        }

        with patch('os.stat') as mock_stat:
            mock_stat_result = MagicMock()
            from stat import S_IFREG
            mock_stat_result.st_mode = S_IFREG | 0o666
            mock_stat_result.st_size = 1024
            mock_stat_result.st_atime = 1500000000
            mock_stat_result.st_mtime = 1500000000
            mock_stat_result.st_ctime = 1500000000
            mock_stat.return_value = mock_stat_result

            with patch('cat_win.src.service.fileattributes.on_windows_os', True):
                with patch('cat_win.src.service.fileattributes.WinStreams') as mock_win:
                    mock_win.return_value.streams = []

                    # Mock attributes with some True, some False
                    mock_attribs = [
                        ['Archive', True],
                        ['System', False],
                        ['Hidden', True],
                        ['Readonly', False],
                        ['Indexed', True],
                        ['Compressed', False],
                        ['Encrypted', True]
                    ]

                    with patch('cat_win.src.service.fileattributes.read_attribs', return_value=mock_attribs):
                        with patch('cat_win.src.service.fileattributes.Signatures.read_signature', return_value='-'):
                            with patch('cat_win.src.service.fileattributes.get_libmagic_file', return_value=''):
                                meta_data = get_file_meta_data('test.bin', color_dic)
                                self.assertIn('Archive, Hidden, Indexed', meta_data)
                                self.assertIn('System, Readonly, Compressed', meta_data)
