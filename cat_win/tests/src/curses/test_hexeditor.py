from copy import deepcopy
from unittest.mock import patch, MagicMock
from unittest import TestCase
import runpy

from cat_win.tests.mocks.edit import getxymax
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.std import IoHelperMock

from cat_win.src.curses import hexeditor
if hexeditor.CURSES_MODULE_ERROR:
    setattr(hexeditor, 'curses', None)
from cat_win.src.curses.hexeditor import HexEditor

ORIGINAL_HEXEDITOR_GETXYMAX = HexEditor.getxymax

mm = MagicMock()
logger = LoggerStub()

@patch.object(hexeditor, 'logger', logger)
@patch('cat_win.src.curses.hexeditor.HexEditor.getxymax', getxymax)
@patch('cat_win.src.curses.hexeditor.curses', mm)
class TestHexEditor(TestCase):
    maxDiff = None

    def test_hexeditor_unknown_file(self):
        editor = HexEditor([('', '')])
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertCountEqual(editor.hex_array, [[]])

    def test_selected_area(self):
        editor = HexEditor([('', '')])
        self.assertEqual(editor.selected_area, ((0, 0), (0, 0)))
        editor.cpos.set_pos((5, 4))
        editor.spos.set_pos((5, 3))
        self.assertEqual(editor.selected_area, ((5, 3), (5, 4)))
        editor.cpos.set_pos((5, 4))
        editor.spos.set_pos((2, 3))
        self.assertEqual(editor.selected_area, ((2, 3), (5, 4)))
        editor.cpos.set_pos((3, 4))
        editor.spos.set_pos((5, 3))
        self.assertEqual(editor.selected_area, ((3, 4), (5, 3)))

    def test_pos_between(self):
        with patch('cat_win.src.curses.hexeditor.HexEditor.columns', 10):
            self.assertListEqual(list(HexEditor.pos_between((5,8),(6,4))), [(5,8),(5,9),(6,0),(6,1),(6,2),(6,3),(6,4)])
        with patch('cat_win.src.curses.hexeditor.HexEditor.columns', 3):
            self.assertListEqual(list(HexEditor.pos_between((2,0),(4,1))), [(2,0),(2,1),(2,2),(3,0),(3,1),(3,2),(4,0),(4,1)])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 723))
    def test__build_file(self):
        editor = HexEditor([('', '')])
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 30)
        self.assertSequenceEqual(editor.hex_array_edit, [[None] * 16] * 30)
        editor.hex_array_edit[15][1] = '00'
        editor._build_file()
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16] * 45 + [['40'] * 3])
        self.assertSequenceEqual(editor.hex_array_edit,
                                 [[None] * 16] * 15 + [[None, '00', None, None, None, None, None, None, None, None, None, None, None, None, None, None]] + [[None] * 16] * 29 + [[None] * 3])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 723))
    def test__build_file_upto_16(self):
        editor = HexEditor([('', '')])
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
    @patch('cat_win.src.curses.hexeditor.HexEditor.columns', 10)
    def test__build_file_upto_10(self):
        editor = HexEditor([('', '')])
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

    @patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_bytes_at_commit', MagicMock(return_value=b'ABC'))
    def test__setup_file_git_content_str(self):
        editor = HexEditor([(__file__, 'test')], file_commit_hash='deadbeef')
        self.assertSequenceEqual(editor.hex_array, [['41', '42', '43']])
        self.assertSequenceEqual(editor.hex_array_edit, [[None, None, None]])
        self.assertEqual(editor.display_name, 'GIT: test')
        self.assertTrue(editor.unsaved_progress)

    def test__key_dc_empty(self):
        editor = HexEditor([('', '')])
        editor._build_file_upto(0)
        editor._key_dc(None)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__get_current_state_bytes_row(self):
        editor = HexEditor([('', '')])
        self.assertEqual(editor._get_current_state_bytes_row(0), b'@' * 16)
        self.assertEqual(editor._get_current_state_bytes_row(1), b'@' * 4)
        editor.hex_array_edit[1][3] = '--'
        self.assertEqual(editor._get_current_state_bytes_row(0), b'@' * 16)
        self.assertEqual(editor._get_current_state_bytes_row(1), b'@' * 3)
        editor.hex_array_edit[0][0] = '21'
        self.assertEqual(editor._get_current_state_bytes_row(0), b'!' + b'@' * 15)
        self.assertEqual(editor._get_current_state_bytes_row(1), b'@' * 3)

    def test__key_dc(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 12))
        editor.hex_array_edit[5][12] = '00'
        editor._key_dc(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 13))

    def test__key_dc_selection(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((1,5))
        editor.spos.set_pos((4,10))
        editor.selecting = True
        editor.hex_array_edit[3][1] = '00'
        editor.hex_array_edit[4][2] = '00'
        editor.hex_array_edit[4][6] = '00'
        editor.hex_array_edit[1][5] = '00'
        editor.hex_array_edit[4][10] = '00'
        editor._key_dc(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (4, 11))

    def test__key_dl_empty(self):
        editor = HexEditor([('', '')])
        editor._build_file_upto(0)
        editor._key_dl(None)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    def test__key_dl(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 12))
        editor._key_dl(None)
        hex_array_edit[5][12] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 13))

    def test__key_dl_selection(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((3, 15))
        editor.spos.set_pos((5, 0))
        editor.selecting = True
        editor._key_dl(None)
        hex_array_edit[3][15] = '--'
        hex_array_edit[4] = ['--'] * 16
        hex_array_edit[5][0] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 1))

    def test__key_backspace_empty(self):
        editor = HexEditor([('', '')])
        editor._build_file_upto(0)
        editor._key_backspace(None)
        editor.cpos.set_pos((5, 5))
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__key_backspace(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 5))
        editor.hex_array_edit[5][5] = '00'
        editor._key_backspace(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 4))

    def test__key_backspace_selection(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((4,10))
        editor.spos.set_pos((1,5))
        editor.selecting = True
        editor.hex_array_edit[3][1] = '00'
        editor.hex_array_edit[4][2] = '00'
        editor.hex_array_edit[4][6] = '00'
        editor.hex_array_edit[1][5] = '00'
        editor.hex_array_edit[4][10] = '00'
        editor._key_backspace(None)
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (1, 4))

    def test__key_ctl_backspace_empty(self):
        editor = HexEditor([('', '')])
        editor._build_file_upto(0)
        editor._key_ctl_backspace(None)
        editor.cpos.set_pos((5, 5))
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__key_ctl_backspace(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 5))
        editor._key_ctl_backspace(None)
        hex_array_edit[5][5] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (5, 4))

    def test__key_ctl_backspace_selection(self):
        editor = HexEditor([(__file__, '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor.cpos.set_pos((5, 0))
        editor.spos.set_pos((3, 15))
        editor.selecting = True
        editor._key_ctl_backspace(None)
        hex_array_edit[3][15] = '--'
        hex_array_edit[4] = ['--'] * 16
        hex_array_edit[5][0] = '--'
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (3, 14))

    def test__move_key_left(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, 1))
        editor._move_key_left()
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, -1))

    def test__move_key_right(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 3))
        editor._move_key_right()
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__move_key_up(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((2, 2))
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (1, 2))
        editor._move_key_up()
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (-1, 2))

    def test__move_key_down(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (6, 2))
        editor._move_key_down()
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (8, 2))

    def test__move_key_ctl_left(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((10, 10))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (10, 2))
        editor._move_key_ctl_left()
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (10, -14))

        with patch('cat_win.src.curses.hexeditor.HexEditor.columns', 9):
            editor._move_key_ctl_left()
            self.assertEqual(editor.cpos.get_pos(), (10, -18))

    def test__move_key_ctl_right(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((10, 10))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (10, 18))
        editor._move_key_ctl_right()
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (10, 34))

        with patch('cat_win.src.curses.hexeditor.HexEditor.columns', 9):
            editor._move_key_ctl_right()
            self.assertEqual(editor.cpos.get_pos(), (10, 38))

    def test__move_key_ctl_up(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((11, 11))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (1, 11))
        editor._move_key_ctl_up()
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (-19, 11))

    def test__move_key_ctl_down(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((11, 11))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (21, 11))
        editor._move_key_ctl_down()
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (41, 11))

    def test__select_key_left(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, 1))
        editor._select_key_left()
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (5, -1))

    def test__select_key_right(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 3))
        editor._select_key_right()
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (5, 5))

    def test__select_key_up(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((2, 2))
        editor._select_key_up()
        self.assertEqual(editor.cpos.get_pos(), (1, 2))
        editor._select_key_up()
        editor._select_key_up()
        self.assertEqual(editor.cpos.get_pos(), (-1, 2))

    def test__select_key_down(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((5, 2))
        editor._select_key_down()
        self.assertEqual(editor.cpos.get_pos(), (6, 2))
        editor._select_key_down()
        editor._select_key_down()
        self.assertEqual(editor.cpos.get_pos(), (8, 2))

    def test__move_key_page_up(self):
        editor = HexEditor([('', '')])
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
        editor = HexEditor([('', '')])
        editor.wpos.set_pos((0, 0))
        editor.cpos.set_pos((3, 11))
        editor._move_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (33, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))
        editor._move_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (63, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))

    def test__select_key_page_up(self):
        editor = HexEditor([('', '')])
        editor.wpos.set_pos((83, 0))
        editor.cpos.set_pos((93, 11))
        editor._select_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (63, 11))
        self.assertEqual(editor.wpos.get_pos(), (53, 0))
        editor._select_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (33, 11))
        self.assertEqual(editor.wpos.get_pos(), (23, 0))
        editor._select_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (3, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))
        editor._select_key_page_up()
        self.assertEqual(editor.cpos.get_pos(), (-27, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))

    def test__select_key_page_down(self):
        editor = HexEditor([('', '')])
        editor.wpos.set_pos((0, 0))
        editor.cpos.set_pos((3, 11))
        editor._select_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (33, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))
        editor._select_key_page_down()
        self.assertEqual(editor.cpos.get_pos(), (63, 11))
        self.assertEqual(editor.wpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__move_key_end(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((0, 2))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0, 15))
        editor.cpos.set_pos((1, 1))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (1, 3))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 70))
    def test__move_key_ctl_end(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((1, 1))
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (4, 5))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__select_key_end(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((0, 2))
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0, 15))
        editor.cpos.set_pos((1, 1))
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (1, 3))

    def test__move_key_home(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((123, 123))
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (123, 0))

    def test__move_key_ctl_home(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((123, 123))
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    def test__select_key_home(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((123, 123))
        editor._select_key_home()
        self.assertEqual(editor.cpos.get_pos(), (123, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__insert_byte_left(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] + ['40'] * 7] + [['40']])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))
        editor._insert_byte('<')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 8 + ['--'] * 2 + ['40'] * 6] + [['40'] * 2])
        self.assertEqual(editor.cpos.get_pos(), (0, 8))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__insert_byte_right(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((0, 8))
        editor._insert_byte('>')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 9 + ['--'] + ['40'] * 6] + [['40']])
        self.assertEqual(editor.cpos.get_pos(), (0, 9))
        editor._insert_byte('>')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 9 + ['--'] * 2 + ['40'] * 5] + [['40'] * 2])
        self.assertEqual(editor.cpos.get_pos(), (0, 10))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__insert_byte_chunk(self):
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((1, 2))
        editor._insert_byte(' ')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16, ['40'] * 4 + ['--'] * 12])
        self.assertEqual(editor.cpos.get_pos(), (1, 4))
        editor._insert_byte(' ')
        self.assertSequenceEqual(editor.hex_array, [['40'] * 16, ['40'] * 4 + ['--'] * 12, ['--'] * 16])
        self.assertEqual(editor.cpos.get_pos(), (2, 0))

    def test__key_string_invalid(self):
        editor = HexEditor([(__file__, '')])
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

        editor = HexEditor([('', '')])
        hex_array = deepcopy(editor.hex_array)
        hex_array_edit = deepcopy(editor.hex_array_edit)
        editor._key_string('0')
        self.assertSequenceEqual(editor.hex_array, hex_array)
        self.assertSequenceEqual(editor.hex_array_edit, hex_array_edit)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__key_string(self):
        editor = HexEditor([('', '')])
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

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 20))
    def test__select_key_all(self):
        editor = HexEditor([('', '')])
        editor.spos.set_pos((1,1))
        editor._select_key_all()
        self.assertEqual(editor.spos.get_pos(), (0, 0))
        self.assertEqual(editor.cpos.get_pos(), (1, 3))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen([]))
    def test_full_integration(self):
        mm_backup1 = mm.error
        mm_backup2 = mm.keyname
        mm_backup2 = mm.initscr
        def char_gen(user_input: list):
            yield from user_input
            while True:
                yield user_input[-1]
        _keyname_mapping = {
            '\x11'     : b'^Q',
            '\x7f'     : b'^?',
            '\r'       : b'^M',
            '\t'       : b'^I',
            'ş'        : b'KEY_BTAB',
            '\x1a'     : b'^Z',
            '\x19'     : b'^Y',
            'Ŋ'        : b'KEY_DC',
            'ȏ'        : b'CTL_DEL',
            'Ą'        : b'KEY_LEFT',
            'ą'        : b'KEY_RIGHT',
            'ă'        : b'KEY_UP',
            'Ă'        : b'KEY_DOWN',
            'Ƈ'        : b'KEY_SLEFT',
            'ȣ'        : b'KEY_SUP',
            'Ȥ'        : b'KEY_SDOWN',
            '\x10'     : b'^P',
            '\x06'     : b'^F',
            '\x0e'     : b'^N',
            '\x14'     : b'^T',
            '\x01'     : b'^A',
            '\x05'     : b'^E',
            'ĉ'        : b'KEY_F(1)',
        }
        def _keyname(x):
            return _keyname_mapping.get(chr(x), chr(x).encode())

        g = [
            ['>', '2', '2', '>', '>', '>', 260, 260, '0', 'd', '0', 'a', '2', '2', '\x11', '\x11'],
            ['\x0e', 'H', 'e', 'x', 'E', 'd', 'i', 't', 'o', 'r', '_', 'F', 'u', 'l', 'l', 'I', 'n', 't', 'e', 'g', 'r', 'a', 't', 'i', 'o', 'n', 'T', 'e', 's', 't', '\r', '\x05', 'd', '\r', '0', 'd', '0', 'a', '\x7f', '\x11', '\x11'],
            ['\x0e', 'H', 'e', 'x', 'E', 'd', 'i', 't', 'o', 'r', '_', 'F', 'u', 'l', 'l', 'I', 'n', 't', 'e', 'g', 'r', 'a', 't', 'i', 'o', 'n', 'T', 'e', 's', 't', '\r', 265, 'a', 260, 547, '\x7f', '\x11', '\x11']
        ]
        r = [
            [
                b'"\r\n"',
            ],
            [
                b'HexEditor_Ful\r\n',
                b'tegrationTest',
            ],
            [
                b'HexEditor_F',
                b't',
            ],
        ]
        mm.keyname = _keyname
        mm.error = KeyboardInterrupt
        for get_wch_, result_ in zip(g, r):
            char_gen_get_wch = char_gen(get_wch_)
            def _get_wch():
                return next(char_gen_get_wch)

            editor = HexEditor([('', '')])
            # editor.debug_mode = True

            curse_window_mock = MagicMock()
            curse_window_mock.get_wch = _get_wch

            mm.initscr = lambda *args: curse_window_mock

            editor._open()
            for i in range(len(result_)):
                self.assertSequenceEqual(editor._get_current_state_bytes_row(i), result_[i])

        mm.error = mm_backup1
        mm.keyname = mm_backup2
        mm.initscr = mm_backup2

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 21))
    def test__action_copy(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '40' * 10 + '21' + '40' * 10)
        editor = HexEditor([('', '')])
        editor.selecting = True
        editor.hex_array_edit[0][10] = '21'
        editor._select_key_all()
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_copy()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 21))
    def test__action_copy_single(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '21')
        editor = HexEditor([('', '')])
        editor.hex_array_edit[0][10] = '21'
        editor.cpos.set_pos((0, 10))
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_copy()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 21))
    def test__action_cut(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '40' * 10 + '21' + '40' * 10)
        editor = HexEditor([('', '')])
        editor.selecting = True
        editor.hex_array_edit[0][10] = '21'
        editor._select_key_all()
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_cut()
        self.assertListEqual(editor.hex_array_edit, [['--'] * 16, ['--'] * 5])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 21))
    def test__action_cut_single(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '21')
        editor = HexEditor([('', '')])
        editor.hex_array_edit[0][10] = '21'
        editor.cpos.set_pos((0, 10))
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_cut()
        self.assertListEqual(editor.hex_array_edit, [[None] * 10 + ['--'] + [None] * 5, [None] * 5])

    def test__action_render_scr(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        self.assertNotEqual(editor.error_bar, '')
        self.assertEqual(editor._action_render_scr(''), None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 496))
    def test__action_save(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, b'!'*16+b'@'*479)
        editor = HexEditor([('', '')])
        editor.hex_array_edit[0] = ['21'] * 16
        editor.cpos.set_pos((5, 2))
        editor._key_dl(None)
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 500))
    @patch('cat_win.src.curses.hexeditor.HexEditor.columns', 5)
    def test__action_save_correctness(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, b'@'*6+b'!@!'+b'@'*492)
        editor = HexEditor([('', '')])
        editor.cpos.set_pos((1,1))
        editor._key_string('2')
        editor._key_string('1')
        for _ in range(100):
            editor._key_string('>')
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
        editor = HexEditor([('', '')])
        editor.hex_array_edit[0] = ['21'] * 16
        editor._action_save()
        self.assertEqual(editor.error_bar, "validn't")

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 496))
    def test__action_jump(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'F', 'F', 'j'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen([5, '\x1b'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen([5, 'N'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 254 + b'!' * 2 + b'@' * 255))
    def test__action_find(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_backspace', b'_key_enter'])
        char_gen_ = char_gen([5, 'G', '2', '1', '0'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 14))
        def char_gen_ctl(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_ctl_backspace', b'_key_enter'])
        char_gen_ = char_gen_ctl(['2', '1', 'F', 'E', 'D', 'C'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        char_gen_ = char_gen_ctl(['4', '0', '\x1b'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (15, 15))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 66))
    def test__action_reload(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'F', 'F', 'j'])
        editor.cpos.set_pos((1, 14))
        editor.hex_array_edit[0][0] = '21'
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.hex_array_edit[0][0], '21')
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.hex_array_edit[0][0], None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test__action_insert(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from user_input
        editor.cpos.set_pos((1, 3))
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('\x1b', b'_key_string')):
            self.assertEqual(editor._action_insert(), True)
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_insert(), True)
        char_gen_ = char_gen([(9, b'_key_string'), ('\ud83e\udd23', b'_key_string'),
                              ('', b'_key_enter')])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_insert(), True)
            self.assertSequenceEqual(editor.hex_array_edit[1], [None, None, None, None,
                                                                'F0', '9F', 'A4', 'A3',
                                                                None, None, None, None,
                                                                None, None, None, None,])
        char_gen_ = char_gen([('A', b'_key_string'), ('B', b'_key_string'),
                              ('C', b'_key_string'), ('', b'_key_ctl_backspace'),
                              ('A', b'_key_string'), ('B', b'_key_string'),
                              ('C', b'_key_string'), ('', b'_key_backspace'),
                              ('', b'_key_enter')])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)):
            self.assertEqual(editor._action_insert(), True)
            self.assertSequenceEqual(editor.hex_array_edit[1], [None, None, None, None,
                                                                'F0', '9F', 'A4', 'A3',
                                                                '41', '42', None, None,
                                                                None, None, None, None,])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test__action_quit(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_quit(), False)
        editor.unsaved_progress = True
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('n', b'_key_string')):
            self.assertEqual(editor._action_quit(), False)
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_quit')):
            self.assertEqual(editor._action_quit(), False)
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('', b'_action_interrupt')):
            self.assertEqual(editor._action_quit(), True)
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('\x1b', b'_key_string')):
            self.assertEqual(editor._action_quit(), True)
        def action_save(_):
            editor.unsaved_progress = False
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        char_gen_ = char_gen([5, 'G', 'j'])
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: next(char_gen_)), \
            patch('cat_win.src.curses.hexeditor.HexEditor._action_save', action_save):
            self.assertEqual(editor._action_quit(), False)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test__action_interrupt(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        self.assertRaises(KeyboardInterrupt, editor._action_interrupt)

    def test__action_resize(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_resize(), True)

    def test__get_next_char(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor.curse_window.get_wch.return_value = '!'
        self.assertEqual(editor._get_next_char(), ('!', b'_key_string'))
        editor.curse_window.get_wch.return_value = 497
        self.assertEqual(editor._get_next_char(), (497, b'_key_string'))
        editor.curse_window.get_wch.return_value = ' '
        editor.debug_mode = True
        logger.clear()
        with patch('cat_win.src.curses.hexeditor.logger', logger) as fake_out:
            self.assertEqual(editor._get_next_char(), (' ', b'_key_string'))
            self.assertIn('DEBUG', fake_out.output())
            self.assertIn("b'_key_string'", fake_out.output())
            self.assertIn('32', fake_out.output())
            self.assertIn("' '", fake_out.output())

    def test__get_color(self):
        editor = HexEditor([('', '')])
        mm.has_colors.return_value = False
        self.assertEqual(editor._get_color(0), 0)
        mm.has_colors.return_value = True
        mm.color_pair.return_value = 5
        self.assertEqual(editor._get_color(0), 5)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 66))
    def test__fix_cursor_position(self):
        editor = HexEditor([('', '')])
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
        editor = HexEditor([('', 'X' * 300)])
        editor.curse_window = MagicMock()
        editor.error_bar = ':)'
        editor.debug_mode = True
        editor.hex_array_edit[0][0] = '00'
        editor.hex_array_edit[1][1] = '00'
        self.assertEqual(editor._render_scr(), None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 16))
    def test__run(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        with patch('cat_win.src.curses.hexeditor.HexEditor._get_next_char', lambda *args: ('\x11', b'_action_quit')):
            self.assertEqual(editor._run(), None)

    @patch('os.environ.setdefault', lambda *args: None)
    def test__open(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        with patch('cat_win.src.curses.hexeditor.HexEditor._run', lambda *args: None):
            self.assertEqual(editor._open(), None)

    @patch('cat_win.src.curses.hexeditor.CURSES_MODULE_ERROR', new=True)
    @patch('cat_win.src.curses.hexeditor.on_windows_os', new=True)
    def test_open_no_curses_error(self):
        logger.clear()
        with patch('cat_win.src.curses.hexeditor.logger', logger) as fake_out:
            self.assertEqual(HexEditor.open([('', '')]), False)
            self.assertIn('could not be loaded', fake_out.output())
            self.assertIn('windows-curses', fake_out.output())
        logger.clear()
        with patch('cat_win.src.curses.hexeditor.logger', logger) as fake_out:
            self.assertEqual(HexEditor.open([('', '')]), False)
            self.assertEqual('', fake_out.output())

    def test_set_flags(self):
        backup_a = HexEditor.save_with_alt
        backup_b = HexEditor.debug_mode
        backup_c = HexEditor.unicode_escaped_search
        backup_d = HexEditor.unicode_escaped_insert
        backup_e = HexEditor.columns
        HexEditor.set_flags(True, True, False, False, 1002)
        self.assertEqual(HexEditor.save_with_alt, True)
        self.assertEqual(HexEditor.debug_mode, True)
        self.assertEqual(HexEditor.unicode_escaped_search, False)
        self.assertEqual(HexEditor.unicode_escaped_insert, False)
        self.assertEqual(HexEditor.columns, 1002)
        HexEditor.set_flags(backup_a, backup_b, backup_c, backup_d, backup_e)

    def test_hexeditor_import_error_path(self):
        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'curses':
                raise ImportError('forced')
            return real_import(name, globals, locals, fromlist, level)

        with patch('builtins.__import__', side_effect=fake_import):
            ns = runpy.run_path(hexeditor.__file__, run_name='__cov_hexeditor_importerror__')
        self.assertTrue(ns['CURSES_MODULE_ERROR'])

    def test_file_selection_help_search_and_highlight_branches(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor.files = [('a.bin', 'A'), ('b.bin', 'B')]
        editor.file = 'a.bin'
        editor.display_name = 'A'
        editor.unsaved_progress = False

        def gen(events):
            yield from events

        editor._get_next_char = gen([
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ]).__next__
        with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', return_value=None):
            self.assertFalse(editor._action_file_selection())
        self.assertEqual(editor.open_next_idx, 1)

        editor2 = HexEditor([('', '')])
        editor2.curse_window = MagicMock()
        editor2.files = [('a.bin', 'A'), ('b.bin', 'B')]
        editor2.file = 'a.bin'
        editor2.display_name = 'A'
        editor2.unsaved_progress = False
        editor2._get_next_char = gen([
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
            ('', b'_action_quit'),
        ]).__next__
        commit = {'hash': 'abc1234', 'date': '2024-01-01', 'author': 'u', 'message': 'm'}
        with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', return_value=[commit]):
            self.assertTrue(editor2._action_file_selection())

        editor3 = HexEditor([('', '')])
        editor3.curse_window = MagicMock()
        mm.error = Exception
        calls = {'n': 0}

        def addstr_once_error(*_args, **_kwargs):
            if calls['n'] == 0:
                calls['n'] += 1
                raise Exception('boom')
            return None

        editor3.curse_window.addstr.side_effect = addstr_once_error
        editor3._get_next_char = lambda: ('x', b'_key_string')
        editor3._function_help()

        editor3.search = ''
        self.assertIsNone(editor3._function_search())
        self.assertIsNone(editor3._function_search_r())
        editor3.search = 'aa'
        with patch.object(editor3, '_action_find') as af:
            editor3._function_search()
            editor3._function_search_r()
        self.assertEqual(af.call_count, 2)

        editor4 = HexEditor([(__file__, '')])
        editor4.curse_window = MagicMock()
        editor4.curse_window.chgat.side_effect = mm.error
        editor4._render_highlight_selection()

        editor4.hex_array_edit[0][0] = '21'
        editor4.curse_window.addstr.side_effect = mm.error
        editor4._render_highlight_edits(5)

        editor4.selecting = True
        editor4.spos.set_pos((0, 0))
        editor4.cpos.set_pos((0, 0))
        editor4.curse_window.chgat.side_effect = mm.error
        editor4._render_highlight_selected_area(5)

    def test_hexeditor_open_windows_loop_and_loading_failed(self):
        HexEditor.loading_failed = True
        self.assertFalse(HexEditor.open([('a', 'A')]))

        created = []

        def fake_init(self, files, file_idx=0, file_commit_hash=None):
            self.files = files
            self.file = files[file_idx][0] if files else ''
            self.display_name = files[file_idx][1] if files else ''
            self.error_bar = ''
            self.open_next_idx = 1 if not created else None
            self.open_next_hash = None
            self.changes_made = not created
            created.append(self)

        with patch('cat_win.src.curses.hexeditor.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.hexeditor.on_windows_os', True):
                with patch.object(HexEditor, '__init__', fake_init):
                    with patch.object(HexEditor, '_open', lambda *_, **__: None):
                        HexEditor.loading_failed = False
                        self.assertTrue(HexEditor.open([('a', 'A'), ('b', 'B')]))

        self.assertGreaterEqual(len(created), 2)
        self.assertTrue(callable(getattr(created[0], '_action_background', None)))
        self.assertTrue(callable(getattr(created[1], '_action_background', None)))

    def test_find_reload_insert_and_search_render_extra_branches(self):
        editor = HexEditor([(__file__, '')])
        editor.curse_window = MagicMock()

        backup_search_escape = HexEditor.unicode_escaped_search
        HexEditor.unicode_escaped_search = True
        try:
            editor._get_next_char = iter([
                ('', b'_action_insert'),
                ('A', b'_key_string'),
                ('', b'_key_enter'),
                ('', b'_action_quit'),
            ]).__next__
            with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory', side_effect=ValueError('bad: ')):
                self.assertTrue(editor._action_find())
            self.assertEqual(editor.search, '41')
        finally:
            HexEditor.unicode_escaped_search = backup_search_escape

        editor2 = HexEditor([(__file__, '')])
        editor2.curse_window = MagicMock()
        editor2.selecting = True
        editor2.spos.set_pos((0, 0))
        editor2.cpos.set_pos((0, 0))
        editor2.search = '41'
        editor2._get_next_char = iter([
            ('', b'_key_enter'),
            ('', b'_action_quit'),
        ]).__next__
        with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory', return_value=iter(())):
            self.assertTrue(editor2._action_find())
        self.assertEqual(editor2.cpos.get_pos(), (0, 0))
        self.assertEqual(editor2.spos.get_pos(), (0, 0))

        editor3 = HexEditor([(__file__, '')])
        editor3.curse_window = MagicMock()
        editor3._get_next_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_reload'),
        ]).__next__
        with patch.object(editor3, '_action_background', return_value=True):
            with patch.object(editor3, '_render_scr') as render_scr:
                with patch.object(editor3, '_setup_file') as setup_file:
                    self.assertTrue(editor3._action_reload())
        self.assertTrue(render_scr.called)
        self.assertTrue(setup_file.called)

        editor4 = HexEditor([(__file__, '')])
        editor4.curse_window = MagicMock()
        editor4.cpos.set_pos((0, 0))
        editor4._get_next_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_insert'),
        ]).__next__
        with patch.object(editor4, '_get_clipboard', return_value='A'):
            self.assertTrue(editor4._action_insert())
        self.assertEqual(editor4.hex_array_edit[0][1], '41')

        editor5 = HexEditor([(__file__, '')])
        editor5.curse_window = MagicMock()
        editor5.search_items = {
            (0, 0): (2, 0),
            (0, 1): (1, 0),
            (0, 2): (1, 1),
        }
        editor5.cpos.set_pos((0, 0))
        editor5._render_search_items(5)
        self.assertEqual(editor5.search_items, {})
        self.assertGreater(editor5.curse_window.chgat.call_count, 0)

    def test_file_selection_and_open_exception_extra_branches(self):
        editor = HexEditor([(__file__, '')])
        editor.curse_window = MagicMock()
        editor.files = [(__file__, f'FILE_{i}_' + 'X' * 100) for i in range(12)]
        editor.file = __file__
        editor.display_name = editor.files[0][1]
        editor.file_commit_hash = 'does-not-exist'
        commit = {'hash': 'abc1234', 'date': '2024-01-01', 'author': 'u', 'message': 'm'}

        def gen(events):
            yield from events
            while True:
                yield ('', b'_action_quit')

        editor._get_next_char = gen([
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_ctl_up'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_key_enter'),
        ]).__next__
        with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', return_value=[commit]):
            self.assertTrue(editor._action_file_selection())

        editor2 = HexEditor([(__file__, '')])
        editor2.curse_window = MagicMock()
        editor2.unsaved_progress = True
        editor2._f_content_gen = MagicMock()
        editor2._f_content_gen.close.side_effect = StopIteration()

        with patch.object(editor2, '_init_screen', lambda *_: None):
            with patch.object(editor2, '_run', side_effect=RuntimeError('boom')):
                with patch.object(editor2, '_action_save', lambda: None):
                    with patch('builtins.input', side_effect=['x', 'Y']):
                        with patch('cat_win.src.curses.hexeditor.curses.endwin'):
                            with self.assertRaises(RuntimeError):
                                editor2._open()

    def test_mouse_helpers_and_actions_extra_branches(self):
        editor = HexEditor([(__file__, '')])
        editor.curse_window = MagicMock()

        self.assertIsNone(editor._move_key_mouse_get_cell_by_mouse_pos(10, 2))
        self.assertEqual(editor._move_key_mouse_get_cell_by_mouse_pos(13, 2), (0, 0))
        self.assertEqual(editor._move_key_mouse_get_cell_by_mouse_pos(13 + HexEditor.columns * 3 + 2, 2), (0, 0))
        self.assertIsNone(editor._move_key_mouse_get_cell_by_mouse_pos(999, 999))

        mm.BUTTON1_CLICKED = 1
        mm.BUTTON1_PRESSED = 2
        mm.BUTTON1_RELEASED = 4
        mm.BUTTON4_PRESSED = 8
        mm.BUTTON5_PRESSED = 16

        with patch('cat_win.src.curses.hexeditor.curses.getmouse', return_value=(0, 13, 2, 0, mm.BUTTON1_CLICKED)):
            editor._move_key_mouse()
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

        editor.cpos.set_pos((1, 1))
        with patch('cat_win.src.curses.hexeditor.curses.getmouse', return_value=(0, 13, 2, 0, mm.BUTTON1_PRESSED)):
            editor._move_key_mouse()
        self.assertEqual(editor.spos.get_pos(), (0, 0))
        self.assertEqual(editor.cpos.get_pos(), (1, 1))

        with patch('cat_win.src.curses.hexeditor.curses.getmouse', return_value=(0, 13, 2, 0, mm.BUTTON1_RELEASED)):
            editor._move_key_mouse()
        self.assertTrue(editor.selecting)
        self.assertEqual(editor.cpos.get_pos(), (0, 0))

        with patch.object(editor, '_move_key_up') as move_up:
            with patch('cat_win.src.curses.hexeditor.curses.getmouse', return_value=(0, 13, 2, 0, mm.BUTTON4_PRESSED)):
                editor._move_key_mouse()
        self.assertEqual(move_up.call_count, 3)

        with patch.object(editor, '_move_key_down') as move_down:
            with patch('cat_win.src.curses.hexeditor.curses.getmouse', return_value=(0, 13, 2, 0, mm.BUTTON5_PRESSED)):
                editor._move_key_mouse()
        self.assertEqual(move_down.call_count, 3)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 32))
    def test_clipboard_paste_and_commit_selection_extra_branches(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        with patch('cat_win.src.service.clipboard.Clipboard.get', return_value=None):
            self.assertTrue(editor._action_paste())
        self.assertIn('clipboard', editor.error_bar.lower())

        editor2 = HexEditor([(__file__, '')])
        editor2.curse_window = MagicMock()
        editor2.hex_array[0][0] = '--'
        editor2.hex_array_edit[0][0] = None
        editor2.cpos.set_pos((0, 0))
        with patch('cat_win.src.service.clipboard.Clipboard.get', return_value='AB'):
            with patch.object(editor2, '_insert_byte') as insert_byte:
                self.assertTrue(editor2._action_paste())
        self.assertTrue(insert_byte.called)

        editor3 = HexEditor([(__file__, 'A')], file_commit_hash={'hash': 'abc1234'})
        editor3.curse_window = MagicMock()
        editor3.files = [(__file__, 'A')]
        editor3.file = __file__
        editor3.display_name = 'A'
        editor3.unsaved_progress = False
        commit = {'hash': 'abc1234', 'date': '2024-01-01', 'author': 'u', 'message': 'm'}
        editor3._get_next_char = iter([
            ('', b'_key_enter'),
            ('', b'_move_key_up'),
            ('', b'_key_enter'),
        ]).__next__
        with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', return_value=[commit]):
            self.assertFalse(editor3._action_file_selection())
        self.assertEqual(editor3.open_next_idx, 0)
        self.assertIsNone(editor3.open_next_hash)

    def test_low_level_helper_and_move_selection_extra_branches_2(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()

        editor.hex_array = [['--']]
        editor.hex_array_edit = [[None]]
        self.assertEqual(editor._get_current_state_bytes_row(0), b'')

        editor = HexEditor([(__file__, '')])
        editor.selecting = True
        editor.spos.set_pos((0, 1))
        editor.cpos.set_pos((1, 2))
        editor._move_key_left()
        editor._move_key_right()
        editor._move_key_up()
        editor._move_key_down()
        editor._move_key_ctl_left()
        editor._move_key_ctl_right()
        editor._move_key_ctl_up()
        editor._move_key_ctl_down()
        editor._move_key_page_up()
        editor._move_key_page_down()

        self.assertIsNone(editor._move_key_mouse_get_cell_by_mouse_pos(13 + HexEditor.columns * 3, 2))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 48))
    def test_action_jump_find_and_insert_hotkey_branches_2(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor._get_next_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_key_ctl_backspace'),
            ('Y', b'_key_string'),
        ]).__next__
        with patch.object(editor, '_get_clipboard', return_value='f2zz'):
            with patch.object(editor, '_action_background', return_value=True):
                with patch.object(editor, '_render_scr') as render_scr:
                    self.assertTrue(editor._action_jump())
        self.assertTrue(render_scr.called)

        editor2 = HexEditor([('', '')])
        editor2.curse_window = MagicMock()
        editor2.search = 'ZZ'
        def gen_find_events():
            events = [
                ('', b'_action_insert'),
                ('', b'_action_paste'),
                ('', b'_action_find'),
                ('', b'_action_background'),
                ('', b'_action_resize'),
                ('', b'_key_enter'),
            ]
            yield from events
            while True:
                yield ('\x1b', b'_key_string')
        editor2._get_next_char = gen_find_events().__next__
        with patch.object(editor2, '_get_clipboard', return_value='A'):
            with patch.object(editor2, '_action_background', return_value=True):
                with patch.object(editor2, '_render_scr') as render_scr2:
                    self.assertTrue(editor2._action_find())
        self.assertTrue(render_scr2.called)

        editor3 = HexEditor([('', '')])
        editor3.curse_window = MagicMock()
        editor3._get_next_char = iter([
            ('', b'_key_enter'),
        ]).__next__
        self.assertTrue(editor3._action_find())

        backup_insert = HexEditor.unicode_escaped_insert
        HexEditor.unicode_escaped_insert = True
        try:
            editor4 = HexEditor([('', '')])
            editor4.curse_window = MagicMock()
            editor4._get_next_char = iter([
                ('', b'_action_background'),
                ('', b'_action_resize'),
                ('A', b'_key_string'),
                ('\\', b'_key_string'),
                ('x', b'_key_string'),
                ('4', b'_key_string'),
                ('1', b'_key_string'),
                ('', b'_key_enter'),
            ]).__next__
            with patch.object(editor4, '_action_background', return_value=True):
                with patch.object(editor4, '_render_scr') as render_scr3:
                    self.assertTrue(editor4._action_insert())
            self.assertTrue(render_scr3.called)
        finally:
            HexEditor.unicode_escaped_insert = backup_insert

    def test_file_selection_render_and_navigation_extra_branches_2(self):
        editor = HexEditor([(__file__, 'A')])
        editor.curse_window = MagicMock()
        editor.files = [(__file__, 'A')] + [(__file__, f'LONG_{i}_' + 'X' * 60) for i in range(30)]
        editor.file = __file__
        editor.display_name = 'not-in-list'
        editor.unsaved_progress = False

        old_getxymax = editor.getxymax
        editor.getxymax = lambda: (1, 20)

        addstr_calls = {'n': 0}
        def addstr_side_effect(*args, **kwargs):
            addstr_calls['n'] += 1
            if addstr_calls['n'] == 1:
                raise mm.error
            if addstr_calls['n'] == 3:
                raise mm.error
            return None

        editor.curse_window.addstr.side_effect = addstr_side_effect
        editor._get_next_char = iter([
            ('', b'_action_file_selection'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_down'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_key_enter'),
        ]).__next__
        with patch.object(editor, '_action_background', return_value=True):
            with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', side_effect=OSError('no git')):
                self.assertTrue(editor._action_file_selection())
        editor.getxymax = old_getxymax

    def test_render_selection_search_and_status_extra_branches_2(self):
        editor = HexEditor([(__file__, '')])
        editor.curse_window = MagicMock()

        editor.selecting = True
        editor.wpos.row = 1
        editor.spos.set_pos((0, 0))
        editor.cpos.set_pos((2, 0))
        editor._render_highlight_selected_area(1)

        editor.search_items = {(0, 0): (0, 0)}
        editor._render_search_items(1)
        editor.search_items = {(0, 0): (200, 0)}
        editor._render_search_items(1)

        old_error = mm.error
        try:
            mm.error = Exception
            editor.curse_window.addstr.side_effect = mm.error
            editor._render_status_bar(2, 20)
        finally:
            mm.error = old_error

    def test_init_open_and_unix_open_loop_extra_branches_2(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()

        with patch('cat_win.src.curses.hexeditor.sys.version_info', (3, 8, 0)):
            with patch('cat_win.src.curses.hexeditor.os.isatty', return_value=True):
                editor._init_screen()
        self.assertTrue(mm.use_default_colors.called)

        editor2 = HexEditor([('', '')])
        editor2.curse_window = MagicMock()
        editor2.unsaved_progress = False
        editor2._f_content_gen = MagicMock()
        editor2._f_content_gen.close.side_effect = StopIteration()
        with patch.object(editor2, '_init_screen', lambda *_: None):
            with patch.object(editor2, '_run', side_effect=RuntimeError('boom-no-save')):
                with patch('cat_win.src.curses.hexeditor.curses.endwin'):
                    with self.assertRaises(RuntimeError):
                        editor2._open()

        editor3 = HexEditor([('', '')])
        editor3.curse_window = MagicMock()
        editor3.unsaved_progress = True
        editor3._f_content_gen = MagicMock()
        editor3._f_content_gen.close.side_effect = StopIteration()

        def save_ok():
            editor3.unsaved_progress = False
            return True

        with patch.object(editor3, '_init_screen', lambda *_: None):
            with patch.object(editor3, '_run', side_effect=RuntimeError('boom-save')):
                with patch.object(editor3, '_action_save', save_ok):
                    with patch('builtins.input', return_value='N'):
                        with patch('cat_win.src.curses.hexeditor.curses.endwin'):
                            with self.assertRaises(RuntimeError):
                                editor3._open()

        with patch.object(editor3, '_init_screen', lambda *_: None):
            with patch.object(editor3, '_run', side_effect=RuntimeError('boom-save2')):
                with patch.object(editor3, '_action_save', save_ok):
                    with patch('builtins.input', return_value='Y'):
                        with patch('cat_win.src.curses.hexeditor.curses.endwin'):
                            with self.assertRaises(RuntimeError):
                                editor3._open()

        created = []
        def fake_init(self, files, file_idx=0, file_commit_hash=None):
            self.files = files
            self.file = files[file_idx][0]
            self.display_name = files[file_idx][1]
            self.error_bar = ''
            self.open_next_idx = None
            self.open_next_hash = None
            self.changes_made = bool(created)
            created.append(self)

        with patch('cat_win.src.curses.hexeditor.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.hexeditor.on_windows_os', False):
                with patch.object(HexEditor, '__init__', fake_init):
                    with patch.object(HexEditor, '_open', lambda *_, **__: None):
                        with patch('cat_win.src.curses.hexeditor.signal.SIGTSTP', 18, create=True):
                            with patch('cat_win.src.curses.hexeditor.signal.SIG_IGN', 1, create=True):
                                with patch('cat_win.src.curses.hexeditor.signal.signal') as sig_call:
                                    HexEditor.loading_failed = False
                                    self.assertFalse(HexEditor.open([('a', 'A')]))
                                    self.assertTrue(sig_call.called)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(b'@' * 80))
    def test_remaining_action_and_resize_branches_3(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor.curse_window.addstr.side_effect = mm.error
        self.assertIsNone(editor._action_render_scr('msg'))

        editor._get_next_char = iter([
            ('', b'_action_jump'),
        ]).__next__
        self.assertTrue(editor._action_jump())

        editor2 = HexEditor([('', '')])
        editor2.curse_window = MagicMock()
        editor2._get_next_char = iter([
            ('A', b'_key_string'),
            ('', b'_key_backspace'),
            ('Y', b'_key_string'),
        ]).__next__
        self.assertTrue(editor2._action_jump())

        editor3 = HexEditor([('', '')])
        editor3.curse_window = MagicMock()
        editor3.search = 'AA'
        with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory', side_effect=ValueError('x')):
            self.assertTrue(editor3._action_find(1))

        backup_search = HexEditor.unicode_escaped_search
        HexEditor.unicode_escaped_search = True
        try:
            editor4 = HexEditor([('', '')])
            editor4.curse_window = MagicMock()
            editor4._get_next_char = iter([
                ('', b'_action_insert'),
                ('', b'_action_paste'),
                ('\\', b'_key_string'),
                ('u', b'_key_string'),
                ('2', b'_key_string'),
                ('0', b'_key_string'),
                ('a', b'_key_string'),
                ('c', b'_key_string'),
                ('', b'_key_enter'),
                ('\x1b', b'_key_string'),
            ]).__next__
            with patch.object(editor4, '_get_clipboard', return_value='AB'):
                with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory', side_effect=ValueError('finderr')):
                    self.assertTrue(editor4._action_find())
        finally:
            HexEditor.unicode_escaped_search = backup_search

        class SearchObj:
            def __init__(self, vals, s_len=2, start_half=0):
                self._it = iter(vals)
                self.s_len = s_len
                self.match_start_half = start_half

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._it)

        editor5 = HexEditor([('', '')])
        editor5.curse_window = MagicMock()
        editor5.search = '41'
        editor5._get_next_char = iter([('', b'_key_enter')]).__next__
        with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory',
                   side_effect=[SearchObj([(0, 0)]), SearchObj([(999, 0)])]):
            self.assertTrue(editor5._action_find(-1))

        editor6 = HexEditor([('', '')])
        editor6.curse_window = MagicMock()
        editor6.selecting = True
        editor6.cpos.set_pos((0, 0))
        editor6.spos.set_pos((0, 1))
        editor6.search = '41'
        editor6._get_next_char = iter([('', b'_key_enter'), ('\x1b', b'_key_string')]).__next__
        with patch('cat_win.src.curses.hexeditor.search_iter_hex_factory', side_effect=StopIteration()):
            self.assertTrue(editor6._action_find(-1))

        backup_insert = HexEditor.unicode_escaped_insert
        HexEditor.unicode_escaped_insert = True
        try:
            editor7 = HexEditor([('', '')])
            editor7.curse_window = MagicMock()
            editor7._get_next_char = iter([
                ('\\', b'_key_string'),
                ('u', b'_key_string'),
                ('2', b'_key_string'),
                ('0', b'_key_string'),
                ('a', b'_key_string'),
                ('c', b'_key_string'),
                ('', b'_key_enter'),
            ]).__next__
            self.assertTrue(editor7._action_insert())
        finally:
            HexEditor.unicode_escaped_insert = backup_insert

        editor8 = HexEditor([('', '')])
        editor8.curse_window = MagicMock()
        with patch('cat_win.src.curses.hexeditor.on_windows_os', True):
            with patch('cat_win.src.persistence.viewstate.save_view_state') as save_state:
                self.assertFalse(editor8._action_background())
        save_state.assert_called_once_with('viewstate.bin', editor8)

        editor9 = HexEditor([('', '')])
        editor9.curse_window = MagicMock()
        editor9.unsaved_progress = True
        editor9._get_next_char = iter([
            ('', b'_action_background'),
            ('', b'_action_save'),
            ('', b'_action_resize'),
            ('N', b'_key_string'),
        ]).__next__
        with patch.object(editor9, '_action_background', return_value=True):
            with patch.object(editor9, '_action_save', return_value=True):
                with patch.object(editor9, '_render_scr') as rs:
                    self.assertFalse(editor9._action_quit())
        self.assertTrue(rs.called)

        old_error = mm.error
        try:
            mm.error = Exception
            mm.resize_term.side_effect = mm.error
            editor10 = HexEditor([('', '')])
            editor10.curse_window = MagicMock()
            self.assertTrue(editor10._action_resize())
        finally:
            mm.resize_term.side_effect = None
            mm.error = old_error

    def test_hexeditor_action_background_unix_path(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        with patch('cat_win.src.curses.hexeditor.on_windows_os', False):
            with patch('cat_win.src.curses.hexeditor.signal.SIGSTOP', 19, create=True):
                with patch('cat_win.src.curses.hexeditor.curses.endwin') as endwin_call:
                    with patch('cat_win.src.curses.hexeditor.os.kill') as kill_call:
                        with patch.object(editor, '_init_screen') as init_call:
                            self.assertTrue(editor._action_background())
        endwin_call.assert_called_once()
        kill_call.assert_called_once()
        init_call.assert_called_once()

    def test_remaining_file_selection_branches_3(self):
        editor = HexEditor([(__file__, 'A')])
        editor.curse_window = MagicMock()
        editor.files = []
        editor.file = 'notfound.bin'
        editor.display_name = 'missing'
        editor.unsaved_progress = False
        editor._get_next_char = iter([
            ('', b'_move_key_down'),
            ('', b'_action_quit'),
        ]).__next__
        self.assertTrue(editor._action_file_selection())

        editor2 = HexEditor([(__file__, 'A')])
        editor2.curse_window = MagicMock()
        editor2.file = 'notfound.bin'
        editor2.display_name = 'missing'
        editor2.files = [('p0', 'L' * 100), ('p1', 'M' * 100), ('p2', 'N' * 100)]
        editor2.unsaved_progress = False
        editor2.status_bar_size = 1
        editor2.getxymax = lambda: (1, 18)

        call_idx = {'n': 0}
        def addstr_side_effect(*args, **kwargs):
            call_idx['n'] += 1
            # force status message write into except branch once
            if call_idx['n'] == 4:
                raise mm.error
            return None

        editor2.curse_window.addstr.side_effect = addstr_side_effect
        editor2._get_next_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_action_file_selection'),
        ]).__next__

        with patch.object(editor2, '_action_background', return_value=True):
            with patch('cat_win.src.curses.hexeditor.GitHelper.get_git_file_history', side_effect=OSError('nogit')):
                self.assertFalse(editor2._action_file_selection())

    def test_final_remaining_find_and_file_selection_branches_4(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor._get_next_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_quit'),
        ]).__next__
        with patch.object(editor, '_get_clipboard', return_value='ab-!'):
            self.assertTrue(editor._action_find())

        editor2 = HexEditor([(__file__, 'A')])
        editor2.curse_window = MagicMock()
        editor2.files = [(f'p{i}', f'Name_{i}') for i in range(6)]
        editor2.file = 'missing-file'
        editor2.display_name = 'missing-display'
        editor2.unsaved_progress = False
        editor2.getxymax = lambda: (0, 20)
        editor2._get_next_char = iter([
            ('', b'_move_key_down'),
            ('', b'_action_quit'),
        ]).__next__
        self.assertTrue(editor2._action_file_selection())

    def test_getxymax_unpatched_extra_branch(self):
        editor = HexEditor([('', '')])
        editor.curse_window = MagicMock()
        editor.curse_window.getmaxyx.return_value = (12, 34)
        self.assertEqual(ORIGINAL_HEXEDITOR_GETXYMAX(editor), (12-editor.status_bar_size-3, 34))
