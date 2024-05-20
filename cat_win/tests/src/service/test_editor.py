from unittest.mock import patch, MagicMock
from unittest import TestCase
import os

from cat_win.tests.mocks.edit import getxymax
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.std import StdOutMock, IoHelperMock

import cat_win.src.service.editor as editor
if editor.CURSES_MODULE_ERROR:
    setattr(editor, 'curses', None)
from cat_win.src.service.editor import Editor

mm = MagicMock()

test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')
test_file_path_editor = os.path.join(test_file_dir, 'test_editor.txt')


@patch('cat_win.src.service.editor.Editor.getxymax', getxymax)
@patch('cat_win.src.service.editor.Editor.wc_width', lambda _: 1)
@patch('cat_win.src.service.editor.curses', mm)
@patch('cat_win.src.service.helper.iohelper.IoHelper.get_newline', lambda *args: '\n')
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
        editor = Editor(test_file_path_editor, '')
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
        editor = Editor(test_file_path_editor, '')
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
        editor._key_ctl_backspace(None)
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

    def test_editor_scroll_key_shift_left(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((1,2))
        editor._scroll_key_shift_left()
        self.assertEqual(editor.wpos.get_pos(), (1,1))
        editor._scroll_key_shift_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_shift_left()
        self.assertEqual(editor.wpos.get_pos(), (1,0))

    def test_editor_scroll_key_shift_right(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((0,2))
        editor._scroll_key_shift_right()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._key_string('x' * 115)
        editor._scroll_key_shift_right()
        self.assertEqual(editor.wpos.get_pos(), (0,1))
        editor._scroll_key_shift_right()
        self.assertEqual(editor.wpos.get_pos(), (0,2))
        editor._scroll_key_shift_right()
        self.assertEqual(editor.wpos.get_pos(), (0,2))

    def test_editor_scroll_key_shift_up(self):
        editor = Editor(test_file_path_editor, '')
        editor.wpos.set_pos((2,0))
        editor._scroll_key_shift_up()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_shift_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        editor._scroll_key_shift_up()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    def test_editor_scroll_key_shift_down(self):
        editor = Editor(test_file_path_editor, '')
        editor._scroll_key_shift_down()
        self.assertEqual(editor.wpos.get_pos(), (0,0))
        for _ in range(30):
            editor._key_enter('')
        editor._scroll_key_shift_down()
        self.assertEqual(editor.wpos.get_pos(), (1,0))
        editor._scroll_key_shift_down()
        self.assertEqual(editor.wpos.get_pos(), (2,0))
        editor._scroll_key_shift_down()
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

    def test_editor_scroll_key_home(self):
        editor = Editor(test_file_path_editor, '')
        for _ in range(61):
            editor._key_enter('')
        editor._key_string('!' * 150)
        editor.wpos.set_pos((33, 37))
        editor._scroll_key_home()
        self.assertEqual(editor.wpos.get_pos(), (0,0))

    @patch('cat_win.src.service.editor.Editor.special_indentation', ':)')
    def test_editor_key_btab(self):
        editor = Editor(test_file_path_editor, '')
        editor._key_string(':):)')
        editor._key_string('\t')
        self.assertListEqual(editor.window_content, [':):):)line 1', 'line 2'])
        editor._move_key_ctl_right()
        self.assertEqual(editor._key_btab(''), ':)')
        self.assertListEqual(editor.window_content, [':):)line 1', 'line 2'])
        self.assertEqual(editor._key_btab(''), ':)')
        self.assertListEqual(editor.window_content, [':)line 1', 'line 2'])
        self.assertEqual(editor._key_btab(''), ':)')
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])
        self.assertEqual(editor._key_btab(''), None)
        self.assertListEqual(editor.window_content, ['line 1', 'line 2'])

    def test_editor_key_btab_reverse(self):
        editor = Editor(test_file_path_editor, '')
        editor.cpos.set_pos((0,4))
        editor._key_btab_reverse(':)')
        self.assertListEqual(editor.window_content, [':)line 1', 'line 2'])
        self.assertEqual(editor.cpos.get_pos(), (0,6))

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
            yield from zip(user_input + ['', ''], [b'_key_string'] * len(user_input) + [b'_key_ctl_backspace', b'_key_enter'])
        editor.get_char = char_gen_ctl([5, 'a', '\\', 'b',  'a', '1', '2', '3', '4'])
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))
        def yield_action_quit():
            yield ('', b'_action_quit')
        editor.get_char = yield_action_quit()
        self.assertEqual(editor._action_find(), True)
        self.assertEqual(editor.cpos.get_pos(), (40, 2))

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
        self.assertEqual(editor.cpos.get_pos(), (0, 0))
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

    # NOTE: DEBUG: this test has bad performance due to *many* magicmock calls
    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', IoHelperMock.yield_file_gen(['a' * 200] * 50))
    def test__render_scr(self):
        editor = Editor('', 'X' * 300)
        editor.curse_window = MagicMock()
        editor.error_bar = ':)'
        editor.debug_mode = True
        editor.cpos.set_pos((4, 205))
        self.assertEqual(editor._render_scr(), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 200))

        editor.cpos.set_pos((4, 0))
        editor.wpos.set_pos((6, 0))
        self.assertEqual(editor._render_scr(), None)
        self.assertEqual(editor.cpos.get_pos(), (4, 0))
        self.assertEqual(editor.wpos.get_pos(), (4, 0))

        editor.cpos.set_pos((34, 0))
        editor.wpos.set_pos((0, 0))
        self.assertEqual(editor._render_scr(), None)
        self.assertEqual(editor.cpos.get_pos(), (34, 0))
        self.assertEqual(editor.wpos.get_pos(), (5, 0))

        editor.cpos.set_pos((7, 4))
        editor.wpos.set_pos((5, 6))
        self.assertEqual(editor._render_scr(), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 4))
        self.assertEqual(editor.wpos.get_pos(), (5, 4))

        editor.cpos.set_pos((7, 180))
        editor.wpos.set_pos((5, 0))
        self.assertEqual(editor._render_scr(), None)
        self.assertEqual(editor.cpos.get_pos(), (7, 180))
        self.assertEqual(editor.wpos.get_pos(), (5, 61))

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
    def test_editor_no_curses_error(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(Editor.open('', '', True), False)
            self.assertIn('could not be loaded', fake_out.getvalue())
            self.assertIn('windows-curses', fake_out.getvalue())
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            self.assertEqual(Editor.open('', '', True), False)
            self.assertEqual('', fake_out.getvalue())

    def test_editor_set_indentation(self):
        self.assertEqual(Editor.special_indentation, '\t')
        self.assertEqual(Editor.auto_indent, False)
        Editor.set_indentation('  ', True)
        self.assertEqual(Editor.special_indentation, '  ')
        self.assertEqual(Editor.auto_indent, True)

    def test_editor_set_flags(self):
        self.assertEqual(Editor.save_with_alt, False)
        self.assertEqual(Editor.debug_mode, False)
        self.assertEqual(Editor.unicode_escaped_search, True)
        self.assertEqual(Editor.file_encoding, 'utf-8')
        Editor.set_flags(True, True, False, 'utf-16')
        self.assertEqual(Editor.save_with_alt, True)
        self.assertEqual(Editor.debug_mode, True)
        self.assertEqual(Editor.unicode_escaped_search, False)
        self.assertEqual(Editor.file_encoding, 'utf-16')
        Editor.set_flags(False, False, True, 'utf-8')
