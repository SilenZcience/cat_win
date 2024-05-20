from copy import deepcopy
from unittest.mock import patch, MagicMock
from unittest import TestCase

from cat_win.tests.mocks.edit import getxymax
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.std import StdOutMock, IoHelperMock

import cat_win.src.service.hexeditor as hexeditor
if hexeditor.CURSES_MODULE_ERROR:
    setattr(hexeditor, 'curses', None)
from cat_win.src.service.hexeditor import HexEditor

mm = MagicMock()

@patch('cat_win.src.service.hexeditor.HexEditor.getxymax', getxymax)
@patch('cat_win.src.service.hexeditor.curses', mm)
class TestHexEditor(TestCase):
    maxDiff = None

    def test_hexeditor_unknown_file(self):
        editor = HexEditor('', '')
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertCountEqual(editor.hex_array, [[]])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 723))
    def test__build_file(self):
        editor = HexEditor('', '')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 30)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 16] * 30)
        editor.hex_array_edit[15][1] = '00'
        editor._build_file()
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 45 + [['40'] * 3])
        self.assertSequenceEqual(editor.hex_array_edit,
                                 [[None] * 16] * 15 + [[None, '00', None, None, None, None, None, None, None, None, None, None, None, None, None, None]] + [[None] * 16] * 29 + [[None] * 3])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 723))
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

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'!' * 454))
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

    def test__move_key_page_up(self):
        editor = HexEditor('', '')
        editor.wpos.set_pos((83, 0))
        editor.cpos.set_pos((93, 11))
        editor._move_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (63, 11))
        self.assertEqual(editor.wpos.get_pos(), (53, 0))
        editor._move_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (33, 11))
        self.assertEqual(editor.wpos.get_pos(), (23, 0))
        editor._move_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (3, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))
        editor._move_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (-27, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))

    def test__move_key_page_down(self):
        editor = HexEditor('', '')
        editor.wpos.set_pos((0, 0))
        editor.cpos.set_pos((3, 11))
        editor._move_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (33, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))
        editor._move_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (63, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__move_key_end(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((0, 2))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0, 15))
        editor.cpos.set_pos((1, 1))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (1, 3))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 70))
    def test__move_key_ctl_end(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((1, 1))
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (4, 5))

    def test__move_key_home(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((123, 123))
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (123, 0))

    def test__move_key_ctl_home(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((123, 123))
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__insert_byte_left(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] + ['40'] * 7] + [['40']])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] * 2 + ['40'] * 6] + [['40'] * 2])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
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
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor._key_string('0')
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
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

    def test__action_render_scr(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        self.assertNotEqual(editor.error_bar, '')
        self.assertEqual(editor._action_render_scr(''), None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 496))
    def test__action_save(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, b'!'*16+b'@'*479)
        editor = HexEditor('', '')
        editor.hex_array_edit[0] = ['21'] * 16
        editor.cpos.set_pos((5, 2))
        editor._key_dl(None)
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 500))
    @patch('cat_win.src.service.hexeditor.HexEditor.columns', 5)
    def test__action_save_correctness(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, b'@'*6+b'!@!'+b'@'*492)
        editor = HexEditor('', '')
        editor.cpos.set_pos((1,1))
        editor._key_string('2')
        editor._key_string('1')
        for _ in range(100):
            editor._key_string(' ')
        editor._build_file_upto(editor.cpos.row+32)
        editor._fix_cursor_position(30)
        for _ in range(4):
            editor._move_key_up()
        editor._key_string('2')
        editor._key_string('1')
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 496))
    @patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', ErrorDefGen.get_def(PermissionError("validn't")))
    def test__action_save_error(self):
        editor = HexEditor('', '')
        editor.hex_array_edit[0] = ['21'] * 16
        editor._action_save()
        self.assertEqual(editor.error_bar, "validn't")

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 496))
    def test__action_jump(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'F', 'F', 'j'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen([5, '\x1b'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen([5, 'N'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 254 + b'!' * 2 + b'@' * 255))
    def test__action_find(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_backspace', b'_key_enter'])
        char_gen_ = char_gen([5, 'G', '2', '1', '0'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 14))
        def char_gen_ctl(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_ctl_backspace', b'_key_enter'])
        char_gen_ = char_gen_ctl(['2', '1', 'F', 'E', 'D', 'C'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen_ctl(['4', '0', '\x1b'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 66))
    def test__action_reload(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'F', 'F', 'j'])
        editor.cpos.set_pos((1, 14))
        editor.hex_array_edit[0][0] = '21'
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.hex_array_edit[0][0], '21')
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.hex_array_edit[0][0], None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test__action_quit(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_quit(), False)
        editor.unsaved_progress = True
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('n', b'_key_string')):
            self.assertEqual(editor._action_quit(), False)
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_quit(), False)
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_interrupt')):
            self.assertEqual(editor._action_quit(), True)
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('\x1b', b'_key_string')):
            self.assertEqual(editor._action_quit(), True)
        def action_save(_):
            editor.unsaved_progress = False
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'j'])
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)), \
            patch('cat_win.src.service.hexeditor.HexEditor._action_save', action_save):
            self.assertEqual(editor._action_quit(), False)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test__action_interrupt(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        self.assertRaises(KeyboardInterrupt, editor._action_interrupt)

    def test__action_resize(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_resize(), True)

    def test__get_next_char(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        editor.curse_window.get_wch.return_value = '!'
        self.assertEqual(editor._get_next_char(), ('!', b'_key_string'))
        editor.curse_window.get_wch.return_value = 497
        self.assertEqual(editor._get_next_char(), (497, b'_key_string'))
        editor.curse_window.get_wch.return_value = ' '
        editor.debug_mode = True
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(editor._get_next_char(), (' ', b'_key_string'))
            self.assertIn('DEBUG', fake_out.getvalue())
            self.assertIn("b'_key_string'", fake_out.getvalue())
            self.assertIn('32', fake_out.getvalue())
            self.assertIn("' '", fake_out.getvalue())

    def test__get_color(self):
        editor = HexEditor('', '')
        mm.has_colors.return_value = False
        self.assertEqual(editor._get_color(0), 0)
        mm.has_colors.return_value = True
        mm.color_pair.return_value = 5
        self.assertEqual(editor._get_color(0), 5)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 66))
    def test__fix_cursor_position(self):
        editor = HexEditor('', '')
        editor.cpos.set_pos((-2, 1))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (0, 1))
        editor.cpos.set_pos((6, 1))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (4, 1))

        editor.cpos.set_pos((3, -18))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        editor.cpos.set_pos((3, -99999))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

        editor.cpos.set_pos((1, 38))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (3, 6))
        editor.cpos.set_pos((1, 99999))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (4, 1))

        editor.cpos.set_pos((1, 5))
        editor.wpos.set_pos((3, 0))
        editor._fix_cursor_position(30)
        self.assertEqual(editor.cpos.get_pos(), (1, 5))
        self.assertEqual(editor.wpos.get_pos(), (1, 0))
        editor.cpos.set_pos((4, 1))
        editor.wpos.set_pos((1, 0))
        editor._fix_cursor_position(2)
        self.assertEqual(editor.cpos.get_pos(), (4, 1))
        self.assertEqual(editor.wpos.get_pos(), (3, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 66))
    def test__render_scr(self):
        editor = HexEditor('', 'X' * 300)
        editor.curse_window = MagicMock()
        editor.error_bar = ':)'
        editor.debug_mode = True
        editor.hex_array_edit[0][0] = '00'
        editor.hex_array_edit[1][1] = '00'
        self.assertEqual(editor._render_scr(), None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__run(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        with patch('cat_win.src.service.hexeditor.HexEditor._get_next_char', lambda *args: ('\x11', b'_action_quit')):
            self.assertEqual(editor._run(), None)

    @patch('os.environ.setdefault', lambda *args: None)
    def test__open(self):
        editor = HexEditor('', '')
        editor.curse_window = MagicMock()
        with patch('cat_win.src.service.hexeditor.HexEditor._run', lambda *args: None):
            self.assertEqual(editor._open(), None)

    @patch('cat_win.src.service.hexeditor.CURSES_MODULE_ERROR', new=True)
    @patch('cat_win.src.service.hexeditor.HexEditor.on_windows_os', new=True)
    def test_open_no_curses_error(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(HexEditor.open('', ''), False)
            self.assertIn('could not be loaded', fake_out.getvalue())
            self.assertIn('windows-curses', fake_out.getvalue())
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(HexEditor.open('', ''), False)
            self.assertEqual('', fake_out.getvalue())

    def test_set_flags(self):
        backup_a = HexEditor.save_with_alt
        backup_b = HexEditor.on_windows_os
        backup_c = HexEditor.debug_mode
        backup_d = HexEditor.columns
        HexEditor.set_flags(True, True, True, 1002)
        self.assertEqual(HexEditor.save_with_alt, True)
        self.assertEqual(HexEditor.on_windows_os, True)
        self.assertEqual(HexEditor.debug_mode, True)
        self.assertEqual(HexEditor.columns, 1002)
        HexEditor.set_flags(backup_a, backup_b, backup_c, backup_d)
