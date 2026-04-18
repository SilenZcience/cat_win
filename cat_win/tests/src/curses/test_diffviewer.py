from unittest import TestCase
from unittest.mock import MagicMock, patch
import runpy
import importlib

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.curses import diffviewer as dv_module
if dv_module.CURSES_MODULE_ERROR:
    setattr(dv_module, 'curses', None)
from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.helper.editorhelper import Position
from cat_win.src.curses.helper.diffviewerhelper import DifflibID
from cat_win.src.persistence import viewstate

from cat_win.tests.mocks.diffviewer import (
    DummyDiffItem,
    DummyDifflibParser,
    DummyWindow,
)
from cat_win.tests.mocks.logger import LoggerStub


mm = MagicMock()
mm.A_UNDERLINE = 1
mm.error = Exception
mm.BUTTON1_PRESSED = 1
mm.BUTTON4_PRESSED = 2
mm.BUTTON5_PRESSED = 4
mm.COLORS = 255

logger = LoggerStub()


@patch('cat_win.src.curses.helper.fileselectionhelper.curses', mm)
@patch('cat_win.src.curses.diffviewer.curses', mm)
class TestDiffViewer(TestCase):
    def _mk_viewer(self):
        viewer = DiffViewer.__new__(DiffViewer)
        viewer.curse_window = DummyWindow()
        viewer.files = [('a.txt', 'A'), ('b.txt', 'B')]
        viewer.file_commit_hashes = (None, None)
        viewer.diff_files = ['a.txt', 'b.txt']
        viewer.display_names = ['A', 'B']
        viewer.open_next_idxs = None
        viewer.open_next_hashes = (None, None)
        viewer.difflibparser = DummyDifflibParser([], equal=1, insert=1, delete=1, changed=1, last_lineno=3)
        viewer.difflibparser_bak = viewer.difflibparser
        viewer.diff_items = [
            DummyDiffItem('1', 'abc', 'abc', DifflibID.EQUAL),
            DummyDiffItem('2', 'abX', 'abY', DifflibID.CHANGED, changes1=[2], changes2=[2]),
            DummyDiffItem('3', 'old', '', DifflibID.DELETE),
            DummyDiffItem('4', '', 'new', DifflibID.INSERT),
        ]
        viewer.diff_items_bak = list(viewer.diff_items)
        viewer.half_width = 20
        viewer.l_offset = 2
        viewer.status_bar_size = 1
        viewer.error_bar = ''
        viewer.search = ''
        viewer.search_items = {}
        viewer.wpos = Position(0, 0)
        viewer.wpos_bak = Position(0, 0)
        viewer.rpos = Position(0, 0)
        viewer.rpos_bak = Position(0, 0)
        viewer.cpos = Position(0, 0)
        viewer.displaying_overview = False
        viewer.difflibparser_cutoff = 0.75
        viewer._watch_text2 = []
        viewer._mtime_cache = [1, 2]
        return viewer

    def test_correct_save_and_load_viewstate(self):
        diffviewer = DiffViewer([(__file__, '')])
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

        with patch('cat_win.src.curses.diffviewer.save_view_state', side_effect=fake_save_view_state), \
             patch('cat_win.src.persistence.viewstate.load_view_state', side_effect=fake_load_view_state), \
             patch('cat_win.src.curses.diffviewer.on_windows_os', True):
            self.assertFalse(diffviewer._action_background())
            restored_dv = viewstate.load_view_state()

        self.assertEqual(saved_state['view_type'], 'DiffViewer')
        self.assertIsInstance(restored_dv, DiffViewer)

        with patch('cat_win.src.curses.diffviewer.DiffViewer._run', lambda *args: None):
            restored_dv._open(fg = True)
        self.assertEqual(diffviewer.difflibparser, restored_dv.difflibparser)


    def test_init_defaults_and_set_flags(self):
        with patch.object(DiffViewer, '_setup_file', lambda s: None):
            d = DiffViewer([('a', 'A'), ('b', 'B')])
        self.assertEqual(d.diff_files, ['a', 'b'])
        self.assertEqual(d.display_names, ['A', 'B'])

        DiffViewer.set_flags(True, True, 'cp1252')
        self.assertTrue(DiffViewer.debug_mode)
        self.assertTrue(DiffViewer.watch_mode)
        self.assertEqual(DiffViewer.file_encoding, 'cp1252')

    def test_setup_file_success_and_error_branches(self):
        with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', side_effect=['l1\nl2', 'r1\nr2']):
            with patch('cat_win.src.curses.diffviewer.get_file_mtime', side_effect=[10, 20]):
                with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'l1', 'r1', DifflibID.CHANGED)], last_lineno=1)):
                    dv = DiffViewer([('a.txt', 'A'), ('b.txt', 'B')])
        self.assertEqual(dv.l_offset, 2)
        self.assertEqual(dv._mtime_cache, [10, 20])

        with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', side_effect=OSError('bad')):
            with patch.object(dv_module, 'logger', logger):
                dv_err = DiffViewer([('a.txt', 'A'), ('b.txt', 'B')])
        self.assertEqual(dv_err.status_bar_size, 2)
        self.assertIn('bad', dv_err.error_bar)

    def test_setup_file_git_paths(self):
        with patch('cat_win.src.curses.diffviewer.GitHelper.get_git_file_content_at_commit', side_effect=[['A'], OSError('git bad')]):
            with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'A', '', DifflibID.DELETE)])):
                dv = DiffViewer([('a.txt', 'A'), ('b.txt', 'B')], file_commit_hashes=('h1', 'h2'))
        self.assertIn('GIT', dv.display_names[0])
        self.assertIn('GIT_ERROR', dv.display_names[1])

    def test_geometry_and_navigation_helpers(self):
        dv = self._mk_viewer()
        self.assertEqual(dv.getxymax(), (29, 120))
        self.assertEqual(dv.lllen(), 3)

        dv.rpos.row = 3
        dv._move_key_up()
        self.assertEqual(dv.rpos.row, 2)
        dv._move_key_down()
        self.assertEqual(dv.rpos.row, 3)

        dv._move_key_left()
        self.assertEqual(dv.wpos.col, -1)
        dv._move_key_right()
        self.assertEqual(dv.wpos.col, 0)

        dv._move_key_ctl_up()
        self.assertEqual(dv.rpos.row, 0)
        dv._move_key_ctl_down()
        self.assertEqual(dv.rpos.row, 3)

        dv._move_key_home()
        self.assertEqual(dv.wpos.col, 0)
        dv._move_key_end()
        self.assertLessEqual(dv.wpos.col, 0)

    def test_mouse_move_and_boundaries_and_color(self):
        dv = self._mk_viewer()
        with patch('cat_win.src.curses.diffviewer.curses.getmouse', return_value=(0, 0, 1, 0, mm.BUTTON1_PRESSED)):
            dv._move_key_mouse()
        self.assertEqual(dv.rpos.row, 1)

        with patch('cat_win.src.curses.diffviewer.curses.getmouse', return_value=(0, 0, 0, 0, mm.BUTTON4_PRESSED)):
            dv._move_key_mouse()
        with patch('cat_win.src.curses.diffviewer.curses.getmouse', return_value=(0, 0, 0, 0, mm.BUTTON5_PRESSED)):
            dv._move_key_mouse()

        dv.wpos = Position(999, 999)
        dv._enforce_boundaries(5)
        self.assertGreaterEqual(dv.wpos.row, 0)
        self.assertGreaterEqual(dv.wpos.col, 0)

        mm.has_colors.return_value = False
        self.assertEqual(dv._get_color(1), 0)

    def test_render_helpers_and_ratios(self):
        dv = self._mk_viewer()
        self.assertEqual(dv._get_diff_ratio(0), 100.0)
        self.assertEqual(dv._get_diff_ratio(2), 0.0)
        self.assertLess(dv._get_diff_ratio(1), 100.0)

        dv.error_bar = 'err'
        dv._render_status_bar(10, 50)
        dv._render_scr()
        self.assertTrue(any(call[0] == 'refresh' for call in dv.curse_window.calls))

        with patch.object(dv, '_get_color', return_value=0):
            with patch.object(dv.curse_window, 'addstr', side_effect=mm.error):
                dv._action_render_scr('msg', 'tmp')

    @patch.object(dv_module, 'logger', logger)
    def test_action_jump_and_find_and_insert(self):
        dv = self._mk_viewer()
        dv.difflibparser.last_lineno = 3
        dv.diff_items = [
            DummyDiffItem('1', 'a', 'a', DifflibID.EQUAL),
            DummyDiffItem('2', 'b', 'b', DifflibID.EQUAL),
            DummyDiffItem('3', 'c', 'c', DifflibID.EQUAL),
        ]
        dv._get_next_char = MagicMock(side_effect=[('3', b'_key_string'), ('', b'_key_enter')])
        dv._action_jump()
        self.assertEqual(dv.rpos.row, 2)

        dv2 = self._mk_viewer()
        dv2._get_next_char = MagicMock(side_effect=[('x', b'_key_string'), ('', b'_key_enter'), (ESC_CODE, b'_key_string')])
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=StopIteration()):
            dv2._action_find(0)
        self.assertEqual(dv2.search, 'x')

        dv3 = self._mk_viewer()
        dv3._get_next_char = MagicMock(side_effect=[('0', b'_key_string'), ('.', b'_key_string'), ('8', b'_key_string'), ('', b'_key_enter')])
        dv3._action_insert()
        self.assertEqual(dv3.difflibparser_cutoff, 0.8)

    def test_action_jump_supports_cursor_move_and_middle_insert(self):
        dv = self._mk_viewer()
        dv.difflibparser.last_lineno = 999
        dv.diff_items = [
            DummyDiffItem('1', 'a', 'a', DifflibID.EQUAL),
            DummyDiffItem('2', 'b', 'b', DifflibID.EQUAL),
            DummyDiffItem('3', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('4', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('5', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('6', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('7', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('8', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('9', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('10', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('11', 'c', 'c', DifflibID.EQUAL),
            DummyDiffItem('12', 'c', 'c', DifflibID.EQUAL),
        ]
        dv._get_next_char = MagicMock(side_effect=[
            ('4', b'_key_string'),
            ('3', b'_key_string'),
            ('', b'_move_key_left'),
            ('', b'_key_dc'),
            ('2', b'_key_string'),
            ('', b'_move_key_left'),
            ('', b'_key_dl'),
            ('1', b'_key_string'),
            ('', b'_move_key_left'),
            ('', b'_key_backspace'),
            ('1', b'_key_string'),
            ('', b'_key_enter'),
        ])
        dv._action_jump()
        self.assertEqual(dv.rpos.row, 10)

    def test_action_reload_watch_quit_interrupt_resize(self):
        dv = self._mk_viewer()
        dv._setup_file = MagicMock()
        self.assertTrue(dv._action_reload())
        dv._setup_file.assert_called_once()

        dvw = self._mk_viewer()
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', side_effect=[2, 3]):
            with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', return_value='n1\nn2'):
                with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'x', 'y', DifflibID.CHANGED)])):
                    dvw._watch_text2 = ['o1']
                    dvw._watch_update()
        self.assertEqual(dvw.status_bar_size, 1)

        dvq = self._mk_viewer()
        dvq.displaying_overview = True
        dvq.open_next_idxs = None
        self.assertTrue(dvq._action_quit())
        self.assertFalse(dvq.displaying_overview)
        self.assertFalse(self._mk_viewer()._action_quit())

        with self.assertRaises(KeyboardInterrupt):
            self._mk_viewer()._action_interrupt()

        dvr = self._mk_viewer()
        dvr.curse_window.getmaxyx = lambda: (40, 130)
        mm.resize_term.side_effect = mm.error
        self.assertTrue(dvr._action_resize())

    def test_file_selection_help_overview_and_search_functions(self):
        dv = self._mk_viewer()
        dv._get_next_char = MagicMock(side_effect=[(ESC_CODE, b'_key_string')])
        self.assertTrue(dv._action_file_selection())

        dv2 = self._mk_viewer()
        dv2._get_next_char = MagicMock(side_effect=[(-1, b'_key_timeout'), ('x', b'_key_string')])
        dv2._function_help()
        self.assertTrue(any(call[0] == 'refresh' for call in dv2.curse_window.calls))

        dv3 = self._mk_viewer()
        with patch('cat_win.src.curses.diffviewer.get_file_size', return_value=10):
            with patch('cat_win.src.curses.diffviewer._convert_size', return_value='10 B'):
                with patch('cat_win.src.curses.diffviewer.get_file_ctime', return_value=1):
                    with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'a', 'b', DifflibID.CHANGED)])):
                        dv3._function_overview()
        self.assertTrue(dv3.displaying_overview)

        dv4 = self._mk_viewer()
        dv4.search = ''
        self.assertIsNone(dv4._function_search())
        self.assertIsNone(dv4._function_search_r())
        dv4.search = 'x'
        with patch.object(dv4, '_action_find') as af:
            dv4._function_search()
            dv4._function_search_r()
        self.assertEqual(af.call_count, 2)

    def test_get_next_char_run_init_open(self):
        dv = self._mk_viewer()
        dv.curse_window.set_input([-1, 'a'])
        mm.keyname.return_value = b'K'
        with patch.dict('cat_win.src.curses.diffviewer.UNIFY_HOTKEYS', {b'K': b'_action_quit'}, clear=False):
            self.assertEqual(dv._get_next_char(), (-1, b'_key_timeout'))
            wchar, key = dv._get_next_char()
            self.assertEqual(wchar, 'a')
            self.assertEqual(key, b'_action_quit')

        dvr = self._mk_viewer()
        dvr._render_scr = MagicMock()
        dvr._get_next_char = MagicMock(side_effect=[(-1, b'_key_timeout'), ('x', b'_action_quit')])
        dvr._action_quit = MagicMock(return_value=False)
        dvr._run()
        dvr._action_quit.assert_called_once()

        dvi = self._mk_viewer()
        dvi.curse_window = DummyWindow()
        mm.initscr.return_value = dvi.curse_window
        mm.has_colors.return_value = False
        mm.can_change_color.return_value = False
        dvi._init_screen()
        self.assertTrue(any(call[0] == 'nodelay' for call in dvi.curse_window.calls))

        dvo = self._mk_viewer()
        dvo._init_screen = MagicMock()
        dvo._run = MagicMock()
        with patch('cat_win.src.curses.diffviewer.curses.endwin'):
            dvo._open()
        dvo._run.assert_called_once()

        with patch('cat_win.src.curses.diffviewer.CURSES_MODULE_ERROR', True):
            with patch.object(dv_module, 'logger', logger):
                DiffViewer.loading_failed = False
                DiffViewer.open([('a', 'A')])
                self.assertTrue(DiffViewer.loading_failed)

        with patch('cat_win.src.curses.diffviewer.CURSES_MODULE_ERROR', False):
            with patch.object(DiffViewer, '_open', side_effect=[None, None]):
                dmain = DiffViewer.__new__(DiffViewer)
                dmain.files = [('a', 'A')]
                dmain.open_next_idxs = (0, 0)
                dmain.open_next_hashes = (None, None)
                with patch.object(DiffViewer, '__init__', return_value=None):
                    with patch('cat_win.src.curses.diffviewer.on_windows_os', False):
                        with patch('cat_win.src.curses.diffviewer.signal.signal'):
                            # ensure method is callable in loop-oriented path
                            DiffViewer.open([('a', 'A'), ('b', 'B')])

    def test_action_file_selection_files_mode_and_commits_mode(self):
        dv = self._mk_viewer()
        dv.files = [('a.txt', 'A'), ('b.txt', 'B'), ('c.txt', 'C')]
        dv.diff_files = ['a.txt', 'a.txt']
        dv.display_names = ['A', 'A']
        dv._get_next_char = MagicMock(side_effect=[('', b'_move_key_down'), ('', b'_key_enter')])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            keep_running = dv._action_file_selection()
        self.assertFalse(keep_running)
        self.assertEqual(dv.open_next_idxs, [1, 0])

        commit_a = {'hash': 'aaaa1111', 'date': '2024-01-01', 'author': 'me', 'message': 'A'}
        commit_b = {'hash': 'bbbb2222', 'date': '2024-01-02', 'author': 'me', 'message': 'B'}
        dv2 = self._mk_viewer()
        dv2.files = [('a.txt', 'A'), ('b.txt', 'B')]
        dv2.diff_files = ['a.txt', 'b.txt']
        dv2.display_names = ['A', 'B']
        dv2._get_next_char = MagicMock(side_effect=[
            ('', b'_key_enter'),
            ('', b'_move_key_down'),
            ('', b'_indent_tab'),
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=[[commit_a], [commit_b]]):
            keep_running2 = dv2._action_file_selection()
        self.assertFalse(keep_running2)
        self.assertEqual(dv2.open_next_idxs, [0, 1])
        self.assertIsInstance(dv2.open_next_hashes[0], dict)
        self.assertIsInstance(dv2.open_next_hashes[1], dict)

    def test_action_file_selection_commits_escape_back_to_files(self):
        dv = self._mk_viewer()
        dv.files = [('a.txt', 'A'), ('b.txt', 'B')]
        dv.diff_files = ['a.txt', 'b.txt']
        dv.display_names = ['A', 'B']
        dv._get_next_char = MagicMock(side_effect=[
            ('', b'_key_enter'),
            (ESC_CODE, b'_key_string'),
            (ESC_CODE, b'_key_string'),
        ])
        commit = {'hash': 'aaaa1111', 'date': '2024-01-01', 'author': 'me', 'message': 'A'}
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=[[commit], [commit]]):
            keep_running = dv._action_file_selection()
        self.assertTrue(keep_running)

    def test_search_value_error_and_replace_navigation(self):
        dv = self._mk_viewer()
        dv._get_next_char = MagicMock(side_effect=[('x', b'_key_string'), ('', b'_key_enter'), (ESC_CODE, b'_key_string')])
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=ValueError('bad regex')):
            dv._action_find(0)
        self.assertEqual(dv.search, 'x')

        dv2 = self._mk_viewer()
        dv2.diff_items = [
            DummyDiffItem('1', 'a', 'a', DifflibID.EQUAL),
            DummyDiffItem('2', 'a', 'b', DifflibID.CHANGED),
            DummyDiffItem('3', 'a', 'a', DifflibID.EQUAL),
        ]
        dv2.rpos.row = 0
        dv2._function_replace()
        self.assertEqual(dv2.rpos.row, 1)
        dv2._function_replace_r()
        self.assertEqual(dv2.rpos.row, 1)

    def test_watch_update_error_path_and_background_and_open_exception(self):
        dv = self._mk_viewer()
        dv._watch_text2 = ['old']
        dv._mtime_cache = [1, 2]
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', side_effect=[3, 4]):
            with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', return_value='new'):
                with patch('cat_win.src.curses.diffviewer.DifflibParser', side_effect=[OSError('oops'), DummyDifflibParser([])]):
                    with patch.object(dv_module, 'logger', logger):
                        dv._watch_update()
        self.assertEqual(dv.status_bar_size, 2)
        self.assertEqual(dv.rpos.row, 0)

        dvb = self._mk_viewer()
        with patch('cat_win.src.curses.diffviewer.on_windows_os', True):
            with patch('cat_win.src.curses.diffviewer.save_view_state') as save_state:
                self.assertFalse(dvb._action_background())
        save_state.assert_called_once_with(dvb)

        dvo = self._mk_viewer()
        with patch.object(dvo, '_init_screen', side_effect=RuntimeError('boom')):
            with patch('cat_win.src.curses.diffviewer.curses.endwin') as ew:
                with patch.object(dv_module, 'logger', logger):
                    with self.assertRaises(RuntimeError):
                        dvo._open()
        self.assertTrue(ew.called)

    def test_action_background_unix_path(self):
        dv = self._mk_viewer()
        with patch('cat_win.src.curses.diffviewer.on_windows_os', False):
            with patch('cat_win.src.curses.diffviewer.signal.SIGSTOP', 19, create=True):
                with patch('cat_win.src.curses.diffviewer.save_view_state') as save_state:
                    with patch('cat_win.src.curses.diffviewer.curses.endwin') as endwin_call:
                        with patch('cat_win.src.curses.diffviewer.os.kill') as kill_call:
                            with patch.object(dv, '_init_screen') as init_call:
                                self.assertTrue(dv._action_background())
        save_state.assert_called_once_with(dv)
        endwin_call.assert_called_once()
        kill_call.assert_called_once()
        init_call.assert_called_once()

    def test_init_screen_color_mode_and_get_color(self):
        dv = self._mk_viewer()
        dv.curse_window = DummyWindow()
        mm.initscr.return_value = dv.curse_window
        mm.can_change_color.return_value = True
        mm.has_colors.return_value = True
        mm.COLORS = 16
        mm.color_pair.return_value = 99
        with patch('cat_win.src.curses.diffviewer.os.isatty', return_value=False):
            dv._init_screen()
        self.assertEqual(dv._get_color(1), 99)

    def test_move_helpers_and_ensure_visible_extra(self):
        dv = self._mk_viewer()
        dv.wpos = Position(2, 2)
        dv.rpos = Position(10, 0)
        dv._ensure_rpos_visible()
        self.assertGreaterEqual(dv.wpos.row, 0)

        dv._move_key_ctl_left()
        self.assertEqual(dv.wpos.col, -8)
        dv._move_key_ctl_right()
        self.assertEqual(dv.wpos.col, 2)
        dv._move_key_page_up()
        dv._move_key_page_down()
        dv._move_key_ctl_home()
        self.assertEqual(dv.wpos.row, 0)
        self.assertEqual(dv.wpos.col, 0)
        dv._move_key_ctl_end()
        self.assertGreaterEqual(dv.rpos.row, 0)

    def test_action_jump_hotkey_subpaths(self):
        dv = self._mk_viewer()
        dv._action_background = MagicMock(return_value=True)
        dv._action_resize = MagicMock(return_value=True)
        dv._render_scr = MagicMock()
        dv._get_next_char = MagicMock(side_effect=[
            (5, b'_action_resize'),
            ('9', b'_key_string'),
            ('', b'_key_backspace'),
            ('1', b'_key_string'),
            ('2', b'_key_string'),
            ('', b'_key_ctl_backspace'),
            ('3', b'_key_string'),
            ('', b'_action_jump'),
        ])
        dv._action_jump()
        dv._action_resize.assert_called_once()
        dv._render_scr.assert_called_once()
        self.assertEqual(dv.rpos.row, 2)

        dv2 = self._mk_viewer()
        dv2._get_next_char = MagicMock(return_value=('', b'_action_quit'))
        self.assertTrue(dv2._action_jump())

    def test_action_find_hotkey_and_view_adjust_paths(self):
        class FakeSearch(object):
            def __init__(self, vals, s_len=2, line2=False):
                self._vals = list(vals)
                self.s_len = s_len
                self.line2_matched = line2

            def __iter__(self):
                return self

            def __next__(self):
                if not self._vals:
                    raise StopIteration()
                return self._vals.pop(0)

            next = __next__

        dv = self._mk_viewer()
        dv.half_width = 5
        dv.wpos = Position(0, 0)
        dv.cpos = Position(99, 99)
        dv._action_background = MagicMock(return_value=True)
        dv._action_resize = MagicMock(return_value=True)
        dv._render_scr = MagicMock()
        dv._get_next_char = MagicMock(side_effect=[
            (7, b'_action_resize'),
            ('a', b'_key_string'),
            ('b', b'_key_string'),
            ('', b'_key_backspace'),
            ('C', b'_key_string'),
            ('1', b'_key_string'),
            ('2', b'_key_string'),
            ('', b'_key_ctl_backspace'),
            ('z', b'_key_string'),
            ('', b'_action_find'),
        ])
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=[
            FakeSearch([(1, 1)]),
            FakeSearch([(1, 1), (2, 0)]),
        ]):
            self.assertTrue(dv._action_find(0))
        self.assertEqual(dv.search, 'z')
        self.assertTrue(dv._render_scr.called)

        dv2 = self._mk_viewer()
        dv2.half_width = 5
        dv2.wpos = Position(0, 0)
        dv2.cpos = Position(0, 0)
        dv2.search = 'abc'
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=[
            FakeSearch([(0, 10)]),
            FakeSearch([(0, 10)]),
        ]):
            self.assertTrue(dv2._action_find(1))
        self.assertGreaterEqual(dv2.wpos.col, 1)

    def test_action_file_selection_navigation_and_error_paths(self):
        dv = self._mk_viewer()
        dv.files = [('a.txt', 'A'), ('b.txt', 'B'), ('c.txt', 'CCCCCCCCCCCC')]
        dv.diff_files = ['a.txt', 'b.txt']
        dv.display_names = ['A', 'B']
        dv._action_background = MagicMock(return_value=True)
        dv._action_resize = MagicMock(return_value=True)
        dv._get_next_char = MagicMock(side_effect=[
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_left'),
            ('', b'_move_key_ctl_left'),
            ('', b'_select_key_right'),
            ('', b'_move_key_down'),
            ('', b'_move_key_ctl_down'),
            ('', b'_move_key_up'),
            ('', b'_move_key_ctl_up'),
            ('', b'_action_resize'),
            ('', b'_action_background'),
            (' ', b'_action_file_selection'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            keep_running = dv._action_file_selection()
        self.assertFalse(keep_running)
        self.assertTrue(dv._action_resize.called)
        self.assertTrue(dv._action_background.called)

        dv2 = self._mk_viewer()
        dv2.files = [('a.txt', 'A')]
        dv2.diff_files = ['a.txt', 'a.txt']
        dv2.display_names = ['A', 'A']
        dv2._get_next_char = MagicMock(side_effect=[(ESC_CODE, b'_key_string')])
        original_addstr = dv2.curse_window.addstr

        def addstr_once_fail(*args, **kwargs):
            if len(dv2.curse_window.calls) < 2:
                raise mm.error
            return original_addstr(*args, **kwargs)

        dv2.curse_window.addstr = addstr_once_fail
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertTrue(dv2._action_file_selection())

    def test_function_help_overflow_and_overview_git_branches(self):
        dv = self._mk_viewer()
        dv.curse_window.addstr = MagicMock(side_effect=[mm.error, None])
        dv._get_next_char = MagicMock(return_value=('x', b'_key_string'))
        dv._function_help()

        dv2 = self._mk_viewer()
        dv2.file_commit_hashes = ({'hash': 'abcdef0', 'date': '2024-01-01 00:00:00', 'author': 'me', 'message': 'm1'}, '1234567')
        dv2._mtime_cache = [0, 0]
        dv2.difflibparser_bak = DummyDifflibParser([], equal=2, insert=1, delete=1, changed=1)
        dv2.diff_items = [
            DummyDiffItem('1', 'aX', 'aY', DifflibID.CHANGED, changes1=[1], changes2=[1]),
            DummyDiffItem('2', 'z', 'z', DifflibID.EQUAL),
        ]
        with patch('cat_win.src.curses.diffviewer.get_file_size', return_value=10):
            with patch('cat_win.src.curses.diffviewer._convert_size', return_value='10 B'):
                with patch('cat_win.src.curses.diffviewer.get_file_ctime', return_value=1):
                    with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'a', 'b', DifflibID.CHANGED)])):
                        dv2._function_overview()
        self.assertTrue(dv2.displaying_overview)
        with patch.object(dv2, '_action_quit') as aq:
            dv2._function_overview()
        aq.assert_called_once()

    def test_render_search_highlight_branches_and_watch_run(self):
        dv = self._mk_viewer()
        dv.half_width = 5
        dv.wpos = Position(0, 1)
        dv.cpos = Position(1, 2)
        dv.search_items = {
            (0, 0, False): 3,
            (1, 2, False): 2,
            (1, 2, True): 2,
            (99, 0, False): 2,
        }
        dv._render_scr()
        self.assertEqual(dv.search_items, {})

        dvr = self._mk_viewer()
        dvr.file_commit_hashes = (None, None)
        dvr._render_scr = MagicMock()
        dvr._watch_update = MagicMock()
        dvr._get_next_char = MagicMock(side_effect=[(-1, b'_key_timeout'), ('x', b'_move_key_left'), ('y', b'_action_quit')])
        dvr._action_quit = MagicMock(return_value=False)
        DiffViewer.watch_mode = True
        with patch('cat_win.src.curses.diffviewer.time.time', side_effect=[0, 6, 6]):
            dvr._run()
        self.assertTrue(dvr._watch_update.called)
        self.assertTrue(any(c[0] == 'timeout' and c[1][0] == -1 for c in dvr.curse_window.calls))

    def test_action_find_and_insert_extra_branches(self):
        dv = self._mk_viewer()
        dv._action_background = MagicMock(return_value=True)
        dv._get_next_char = MagicMock(side_effect=[('', b'_action_background'), ('', b'_action_quit')])
        self.assertTrue(dv._action_find(0))
        dv._action_background.assert_called_once()

        dv2 = self._mk_viewer()
        dv2._get_next_char = MagicMock(side_effect=[('a', b'_key_string'), ('', b'_key_backspace'), ('', b'_key_enter')])
        self.assertTrue(dv2._action_find(0))
        self.assertEqual(dv2.search, '')

        dvi = self._mk_viewer()
        dvi._action_background = MagicMock(return_value=True)
        dvi._action_resize = MagicMock(return_value=True)
        dvi._render_scr = MagicMock()
        dvi._setup_file = MagicMock()
        dvi._get_next_char = MagicMock(side_effect=[
            ('x', b'_key_string'),
            ('1', b'_key_string'),
            ('', b'_key_backspace'),
            ('2', b'_key_string'),
            ('', b'_key_ctl_backspace'),
            ('0', b'_key_string'),
            ('.', b'_key_string'),
            ('7', b'_key_string'),
            ('', b'_action_resize'),
            ('', b'_action_background'),
            ('', b'_key_enter'),
        ])
        self.assertTrue(dvi._action_insert())
        self.assertAlmostEqual(dvi.difflibparser_cutoff, 0.7)
        self.assertTrue(dvi._setup_file.called)
        self.assertTrue(dvi._render_scr.called)

    def test_watch_update_early_returns(self):
        dv = self._mk_viewer()
        dv.displaying_overview = True
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', return_value=3):
            dv._watch_update()
        self.assertEqual(dv.status_bar_size, 1)

        dv2 = self._mk_viewer()
        dv2.displaying_overview = False
        dv2._mtime_cache = [1, 5]
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', return_value=5):
            dv2._watch_update()
        self.assertEqual(dv2.status_bar_size, 1)

        dv3 = self._mk_viewer()
        dv3._mtime_cache = [1, 2]
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', return_value=3):
            with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', side_effect=UnicodeError('enc')):
                dv3._watch_update()
        self.assertEqual(dv3.status_bar_size, 1)

    def test_file_selection_index_and_commit_edge_paths(self):
        commit_x = {'hash': 'xx11111', 'date': '2024-01-01', 'author': 'u', 'message': 'x'}
        commit_y = {'hash': 'yy22222', 'date': '2024-01-02', 'author': 'u', 'message': 'y'}

        dv = self._mk_viewer()
        dv.files = [('a.txt', 'A'), ('b.txt', 'B')]
        dv.diff_files = ['a.txt', 'b.txt']
        dv.display_names = ['different-a', 'different-b']
        dv.file_commit_hashes = ('does-not-exist', {'hash': 'does-not-exist'})
        dv._get_next_char = MagicMock(side_effect=[
            ('', b'_key_enter'),
            ('', b'_move_key_ctl_right'),
            ('', b'_move_key_right'),
            ('', b'_move_key_ctl_left'),
            ('', b'_move_key_left'),
            ('', b'_key_enter'),
        ])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=[[commit_x], [commit_y]]):
            keep_running = dv._action_file_selection()
        self.assertFalse(keep_running)
        self.assertIsNotNone(dv.open_next_idxs)

    def test_get_next_char_error_and_render_status_exception(self):
        dv = self._mk_viewer()

        def raise_curses_error():
            raise mm.error

        dv.curse_window.get_wch = raise_curses_error
        self.assertEqual(dv._get_next_char(), (-1, b'_key_timeout'))

        dv2 = self._mk_viewer()
        dv2.curse_window.addstr = MagicMock(side_effect=mm.error)
        dv2._render_status_bar(5, 20)

    def test_init_screen_set_escdelay_and_low_color_branches(self):
        d1 = self._mk_viewer()
        d1.curse_window = DummyWindow()
        mm.initscr.return_value = d1.curse_window
        mm.can_change_color.return_value = False
        mm.set_escdelay = MagicMock()
        with patch.object(dv_module.sys, 'version_info', (3, 10, 0)):
            d1._init_screen()
        self.assertTrue(mm.set_escdelay.called)

        d2 = self._mk_viewer()
        d2.curse_window = DummyWindow()
        mm.initscr.return_value = d2.curse_window
        mm.can_change_color.return_value = True
        mm.COLORS = 8
        mm.init_pair = MagicMock()
        with patch('cat_win.src.curses.diffviewer.os.isatty', return_value=False):
            d2._init_screen()
        self.assertTrue(mm.init_pair.called)

        d3 = self._mk_viewer()
        d3.curse_window = DummyWindow()
        mm.initscr.return_value = d3.curse_window
        mm.can_change_color.return_value = False
        with patch.object(dv_module.sys, 'version_info', (3, 8, 0)):
            with patch('cat_win.src.curses.diffviewer.os.environ.setdefault') as setdefault:
                d3._init_screen()
        setdefault.assert_called_with('ESCDELAY', '25')

    def test_open_loading_failed_and_unix_open_loop(self):
        DiffViewer.loading_failed = True
        DiffViewer.open([('a', 'A')])

        captured = []
        open_count = {'n': 0}

        def fake_init(self, files, file_idxs=None, file_commit_hashes=(None, None)):
            self.files = files
            self.file_commit_hashes = file_commit_hashes
            self.open_next_idxs = None
            self.open_next_hashes = (None, None)
            self._open_counter = 0
            captured.append((file_idxs, file_commit_hashes))

        def fake_open(self, *_, **__):
            if open_count['n'] == 0:
                self.open_next_idxs = (1, 0)
                self.open_next_hashes = ('h1', 'h2')
            else:
                self.open_next_idxs = None
            open_count['n'] += 1

        with patch('cat_win.src.curses.diffviewer.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.diffviewer.on_windows_os', False):
                with patch('cat_win.src.curses.diffviewer.signal.signal') as sig:
                    with patch('cat_win.src.curses.diffviewer.signal.SIGTSTP', 20, create=True):
                        with patch('cat_win.src.curses.diffviewer.signal.SIG_IGN', 1, create=True):
                            with patch.object(DiffViewer, '__init__', fake_init):
                                with patch.object(DiffViewer, '_open', fake_open):
                                    DiffViewer.loading_failed = False
                                    DiffViewer.open([('a', 'A'), ('b', 'B')])
        self.assertTrue(sig.called)
        self.assertGreaterEqual(len(captured), 2)

    def test_setup_helpers_and_ratio_uncovered_branches(self):
        dv = self._mk_viewer()
        dv.file_commit_hashes = ('h1', 'h2')
        with patch('cat_win.src.curses.diffviewer.GitHelper.get_git_file_content_at_commit', side_effect=[OSError('bad-left'), ['ok-right']]):
            with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'a', 'b', DifflibID.CHANGED)])):
                dv._setup_file()
        self.assertIn('<GIT_ERROR>', dv.display_names[0])
        self.assertIn('GIT:', dv.display_names[1])

        dv.diff_items = []
        self.assertEqual(dv.lllen(), 0)
        self.assertEqual(dv._get_diff_ratio(0), 100.0)

        dv.diff_items = [DummyDiffItem('1', 'a', 'a', DifflibID.EQUAL)] * 60
        dv.wpos = Position(0, 0)
        dv.rpos = Position(50, 0)
        dv.getxymax = lambda: (10, 80)
        dv._ensure_rpos_visible()
        self.assertEqual(dv.wpos.row, 41)

    @patch.object(dv_module, 'logger', logger)
    def test_action_find_insert_and_replace_r_remaining_paths(self):
        class FakeSearch(object):
            def __init__(self, vals, s_len=1, line2=False):
                self._vals = list(vals)
                self.s_len = s_len
                self.line2_matched = line2

            def __iter__(self):
                return self

            def __next__(self):
                if not self._vals:
                    raise StopIteration()
                return self._vals.pop(0)

            next = __next__

        dv = self._mk_viewer()
        dv.search = 'x'
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=ValueError('bad')):
            self.assertTrue(dv._action_find(1))

        dv2 = self._mk_viewer()
        dv2.search = 'x'
        dv2.half_width = 5
        dv2.cpos = Position(99, 99)
        dv2.getxymax = lambda: (3, 60)
        with patch('cat_win.src.curses.diffviewer.search_iter_diff_factory', side_effect=[
            FakeSearch([(3, 1)]),
            FakeSearch([(3, 1), (20, 1)]),
        ]):
            self.assertTrue(dv2._action_find(-1))
        self.assertEqual(dv2.wpos.row, 1)
        self.assertEqual(dv2.wpos.col, 0)

        dvi = self._mk_viewer()
        dvi._get_next_char = MagicMock(return_value=('', b'_action_quit'))
        self.assertTrue(dvi._action_insert())

        dvi2 = self._mk_viewer()
        dvi2._get_next_char = MagicMock(side_effect=[(7, b'_action_insert')])
        self.assertTrue(dvi2._action_insert())

        dvi3 = self._mk_viewer()
        dvi3._get_next_char = MagicMock(side_effect=[(5, b'_key_string'), ('', b'_action_quit')])
        self.assertTrue(dvi3._action_insert())

        dvi4 = self._mk_viewer()
        dvi4._get_next_char = MagicMock(side_effect=[
            ('1', b'_key_string'),
            ('2', b'_key_string'),
            ('', b'_key_enter'),
        ])
        self.assertTrue(dvi4._action_insert())

        dvr = self._mk_viewer()
        dvr.diff_items = [
            DummyDiffItem('1', 'a', 'a', DifflibID.EQUAL),
            DummyDiffItem('2', 'a', 'b', DifflibID.CHANGED),
            DummyDiffItem('3', 'a', 'a', DifflibID.EQUAL),
        ]
        dvr.rpos.row = 0
        dvr._function_replace_r()
        self.assertEqual(dvr.rpos.row, 1)

    def test_watch_selection_overview_render_init_and_open_windows_paths(self):
        dvw = self._mk_viewer()
        dvw._watch_text2 = ['a']
        dvw._mtime_cache = [1, 1]
        with patch('cat_win.src.curses.diffviewer.get_file_mtime', side_effect=[2, 3]):
            with patch('cat_win.src.curses.diffviewer.IoHelper.read_file', return_value='b\nc'):
                with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'a', 'b', DifflibID.CHANGED)])):
                    dvw._watch_update()
        self.assertEqual(dvw.status_bar_size, 1)

        dv0 = self._mk_viewer()
        dv0.files = [('a.txt', 'A')]
        dv0.diff_files = ['missing-left', 'missing-right']
        dv0.display_names = ['L', 'R']
        dv0._get_next_char = MagicMock(side_effect=[(ESC_CODE, b'_key_string')])
        self.assertTrue(dv0._action_file_selection())

        dv1 = self._mk_viewer()
        dv1.files = [('a.txt', 'A')] * 40
        dv1.getxymax = lambda: (3, 40)
        dv1._get_next_char = MagicMock(side_effect=[('', b'_action_quit')])
        self.assertTrue(dv1._action_file_selection())

        dv2 = self._mk_viewer()
        dv2.files = [('a.txt', 'A')] * 40
        dv2.getxymax = lambda: (3, 40)
        dv2._get_next_char = MagicMock(side_effect=[('', b'_move_key_ctl_down'), ('', b'_select_key_right'), (ESC_CODE, b'_key_string')])
        self.assertTrue(dv2._action_file_selection())

        dv3 = self._mk_viewer()
        dv3.files = [('a.txt', 'A'), ('b.txt', 'B')]
        dv3._get_next_char = MagicMock(side_effect=[('', b'_key_enter'), ('', b'_indent_tab'), ('', b'_move_key_up'), (ESC_CODE, b'_key_string'), (ESC_CODE, b'_key_string')])
        c = {'hash': 'h', 'date': '2024', 'author': 'u', 'message': 'm'}
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=[[c], None]):
            self.assertTrue(dv3._action_file_selection())

        dv4 = self._mk_viewer()
        dv4.files = [('a.txt', 'A'), ('b.txt', 'B')]
        dv4._get_next_char = MagicMock(side_effect=[('', b'_key_enter')])
        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=OSError('git')):
            self.assertTrue(dv4._action_file_selection())

        dv5 = self._mk_viewer()
        dv5.file_commit_hashes = ('1234567', {'hash': 'abcdef0', 'date': '2024-01-01 00:00:00', 'author': 'u', 'message': 'm'})
        with patch('cat_win.src.curses.diffviewer.get_file_size', return_value=10):
            with patch('cat_win.src.curses.diffviewer._convert_size', return_value='10 B'):
                with patch('cat_win.src.curses.diffviewer.get_file_ctime', return_value=1):
                    with patch('cat_win.src.curses.diffviewer.DifflibParser', return_value=DummyDifflibParser([DummyDiffItem('1', 'a', 'b', DifflibID.CHANGED)])):
                        dv5._function_overview()
        self.assertTrue(dv5.displaying_overview)

        dvr = self._mk_viewer()
        dvr.diff_items = [
            DummyDiffItem('1', 'abcdefghijk', 'abXYefghijk', DifflibID.CHANGED, changes1=[0], changes2=[50]),
        ]
        dvr.wpos = Position(0, 5)
        dvr.half_width = 3
        dvr.search_items = {
            (0, 9, False): 2,
            (0, 3, False): 4,
        }
        dvr._render_scr()

        di = self._mk_viewer()
        di.curse_window = DummyWindow()
        mm.initscr.return_value = di.curse_window
        mm.can_change_color.return_value = True
        mm.COLORS = 16
        mm.COLOR_BLACK = 0
        mm.COLOR_WHITE = 7
        mm.COLOR_RED = 1
        mm.COLOR_GREEN = 2
        mm.COLOR_MAGENTA = 5
        mm.COLOR_BLUE = 4
        mm.COLOR_CYAN = 6

        raised_for = set()

        def init_pair_side_effect(pair_id, *_args):
            if pair_id in (4, 6, 9, 14, 15) and pair_id not in raised_for:
                raised_for.add(pair_id)
                raise mm.error
            return None

        mm.init_pair = MagicMock(side_effect=init_pair_side_effect)
        with patch('cat_win.src.curses.diffviewer.on_windows_os', False):
            di._init_screen()
        self.assertTrue(mm.use_default_colors.called)

        created = []
        open_count = {'n': 0}

        def fake_init(self, files, file_idxs=None, file_commit_hashes=(None, None)):
            self.files = files
            self.file_commit_hashes = file_commit_hashes
            self.open_next_hashes = (None, None)
            if open_count['n'] == 0:
                self.open_next_idxs = (1, 0)
            else:
                self.open_next_idxs = None
            created.append(self)
            open_count['n'] += 1

        def fake_open(self, *_, **__):
            return None

        with patch('cat_win.src.curses.diffviewer.CURSES_MODULE_ERROR', False):
            with patch('cat_win.src.curses.diffviewer.on_windows_os', True):
                with patch.object(DiffViewer, '__init__', fake_init):
                    with patch.object(DiffViewer, '_open', fake_open):
                        DiffViewer.loading_failed = False
                        DiffViewer.open([('a', 'A'), ('b', 'B')])
        self.assertGreaterEqual(len(created), 2)
        self.assertTrue(callable(getattr(created[0], '_action_background', None)))
        self.assertTrue(callable(getattr(created[1], '_action_background', None)))

    def test_final_edge_branches_for_full_coverage(self):
        dvj = self._mk_viewer()
        dvj._action_background = MagicMock(return_value=True)
        dvj._get_next_char = MagicMock(side_effect=[
            ('', b'_action_background'),
            ('', b'_action_quit'),
        ])
        self.assertTrue(dvj._action_jump())
        dvj._action_background.assert_called_once()

        dvf = self._mk_viewer()
        dvf.files = [('a.txt', 'A')] * 50
        dvf.diff_files = ['a.txt', 'a.txt']
        dvf.display_names = ['A', 'A']
        dvf.getxymax = lambda: (3, 40)

        original_addstr = dvf.curse_window.addstr

        def addstr_fail_branches(y, x, *args):
            if y == 0 and x == 0:
                raise mm.error
            if y == 4 and x == 0:
                raise mm.error
            return original_addstr(y, x, *args)

        dvf.curse_window.addstr = addstr_fail_branches
        dvf._get_next_char = MagicMock(side_effect=[
            ('', b'_move_key_down'),
            ('', b'_action_quit'),
        ])
        self.assertTrue(dvf._action_file_selection())

        dvr = self._mk_viewer()
        dvr.diff_items = [
            DummyDiffItem('1', 'abcdefghijk', 'abXYefghijk', DifflibID.CHANGED, changes1=[-1, 999], changes2=[1]),
        ]
        dvr.wpos = Position(0, 0)
        dvr.half_width = 3
        dvr._render_scr()

        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'curses':
                raise ImportError('forced')
            return real_import(name, globals, locals, fromlist, level)

        with patch('builtins.__import__', side_effect=fake_import):
            ns = runpy.run_path(dv_module.__file__, run_name='__cov_diffviewer_importerror__')
        self.assertTrue(ns['CURSES_MODULE_ERROR'])

    def test_file_selection_status_addstr_exception_path(self):
        dv = self._mk_viewer()
        dv.files = [('a.txt', 'A')]
        dv.diff_files = ['a.txt', 'a.txt']
        dv.display_names = ['A', 'A']
        dv._get_next_char = MagicMock(side_effect=[('', b'_action_quit')])

        original_addstr = dv.curse_window.addstr

        def addstr_raise_on_status(y, x, *args):
            if args and isinstance(args[0], str) and args[0].startswith('Select two files'):
                raise mm.error
            return original_addstr(y, x, *args)

        dv.curse_window.addstr = addstr_raise_on_status
        self.assertTrue(dv._action_file_selection())
