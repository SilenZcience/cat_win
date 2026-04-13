from unittest.mock import patch, MagicMock
from unittest import TestCase
import os
import re
import runpy
import importlib

from cat_win.tests.mocks.edit import getxymax
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.std import IoHelperMock

from cat_win.src.curses import editor
if editor.CURSES_MODULE_ERROR:
    setattr(editor, 'curses', None)
from cat_win.src.curses.editor import Editor
from cat_win.src.persistence import viewstate

ORIGINAL_EDITOR_GETXYMAX = Editor.getxymax

mm = MagicMock()
mm.error = Exception
logger = LoggerStub()

test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')
test_file_path_editor = os.path.join(test_file_dir, 'test_editor.txt')


@patch.object(editor, 'logger', logger)
@patch('cat_win.src.curses.helper.fileselectionhelper.curses', mm)
@patch('cat_win.src.curses.editor.curses', mm)
@patch('cat_win.src.curses.editor.Editor.getxymax', getxymax)
@patch('cat_win.src.service.helper.iohelper.IoHelper.get_newline', lambda *_: '\n')
class TestEditor(TestCase):
    maxDiff = None

    def test_correct_save_and_load_viewstate(self):
        with open(__file__, 'r', encoding='utf-8') as f:
            self_content = f.read()
            if self_content.endswith('\n'):
                self_content += '\n'
        editor = Editor([(__file__, '')])
        self.assertListEqual(editor.window_content, self_content.splitlines()[:30])
        editor._build_file_upto(40)
        self.assertListEqual(editor.window_content, self_content.splitlines()[:40])
        saved_state = {}

        def fake_save_view_state(view_obj):
            saved_state.update({
                'view_type': type(view_obj).__name__,
                'view_module': type(view_obj).__module__,
                'state': viewstate._collect_state(view_obj),
            })
            return True

        def fake_load_view_state():
            view_module_name = saved_state['view_module']
            self.assertEqual(
                viewstate._SUPPORTED_VIEWS.get(saved_state['view_type']),
                view_module_name
            )
            view_module = importlib.import_module(view_module_name)
            view_type = getattr(view_module, saved_state['view_type'])
            restored = view_type.__new__(view_type)
            restored.__dict__.update(saved_state['state'])
            return restored

        with patch('cat_win.src.curses.editor.save_view_state', side_effect=fake_save_view_state), \
             patch('cat_win.src.persistence.viewstate.load_view_state', side_effect=fake_load_view_state), \
             patch('cat_win.src.curses.editor.on_windows_os', True):
            self.assertFalse(editor._action_background())
            restored_editor = viewstate.load_view_state()

        self.assertEqual(saved_state['view_type'], 'Editor')
        self.assertIsInstance(restored_editor, Editor)
        self.assertListEqual(restored_editor.window_content, self_content.splitlines())

        with patch('cat_win.src.curses.editor.Editor._run', lambda *args: None):
            restored_editor._open(fg = True)
        restored_editor._build_file()
        self.assertListEqual(restored_editor.window_content, self_content.splitlines())

    def test_editor_special_chars(self):
        editor = Editor([(test_file_path_oneline, '')])
        self.assertEqual(editor._get_special_char('\b'), '?')

        editor._set_special_chars({'\b': '!'})
        self.assertEqual(editor._get_special_char('\b'), '!')

    def test_editor_unknown_file(self):
        editor = Editor([('', '')])
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertListEqual(editor.window_content, [''])

    def test_selected_area(self):
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 30)
        editor._build_file()
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 50)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__build_file_upto(self):
        editor = Editor([('', '')])
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 30)
        editor._build_file_upto(40)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 40)
        editor.window_content[15] = '0'
        editor._build_file_upto(50)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 15 + ['0'] + ['a' * 10] * 34)
        editor._build_file_upto(60)
        self.assertSequenceEqual(editor.window_content, ['a' * 10] * 15 + ['0'] + ['a' * 10] * 34)

    def test_editor_key_enter(self):
        editor = Editor([(test_file_path_oneline, '')])
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 'test'])
        editor._move_key_right()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est'])
        editor._move_key_end()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est', ''])

    def test_editor_key_dc(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
        self.assertEqual(editor._move_key_left(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,0))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,5))

    def test_editor_move_key_right(self):
        editor = Editor([(test_file_path_editor, '')])
        editor.cpos.set_pos((1,6))
        self.assertEqual(editor._move_key_right(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((0,6))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,1))

    def test_editor_move_key_up(self):
        editor = Editor([(test_file_path_editor, '')])
        editor.cpos.set_pos((1,3))
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (0,3))
        self.assertEqual(editor._move_key_up(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,3))

    def test_editor_move_key_down(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        self.assertEqual(editor._move_key_down(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_left(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,6))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((11,4))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (1,4))

    def test_editor_move_key_ctl_down(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((-9, 3))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,3))

    def test_editor_select_key_left(self):
        editor = Editor([(test_file_path_editor, '')])
        self.assertEqual(editor._select_key_left(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,0))
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._select_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,5))

    def test_editor_select_key_right(self):
        editor = Editor([(test_file_path_editor, '')])
        editor.cpos.set_pos((1,6))
        self.assertEqual(editor._select_key_right(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((0,6))
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._select_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,1))

    def test_editor_select_key_up(self):
        editor = Editor([(test_file_path_editor, '')])
        editor.cpos.set_pos((1,3))
        editor._select_key_up()
        self.assertEqual(editor.cpos.get_pos(), (0,3))
        self.assertEqual(editor._select_key_up(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,3))

    def test_editor_select_key_down(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._select_key_down()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        self.assertEqual(editor._select_key_down(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_scroll_key_left(self):
        editor = Editor([(test_file_path_editor, '')])
        editor.wpos.set_pos((1,2))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,1))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))

    def test_editor_scroll_key_right(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
        editor.wpos.set_pos((2,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._scroll_key_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    def test_editor_scroll_key_down(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_move_key_ctl_end(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))

    def test_editor_select_key_end(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._select_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_scroll_key_end(self):
        editor = Editor([(test_file_path_editor, '')])
        for _ in range(61):
            editor._key_enter('')
        editor._key_string('!' * 150)
        editor._scroll_key_end()
        self.assertEqual(editor.wpos.get_pos(), (33, 37))

    def test_editor_move_key_home(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_home(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))

    def test_editor_select_key_home(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._select_key_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._select_key_home()
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_scroll_key_home(self):
        editor = Editor([(test_file_path_editor, '')])
        for _ in range(61):
            editor._key_enter('')
        editor._key_string('!' * 150)
        editor.wpos.set_pos((33, 37))
        editor._scroll_key_home()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    @patch('cat_win.src.curses.editor.Editor.special_indentation', ':)')
    def test_editor_indent_tab(self):
        editor = Editor([(test_file_path_editor, '')])
        editor._key_string('TEST')
        self.assertListEqual(editor.window_content, ['TESTline 1', 'line 2'])
        editor._move_key_ctl_right()
        self.assertEqual(editor._indent_tab('\t'), '\t')
        self.assertListEqual(editor.window_content, ['TESTline\t 1', 'line 2'])
        editor._move_key_home()
        self.assertEqual(editor._indent_tab('\t'), ':)')
        self.assertListEqual(editor.window_content, [':)TESTline\t 1', 'line 2'])

    @patch('cat_win.src.curses.editor.Editor.special_indentation', ':)')
    def test_editor_indent_tab_select(self):
        editor = Editor([(test_file_path_editor, '')])
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

    @patch('cat_win.src.curses.editor.Editor.special_indentation', ':)')
    def test_editor_indent_btab(self):
        editor = Editor([(test_file_path_editor, '')])
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

    @patch('cat_win.src.curses.editor.Editor.special_indentation', ':)')
    def test_editor_indent_btab_select(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([(test_file_path, '')])
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
        editor = Editor([(test_file_path, '')])
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
        editor = Editor([('', '')])
        editor.debug_mode = True
        logger.clear()
        with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            editor._key_string('\ud83d\ude01')
            self.assertIn('Changed', fake_out.output())
            self.assertIn('😁', fake_out.output())
            self.assertIn('128513', fake_out.output())
        logger.clear()
        with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            editor._key_string('\x1bTEST:)!')
            self.assertEqual(fake_out.output(), '')

    @patch('cat_win.src.curses.editor.Editor.special_indentation', '!!!')
    def test_editor_key_string(self):
        editor = Editor([(test_file_path_editor, '')])
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
        editor = Editor([('', '')])
        editor.spos.set_pos((1,1))
        editor._select_key_all()
        self.assertEqual(editor.spos.get_pos(), (0, 0))
        self.assertEqual(editor.cpos.get_pos(), (3, 3))

    @patch('cat_win.src.curses.editor.Editor.auto_indent', True)
    @patch('cat_win.src.curses.editor.Editor.special_indentation', '$')
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
        mm.error = KeyboardInterrupt
        for get_wch_, result_ in zip(g, r):
            char_gen_get_wch = char_gen(get_wch_)
            def _get_wch():
                return next(char_gen_get_wch)

            editor = Editor([('', '')])
            # editor.debug_mode = True

            curse_window_mock = MagicMock()
            curse_window_mock.get_wch = _get_wch

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
        editor = Editor([('', '')])
        editor.selecting = True
        editor._select_key_all()
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_copy()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 4))
    def test__action_cut(self):
        def assertCopy(_s: str):
            self.assertEqual(_s, '\n'.join(['@@', '@@@', '@@@', '@@']))
        editor = Editor([('', '')])
        editor.selecting = True
        editor.cpos.set_pos((0, 1))
        editor.spos.set_pos((3, 2))
        with patch('cat_win.src.service.clipboard.Clipboard.put', assertCopy):
            editor._action_cut()
        self.assertListEqual(editor.window_content, ['@@'])

    def test__action_render_scr(self):
        editor = Editor([('', '')])
        editor.curse_window = MagicMock()
        self.assertNotEqual(editor.error_bar, '')
        self.assertEqual(editor._action_render_scr(''), None)

    def test_editor_action_save(self):
        editor = Editor([(test_file_path, '')])
        editor.debug_mode = True
        error_def = ErrorDefGen.get_def(OSError('TestError'))
        logger.clear()
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', new=error_def), patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            self.assertEqual(editor._action_save(), True)
            self.assertEqual(editor.error_bar, 'TestError')
            self.assertEqual('TestError\n', fake_out.output())

        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', new=lambda *_: None):
            self.assertEqual(editor._action_save(), True)
            self.assertEqual(editor.error_bar, '')

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['@@@'] * 501))
    def test_editor_action_save_correctness(self):
        def assertWriteFile(_, _s: str):
            self.assertEqual(_s, (b'@@@\n@!\n'+b'\n'*99+b'@@\n'+b'@@@\n'*498+b'@@@'))
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
        self.assertEqual(editor.window_content, ['a' * 10] * 30)
        editor.window_content[29] = 'TEST'
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', assertWriteFile):
            editor._action_save()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 50))
    def test__action_jump(self):
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
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
        editor = Editor([('', '')])
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
        editor = Editor([(test_file_path, '')])
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
        with patch('cat_win.src.curses.editor.Editor._action_save', action_save):
            self.assertEqual(editor._action_quit(), False)

    def test_editor_interrupt(self):
        editor = Editor([(test_file_path_oneline, '')])
        editor.debug_mode = True
        logger.clear()
        with self.assertRaises(KeyboardInterrupt):
            with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
                editor._action_interrupt()
        self.assertEqual('Interrupting...\n', fake_out.output())

    def test__action_resize(self):
        editor = Editor([('', '')])
        editor.curse_window = MagicMock()
        self.assertEqual(editor._action_resize(), True)

    def test__get_color(self):
        editor = Editor([('', '')])
        mm.has_colors.return_value = False
        self.assertEqual(editor._get_color(0), 0)
        mm.has_colors.return_value = True
        mm.color_pair.return_value = 5
        self.assertEqual(editor._get_color(0), 5)

    def test__get_new_char(self):
        mm.keyname.return_value = b'^M'
        editor = Editor([('', '')])
        editor.curse_window = MagicMock()
        editor.curse_window.get_wch.return_value = '\r'
        new_char = editor._get_new_char()
        self.assertEqual(next(new_char), ('\r', b'_key_enter'))
        new_char = editor._get_new_char()
        editor.debug_mode = True
        logger.clear()
        with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            self.assertEqual(next(new_char), ('\r', b'_key_enter'))
            self.assertIn('DEBUG', fake_out.output())
            self.assertIn("b'_key_enter'", fake_out.output())
            self.assertIn('13', fake_out.output())
            self.assertIn("b'^M'", fake_out.output())
            self.assertIn("'\\r'", fake_out.output())

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 200] * 50))
    def test__enforce_boundaries(self):
        editor = Editor([('', 'X' * 300)])
        editor.cpos.set_pos((4, 205))
        self.assertEqual(editor._enforce_boundaries(b''), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 200))

        editor.cpos.set_pos((4, 0))
        editor.wpos.set_pos((6, 0))
        self.assertEqual(editor._enforce_boundaries(b''), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 0))
        self.assertEqual(editor.wpos.get_pos(), (4, 0))

        editor.cpos.set_pos((34, 0))
        editor.wpos.set_pos((0, 0))
        self.assertEqual(editor._enforce_boundaries(b''), None)
        self.assertEqual(editor.cpos.get_pos(), (34, 0))
        self.assertEqual(editor.wpos.get_pos(), (5, 0))

        editor.cpos.set_pos((7, 4))
        editor.wpos.set_pos((5, 6))
        self.assertEqual(editor._enforce_boundaries(b''), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 4))
        self.assertEqual(editor.wpos.get_pos(), (5, 4))

        editor.cpos.set_pos((7, 180))
        editor.wpos.set_pos((5, 0))
        self.assertEqual(editor._enforce_boundaries(b''), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 180))
        self.assertEqual(editor.wpos.get_pos(), (5, 61))

    # NOTE: DEBUG: this test has bad performance due to *many* magicmock calls
    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 200] * 50))
    def test__render_scr(self):
        editor = Editor([('', 'X' * 300)])
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
        editor = Editor([('', '')])
        editor.curse_window = MagicMock()
        def yield_tuple(a, b):
            yield (a, b)
            while True:
                yield ('', b'_key_string')
        editor.get_char = yield_tuple('\x11', b'_action_quit')
        self.assertEqual(editor._run(), None)

    @patch('os.environ.setdefault', lambda *args: None)
    def test__open(self):
        editor = Editor([('', '')])
        editor.curse_window = MagicMock()
        with patch('cat_win.src.curses.editor.Editor._run', lambda *args: None):
            self.assertEqual(editor._open(), None)

    @patch('cat_win.src.curses.editor.CURSES_MODULE_ERROR', new=True)
    @patch('cat_win.src.curses.editor.on_windows_os', new=True)
    def test_editor_no_curses_error(self):
        logger.clear()
        with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            self.assertEqual(Editor.open([('', '')], True), False)
            self.assertIn('could not be loaded', fake_out.output())
            self.assertIn('windows-curses', fake_out.output())
        logger.clear()
        with patch('cat_win.src.curses.editor.logger', logger) as fake_out:
            self.assertEqual(Editor.open([('', '')], True), False)
            self.assertEqual('', fake_out.output())

    def test_editor_set_indentation(self):
        backup_a = Editor.special_indentation
        backup_b = Editor.auto_indent
        Editor.set_indentation('  ', True)
        self.assertEqual(Editor.special_indentation, '  ')
        self.assertEqual(Editor.auto_indent, True)
        Editor.set_indentation(backup_a, backup_b)

    def test_editor_set_flags(self):
        backup_a = Editor.save_with_alt
        backup_b = Editor.debug_mode
        backup_c = Editor.unicode_escaped_search
        backup_d = Editor.unicode_escaped_replace
        backup_e = Editor.file_encoding
        Editor.set_flags(True, True, False, False, 'utf-16')
        self.assertEqual(Editor.save_with_alt, True)
        self.assertEqual(Editor.debug_mode, True)
        self.assertEqual(Editor.unicode_escaped_search, False)
        self.assertEqual(Editor.unicode_escaped_replace, False)
        self.assertEqual(Editor.file_encoding, 'utf-16')
        Editor.set_flags(backup_a, backup_b, backup_c, backup_d, backup_e)

    def test_editor_import_error_path(self):
        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'curses':
                raise ImportError('forced')
            return real_import(name, globals, locals, fromlist, level)

        with patch('builtins.__import__', side_effect=fake_import):
            ns = runpy.run_path(editor.__file__, run_name='__cov_editor_importerror__')
        self.assertTrue(ns['CURSES_MODULE_ERROR'])

    def test_action_file_selection_and_help_highlighter_paths(self):
        ed = Editor([(test_file_path_editor, 'A')])
        ed.files = [(test_file_path_editor, 'A'), (test_file_path_editor, 'B')]
        ed.file = test_file_path_editor
        ed.display_name = 'A'
        ed.curse_window = MagicMock()

        ed.get_char = iter([
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertFalse(ed._action_file_selection())
        self.assertEqual(ed.open_next_idx, 1)

        ed2 = Editor([(test_file_path_editor, 'A')])
        ed2.files = [(test_file_path_editor, 'A'), (test_file_path_editor, 'B')]
        ed2.file = test_file_path_editor
        ed2.display_name = 'A'
        ed2.curse_window = MagicMock()
        commit = {'hash': 'abc1234', 'date': '2024-01-01', 'author': 'u', 'message': 'm'}
        ed2.get_char = iter([
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
            ('', b'_action_quit'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=[commit]):
            self.assertTrue(ed2._action_file_selection())

        ed3 = Editor([(test_file_path_editor, 'A')])
        ed3.curse_window = MagicMock()
        mm_error_backup = mm.error
        mm.error = Exception
        calls = {'n': 0}

        def addstr_once_error(*_args, **_kwargs):
            if calls['n'] == 0:
                calls['n'] += 1
                raise Exception('boom')
            return None

        ed3.curse_window.addstr.side_effect = addstr_once_error
        ed3.get_char = iter([('x', b'_key_string')])
        try:
            ed3._function_help()

            ed3.search = ''
            self.assertIsNone(ed3._function_search())
            self.assertIsNone(ed3._function_search_r())
            self.assertIsNone(ed3._function_replace())
            self.assertIsNone(ed3._function_replace_r())
            ed3.search = 'abc'
            with patch.object(ed3, '_action_find') as af, patch.object(ed3, '_action_replace') as ar:
                ed3._function_search()
                ed3._function_search_r()
                ed3._function_replace()
                ed3._function_replace_r()
            self.assertEqual(af.call_count, 2)
            self.assertEqual(ar.call_count, 2)
        finally:
            mm.error = mm_error_backup

        ed4 = Editor([(test_file_path_editor, 'A')])
        ed4.curse_window = MagicMock()
        ed4.get_char = iter([('', b'_key_enter')])
        plugin = MagicMock()
        plugin.token_color_map = {}
        with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=({'None': None, 'Py': 'py-plugin'}, {'None': '', 'Py': '.py'})):
            with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_plugin', return_value=plugin):
                ed4._function_sel_highlight()
        self.assertEqual(ed4._syntax_highlighter, plugin)

    def test_open_and_open_classmethod_extra_branches(self):
        ed = Editor([(test_file_path_editor, 'A')])
        ed.curse_window = MagicMock()
        ed.unsaved_progress = True
        ed._f_content_gen = MagicMock()
        ed._f_content_gen.close.side_effect = StopIteration()

        with patch.object(ed, '_init_screen', lambda *_: None):
            with patch.object(ed, '_init_highlighter_colors', lambda *_: None):
                with patch.object(ed, '_build_file_upto', lambda *_: None):
                    with patch.object(ed, '_run', side_effect=RuntimeError('boom')):
                        with patch('builtins.input', return_value='N'):
                            with patch('cat_win.src.curses.editor.curses.endwin'):
                                with self.assertRaises(RuntimeError):
                                    ed._open()

        ed2 = Editor([(test_file_path_editor, 'A')])
        ed2.curse_window = MagicMock()
        ed2.unsaved_progress = True
        ed2._f_content_gen = MagicMock()
        ed2._f_content_gen.close.side_effect = StopIteration()

        def fake_save():
            ed2.unsaved_progress = False
            return True

        with patch.object(ed2, '_init_screen', lambda *_: None):
            with patch.object(ed2, '_init_highlighter_colors', lambda *_: None):
                with patch.object(ed2, '_build_file_upto', lambda *_: None):
                    with patch.object(ed2, '_run', side_effect=RuntimeError('boom2')):
                        with patch.object(ed2, '_action_save', fake_save):
                            with patch('builtins.input', return_value='Y'):
                                with patch('cat_win.src.curses.editor.curses.endwin'):
                                    with self.assertRaises(RuntimeError):
                                        ed2._open()

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

        with patch('cat_win.src.curses.editor.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.editor.on_windows_os', True):
                with patch.object(Editor, '__init__', fake_init):
                    with patch.object(Editor, '_open', lambda *_, **__: None):
                        Editor.loading_failed = False
                        self.assertTrue(Editor.open([('a', 'A'), ('b', 'B')], False))

        self.assertGreaterEqual(len(created), 2)
        self.assertTrue(callable(getattr(created[0], '_action_background', None)))
        self.assertTrue(callable(getattr(created[1], '_action_background', None)))

        def fake_init_skip(self, files, file_idx=0, file_commit_hash=None):
            self.files = files
            self.file = files[file_idx][0] if files else ''
            self.display_name = files[file_idx][1] if files else ''
            self.error_bar = 'binary'
            self.open_next_idx = None
            self.open_next_hash = None
            self.changes_made = False

        with patch('cat_win.src.curses.editor.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.editor.on_windows_os', True):
                with patch.object(Editor, '__init__', fake_init_skip):
                    Editor.loading_failed = False
                    self.assertFalse(Editor.open([('a', 'A')], True))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 10] * 60))
    def test_jump_find_and_selection_navigation_extra_branches(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()

        ed.get_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_jump'),
        ])
        with patch.object(ed, '_get_clipboard', return_value='7'):
            self.assertTrue(ed._action_jump())
        self.assertEqual(ed.cpos.row, 6)

        ed.get_char = iter([
            ('', b'_action_resize'),
            ('', b'_action_insert'),
            ('', b'_action_paste'),
            ('', b'_action_find'),
            ('', b'_action_quit'),
        ])
        with patch.object(ed, '_render_scr') as render_scr:
            with patch.object(ed, '_get_clipboard', return_value='abc'):
                with patch('cat_win.src.curses.editor.search_iter_factory', side_effect=ValueError('bad search: ')):
                    self.assertTrue(ed._action_find())
        self.assertTrue(render_scr.called)

        ed2 = Editor([(test_file_path_editor, 'A')])
        ed2.curse_window = MagicMock()
        ed2.files = [
            (test_file_path_editor, f'File_{i}_' + 'X' * 90)
            for i in range(15)
        ]
        ed2.file = test_file_path_editor
        ed2.display_name = ed2.files[0][1]
        ed2.get_char = iter([
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_ctl_up'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_key_enter'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertTrue(ed2._action_file_selection())

    def test_syntax_selection_navigation_and_init_highlighter_colors_extra_branches(self):
        ed = Editor([(test_file_path_editor, 'A')])
        ed.curse_window = MagicMock()

        plugin = MagicMock()
        plugin.token_color_map = {}
        available = {
            'None': None,
            'PythonLongName': 'py-plugin',
            'JavaScriptLongName': 'js-plugin',
        }
        extensions = {'None': '', 'PythonLongName': '.py', 'JavaScriptLongName': '.js'}

        ed.get_char = iter([
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_ctl_up'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_function_sel_highlight'),
        ])
        with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=(available, extensions)):
            with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_plugin', return_value=plugin):
                ed._function_sel_highlight()
        self.assertEqual(ed._syntax_highlighter, plugin)

        class DummyCurses:
            COLOR_CYAN = 6
            COLOR_GREEN = 2
            COLOR_RED = 1
            COLOR_BLACK = 0
            COLOR_BLUE = 4

            def __init__(self):
                self.pairs = []

            @staticmethod
            def can_change_color():
                return True

            def init_pair(self, pair_id, fg, bg):
                self.pairs.append((pair_id, fg, bg))

        dummy = DummyCurses()
        backup_color_ids = dict(ed._SYNTAX_COLOR_IDS)
        try:
            ed._syntax_highlighter = MagicMock()
            ed._syntax_highlighter.token_color_map = {
                'custom_light_red': 'lightred',
                'custom_blue': 'blue',
                'custom_unknown': 'notacolor',
            }
            with patch('cat_win.src.curses.editor.curses', dummy):
                ed._init_highlighter_colors()
            self.assertIn('custom_light_red', ed._SYNTAX_COLOR_IDS)
            self.assertIn('custom_blue', ed._SYNTAX_COLOR_IDS)
            self.assertGreaterEqual(len(dummy.pairs), 7)
        finally:
            ed._SYNTAX_COLOR_IDS = backup_color_ids

    def test_selected_text_setup_file_and_syntax_cache_extra_branches(self):
        ed = Editor([('', '')])
        ed.window_content = ['abc', 'def']
        ed.cpos.set_pos((0, 1))
        ed.selecting = False
        self.assertEqual(ed.selected_text, ['b'])

        ed.selecting = True
        ed.spos.set_pos((0, 1))
        ed.cpos.set_pos((1, 2))
        self.assertEqual(ed.selected_text, ['bc', 'de'])

        with patch('cat_win.src.curses.editor.GitHelper.get_git_file_content_at_commit', return_value=['git-line']):
            ed_git = Editor([(test_file_path_editor, 'A')], file_commit_hash='deadbeef')
        self.assertEqual(ed_git.window_content, ['git-line'])
        self.assertTrue(ed_git.unsaved_progress)
        self.assertTrue(ed_git.display_name.startswith('GIT: '))

        with patch('cat_win.src.curses.editor.IoHelper.get_newline', side_effect=UnicodeError('bad-encoding')):
            ed_err = Editor([(test_file_path_editor, 'A')])
        self.assertEqual(ed_err.status_bar_size, 2)
        self.assertIn('bad-encoding', ed_err.error_bar)
        self.assertEqual(ed_err.window_content, [''])

        ed_cache = Editor([('', '')])
        ed_cache.window_content = ['one', 'two', 'three']

        class DummyHighlighter:
            def __init__(self):
                self.calls = []

            def tokenize_line(self, line, state):
                self.calls.append((line, state))
                return ([(0, len(line), 'kw')], f'state-{line}')

        hl = DummyHighlighter()
        ed_cache._syntax_highlighter = hl
        ed_cache._syntax_cache = {
            0: ('one', None, 's0', []),
            1: ('two', 's0', 's1', []),
        }
        ed_cache._get_syntax_tokens(2, 3)
        self.assertEqual(hl.calls, [('three', 's1')])

        ed_cache._syntax_cache[2] = ('three', 's1', 'state-three', [(0, 5, 'kw')])
        ed_cache._get_syntax_tokens(2, 3)
        self.assertEqual(len(hl.calls), 1)

    def test_action_transform_extra_branches(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.window_content = ['ab cd']
        ed.cpos.set_pos((0, 1))
        ed.spos.set_pos((0, 0))

        ed.get_char = iter([
            ('i', b'_key_string'),
            ('s', b'_key_string'),
            ('a', b'_key_string'),
            ('l', b'_key_string'),
            ('n', b'_key_string'),
            ('u', b'_key_string'),
            ('m', b'_key_string'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        self.assertTrue(ed._action_transform())

        ed2 = Editor([('', '')])
        ed2.curse_window = MagicMock()
        ed2.window_content = ['ab cd']
        ed2.cpos.set_pos((0, 1))
        ed2.spos.set_pos((0, 0))
        ed2.get_char = iter([
            ('u', b'_key_string'),
            ('p', b'_key_string'),
            ('p', b'_key_string'),
            ('e', b'_key_string'),
            ('r', b'_key_string'),
            ('', b'_key_enter'),
        ])
        self.assertTrue(ed2._action_transform())
        self.assertEqual(ed2.window_content[0], 'aB cd')

        ed3 = Editor([('', '')])
        ed3.curse_window = MagicMock()
        ed3.window_content = ['ab']
        ed3.cpos.set_pos((0, 1))
        ed3.spos.set_pos((0, 0))
        def _gen_transform_events():
            events = [
                ('', b'_action_insert'),
                ('a', b'_key_string'),
                ('', b'_key_enter'),
                ('\\', b'_key_string'),
                ('x', b'_key_string'),
                ('4', b'_key_string'),
                ('1', b'_key_string'),
                ('', b'_key_enter'),
                ('', b'_action_find'),
                ('', b'_action_transform'),
            ]
            yield from events
            while True:
                yield ('\x1b', b'_key_string')

        ed3.get_char = _gen_transform_events()
        with patch.object(ed3, '_get_clipboard', return_value='exit'):
            with patch.object(ed3, '_render_scr'):
                self.assertTrue(ed3._action_transform())

        ed4 = Editor([('', '')])
        ed4.curse_window = MagicMock()
        ed4.window_content = ['ab']
        ed4.cpos.set_pos((0, 1))
        ed4.spos.set_pos((0, 0))
        ed4.get_char = iter([
            ('l', b'_key_string'),
            ('a', b'_key_string'),
            ('m', b'_key_string'),
            ('b', b'_key_string'),
            ('d', b'_key_string'),
            ('a', b'_key_string'),
            (' ', b'_key_string'),
            ('x', b'_key_string'),
            (':', b'_key_string'),
            (' ', b'_key_string'),
            ('x', b'_key_string'),
            ('.', b'_key_string'),
            ('u', b'_key_string'),
            ('p', b'_key_string'),
            ('p', b'_key_string'),
            ('e', b'_key_string'),
            ('r', b'_key_string'),
            ('(', b'_key_string'),
            (')', b'_key_string'),
            ('', b'_key_enter'),
        ])
        self.assertTrue(ed4._action_transform())
        self.assertEqual(ed4.window_content[0], 'aB')

        ed5 = Editor([('', '')])
        ed5.curse_window = MagicMock()
        ed5.window_content = ['ab']
        ed5.cpos.set_pos((0, 1))
        ed5.spos.set_pos((0, 0))
        ed5.get_char = iter([
            ('l', b'_key_string'),
            ('a', b'_key_string'),
            ('m', b'_key_string'),
            ('b', b'_key_string'),
            ('d', b'_key_string'),
            ('a', b'_key_string'),
            (' ', b'_key_string'),
            ('x', b'_key_string'),
            (':', b'_key_string'),
            (' ', b'_key_string'),
            ('1', b'_key_string'),
            ('/', b'_key_string'),
            ('0', b'_key_string'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        self.assertTrue(ed5._action_transform())

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['abcde'] * 20))
    def test_render_search_focus_span_clipping_extra_branch(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.cpos.set_pos((0, 2))
        ed.wpos.set_pos((0, 1))
        ed.search_items = {(0, 2): 3}
        ed.search_items_focused_span = [((0, 0), 4)]

        ed._render_scr()

        self.assertEqual(ed.search_items, {})
        self.assertEqual(ed.search_items_focused_span, [])
        self.assertGreaterEqual(ed.curse_window.chgat.call_count, 2)

    def test_editor_lowlevel_mouse_and_move_selection_branches_3(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()

        class DummyHighlighter:
            def tokenize_line(self, line, state):
                return ([(0, len(line), 'kw')], state)

        ed.window_content = ['ab', 'cd']
        ed._syntax_highlighter = DummyHighlighter()
        ed._syntax_cache = {
            0: ('xx', None, 's0', []),
            1: ('yy', 's0', 's1', []),
        }
        ed._get_syntax_tokens(1, 2)

        with patch('cat_win.src.service.clipboard.Clipboard.get', return_value=None):
            self.assertIsNone(ed._get_clipboard())
        self.assertIn('clipboard', ed.error_bar.lower())

        mm.BUTTON1_CLICKED = 1
        mm.BUTTON1_PRESSED = 2
        mm.BUTTON1_RELEASED = 4
        mm.BUTTON4_PRESSED = 8
        mm.BUTTON5_PRESSED = 16

        with patch('cat_win.src.curses.editor.curses.getmouse', return_value=(0, 1, 0, 0, mm.BUTTON1_CLICKED)):
            ed._move_key_mouse()
        with patch('cat_win.src.curses.editor.curses.getmouse', return_value=(0, 1, 0, 0, mm.BUTTON1_PRESSED)):
            ed._move_key_mouse()
        with patch('cat_win.src.curses.editor.curses.getmouse', return_value=(0, 1, 0, 0, mm.BUTTON1_RELEASED)):
            ed._move_key_mouse()
        with patch('cat_win.src.curses.editor.curses.getmouse', return_value=(0, 1, 0, 0, mm.BUTTON4_PRESSED)):
            ed._move_key_mouse()
        with patch('cat_win.src.curses.editor.curses.getmouse', return_value=(0, 1, 0, 0, mm.BUTTON5_PRESSED)):
            ed._move_key_mouse()

        ed.window_content = ['ab', 'cd', 'efghij']
        ed.selecting = True
        ed.spos.set_pos((0, 0))
        ed.cpos.set_pos((1, 1))
        ed._move_key_left()
        ed._move_key_right()
        ed._move_key_up()
        ed._move_key_down()
        ed._move_key_ctl_left()
        ed._move_key_ctl_right()
        ed._move_key_ctl_up()
        ed._move_key_ctl_down()
        ed._move_key_page_up()
        ed._move_key_page_down()

    def test_editor_chunk_and_render_action_branches_3(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.window_content = ['abc']
        ed.cpos.set_pos((0, 1))

        class DummySearch:
            s_len = 1
            replace = 'Z'

        ed._replace_search(None, '', DummySearch())
        ed._replace_search('', '', DummySearch())

        ed2 = Editor([('', '')])
        ed2.window_content = ['xy']
        ed2.cpos.set_pos((0, 1))
        ed2._add_chunk('A\r\nB')
        self.assertEqual(ed2.window_content, ['xA', 'By'])

        ed3 = Editor([('', '')])
        ed3.curse_window = MagicMock()
        ed3.selecting = False
        self.assertTrue(ed3._action_copy())

        ed3.selecting = True
        ed3.spos.set_pos((0, 0))
        ed3.cpos.set_pos((0, 0))
        with patch('cat_win.src.service.clipboard.Clipboard.put', return_value=False):
            self.assertTrue(ed3._action_copy())
        self.assertIn('copying', ed3.error_bar)

        with patch.object(ed3, '_get_clipboard', return_value=None):
            self.assertTrue(ed3._action_paste())

        ed3.selecting = True
        with patch.object(ed3, '_get_clipboard', return_value='Q'):
            with patch.object(ed3, '_remove_chunk') as rm:
                with patch.object(ed3, '_add_chunk') as add:
                    self.assertTrue(ed3._action_paste())
        self.assertTrue(rm.called)
        self.assertTrue(add.called)

        ed3.curse_window.addstr.side_effect = mm.error
        self.assertIsNone(ed3._action_render_scr('msg', 'err'))

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['abc'] * 40))
    def test_editor_action_heavy_remaining_branches_3(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.get_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_key_backspace'),
            ('', b'_key_ctl_backspace'),
            ('Y', b'_key_string'),
        ])
        with patch.object(ed, '_get_clipboard', return_value='12a'):
            with patch.object(ed, '_action_background', return_value=True):
                with patch.object(ed, '_render_scr') as rs:
                    self.assertTrue(ed._action_jump())
        self.assertTrue(rs.called)

        edf = Editor([('', '')])
        edf.curse_window = MagicMock()
        edf.search = 'x'
        with patch('cat_win.src.curses.editor.search_iter_factory', side_effect=ValueError('bad')):
            self.assertTrue(edf._action_find(1))

        edf2 = Editor([('', '')])
        edf2.curse_window = MagicMock()
        edf2.search = 'x'
        edf2.get_char = iter([
            ('', b'_action_insert'),
            ('[', b'_key_string'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        with patch('cat_win.src.curses.editor.compile_re', side_effect=re.error('regex')):
            self.assertTrue(edf2._action_find())

        edr = Editor([('', '')])
        edr.curse_window = MagicMock()
        edr.search = ''
        edr.get_char = iter([('', b'_key_enter'), ('\x1b', b'_key_string')])
        self.assertTrue(edr._action_replace())

        edr2 = Editor([('', '')])
        edr2.curse_window = MagicMock()
        edr2.get_char = iter([
            ('', b'_action_reload'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_quit'),
        ])
        with patch.object(edr2, '_action_background', return_value=True):
            with patch.object(edr2, '_render_scr') as rs2:
                self.assertTrue(edr2._action_reload())
        self.assertIsNotNone(rs2)

        edi = Editor([('', '')])
        edi.curse_window = MagicMock()
        edi.get_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_insert'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('G', b'_key_string'),
            ('', b'_key_backspace'),
            ('', b'_key_ctl_backspace'),
            ('4', b'_key_string'),
            ('1', b'_key_string'),
            ('', b'_key_enter'),
        ])
        with patch.object(edi, '_get_clipboard', return_value='4Z1'):
            with patch.object(edi, '_action_background', return_value=True):
                with patch.object(edi, '_render_scr') as rs3:
                    self.assertTrue(edi._action_insert())
        self.assertIsNotNone(rs3)

        edq = Editor([('', '')])
        edq.curse_window = MagicMock()
        edq.unsaved_progress = True
        edq.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_save'),
            ('', b'_action_resize'),
            ('N', b'_key_string'),
        ])
        with patch.object(edq, '_action_background', return_value=True):
            with patch.object(edq, '_action_save', return_value=True):
                with patch.object(edq, '_render_scr') as rs4:
                    self.assertFalse(edq._action_quit())
        self.assertTrue(rs4.called)

        edfs = Editor([(test_file_path_editor, 'A')])
        edfs.curse_window = MagicMock()
        edfs.files = [(test_file_path_editor, 'A')] + [(test_file_path_editor, f'N{i}' + 'X' * 50) for i in range(8)]
        edfs.file = test_file_path_editor
        edfs.display_name = 'missing'
        edfs.file_commit_hash = {'hash': 'abc'}
        edfs.get_char = iter([
            ('', b'_action_file_selection'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_key_enter'),
        ])
        call_no = {'n': 0}
        def addstr_side(*_args, **_kwargs):
            call_no['n'] += 1
            if call_no['n'] in (1, 4):
                raise mm.error
            return None
        edfs.curse_window.addstr.side_effect = addstr_side
        with patch.object(edfs, '_action_background', return_value=True):
            with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=OSError('nogit')):
                self.assertTrue(edfs._action_file_selection())

        mm.resize_term.side_effect = mm.error
        try:
            self.assertTrue(edfs._action_resize())
        finally:
            mm.resize_term.side_effect = None

    def test_editor_ui_runtime_and_open_unix_branches_3(self):
        ed = Editor([(test_file_path_editor, 'A')])
        ed.curse_window = MagicMock()
        plugin = MagicMock()
        ed._syntax_highlighter = plugin
        ed.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_function_sel_highlight'),
        ])
        with patch.object(ed, '_action_background', return_value=True):
            with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=({'None': None, 'Py': plugin}, {'None': '', 'Py': '.py'})):
                with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_plugin', return_value=plugin):
                    ed._function_sel_highlight()

        ed2 = Editor([('', '')])
        ed2.curse_window = MagicMock()
        seq = iter(['a'])
        def get_wch_side():
            try:
                return next(seq)
            except StopIteration:
                raise mm.error
        ed2.curse_window.get_wch.side_effect = get_wch_side
        gen = ed2._get_new_char()
        self.assertEqual(next(gen)[0], 'a')

        ed3 = Editor([('', '')])
        ed3.curse_window = MagicMock()
        ed3.window_content = ['\t\x01  ']
        ed3.selecting = True
        ed3.spos.set_pos((0, 0))
        ed3.cpos.set_pos((0, 1))
        ed3.search_items = {(0, 0): 2, (0, 5): 1}
        ed3.search_items_focused_span = [((0, 0), 2)]
        ed3._syntax_highlighter = MagicMock()
        ed3._syntax_cache = {0: ('\t\x01  ', None, None, [(0, 1, 'unknown')])}
        ed3._render_scr()

        ed4 = Editor([('', '')])
        ed4.curse_window = MagicMock()
        ed4.unsaved_progress = False
        ed4._f_content_gen = MagicMock()
        ed4._f_content_gen.close.side_effect = StopIteration()
        with patch.object(ed4, '_init_screen', lambda *_: None):
            with patch.object(ed4, '_init_highlighter_colors', lambda *_: None):
                with patch.object(ed4, '_build_file_upto', lambda *_: None):
                    with patch.object(ed4, '_run', side_effect=RuntimeError('boom')):
                        with patch('cat_win.src.curses.editor.curses.endwin'):
                            with self.assertRaises(RuntimeError):
                                ed4._open()

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['abc'] * 20))
    def test_editor_transform_find_replace_remaining_branches_4(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.window_content = ['abc']
        ed.cpos.set_pos((0, 1))
        ed.spos.set_pos((0, 1))
        ed.get_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            (5, b'_key_string'),
            ('', b'_key_ctl_backspace'),
            ('', b'_key_backspace'),
            ('u', b'_key_string'),
            ('p', b'_key_string'),
            ('p', b'_key_string'),
            ('e', b'_key_string'),
            ('r', b'_key_string'),
            ('', b'_key_enter'),
            ('l', b'_key_string'),
            ('a', b'_key_string'),
            ('m', b'_key_string'),
            ('b', b'_key_string'),
            ('d', b'_key_string'),
            ('a', b'_key_string'),
            (' ', b'_key_string'),
            ('x', b'_key_string'),
            (':', b'_key_string'),
            (' ', b'_key_string'),
            ('1', b'_key_string'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        with patch.object(ed, '_get_clipboard', return_value='exit'):
            with patch.object(ed, '_action_background', return_value=True):
                with patch.object(ed, '_render_scr'):
                    self.assertTrue(ed._action_transform())

        class DummySearch:
            def __init__(self, vals, s_len=2, s_rows=None):
                self._it = iter(vals)
                self.s_len = s_len
                self.s_rows = s_rows or [((0, 0), 1)]

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._it)

        edf = Editor([('', '')])
        edf.curse_window = MagicMock()
        edf.window_content = ['abc', 'def']
        edf.selecting = True
        edf.spos.set_pos((0, 0))
        edf.cpos.set_pos((1, 0))
        edf.search = 'a'
        edf.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_insert'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        with patch.object(edf, '_action_background', return_value=True):
            with patch.object(edf, '_render_scr'):
                with patch('cat_win.src.curses.editor.search_iter_factory',
                           side_effect=[DummySearch([(0, 0)]), DummySearch([(999, 0)])]):
                    self.assertTrue(edf._action_find())

        edf2 = Editor([('', '')])
        edf2.curse_window = MagicMock()
        edf2.search = ''
        edf2.get_char = iter([('', b'_key_enter')])
        self.assertTrue(edf2._action_find())

        edf3 = Editor([('', '')])
        edf3.curse_window = MagicMock()
        edf3.selecting = True
        edf3.spos.set_pos((0, 0))
        edf3.cpos.set_pos((0, 1))
        edf3.search = 'x'
        edf3.get_char = iter([('', b'_key_enter'), ('\x1b', b'_key_string')])
        with patch('cat_win.src.curses.editor.search_iter_factory', side_effect=StopIteration()):
            self.assertTrue(edf3._action_find(-1))

        class DummyReplaceSearch:
            def __init__(self):
                self.r_len = 1
                self.yielded_result = False

            def __iter__(self):
                self.yielded_result = False
                return iter([])

        edr = Editor([('', '')])
        edr.curse_window = MagicMock()
        edr.search = re.compile('x')
        edr.get_char = iter([
            ('', b'_action_paste'),
            ('', b'_action_find'),
            ('', b'_action_replace'),
            ('', b'_action_insert'),
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_key_enter'),
            ('\x1b', b'_key_string'),
        ])
        with patch.object(edr, '_get_clipboard', return_value='R'):
            with patch.object(edr, '_action_background', return_value=True):
                with patch.object(edr, '_render_scr'):
                    with patch('cat_win.src.curses.editor.search_iter_factory', return_value=DummyReplaceSearch()):
                        self.assertTrue(edr._action_replace())

    def test_editor_reload_insert_background_and_file_selection_remaining_4(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_reload'),
        ])
        with patch.object(ed, '_action_background', return_value=True):
            with patch.object(ed, '_render_scr'):
                with patch.object(ed, '_setup_file'):
                    self.assertTrue(ed._action_reload())

        edi = Editor([('', '')])
        edi.curse_window = MagicMock()
        edi.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_paste'),
            ('', b'_action_insert'),
        ])
        with patch.object(edi, '_action_background', return_value=True):
            with patch.object(edi, '_get_clipboard', return_value='4142'):
                with patch.object(edi, '_render_scr'):
                    self.assertTrue(edi._action_insert())

        edb = Editor([('', '')])
        edb.curse_window = MagicMock()
        with patch('cat_win.src.curses.editor.on_windows_os', True):
            with patch('cat_win.src.curses.editor.save_view_state') as save_state:
                self.assertFalse(edb._action_background())
        save_state.assert_called_once_with(edb)
        self.assertIsNotNone(edb.get_char)

        edfs = Editor([(test_file_path_editor, 'A')])
        edfs.curse_window = MagicMock()
        edfs.files = [(test_file_path_editor, 'A')] + [(test_file_path_editor, f'LONG_{i}_' + 'X' * 80) for i in range(20)]
        edfs.file = test_file_path_editor
        edfs.display_name = 'missing'
        edfs.file_commit_hash = {'hash': 'not-found'}
        edfs.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_file_selection'),
            ('', b'_move_key_up'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_key_enter'),
            ('', b'_move_key_up'),
            ('', b'_key_enter'),
        ])
        calls = {'n': 0}
        def addstr_side(*_a, **_k):
            calls['n'] += 1
            if calls['n'] in (3, 8):
                raise mm.error
            return None
        edfs.curse_window.addstr.side_effect = addstr_side
        commit = {'hash': 'abc1234', 'date': '2024-01-01', 'author': 'u', 'message': 'm'}
        with patch.object(edfs, '_action_background', return_value=True):
            with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=[commit]):
                self.assertFalse(edfs._action_file_selection())

    def test_editor_action_background_unix_path(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        with patch('cat_win.src.curses.editor.on_windows_os', False):
            with patch('cat_win.src.curses.editor.signal.SIGSTOP', 19, create=True):
                with patch('cat_win.src.curses.editor.curses.endwin') as endwin_call:
                    with patch('cat_win.src.curses.editor.os.kill') as kill_call:
                        with patch.object(ed, '_init_screen') as init_call:
                            self.assertTrue(ed._action_background())
        endwin_call.assert_called_once()
        kill_call.assert_called_once()
        init_call.assert_called_once()
        self.assertIsNotNone(ed.get_char)

    def test_editor_highlighter_getchar_render_run_open_remaining_4(self):
        ed = Editor([(test_file_path_editor, 'A')])
        ed.curse_window = MagicMock()
        ed._syntax_highlighter = 'p1'
        ed.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_up'),
            ('', b'_move_key_left'),
            ('', b'_function_sel_highlight'),
        ])
        with patch.object(ed, '_action_background', return_value=True):
            with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=({'None': None, 'Py': 'p1', 'Js': 'p2', 'Txt': 'p3'}, {'None': '', 'Py': '.py', 'Js': '.js', 'Txt': '.txt'})):
                with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_plugin', return_value=MagicMock()):
                    ed._function_sel_highlight()

        ed2 = Editor([('', '')])
        ed2.curse_window = MagicMock()
        seq = iter(['a'])
        def get_wch_side():
            try:
                return next(seq)
            except StopIteration:
                raise mm.error
        ed2.curse_window.get_wch.side_effect = get_wch_side
        gen = ed2._get_new_char()
        _ = next(gen)

        ed3 = Editor([('', '')])
        ed3.curse_window = MagicMock()
        ed3.window_content = ['\tabc', '\x01  ']
        ed3.wpos.set_pos((0, 1))
        ed3.cpos.set_pos((0, 1))
        ed3.selecting = True
        ed3.spos.set_pos((0, 0))
        ed3.search_items = {(0, 0): 3, (0, 10): 1}
        ed3.search_items_focused_span = [((0, 0), 2), ((1, 0), 2)]
        ed3._syntax_highlighter = MagicMock()
        ed3._syntax_cache = {0: ('\tabc', None, None, [(0, 2, 'kw')]), 1: ('\x01  ', None, None, [(0, 1, 'unknown')])}
        ed3._SYNTAX_COLOR_IDS['kw'] = 10
        ed3._render_scr()

        ed4 = Editor([('', '')])
        ed4.curse_window = MagicMock()
        class ErrThenQuit:
            def __init__(self):
                self.i = 0

            def __iter__(self):
                return self

            def __next__(self):
                self.i += 1
                if self.i == 1:
                    raise mm.error()
                return ('', b'_action_quit')

        def quit_gen():
            while True:
                yield ('', b'_action_quit')

        ed4.get_char = iter(ErrThenQuit())
        with patch.object(ed4, '_render_scr', return_value=None):
            with patch.object(ed4, '_build_file_upto', return_value=None):
                with patch.object(ed4, '_get_new_char', return_value=quit_gen()):
                    ed4._run()

        mm.resize_term.side_effect = mm.error
        try:
            self.assertTrue(ed4._action_resize())
        finally:
            mm.resize_term.side_effect = None

        ed5 = Editor([('', '')])
        ed5.curse_window = MagicMock()
        with patch('cat_win.src.curses.editor.sys.version_info', (3, 8, 0)):
            with patch('cat_win.src.curses.editor.os.isatty', return_value=True):
                ed5._init_screen()

        ed6 = Editor([('', '')])
        ed6.curse_window = MagicMock()
        ed6.unsaved_progress = True
        ed6._f_content_gen = MagicMock()
        ed6._f_content_gen.close.side_effect = StopIteration()
        with patch.object(ed6, '_init_screen', lambda *_: None):
            with patch.object(ed6, '_init_highlighter_colors', lambda *_: None):
                with patch.object(ed6, '_build_file_upto', lambda *_: None):
                    with patch.object(ed6, '_run', side_effect=RuntimeError('boom-save-fail')):
                        with patch.object(ed6, '_action_save', return_value=True):
                            with patch('builtins.input', return_value='Y'):
                                with patch('cat_win.src.curses.editor.curses.endwin'):
                                    with self.assertRaises(RuntimeError):
                                        ed6._open()

    def test_editor_transform_find_replace_remaining_5(self):
        def _events_for_query(query: str):
            return [(c, b'_key_string') for c in query] + [('', b'_key_enter')]

        native_str = ''.__class__

        class StrCompatNoAscii:
            __call__ = staticmethod(lambda x='': native_str(x))
            isalnum = staticmethod(native_str.isalnum)
            isalpha = staticmethod(native_str.isalpha)
            isdecimal = staticmethod(native_str.isdecimal)
            isdigit = staticmethod(native_str.isdigit)
            isidentifier = staticmethod(native_str.isidentifier)
            islower = staticmethod(native_str.islower)
            isnumeric = staticmethod(native_str.isnumeric)
            isprintable = staticmethod(native_str.isprintable)
            isspace = staticmethod(native_str.isspace)
            istitle = staticmethod(native_str.istitle)
            isupper = staticmethod(native_str.isupper)
            capitalize = staticmethod(native_str.capitalize)
            casefold = staticmethod(native_str.casefold)
            lower = staticmethod(native_str.lower)
            lstrip = staticmethod(native_str.lstrip)
            rstrip = staticmethod(native_str.rstrip)
            strip = staticmethod(native_str.strip)
            swapcase = staticmethod(native_str.swapcase)
            title = staticmethod(native_str.title)
            upper = staticmethod(native_str.upper)

        # _action_transform: Python <3.7 isascii fallback branch
        ed0 = Editor([('', '')])
        ed0.curse_window = MagicMock()
        ed0.get_char = iter([('', b'_action_quit')])
        with patch('cat_win.src.curses.editor.str', StrCompatNoAscii()):
            self.assertTrue(ed0._action_transform())

        # _action_transform: quit hotkey and explicit "exit" path
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.get_char = iter([('', b'_action_quit')])
        self.assertTrue(ed._action_transform())

        ed2 = Editor([('', '')])
        ed2.curse_window = MagicMock()
        ed2.get_char = iter(_events_for_query('exit'))
        self.assertTrue(ed2._action_transform())

        # _action_transform: force non-callable lambda eval branch
        ed3 = Editor([('', '')])
        ed3.curse_window = MagicMock()
        ed3.window_content = ['abc']
        ed3.get_char = iter(_events_for_query('lambda x: x') + [('\x1b', b'_key_string')])
        with patch('builtins.eval', return_value=1):
            self.assertTrue(ed3._action_transform())

        # _action_transform: lambda bool-result branch
        ed4 = Editor([('', '')])
        ed4.curse_window = MagicMock()
        ed4.window_content = ['abc']
        ed4.selecting = True
        ed4.spos.set_pos((0, 0))
        ed4.cpos.set_pos((0, 1))
        ed4.get_char = iter(_events_for_query('lambda x: x.isalpha()') + [('\x1b', b'_key_string')])
        self.assertTrue(ed4._action_transform())

        # _action_transform: lambda string-result branch with invalid area
        ed5 = Editor([('', '')])
        ed5.curse_window = MagicMock()
        ed5.window_content = ['abc']
        ed5.spos.set_pos((0, 0))
        ed5.cpos.set_pos((0, 0))
        ed5.get_char = iter(_events_for_query('lambda x: x') + [('\x1b', b'_key_string')])
        self.assertTrue(ed5._action_transform())

        class DummySearch:
            def __init__(self, vals, s_len=1, s_rows=None):
                self._it = iter(vals)
                self.s_len = s_len
                self.s_rows = s_rows or [((0, 0), s_len)]

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._it)

        # _action_find: selecting + next direction branch
        edf = Editor([('', '')])
        edf.curse_window = MagicMock()
        edf.window_content = ['abc'] * 60
        edf.selecting = True
        edf.spos.set_pos((0, 0))
        edf.cpos.set_pos((0, 1))
        edf.search = 'a'
        with patch(
            'cat_win.src.curses.editor.search_iter_factory',
            side_effect=[
                DummySearch([(10, 2)], s_len=2, s_rows=[((10, 2), 2)]),
                DummySearch([(10, 3), (999, 0)], s_len=1, s_rows=[((10, 3), 1)]),
            ],
        ):
            self.assertTrue(edf._action_find(1))

        # _action_find: selecting + reverse direction branch
        edf2 = Editor([('', '')])
        edf2.curse_window = MagicMock()
        edf2.window_content = ['abc'] * 60
        edf2.selecting = True
        edf2.spos.set_pos((0, 2))
        edf2.cpos.set_pos((0, 0))
        edf2.search = 'a'
        with patch(
            'cat_win.src.curses.editor.search_iter_factory',
            side_effect=[
                DummySearch([(5, 1)], s_len=1, s_rows=[((5, 1), 1)]),
                DummySearch([(5, 2)], s_len=1, s_rows=[((5, 2), 1)]),
            ],
        ):
            self.assertTrue(edf2._action_find(-1))

        # _action_find: non-selecting + reverse cursor offset path
        edf3 = Editor([('', '')])
        edf3.curse_window = MagicMock()
        edf3.window_content = ['abc'] * 60
        edf3.search = 'a'
        with patch(
            'cat_win.src.curses.editor.search_iter_factory',
            side_effect=[
                DummySearch([(40, 1)], s_len=1, s_rows=[((40, 1), 1)]),
                DummySearch([], s_len=1, s_rows=[]),
            ],
        ):
            self.assertTrue(edf3._action_find(-1))

        class DummyReplaceSearch:
            def __init__(self, vals, r_len=1, yielded_result=True):
                self._vals = vals
                self.r_len = r_len
                self.yielded_result = yielded_result

            def __iter__(self):
                return iter(self._vals)

        # _action_replace: running-branch break when replace_next != 0 and no result
        edr0 = Editor([('', '')])
        edr0.curse_window = MagicMock()
        edr0.search = 'a'
        edr0.selecting = True
        edr0.spos.set_pos((0, 0))
        edr0.cpos.set_pos((0, 1))
        with patch(
            'cat_win.src.curses.editor.search_iter_factory',
            return_value=DummyReplaceSearch([], r_len=1, yielded_result=False),
        ):
            self.assertTrue(edr0._action_replace(1))

        # _action_replace: action hotkeys while prompting + ValueError path
        edr1 = Editor([('', '')])
        edr1.curse_window = MagicMock()
        edr1.search = 'a'
        edr1.get_char = iter([
            ('', b'_action_background'),
            ('', b'_action_resize'),
            ('', b'_action_replace'),
            ('', b'_key_enter'),
            ('', b'_action_quit'),
        ])
        with patch.object(edr1, '_action_background', return_value=True):
            with patch.object(edr1, '_render_scr'):
                with patch('cat_win.src.curses.editor.search_iter_factory', side_effect=ValueError('bad')):
                    self.assertTrue(edr1._action_replace())

        # _action_replace: selecting + next direction branch
        edr2 = Editor([('', '')])
        edr2.curse_window = MagicMock()
        edr2.search = 'a'
        edr2.selecting = True
        edr2.spos.set_pos((0, 0))
        edr2.cpos.set_pos((0, 1))
        with patch.object(edr2, '_replace_search', return_value=None):
            with patch(
                'cat_win.src.curses.editor.search_iter_factory',
                return_value=DummyReplaceSearch([(0, 0)], r_len=1, yielded_result=True),
            ):
                self.assertTrue(edr2._action_replace(1))

        # _action_replace: selecting + reverse direction branch
        edr3 = Editor([('', '')])
        edr3.curse_window = MagicMock()
        edr3.search = 'a'
        edr3.selecting = True
        edr3.spos.set_pos((0, 2))
        edr3.cpos.set_pos((0, 0))
        with patch.object(edr3, '_replace_search', return_value=None):
            with patch(
                'cat_win.src.curses.editor.search_iter_factory',
                return_value=DummyReplaceSearch([(0, 1)], r_len=1, yielded_result=True),
            ):
                self.assertTrue(edr3._action_replace(-1))

        # _action_replace: selecting restore + no-match message
        edr4 = Editor([('', '')])
        edr4.curse_window = MagicMock()
        edr4.search = 'a'
        edr4.selecting = True
        edr4.spos.set_pos((0, 0))
        edr4.cpos.set_pos((0, 1))
        with patch(
            'cat_win.src.curses.editor.search_iter_factory',
            return_value=DummyReplaceSearch([], r_len=1, yielded_result=False),
        ):
            self.assertTrue(edr4._action_replace(1))

    def test_editor_file_highlighter_render_run_remaining_5(self):
        # _action_file_selection: fallback index path and empty-list move branch
        ed = Editor([(test_file_path_editor, 'A')])
        ed.curse_window = MagicMock()
        ed.files = []
        ed.file = 'missing-file'
        ed.display_name = 'missing-name'
        ed.getxymax = lambda: (3, 20)
        ed.get_char = iter([('', b'_move_key_down'), ('', b'_action_quit')])
        self.assertTrue(ed._action_file_selection())

        # _action_file_selection: paging footer, status-bar curses.error and nav_y shifts
        ed2 = Editor([(test_file_path_editor, 'A')])
        ed2.curse_window = MagicMock()
        ed2.files = [(test_file_path_editor, f'N{i}_' + 'X' * 60) for i in range(30)]
        ed2.file = test_file_path_editor
        ed2.display_name = ed2.files[0][1]
        ed2.getxymax = lambda: (3, 15)
        ed2.get_char = iter([
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_action_quit'),
        ])

        def _file_addstr_side(y, *_args, **_kwargs):
            if y == 3:
                raise mm.error
            return None

        ed2.curse_window.addstr.side_effect = _file_addstr_side
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertTrue(ed2._action_file_selection())

        # _function_sel_highlight: empty-list move continue + action quit + status error
        eh = Editor([(test_file_path_editor, 'A')])
        eh.curse_window = MagicMock()
        eh.getxymax = lambda: (3, 15)
        eh.get_char = iter([('', b'_move_key_down'), ('', b'_action_quit')])

        def _hl_addstr_status_side(y, *_args, **_kwargs):
            if y == 3:
                raise mm.error
            return None

        eh.curse_window.addstr.side_effect = _hl_addstr_status_side
        with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=({}, {})):
            eh._function_sel_highlight()

        # _function_sel_highlight: row addstr error and paging footer
        eh2 = Editor([(test_file_path_editor, 'A')])
        eh2.curse_window = MagicMock()
        eh2.getxymax = lambda: (3, 15)
        eh2.get_char = iter([('', b'_action_quit')])
        plugins = ({'None': None, 'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, {'None': ''})
        eh2.curse_window.addstr.side_effect = mm.error
        with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=plugins):
            eh2._function_sel_highlight()

        eh3 = Editor([(test_file_path_editor, 'A')])
        eh3.curse_window = MagicMock()
        eh3.getxymax = lambda: (3, 15)
        eh3.get_char = iter([
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_action_quit'),
        ])
        with patch('cat_win.src.curses.editor.SyntaxHighlighter.get_available_plugins', return_value=plugins):
            eh3._function_sel_highlight()

        # _get_new_char: nodelay read loop exits via curses.error
        eg = Editor([('', '')])
        eg.curse_window = MagicMock()
        chars = iter(['a'])

        def _get_wch_buffered():
            try:
                return next(chars)
            except StopIteration:
                raise editor.curses.error()

        eg.curse_window.get_wch.side_effect = _get_wch_buffered
        _ = next(eg._get_new_char())

        eg2 = Editor([('', '')])
        eg2.curse_window = MagicMock()
        eg2.curse_window.get_wch.side_effect = ['a', editor.curses.error()]
        with patch('cat_win.src.curses.editor.curses.keyname', return_value=b'a'):
            _ = next(eg2._get_new_char())

        # _get_syntax_tokens: stale cache continuation path
        ets = Editor([('', '')])
        ets.window_content = ['line0', 'line1']
        ets._syntax_highlighter = MagicMock()
        ets._syntax_highlighter.tokenize_line.return_value = ([], None)
        ets._syntax_cache = {}
        ets._get_syntax_tokens(1, 2)

        # _render_scr: special-char replacement, clipping continues, status and cursor move errors
        er = Editor([('', '')])
        er.curse_window = MagicMock()
        er.getxymax = lambda: (1, 10)
        er.window_content = ['界abc', 'row1', 'row2', 'row3', 'row4', 'row5']
        er.wpos.set_pos((0, 0))
        er.cpos.set_pos((0, 0))
        er.search_items = {(-1, 0): 1, (0, 500): 1, (0, 0): 1}
        er.search_items[(0, 0)] = 1
        er.search_items_focused_span = [((-1, 0), 1), ((0, 500), 1)]

        move_calls = {'n': 0}

        def _move_side(y, x):
            move_calls['n'] += 1
            if move_calls['n'] == 3:
                raise mm.error
            return None

        er.curse_window.move.side_effect = _move_side
        er.curse_window.addstr.side_effect = mm.error
        er._render_scr()

        # _run: scroll branch path
        erun = Editor([('', '')])
        erun.curse_window = MagicMock()

        def _run_events():
            yield ('', b'_scroll_key_down')
            while True:
                yield ('', b'_action_quit')

        erun.get_char = _run_events()
        with patch.object(erun, '_render_scr', return_value=None):
            with patch.object(erun, '_build_file_upto', return_value=None):
                with patch.object(erun, '_scroll_key_down') as scroll_down:
                    erun._run()
                    self.assertTrue(scroll_down.called)

    def test_editor_getxymax_unpatched_and_open_unix_signal_branch(self):
        ed = Editor([('', '')])
        ed.curse_window = MagicMock()
        ed.curse_window.getmaxyx.return_value = (20, 80)
        self.assertEqual(ORIGINAL_EDITOR_GETXYMAX(ed), (20-ed.status_bar_size, 80))

        def fake_init(self, files, file_idx=0, file_commit_hash=None):
            self.files = files
            self.file = files[file_idx][0]
            self.display_name = files[file_idx][1]
            self.error_bar = ''
            self.open_next_idx = None
            self.open_next_hash = None
            self.changes_made = False

        with patch('cat_win.src.curses.editor.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.editor.on_windows_os', False):
                with patch.object(Editor, '__init__', fake_init):
                    with patch.object(Editor, '_open', lambda *_, **__: None):
                        with patch('cat_win.src.curses.editor.signal.SIGTSTP', 18, create=True):
                            with patch('cat_win.src.curses.editor.signal.SIG_IGN', 1, create=True):
                                with patch('cat_win.src.curses.editor.signal.signal') as sig_call:
                                    Editor.loading_failed = False
                                    self.assertFalse(Editor.open([('a', 'A')], False))
                                    self.assertTrue(sig_call.called)
