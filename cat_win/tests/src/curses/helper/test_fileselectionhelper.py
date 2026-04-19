from unittest import TestCase
from unittest.mock import MagicMock, patch
import os

from cat_win.src.const.escapecodes import ESC_CODE


from cat_win.src.curses.helper import fileselectionhelper
if fileselectionhelper.CURSES_MODULE_ERROR:
    setattr(fileselectionhelper, 'curses', None)
from cat_win.src.curses.helper.fileselectionhelper import run_file_selection


mm = MagicMock()
mm.error = Exception
mm.curs_set = MagicMock()


class _SingleOwner:
    def __init__(self):
        self.curse_window = MagicMock()
        self.files = [('a.txt', 'A'), ('b.txt', 'B')]
        self.file = 'a.txt'
        self.display_name = 'A'
        self.file_commit_hash = None
        self.open_next_idx = None
        self.status_bar_size = 1
        self._color_calls = []
        self.get_char = iter([])

    def getxymax(self):
        return (6, 40)

    def _get_color(self, value):
        self._color_calls.append(value)
        return value


class _SplitOwner:
    def __init__(self):
        self.curse_window = MagicMock()
        self.files = [('a.txt', 'A'), ('b.txt', 'B')]
        self.diff_files = ['a.txt', 'b.txt']
        self.display_names = ['A', 'B']
        self.file_commit_hashes = (None, None)
        self.open_next_idxs = None
        self.open_next_hashes = (None, None)
        self.status_bar_size = 1
        self._color_calls = []
        self._get_next_char = lambda: ('', b'_action_quit')

    def getxymax(self):
        return (6, 40)

    def _get_color(self, value):
        self._color_calls.append(value)
        return value


@patch('cat_win.src.curses.helper.fileselectionhelper.curses', mm)
class TestFileSelectionHelper(TestCase):
    def test_single_panel_history_selection_updates_open_next_idx(self):
        owner = _SingleOwner()
        owner.get_char = iter([
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ])

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertTrue(run_file_selection(owner))

        self.assertEqual(owner.open_next_idx, 1)

    def test_single_panel_no_change_returns_false(self):
        owner = _SingleOwner()
        owner.get_char = iter([
            ('', b'_key_enter'),
        ])

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertFalse(run_file_selection(owner))

        self.assertIsNone(owner.open_next_idx)

    def test_split_panel_updates_indexes_and_hashes(self):
        owner = _SplitOwner()
        commit_a = {'hash': 'aaaa1111', 'date': '2024-01-01', 'author': 'me', 'message': 'A'}
        commit_b = {'hash': 'bbbb2222', 'date': '2024-01-02', 'author': 'me', 'message': 'B'}
        owner._get_next_char = iter([
            ('', b'_key_enter'),
            ('', b'_move_key_down'),
            ('', b'_indent_tab'),
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ]).__next__

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=[[commit_a], [commit_b]]):
            self.assertTrue(run_file_selection(owner, split_panel=True))

        self.assertEqual(owner.open_next_idxs, [0, 1])
        self.assertIsInstance(owner.open_next_hashes[0], dict)
        self.assertIsInstance(owner.open_next_hashes[1], dict)

    def test_split_panel_no_history_returns_true_when_unchanged(self):
        owner = _SplitOwner()
        owner._get_next_char = iter([
            (ESC_CODE, b'_key_string'),
        ]).__next__

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', side_effect=OSError('git')):
            self.assertFalse(run_file_selection(owner, split_panel=True))

        self.assertIsNone(owner.open_next_idxs)

    def test_large_file_list_uses_path_parts_browser(self):
        owner = _SingleOwner()
        owner.files = [
            ('root1.txt', 'root1'),
            ('root2.txt', 'root2'),
            ('folder/a.txt', 'a'),
            ('folder/b.txt', 'b'),
            ('folder/sub/c.txt', 'c'),
            ('folder/sub/d.txt', 'd'),
            ('other/e.txt', 'e'),
            ('other/f.txt', 'f'),
            ('x/g.txt', 'g'),
            ('y/h.txt', 'h'),
            ('alpha/i.txt', 'i'),
            ('beta/j.txt', 'j'),
            ('gamma/k.txt', 'k'),
            ('delta/l.txt', 'l'),
            ('epsilon/m.txt', 'm'),
            ('z/n.txt', 'n'),
            ('omega/o.txt', 'o'),
        ]
        owner.file = 'root1.txt'
        owner.display_name = 'root1'
        owner.get_char = iter([
            (ESC_CODE, b'_key_string'),
        ])

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertFalse(run_file_selection(owner))

        rendered_texts = [
            call[0][2]
            for call in owner.curse_window.addstr.call_args_list
            if len(call[0]) >= 3 and isinstance(call[0][2], str)
        ]
        # Path-parts mode renders directory entries with a trailing path separator.
        self.assertTrue(any(text.strip().endswith(os.sep) for text in rendered_texts))

    def test_small_file_list_stays_flat(self):
        owner = _SingleOwner()
        owner.files = [
            ('folder/a.txt', 'A'),
            ('folder/b.txt', 'B'),
            ('folder/sub/c.txt', 'C'),
            ('folder/sub/d.txt', 'D'),
            ('other/e.txt', 'E'),
            ('other/f.txt', 'F'),
            ('x/g.txt', 'G'),
            ('y/h.txt', 'H'),
            ('z/i.txt', 'I'),
        ]
        owner.file = 'folder/a.txt'
        owner.display_name = 'A'
        owner.get_char = iter([
            ('', b'_move_key_down'),
            ('', b'_move_key_down'),
            ('', b'_key_enter'),
        ])

        with patch('cat_win.src.curses.helper.fileselectionhelper.GitHelper.get_git_file_history', return_value=None):
            self.assertTrue(run_file_selection(owner))

        rendered_texts = [
            call[0][2]
            for call in owner.curse_window.addstr.call_args_list
            if len(call[0]) >= 3 and isinstance(call[0][2], str)
        ]
        self.assertFalse(any(text.strip().endswith(os.sep) for text in rendered_texts))
        self.assertEqual(owner.open_next_idx, 2)
