from unittest.mock import patch
from unittest import TestCase
import os

from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.std import StdOutMock
from cat_win.util.editor import Editor, get_newline
# import sys
# sys.path.append('../cat_win')
test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')
test_file_path_editor = os.path.join(test_file_dir, 'test_editor.txt')


class TestEditor(TestCase):
    maxDiff = None

    def test_get_newline(self):
        self.assertEqual(get_newline(test_file_path), '\r\n')
        self.assertEqual(get_newline(test_file_path_empty), '\n')
        self.assertEqual(get_newline(test_file_path_oneline), '\n')

    def test_editor_special_chars(self):
        editor = Editor(test_file_path_oneline, 'utf-8')
        self.assertEqual(editor._get_special_char('\b'), '?')

        editor._set_special_chars({'\b': '!'})
        self.assertEqual(editor._get_special_char('\b'), '!')

    def test_editor_unknown_file(self):
        editor = Editor('', 'utf-8')
        self.assertEqual(editor.error_bar, "[Errno 2] No such file or directory: ''")
        self.assertListEqual(editor.window_content, [''])

    def test_editor_key_enter(self):
        editor = Editor(test_file_path_oneline, 'utf-8')
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 'test'])
        editor._move_key_right()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est'])
        editor._move_key_end()
        editor._key_enter(None)
        self.assertListEqual(editor.window_content, ['', 't', 'est', ''])

    def test_editor_key_dc(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._key_dc(None)
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

    def test_editor_key_dl(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' 1', 'line 2'])
        editor._move_key_right()
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' ', 'line 2'])
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' line 2'])
        editor._move_key_end()
        editor._key_dl(None)
        self.assertListEqual(editor.window_content, [' line 2'])

    def test_editor_key_backspace(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_ctl_end()
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1', 'line '])
        editor._move_key_left()
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1', 'lin '])
        editor._move_key_home()
        editor._key_backspace('\b')
        self.assertListEqual(editor.window_content, ['line 1lin '])

    def test_editor_key_ctl_backspace(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_ctl_end()
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'line'])
        editor._move_key_home()
        editor._move_key_right()
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1', 'ine'])
        editor._key_ctl_backspace(None)
        self.assertListEqual(editor.window_content, ['line 1ine'])

    def test_editor_move_key_left(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        self.assertEqual(editor._move_key_left(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,0))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_left()
        self.assertEqual(editor.cpos.get_pos(), (0,5))

    def test_editor_move_key_right(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor.cpos.set_pos((1,6))
        self.assertEqual(editor._move_key_right(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((0,6))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        editor._move_key_right()
        self.assertEqual(editor.cpos.get_pos(), (1,1))

    def test_editor_move_key_up(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor.cpos.set_pos((1,3))
        editor._move_key_up()
        self.assertEqual(editor.cpos.get_pos(), (0,3))
        self.assertEqual(editor._move_key_up(), None)
        self.assertEqual(editor.cpos.get_pos(), (0,3))

    def test_editor_move_key_down(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_down()
        self.assertEqual(editor.cpos.get_pos(), (1,0))
        self.assertEqual(editor._move_key_down(), None)
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_left(self):
        editor = Editor(test_file_path_editor, 'utf-8')
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
        editor = Editor(test_file_path_editor, 'utf-8')
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
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,6))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((11,4))
        editor._move_key_ctl_up()
        self.assertEqual(editor.cpos.get_pos(), (1,4))

    def test_editor_move_key_ctl_down(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor.cpos.set_pos((-9, 3))
        editor._move_key_ctl_down()
        self.assertEqual(editor.cpos.get_pos(), (1,3))

    def test_editor_move_key_end(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))
        editor._move_key_end()
        self.assertEqual(editor.cpos.get_pos(), (0,6))

    def test_editor_move_key_ctl_end(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))
        editor._move_key_ctl_end()
        self.assertEqual(editor.cpos.get_pos(), (1,6))

    def test_editor_move_key_home(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_home()
        self.assertEqual(editor.cpos.get_pos(), (1,0))

    def test_editor_move_key_ctl_home(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))
        editor.cpos.set_pos((1,3))
        editor._move_key_ctl_home()
        self.assertEqual(editor.cpos.get_pos(), (0,0))

    def test_editor_key_string(self):
        editor = Editor(test_file_path_editor, 'utf-8')
        self.assertEqual(editor._key_string(1), '')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        editor._move_key_right()
        editor._key_string('test')
        self.assertListEqual(editor.window_content, ['ltestine 1', 'line 2'])

    def test_editor_action_save(self):
        editor = Editor(test_file_path, 'utf-8', True)
        exc = OSError('TestError')
        error_def = ErrorDefGen.get_def(exc)
        with patch('cat_win.cat.sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(editor._action_save(error_def), True)
            self.assertEqual(editor.error_bar, 'TestError')
            self.assertEqual('TestError\n', fake_out.getvalue())

        no_error_def = lambda *_: None
        self.assertEqual(editor._action_save(no_error_def), True)
        self.assertEqual(editor.error_bar, '')

    def test_editor_action_quit(self):
        editor = Editor(test_file_path, 'utf-8')
        self.assertEqual(editor._action_quit(None), False)

    def test_editor_interrupt(self):
        editor = Editor(test_file_path_oneline, 'utf-8', True)
        with self.assertRaises(KeyboardInterrupt):
            with patch('cat_win.cat.sys.stderr', new=StdOutMock()) as fake_out:
                editor._action_interrupt(None)
                self.assertEqual('Interrupting...\n', fake_out.getvalue())

    @patch('cat_win.util.editor.CURSES_MODULE_ERROR', new=True)
    def test_editor_no_curses_error(self):
        with patch('cat_win.cat.sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(Editor.open('', '', None, True), False)
            self.assertIn('could not be loaded', fake_out.getvalue())
            self.assertIn('windows-curses', fake_out.getvalue())
