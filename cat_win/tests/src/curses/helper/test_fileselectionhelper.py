from unittest import TestCase
from unittest.mock import MagicMock, patch

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
