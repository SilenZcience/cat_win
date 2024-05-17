from unittest.mock import patch
from unittest import TestCase
from copy import deepcopy

from cat_win.tests.mocks.edit import getxymax
from cat_win.src.service.hexeditor import HexEditor
# import sys
# sys.path.append('../cat_win')


@patch('cat_win.src.service.hexeditor.HexEditor.getxymax', getxymax)
class TestHexEditor(TestCase):
    maxDiff = None

    def test_hexeditor_unknown_file(self):
        editor = HexEditor('', '')
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertCountEqual(editor.hex_array, [[]])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *args: b'@' * 723)
    def test__build_file_upto_16(self):
        editor = HexEditor('', '')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 30)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 16] * 30)
        editor._build_file_upto(40)
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 40)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 16] * 40)
        editor.hex_array_edit[15][1] = '00'
        editor._build_file_upto(50)
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 45 + [['40'] * 3])
        self.assertSequenceEqual(editor.hex_array_edit,
                                 [[None] * 16] * 15 + [[None, '00', None, None, None, None, None, None, None, None, None, None, None, None, None, None]] + [[None] * 16] * 29 + [[None] * 3])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *args: b'!' * 454)
    @patch('cat_win.src.service.hexeditor.HexEditor.columns', 10)
    def test__build_file_upto_10(self):
        editor = HexEditor('', '')
        self.assertSequenceEqual(editor.hex_array, [['21'] * 10] * 30)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 10] * 30)
        editor._build_file_upto(40)
        self.assertSequenceEqual(editor.hex_array, [['21'] * 10] * 40)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 10] * 40)
        editor.hex_array_edit[15][1] = '00'
        editor._build_file_upto(50)
        self.assertSequenceEqual(editor.hex_array, [['21'] * 10] * 45 + [['21'] * 4])
        self.assertSequenceEqual(editor.hex_array_edit,
                                 [[None] * 10] * 15 + [[None, '00', None, None, None, None, None, None, None, None]] + [[None] * 10] * 29 + [[None] * 4])

    def test__key_dc_empty(self):
        editor = HexEditor('', '')
        editor._build_file_upto(0)
        editor._key_dc(None)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    def test__key_dc(self):
        editor = HexEditor(__file__, '')
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 12))
        editor.hex_array_edit[5][12] = '00'
        editor._key_dc(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 13))

    def test__key_dl_empty(self):
        editor = HexEditor('', '')
        editor._build_file_upto(0)
        editor._key_dl(None)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    def test__key_dl(self):
        editor = HexEditor(__file__, '')
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 12))
        editor._key_dl(None)
        hex_array_edit[5][12] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 13))

    def test__key_backspace_empty(self):
        editor = HexEditor('', '')
        editor._build_file_upto(0)
        editor._key_backspace(None)
        editor.cpos.set_pos((5, 5))
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__key_backspace(self):
        editor = HexEditor(__file__, '')
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 5))
        editor.hex_array_edit[5][5] = '00'
        editor._key_backspace(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 4))

    def test__key_ctl_backspace_empty(self):
        editor = HexEditor('', '')
        editor._build_file_upto(0)
        editor._key_ctl_backspace(None)
        editor.cpos.set_pos((5, 5))
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__key_ctl_backspace(self):
        editor = HexEditor(__file__, '')
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 5))
        editor._key_ctl_backspace(None)
        hex_array_edit[5][5] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 4))

    def test__move_key_left(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((5, 2))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, 1))
        editor._move_key_left()
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, -1))

    def test__move_key_right(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((5, 2))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 3))
        editor._move_key_right()
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__move_key_up(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((2, 2))
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (1, 2))
        editor._move_key_up()
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (-1, 2))

    def test__move_key_down(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((5, 2))
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (6, 2))
        editor._move_key_down()
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (8, 2))

    def test__move_key_ctl_left(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((10, 10))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (10, 2))
        editor._move_key_ctl_left()
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (10, -14))

        with patch('cat_win.src.service.hexeditor.HexEditor.columns', 9):
            editor._move_key_ctl_left()
            self.assertEqual(editor.cpos.get_pos(), (10, -18))

    def test__move_key_ctl_right(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((10, 10))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (10, 18))
        editor._move_key_ctl_right()
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (10, 34))

        with patch('cat_win.src.service.hexeditor.HexEditor.columns', 9):
            editor._move_key_ctl_right()
            self.assertEqual(editor.cpos.get_pos(), (10, 38))

    def test__move_key_ctl_up(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((11, 11))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (1, 11))
        editor._move_key_ctl_up()
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (-19, 11))

    def test__move_key_ctl_down(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((11, 11))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (21, 11))
        editor._move_key_ctl_down()
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (41, 11))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *args: b'@' * 16)
    def test__insert_byte_left(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] + ['40'] * 7] + [['40']])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] * 2 + ['40'] * 6] + [['40'] * 2])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *args: b'@' * 16)
    def test__insert_byte_right(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((0, 8))
        editor._insert_byte('>')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 9 + ['--'] + ['40'] * 6] + [['40']])
        self.assertEqual(editor.cpos.get_pos(), (0, 9))
        editor._insert_byte(' ')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 9 + ['--'] * 2 + ['40'] * 5] + [['40'] * 2])
        self.assertEqual(editor.cpos.get_pos(), (0, 10))

    def test__key_string_invalid(self):
        editor = HexEditor(__file__, '')
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor._key_string('')
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))
        editor._key_string(1)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))
        editor._key_string('G')
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

        editor = HexEditor('', '')
        editor._build_file_upto(0)
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor._key_string('0')
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *args: b'@' * 16)
    def test__key_string(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((0, 1))
        editor._key_string('f')
        self.assertSequenceEqual(editor.hex_array_edit, [[None] + ['F0'] + [None] * 14])
        self.assertEqual(editor.cpos.get_pos(), (0, 1))
        editor._key_string('e')
        self.assertSequenceEqual(editor.hex_array_edit, [[None] + ['FE'] + [None] * 14])
        self.assertEqual(editor.cpos.get_pos(), (0, 2))
        editor._key_string('4')
        self.assertSequenceEqual(editor.hex_array_edit, [[None] + ['FE'] + ['40'] + [None] * 13])
        self.assertEqual(editor.cpos.get_pos(), (0, 2))

    def test_set_flags(self):
        backup_a = HexEditor.save_with_alt
        backup_b = HexEditor.debug_mode
        backup_c = HexEditor.columns
        HexEditor.set_flags(True, True, 1002)
        self.assertEqual(HexEditor.save_with_alt, True)
        self.assertEqual(HexEditor.debug_mode, True)
        self.assertEqual(HexEditor.columns, 1002)
        HexEditor.set_flags(backup_a, backup_b, backup_c)
