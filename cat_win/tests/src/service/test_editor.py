from unittest.mock import patch, MagicMock
from unittest import TestCase
import os

from cat_win.tests.mocks.edit import getxymax
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.std import StdOutMock, IoHelperMock

import cat_win.src.service.editor as editor_pkg
if editor_pkg.CURSES_MODULE_ERROR:
    setattr(editor_pkg, 'curses', None)
from cat_win.src.service.editor import Editor

mm = MagicMock()

test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')
test_file_path_editor = os.path.join(test_file_dir, 'test_editor.txt')


@patch('cat_win.src.service.editor.Editor.getxymax', getxymax)
@patch('cat_win.src.service.editor.curses', mm)
@patch('cat_win.src.service.helper.iohelper.IoHelper.get_newline', lambda *_: '\n')
class TestEditor(TestCase):
    maxDiff = None

    def test_editor_special_chars(self):
        editor = Editor(test_file_path_oneline, '')
        self.assertEqual(editor._get_special_char('\b'), '?')

        editor._set_special_chars({'\b': '!'})
        self.assertEqual(editor._get_special_char('\b'), '!')

    def test_editor_unknown_file(self):
        editor = Editor('', '')
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertListEqual(editor.window_content, [''])

    def test_selected_area(self):
        editor = Editor('', '')
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

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__build_file(self):
        editor = Editor('', '')
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 30)
        editor._build_file()
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 50)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__build_file_upto(self):
        editor = Editor('', '')
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 30)
        editor._build_file_upto(40)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 40)
        editor.window_content[15] = '0'
        editor._build_file_upto(50)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 15 + ['0'] + ['a' * 10] * 34)
        editor._build_file_upto(60)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 15 + ['0'] + ['a' * 10] * 34)

    def test_editor_key_enter(self):
        editor = Editor(test_file_path_oneline, '')
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 'test'])
        editor._move_key_right()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est'])
        editor._move_key_end()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est', ''])

    def test_editor_key_dc(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._key_dc(None), 'l')
        self.assertListEqual(editor.window_content, ['ine 1', 'line 2'])
        editor._move_key_right()
        editor._key_dc(None)
        self.assertListEqual(editor.window_content, ['ie 1', 'line 2'])
        editor._move_key_end()
        editor._key_dc(None)
        self.assertListEqual(editor.window_content, ['ie 1line 2'])
        editor._move_key_end()
        editor._key_dc(None)
        self.assertListEqual(editor.window_content, ['ie 1line 2'])
        editor.selecting = True
        editor.cpos.set_pos((0, 3))
        self.assertEqual(editor._key_dc(None), None)
        self.assertListEqual(editor.window_content, ['ie 1line 2'])

    def test_editor_key_dl(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._key_dl(None), 'line')
        self.assertListEqual(editor.window_content, [' 1', 'line 2'])
        editor._move_key_right()
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' ', 'line 2'])
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' line 2'])
        editor._move_key_end()
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' line 2'])
        editor.selecting = True
        editor.cpos.set_pos((0, 3))
        self.assertEqual(editor._key_dl(None), None)
        self.assertListEqual(editor.window_content, [' line 2'])

    def test_editor_key_backspace(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._key_backspace('\b'), None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_ctl_end()
        self.assertEqual(editor._key_backspace('\b'), '2')
        self.assertListEqual(editor.window_content, ['line 1', 'line '])
        editor._move_key_left()
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1', 'lin '])
        editor._move_key_home()
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1lin '])
        editor.selecting = True
        editor.cpos.set_pos((0, 4))
        self.assertEqual(editor._key_backspace('\b'), None)
        self.assertListEqual(editor.window_content, ['line 1lin '])

    def test_editor_key_ctl_backspace(self):
        editor = Editor(test_file_path_editor, '')
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_ctl_end()
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'line '])
        editor._move_key_home()
        editor._move_key_right()
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'ine '])
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1ine '])
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line ine '])
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['lineine '])
        self.assertEqual(editor._key_ctl_backspace(None), 'line')
        self.assertListEqual(editor.window_content, ['ine '])
        editor.selecting = True
        editor.cpos.set_pos((0, 2))
        self.assertEqual(editor._key_ctl_backspace(None), None)
        self.assertListEqual(editor.window_content, ['ine '])

    def test_editor_move_key_left(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._move_key_left(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,0))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,5))

    def test_editor_move_key_right(self):
        editor = Editor(test_file_path_editor, '')
        editor.cpos.set_pos((1,6))
        self.assertEqual(editor._move_key_right(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((0,6))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,1))

    def test_editor_move_key_up(self):
        editor = Editor(test_file_path_editor, '')
        editor.cpos.set_pos((1,3))
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (0,3))
        self.assertEqual(editor._move_key_up(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,3))

    def test_editor_move_key_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        self.assertEqual(editor._move_key_down(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_left(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,6))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (1,4))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor.cpos.set_pos((1,1))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._move_key_ctl_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_move_key_ctl_right(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (0,4))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor.cpos.set_pos((0,5))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor.cpos.set_pos((1,6))
        editor._move_key_ctl_right()
        self.assertEqual(editor.cpos.get_pos(), (1,6))

    def test_editor_move_key_ctl_up(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,6))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((11,4))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (1,4))

    def test_editor_move_key_ctl_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((-9, 3))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,3))

    def test_editor_select_key_left(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._select_key_left(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,0))
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,5))

    def test_editor_select_key_right(self):
        editor = Editor(test_file_path_editor, '')
        editor.cpos.set_pos((1,6))
        self.assertEqual(editor._select_key_right(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((0,6))
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,1))

    def test_editor_select_key_up(self):
        editor = Editor(test_file_path_editor, '')
        editor.cpos.set_pos((1,3))
        editor._select_key_up()
        self.assertEqual(editor.cpos.get_pos(), (0,3))
        self.assertEqual(editor._select_key_up(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,3))

    def test_editor_select_key_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._select_key_down()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        self.assertEqual(editor._select_key_down(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_scroll_key_left(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((1,2))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,1))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))

    def test_editor_scroll_key_right(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((0,2))
        editor._scroll_key_right()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._key_string('x' * 115)
        editor._scroll_key_right()
        self.assertEqual(editor.wpos.get_pos(), (0,1))
        editor._scroll_key_right()
        self.assertEqual(editor.wpos.get_pos(), (0,2))
        editor._scroll_key_right()
        self.assertEqual(editor.wpos.get_pos(), (0,2))

    def test_editor_scroll_key_up(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((2,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    def test_editor_scroll_key_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._scroll_key_down()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        for _ in range(30):
            editor._key_enter('')
        editor._scroll_key_down()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_down()
        self.assertEqual(editor.wpos.get_pos(), (2,0))
        editor._scroll_key_down()
        self.assertEqual(editor.wpos.get_pos(), (2,0))

    def test_editor_move_key_page_up(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        for _ in range(61):
            editor._key_enter('')
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (61,1))
        editor.wpos.set_pos(editor.cpos.get_pos())
        editor._move_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (31,1))
        self.assertEqual(editor.cpos.get_pos(), (31,1))
        editor._move_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (1,1))
        self.assertEqual(editor.cpos.get_pos(), (1,1))
        editor._move_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,1))
        self.assertEqual(editor.cpos.get_pos(), (0,1))

    def test_editor_move_key_page_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_page_down()
        for _ in range(61): # file_len == 63
            editor._key_enter('')
            editor._move_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._move_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (30,0))
        self.assertEqual(editor.cpos.get_pos(), (31,0))
        editor._move_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))
        self.assertEqual(editor.cpos.get_pos(), (61,0))
        editor._move_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))
        self.assertEqual(editor.cpos.get_pos(), (62,0))

    def test_editor_select_key_page_up(self):
        editor = Editor(test_file_path_editor, '')
        editor._select_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        for _ in range(61):
            editor._key_enter('')
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (61,1))
        editor.wpos.set_pos(editor.cpos.get_pos())
        editor._select_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (31,1))
        self.assertEqual(editor.cpos.get_pos(), (31,1))
        editor._select_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (1,1))
        self.assertEqual(editor.cpos.get_pos(), (1,1))
        editor._select_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,1))
        self.assertEqual(editor.cpos.get_pos(), (0,1))

    def test_editor_select_key_page_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._select_key_page_down()
        for _ in range(61): # file_len == 63
            editor._key_enter('')
            editor._move_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._select_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (30,0))
        self.assertEqual(editor.cpos.get_pos(), (31,0))
        editor._select_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))
        self.assertEqual(editor.cpos.get_pos(), (61,0))
        editor._select_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))
        self.assertEqual(editor.cpos.get_pos(), (62,0))

    def test_editor_scroll_key_page_up(self):
        editor = Editor(test_file_path_editor, '')
        editor._scroll_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        for _ in range(61):
            editor._key_enter('')
        editor.wpos.set_pos(editor.cpos.get_pos())
        editor._scroll_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (31,0))
        editor._scroll_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_page_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    def test_editor_scroll_key_page_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._scroll_key_page_down()
        for _ in range(61): # file_len == 63
            editor._key_enter('')
            editor._move_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._scroll_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (30,0))
        editor._scroll_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))
        editor._scroll_key_page_down()
        self.assertEqual(editor.wpos.get_pos(), (33,0))

    def test_editor_move_key_end(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_move_key_ctl_end(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))

    def test_editor_select_key_end(self):
        editor = Editor(test_file_path_editor, '')
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_scroll_key_end(self):
        editor = Editor(test_file_path_editor, '')
        for _ in range(61):
            editor._key_enter('')
        editor._key_string('!' * 150)
        editor._scroll_key_end()
        self.assertEqual(editor.wpos.get_pos(), (33, 37))

    def test_editor_move_key_home(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_home(self):
        editor = Editor(test_file_path_editor, '')
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))

    def test_editor_select_key_home(self):
        editor = Editor(test_file_path_editor, '')
        editor._select_key_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._select_key_home()
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_scroll_key_home(self):
        editor = Editor(test_file_path_editor, '')
        for _ in range(61):
            editor._key_enter('')
        editor._key_string('!' * 150)
        editor.wpos.set_pos((33, 37))
        editor._scroll_key_home()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    @patch('cat_win.src.service.editor.Editor.special_indentation', ':)')
    def test_editor_indent_tab(self):
        editor = Editor(test_file_path_editor, '')
        editor._key_string('TEST')
        self.assertListEqual(editor.window_content, ['TESTline 1', 'line 2'])
        editor._move_key_ctl_right()
        self.assertEqual(editor._indent_tab('\t'), '\t')
        self.assertListEqual(editor.window_content, ['TESTline\t 1', 'line 2'])
        editor._move_key_home()
        self.assertEqual(editor._indent_tab('\t'), ':)')
        self.assertListEqual(editor.window_content, [':)TESTline\t 1', 'line 2'])

    @patch('cat_win.src.service.editor.Editor.special_indentation', ':)')
    def test_editor_indent_tab_select(self):
        editor = Editor(test_file_path_editor, '')
        editor.selecting = True
        editor.spos.set_pos((0,2))
        editor.cpos.set_pos((0,4))
        self.assertEqual(editor._indent_tab('\t'), ':)\0')
        self.assertListEqual(editor.window_content, [':)line 1', 'line 2'])
        editor.spos.set_pos((0,2))
        editor.cpos.set_pos((1,4))
        self.assertEqual(editor._indent_tab('\t'), ':)\0:)\0')
        self.assertListEqual(editor.window_content, [':):)line 1', ':)line 2'])
        self.assertEqual(editor._indent_tab(':)\0'), ':)\0')
        self.assertListEqual(editor.window_content, [':):)line 1', ':):)line 2'])
        self.assertEqual(editor._indent_tab(':)\0:)\0'), ':)\0:)\0')
        self.assertListEqual(editor.window_content, [':):):)line 1', ':):):)line 2'])

    @patch('cat_win.src.service.editor.Editor.special_indentation', ':)')
    def test_editor_indent_btab(self):
        editor = Editor(test_file_path_editor, '')
        editor._key_string(':):):)')
        self.assertListEqual(editor.window_content, [':):):)line 1', 'line 2'])
        editor._move_key_ctl_right()
        self.assertEqual(editor._indent_btab(''), ':)\0')
        self.assertListEqual(editor.window_content, [':):)line 1', 'line 2'])
        self.assertEqual(editor._indent_btab(''), ':)\0')
        self.assertListEqual(editor.window_content, [':)line 1', 'line 2'])
        self.assertEqual(editor._indent_btab(''), ':)\0')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        self.assertEqual(editor._indent_btab(''), None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])

    @patch('cat_win.src.service.editor.Editor.special_indentation', ':)')
    def test_editor_indent_btab_select(self):
        editor = Editor(test_file_path_editor, '')
        editor.selecting = True
        editor.spos.set_pos((0,2))
        editor.cpos.set_pos((0,4))
        self.assertEqual(editor._indent_btab(351), None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor.cpos.set_pos((0,0))
        editor._key_string(':):):)')
        editor.cpos.set_pos((1,0))
        editor._key_string(':):):):)')
        self.assertListEqual(editor.window_content, [':):):)line 1', ':):):):)line 2'])
        editor.spos.set_pos((0,2))
        editor.cpos.set_pos((0,4))
        self.assertEqual(editor._indent_btab(351), ':)\0')
        self.assertListEqual(editor.window_content, [':):)line 1', ':):):):)line 2'])
        editor.cpos.set_pos((1,3))
        self.assertEqual(editor._indent_btab(351), ':)\0:)\0')
        self.assertListEqual(editor.window_content, [':)line 1', ':):):)line 2'])
        editor.selecting = False
        self.assertEqual(editor._indent_btab(351), ':)\0')
        self.assertListEqual(editor.window_content, [':)line 1', ':):)line 2'])
        self.assertEqual(editor._indent_btab(':)\0:)\0'), ':)\0:)\0')
        self.assertListEqual(editor.window_content, ['line 1', ':)line 2'])
        self.assertEqual(editor._indent_btab(':)\0:)\0'), '\0:)\0')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])

    def test_editor_key_remove_add_selected(self):
        editor = Editor(test_file_path, '')
        editor.spos.set_pos((4,8))
        editor.cpos.set_pos((6,2))
        self.assertEqual(editor._key_remove_chunk(None),
                         'owing Line is Empty:\n\nTh')
        self.assertListEqual(editor.window_content,
                             [
                                 'Sample Text:',
                                 'This is a Tab-Character: >\t<',
                                 'These are Special Chars: äöüÄÖÜ',
                                 'N-Ary Summation: ∑',
                                 'The follis Line is a Duplicate!',
                                 'This Line is a Duplicate!'
                                 ])
        self.assertEqual(editor.cpos.get_pos(), (4,8))
        self.assertEqual(editor._key_add_chunk('owing Line is Empty:\n\nTh'),
                         'owing Line is Empty:\n\nTh')
        self.assertEqual(editor.window_content,
                         [
                             'Sample Text:',
                             'This is a Tab-Character: >\t<',
                             'These are Special Chars: äöüÄÖÜ',
                             'N-Ary Summation: ∑',
                             'The following Line is Empty:',
                             '',
                             'This Line is a Duplicate!',
                             'This Line is a Duplicate!'
                             ])

    def test_editor_remove_chunk(self):
        editor = Editor(test_file_path, '')
        editor.spos.set_pos((4,8))
        editor.cpos.set_pos((6,2))
        self.assertEqual(len(editor.history._stack_undo), 0)
        editor._remove_chunk()
        self.assertEqual(len(editor.history._stack_undo), 1)
        action = editor.history._stack_undo[0]
        self.assertEqual(action.key_action,       b'_key_remove_chunk')
        self.assertEqual(action.action_text, ('owing Line is Empty:\n\nTh',))
        self.assertEqual(action.size_change, True)
        self.assertEqual(action.pre_cpos,    (6,2))
        self.assertEqual(action.post_cpos,   (4,8))
        self.assertEqual(action.pre_spos,    (4,8))

    def test_editor_key_string_surrogatepass(self):
        editor = Editor('', '')
        editor.debug_mode = True
        with patch('sys.stderr', StdOutMock()) as fake_out:
            editor._key_string('\ud83d\ude01')
            self.assertIn('Changed', fake_out.getvalue())
            self.assertIn('😁', fake_out.getvalue())
            self.assertIn('128513', fake_out.getvalue())
        with patch('sys.stderr', StdOutMock()) as fake_out:
            editor._key_string('\x1bTEST:)!')
            self.assertEqual(fake_out.getvalue(), '')

    @patch('cat_win.src.service.editor.Editor.special_indentation', '!!!')
    def test_editor_key_string(self):
        editor = Editor(test_file_path_editor, '')
        self.assertEqual(editor._key_string(1), '')
        self.assertEqual(editor._key_string(''), '')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_right()
        editor._key_string('test')
        self.assertListEqual(editor.window_content, ['ltestine 1', 'line 2'])
        editor._key_string('\t')
        self.assertListEqual(editor.window_content, ['ltest\tine 1', 'line 2'])
        editor._key_enter('')
        editor._key_string('\t')
        self.assertListEqual(editor.window_content, ['ltest\t', '!!!ine 1', 'line 2'])
        editor._key_string('\t')
        self.assertListEqual(editor.window_content, ['ltest\t', '!!!!!!ine 1', 'line 2'])

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 4))
    def test_editor_select_key_all(self):
        editor = Editor('', '')
        editor.spos.set_pos((1,1))
        editor._select_key_all()
        self.assertEqual(editor.spos.get_pos(), (0, 0))
        self.assertEqual(editor.cpos.get_pos(), (3, 3))

    @patch('cat_win.src.service.editor.Editor.auto_indent', True)
    @patch('cat_win.src.service.editor.Editor.special_indentation', '$')
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
        }
        def _keyname(x):
            return _keyname_mapping.get(chr(x), chr(x).encode())

        # note that _get_new_char() buffers the input, so the test behaves different than manual input
        # e.g. the test inserts an entire string at once meaning that undo and redo will do the same
        g = [
            ['a','b','c','\r','\t','z',351,'\r','\x1a','\x1a','\x1a','\x1a','\x1a','\x19','\x19','\x19','\x19','\x19','\x1a','\x1a','\x1a','\x1a','\x1a','\x1a','\x11'],
            ['T','E','S','T','\r','\r','\r','\r',259,259,259,527,330,'\x7f',330,258,'\r','\x11','\x11'],
            ['a', 'a', 'a', 'a', 'a', '\r', 'b', 'b', 'b', 'b', 'b', 260, 547, '\t', '\t', 351, '\x1a', '\x1a', '\x1a', '\x1a', '\x1a','\x11'],
            ['\t', '\r', '\x11', '\x11'],
            ['\t', 'a', '\t', 'b', 391, '\t', '\t', 351, '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x19', '\x19', '\x19', '\x19', '\x19', '\x19', '\x19', '\x19', '\x11'],
            ['\t', 'a', '\t', 'b', 391, '\t', 351, '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x19', '\x19', '\x19', '\x19', '\x19', '\x11'],
            ['\t', 'a', '\r', 'b', 391, '\t', '\r', 'c', '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x1a', '\x19', '\x19', '\x19', '\x19', '\x19', '\x19', '\x11'],
            ['a', 'b', '\r', '\t', 'c', 'd', '\r', '\t', 'e', 'f', 259, 259, 'x', 258, 548, '\t', 261, '\x1a', '\x1a', '\x11'],
            ['a', '\r', 'b', '\r', 'c', 259, 547, '\t', '\x1a','\x1a', '\x11'],
            ['a', 'a', 'b', 'a', '\x10', '\x06', 'a', '\r', 'X', '\r', '\x10', 'Y', '\x0e', '\r', '\x1a', '\x1a', '\x1a', '\x19', '\x19', '\x11'],
            ['a', 'b', 'c', '\r', 'd', 'e', 'f', 260, 547, '\x14', 'u', 'p', 'p', 'e', 'r', '\r', '\x1a', '\x19', '\x11', '\x11'],
            ['A', 'B', 'C', 'D', 'E', 'F', '\r', ' ', ' ', 'X', 'X', ' ', ' ', '\x01', '\x14', 's', 't', 'r', 'i', 'p', '\r', '\x1a', '\x19', '\x1a', '\x19', '\x14', 'l', 'o', 'w', 'e', 'r', '\r', '\x1a', '\x1a', '\x11', '\x11'],
        ]
        r = [
            [''],
            ['TEST', ''],
            ['aaaaa'],
            ['$', '$'],
            ['$$a\tb'],
            ['$$a\tb'],
            ['$a', '$$', '$$c'],
            ['ab', '$cd', '$$ef'],
            ['a', 'b', ''],
            ['XYba'],
            ['abC', 'DEf'],
            ['ABCDEF', ''],
        ]
        mm.keyname = _keyname
        for get_wch_, result_ in zip(g, r):
            char_gen_get_wch = char_gen(get_wch_)
            def _get_wch():
                return next(char_gen_get_wch)

            editor = Editor('', '')
            # editor.debug_mode = True

            curse_window_mock = MagicMock()
            curse_window_mock.get_wch = _get_wch

            mm.error = KeyboardInterrupt
            mm.initscr = lambda *args: curse_window_mock

            editor._open()
            self.assertSequenceEqual(editor.window_content, result_)

        mm.error = mm_backup1
        mm.keyname = mm_backup2
        mm.initscr = mm_backup2

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 4))
    def test__action_copy(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '\n'.join(['@@@'] * 4))
        editor = Editor('', '')
        editor.selecting = True
        editor._select_key_all()
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_copy()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 4))
    def test__action_cut(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '\n'.join(['@@', '@@@', '@@@', '@@']))
        editor = Editor('', '')
        editor.selecting = True
        editor.cpos.set_pos((0, 1))
        editor.spos.set_pos((3, 2))
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_cut()
        self.assertListEqual(editor.window_content, ['@@'])

    def test__action_render_scr(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        self.assertNotEqual(editor.error_bar, '')
        self.assertEqual(editor._action_render_scr(''), None)

    def test_editor_action_save(self):
        editor = Editor(test_file_path, '')
        editor.debug_mode = True
        error_def = ErrorDefGen.get_def(OSError('TestError'))
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', new=error_def), patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(editor._action_save(), True)
            self.assertEqual(editor.error_bar, 'TestError')
            self.assertEqual('TestError\n', fake_out.getvalue())

        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', new=lambda *_: None):
            self.assertEqual(editor._action_save(), True)
            self.assertEqual(editor.error_bar, '')

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 501))
    def test_editor_action_save_correctness(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, (b'@@@\n@!\n'+b'\n'*99+b'@@\n'+b'@@@\n'*498+b'@@@'))
        editor = Editor('', '')
        editor.cpos.set_pos((1,1))
        editor._key_string('!')
        for _ in range(100):
            editor._key_enter(None)
        self.assertEqual(editor.cpos.get_pos(), (101, 0))
        self.assertEqual(len(editor.window_content), 130)
        self.assertEqual(editor.window_content[editor.cpos.row], '@@')
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__action_save_lazy_load(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, ('\n'.join(['a' * 10] * 29) + '\nTEST\n' + '\n'.join(['a' * 10] * 20)).encode(editor.file_encoding))
        editor = Editor('', '')
        self.assertEqual(editor.window_content, ['a' * 10] * 30)
        editor.window_content[29] = 'TEST'
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__action_jump(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        def yield_action_quit():
            yield ('', b'_action_quit')
        editor.get_char = char_gen([5, 'G', '0', '4', 'j'])
        self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (3, 0))
        editor.get_char = char_gen([5, '\x1b'])
        self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (3, 0))
        editor.get_char = char_gen([5, 'N'])
        self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (3, 0))
        editor.get_char = yield_action_quit()
        self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (3, 0))
        editor.get_char = char_gen([5, '9', '9', '9', 'Y'])
        self.assertEqual(editor._action_jump(), True)
        self.assertEqual(editor.cpos.get_pos(), (49, 0))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 40 + ['aaa\ba\baa'] + ['a' * 10] * 12))
    def test__action_find(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_backspace', b'_key_enter'])
        editor.get_char = char_gen([5, 'a', '\\', 'b',  'a', 'a'])
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))
        editor.get_char = char_gen([5, 'a', '\\', 'b',  'a', 'a'])
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 4))
        editor.get_char = char_gen([5, 'a', '\\', 'b',  'a', 'a'])
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))
        def char_gen_ctl(user_input: list):
            yield from zip(user_input + ['', '', ''], [b'_key_string'] * len(user_input) + [b'_key_ctl_backspace', b'_key_enter', b'_action_quit'])
        editor.get_char = char_gen_ctl([5, 'a', '\\', 'b',  'a', '1', '2', '3', '4'])
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))
        def yield_action_quit():
            yield ('', b'_action_quit')
        editor.get_char = yield_action_quit()
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 40 + ['aaa\ba\baa'] + ['a' * 10] * 12))
    def test__action_replace(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_backspace', b'_key_enter'])
        editor.search = 'a\baa'
        editor.get_char = char_gen([5, 't', 'e', 's', 't', 't'])
        self.assertEqual(editor._action_replace(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 8))
        self.assertEqual(editor.window_content[40], 'aaa\btest')
        def char_gen_ctl(user_input: list):
            yield from zip(user_input + ['', '', ''], [b'_key_string'] * len(user_input) + [b'_key_ctl_backspace', b'_key_enter', b'_action_quit'])
        editor.search = 'a\bte'
        editor.get_char = char_gen_ctl([5, 'a', '\\', 'b',  'a', '1', '2', '3', '4'])
        self.assertEqual(editor._action_replace(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 4))
        self.assertEqual(editor.window_content[40], 'aaa\\st')
        def yield_action_quit():
            yield ('', b'_action_quit')
        editor.get_char = yield_action_quit()
        self.assertEqual(editor._action_replace(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 4))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__action_reload(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        editor.get_char = char_gen([5, 'G', 'F', 'F', 'j'])
        editor.cpos.set_pos((1, 14))
        editor.window_content[0] = 'TEST'
        self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.window_content[0], 'aaaaaaaaaa')
        def yield_action_quit():
            yield ('', b'_action_quit')
        editor.get_char = yield_action_quit()
        editor.cpos.set_pos((1, 14))
        editor.window_content[0] = 'TEST'
        self.assertEqual(editor._action_reload(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 14))
        self.assertEqual(editor.window_content[0], 'TEST')

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test_editor_action_insert(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        editor.history = MagicMock()
        def yield_tuple(a, b):
            yield (a, b)
        def char_gen(user_input: list):
            yield from user_input
        editor.cpos.set_pos((1, 8))
        editor.get_char = yield_tuple('\x1b', b'_key_string')
        self.assertEqual(editor._action_insert(), True)
        editor.get_char = yield_tuple('', b'_action_quit')
        self.assertEqual(editor._action_insert(), True)
        editor.get_char = char_gen([(5, b'_key_string'), ('2', b'_key_string'),
                                    ('G', b'_key_string'), ('X', b'_key_string'),
                                    ('1', b'_key_string'), ('2', b'_key_string'),
                                    ('1', b'_key_string'), ('A', b'_key_string'),
                                    ('A', b'_key_string'), ('', b'_key_ctl_backspace'),
                                    ('0', b'_key_string'), ('', b'_key_backspace'),
                                    ('', b'_key_enter')])
        self.assertEqual(editor._action_insert(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 10))
        self.assertEqual(editor.window_content[1], 'aaaaaaaa!!aa')
        editor.get_char = char_gen([('2', b'_key_string'), ('3', b'_key_string'),
                                    ('2', b'_key_string'), ('', b'_key_enter'),
                                    ('3', b'_key_string'), ('', b'_key_enter'),
                                    ])
        self.assertEqual(editor._action_insert(), True)
        self.assertEqual(editor.cpos.get_pos(), (1, 12))
        self.assertEqual(editor.window_content[1], 'aaaaaaaa!!##aa')

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test_editor_action_quit(self):
        editor = Editor(test_file_path, '')
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_quit(), False)
        editor.unsaved_progress = True
        def yield_tuple(a, b):
            yield (a, b)
        editor.get_char = yield_tuple('n', b'_key_string')
        self.assertEqual(editor._action_quit(), False)
        editor.get_char = yield_tuple('', b'_action_quit')
        self.assertEqual(editor._action_quit(), False)
        editor.get_char = yield_tuple('', b'_action_interrupt')
        self.assertEqual(editor._action_quit(), True)
        editor.get_char = yield_tuple('\x1b', b'_key_string')
        self.assertEqual(editor._action_quit(), True)
        def action_save(_):
            editor.unsaved_progress = False
        def char_gen(user_input: list):
            yield from zip(user_input, [b'_key_string'] * len(user_input))
        editor.get_char = char_gen([5, 'G', 'j'])
        with patch('cat_win.src.service.editor.Editor._action_save', action_save):
            self.assertEqual(editor._action_quit(), False)

    def test_editor_interrupt(self):
        editor = Editor(test_file_path_oneline, '')
        editor.debug_mode = True
        with self.assertRaises(KeyboardInterrupt):
            with patch('sys.stderr', new=StdOutMock()) as fake_out:
                editor._action_interrupt()
                self.assertEqual('Interrupting...\n', fake_out.getvalue())

    def test__action_resize(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_resize(), True)

    def test__get_color(self):
        editor = Editor('', '')
        mm.has_colors.return_value = False
        self.assertEqual(editor._get_color(0), 0)
        mm.has_colors.return_value = True
        mm.color_pair.return_value = 5
        self.assertEqual(editor._get_color(0), 5)

    def test__get_new_char(self):
        mm.keyname.return_value = b'^M'
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        editor.curse_window.get_wch.return_value = '\r'
        new_char = editor._get_new_char()
        self.assertEqual(next(new_char), ('\r', b'_key_enter'))
        new_char = editor._get_new_char()
        editor.debug_mode = True
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(next(new_char), ('\r', b'_key_enter'))
            self.assertIn('DEBUG', fake_out.getvalue())
            self.assertIn("b'_key_enter'", fake_out.getvalue())
            self.assertIn('13', fake_out.getvalue())
            self.assertIn("b'^M'", fake_out.getvalue())
            self.assertIn("'\\r'", fake_out.getvalue())

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 200] * 50))
    def test__enforce_boundaries(self):
        editor = Editor('', 'X' * 300)
        editor.cpos.set_pos((4, 205))
        self.assertEqual(editor._enforce_boundaries(), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 200))

        editor.cpos.set_pos((4, 0))
        editor.wpos.set_pos((6, 0))
        self.assertEqual(editor._enforce_boundaries(), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 0))
        self.assertEqual(editor.wpos.get_pos(), (4, 0))

        editor.cpos.set_pos((34, 0))
        editor.wpos.set_pos((0, 0))
        self.assertEqual(editor._enforce_boundaries(), None)
        self.assertEqual(editor.cpos.get_pos(), (34, 0))
        self.assertEqual(editor.wpos.get_pos(), (5, 0))

        editor.cpos.set_pos((7, 4))
        editor.wpos.set_pos((5, 6))
        self.assertEqual(editor._enforce_boundaries(), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 4))
        self.assertEqual(editor.wpos.get_pos(), (5, 4))

        editor.cpos.set_pos((7, 180))
        editor.wpos.set_pos((5, 0))
        self.assertEqual(editor._enforce_boundaries(), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 180))
        self.assertEqual(editor.wpos.get_pos(), (5, 61))

    # NOTE: DEBUG: this test has bad performance due to *many* magicmock calls
    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 200] * 50))
    def test__render_scr(self):
        editor = Editor('', 'X' * 300)
        editor.curse_window = MagicMock()
        editor.error_bar = ':)'
        editor.debug_mode = True
        editor.cpos.set_pos((4, 205))
        self.assertEqual(editor._render_scr(), None)
        editor.cpos.set_pos((34, 0))
        editor.wpos.set_pos((0, 0))
        self.assertEqual(editor._render_scr(), None)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__run(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        def yield_tuple(a, b):
            yield (a, b)
            while True:
                yield ('', b'_key_string')
        editor.get_char = yield_tuple('\x11', b'_action_quit')
        self.assertEqual(editor._run(), None)

    @patch('os.environ.setdefault', lambda *args: None)
    def test__open(self):
        editor = Editor('', '')
        editor.curse_window = MagicMock()
        with patch('cat_win.src.service.editor.Editor._run', lambda *args: None):
            self.assertEqual(editor._open(), None)

    @patch('cat_win.src.service.editor.CURSES_MODULE_ERROR', new=True)
    @patch('cat_win.src.service.editor.Editor.on_windows_os', new=True)
    def test_editor_no_curses_error(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(Editor.open('', '', True), False)
            self.assertIn('could not be loaded', fake_out.getvalue())
            self.assertIn('windows-curses', fake_out.getvalue())
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(Editor.open('', '', True), False)
            self.assertEqual('', fake_out.getvalue())

    def test_editor_set_indentation(self):
        backup_a = Editor.special_indentation
        backup_b = Editor.auto_indent
        Editor.set_indentation('  ', True)
        self.assertEqual(Editor.special_indentation, '  ')
        self.assertEqual(Editor.auto_indent, True)
        Editor.set_indentation(backup_a, backup_b)

    def test_editor_set_flags(self):
        backup_a = Editor.save_with_alt
        backup_b = Editor.on_windows_os
        backup_c = Editor.debug_mode
        backup_d = Editor.unicode_escaped_search
        backup_e = Editor.unicode_escaped_replace
        backup_f = Editor.file_encoding
        Editor.set_flags(True, True, True, False, False, 'utf-16')
        self.assertEqual(Editor.save_with_alt, True)
        self.assertEqual(Editor.on_windows_os, True)
        self.assertEqual(Editor.debug_mode, True)
        self.assertEqual(Editor.unicode_escaped_search, False)
        self.assertEqual(Editor.unicode_escaped_replace, False)
        self.assertEqual(Editor.file_encoding, 'utf-16')
        Editor.set_flags(backup_a, backup_b, backup_c, backup_d, backup_e, backup_f)
