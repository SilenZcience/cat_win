from unittest.mock import call, patch, MagicMock
from unittest import skipUnless, TestCase
import importlib.util
import os
import signal
import sys

from cat_win.src.curses.helper import curseshelper
if not hasattr(curseshelper, 'curses'):
    setattr(curseshelper, 'curses', None)
from cat_win.src.curses.helper.curseshelper import (
    Position, History, frepr,
    release_sigwinch, resize_term,
)
from cat_win.tests.mocks.edit import EditorHistoryMock

mm = MagicMock()

UNIX_SIGWINCH = getattr(signal, 'SIGWINCH', 28)


class TestSigwinchHandover(TestCase):
    @skipUnless(hasattr(signal, 'SIGWINCH'), 'unix only: SIGWINCH does not exist on windows')
    def test_hands_sigwinch_back_to_ncurses(self):
        with patch('cat_win.src.curses.helper.curseshelper.signal.signal') as sig:
            release_sigwinch()
        sig.assert_called_once_with(signal.SIGWINCH, signal.SIG_DFL)

    def test_is_a_noop_without_sigwinch(self):
        with patch.object(curseshelper, 'SIGWINCH', None):
            with patch('cat_win.src.curses.helper.curseshelper.signal.signal') as sig:
                release_sigwinch()
        sig.assert_not_called()

    def test_survives_a_refused_signal_call(self):
        for error in (ValueError('main thread'), OSError('not permitted')):
            with patch('cat_win.src.curses.helper.curseshelper.signal.signal', side_effect=error):
                release_sigwinch()


class TestResizeTerm(TestCase):
    def setUp(self):
        patcher = patch.object(curseshelper, 'SIGWINCH', UNIX_SIGWINCH)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _win(self, rows=24, cols=80):
        win = MagicMock()
        win.getmaxyx.return_value = (rows, cols)
        return win

    def _terminal(self, columns, lines):
        return os.terminal_size((columns, lines))

    def _curses_stub(self, resize_term_error=None):
        stub = MagicMock()
        stub.error = Exception
        if resize_term_error is not None:
            stub.resize_term.side_effect = resize_term_error
        return stub

    def test_resizes_to_the_real_terminal_size(self):
        win = self._win(24, 80)
        with patch.object(curseshelper, 'curses', self._curses_stub()):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(91, 31)):
                self.assertTrue(resize_term(win))
        win.clear.assert_called_once()

    def test_does_nothing_when_the_size_already_matches(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        with patch.object(curseshelper, 'curses', curses_stub):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(80, 24)):
                self.assertFalse(resize_term(win))
        curses_stub.resize_term.assert_not_called()
        win.clear.assert_not_called()

    def test_resizes_again_after_the_terminal_grew_back(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        with patch.object(curseshelper, 'curses', curses_stub):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(60, 20)):
                self.assertTrue(resize_term(win))
            win.getmaxyx.return_value = (20, 60)
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(80, 24)):
                self.assertTrue(resize_term(win))
        self.assertEqual(
            curses_stub.resize_term.call_args_list,
            [call(20, 60), call(24, 80)]
        )

    def test_passes_lines_and_columns_in_that_order(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        with patch.object(curseshelper, 'curses', curses_stub):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(91, 31)):
                resize_term(win)
        curses_stub.resize_term.assert_called_once_with(31, 91)
        curses_stub.resizeterm.assert_not_called()

    def test_survives_a_failing_curses(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub(resize_term_error=Exception('boom'))
        with patch.object(curseshelper, 'curses', curses_stub):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(91, 31)):
                self.assertFalse(resize_term(win))
        win.clear.assert_not_called()

    def test_is_a_noop_without_a_queryable_terminal(self):
        # stdout may not be a terminal, and os.get_terminal_size may be absent.
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        for error in (OSError('not a terminal'), AttributeError('no such function')):
            with patch.object(curseshelper, 'curses', curses_stub):
                with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                           side_effect=error):
                    self.assertFalse(resize_term(win))
        curses_stub.resize_term.assert_not_called()
        win.clear.assert_not_called()

    def test_is_a_noop_on_an_unknown_size(self):
        # A non-console handle on Windows reports 0x0.
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        for columns, lines in ((0, 0), (91, 0), (0, 31), (-1, 24)):
            with patch.object(curseshelper, 'curses', curses_stub):
                with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                           return_value=self._terminal(columns, lines)):
                    self.assertFalse(resize_term(win))
        curses_stub.resize_term.assert_not_called()
        win.clear.assert_not_called()

    def test_is_a_noop_without_curses(self):
        win = self._win(24, 80)
        with patch.object(curseshelper, 'CURSES_MODULE_ERROR', True):
            with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size',
                       return_value=self._terminal(91, 31)):
                self.assertFalse(resize_term(win))
        win.clear.assert_not_called()


class TestResizeTermWithoutSigwinch(TestCase):
    def _win(self, rows=31, cols=91):
        win = MagicMock()
        win.getmaxyx.return_value = (rows, cols)
        return win

    def _curses_stub(self, resize_term_error=None):
        stub = MagicMock()
        stub.error = Exception
        if resize_term_error is not None:
            stub.resize_term.side_effect = resize_term_error
        return stub

    def test_uses_getmaxyx_instead_of_get_terminal_size(self):
        win = self._win(31, 91)
        curses_stub = self._curses_stub()
        with patch.object(curseshelper, 'SIGWINCH', None):
            with patch.object(curseshelper, 'curses', curses_stub):
                with patch('cat_win.src.curses.helper.curseshelper.os.get_terminal_size') as gts:
                    self.assertTrue(resize_term(win))
        gts.assert_not_called()
        curses_stub.resize_term.assert_called_once_with(31, 91)
        curses_stub.resizeterm.assert_not_called()
        win.clear.assert_called_once()

    def test_resizes_even_though_getmaxyx_matches(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub()
        with patch.object(curseshelper, 'SIGWINCH', None):
            with patch.object(curseshelper, 'curses', curses_stub):
                self.assertTrue(resize_term(win))
        curses_stub.resize_term.assert_called_once_with(24, 80)
        win.clear.assert_called_once()

    def test_survives_a_failing_curses(self):
        win = self._win(24, 80)
        curses_stub = self._curses_stub(resize_term_error=Exception('boom'))
        with patch.object(curseshelper, 'SIGWINCH', None):
            with patch.object(curseshelper, 'curses', curses_stub):
                self.assertFalse(resize_term(win))
        win.clear.assert_not_called()

    def test_is_a_noop_without_curses(self):
        win = self._win(24, 80)
        with patch.object(curseshelper, 'SIGWINCH', None):
            with patch.object(curseshelper, 'CURSES_MODULE_ERROR', True):
                self.assertFalse(resize_term(win))
        win.clear.assert_not_called()

@patch('cat_win.src.curses.helper.curseshelper.curses', mm)
class TestCursesHelper(TestCase):
    def test_frepr(self):
        self.assertEqual(frepr('test'), 'test')
        self.assertEqual(frepr('test\ntest'), 'test\\ntest')
        self.assertEqual(frepr('test\ttest'), 'test\\ttest')
        self.assertEqual(frepr('test\ntest\ttest'), 'test\\ntest\\ttest')

    def test_position_get_set(self):
        pos = Position(2, 3)
        self.assertEqual(pos.get_pos(), (2, 3))
        pos.set_pos((7, 11))
        self.assertEqual(pos.get_pos(), (7, 11))

    def _load_curseshelper_module(self, module_name, modules):
        file_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', '..', 'src', 'curses', 'helper', 'curseshelper.py'
        ))
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules, clear=False):
            spec.loader.exec_module(module)
        return module

    def test_importerror_on_curses_is_ignored(self):
        real_import = __import__

        def _fake_import(name, globals_=None, locals_=None, fromlist=(), level=0):
            if name == 'curses':
                raise ImportError('forced')
            return real_import(name, globals_, locals_, fromlist, level)

        file_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', '..', 'src', 'curses', 'helper', 'curseshelper.py'
        ))
        spec = importlib.util.spec_from_file_location('curseshelper_cov_no_curses', file_path)
        module = importlib.util.module_from_spec(spec)
        with patch('builtins.__import__', side_effect=_fake_import):
            spec.loader.exec_module(module)

        self.assertFalse(hasattr(module, 'curses'))


@patch('cat_win.src.curses.helper.curseshelper.curses', mm)
class TestHistory(TestCase):
    def _mk(self, stack_size=20):
        return History(stack_size=stack_size), EditorHistoryMock()

    def test_stack_size_is_at_least_one(self):
        history = History(stack_size=0)
        self.assertEqual(history.stack_size, 1)

    def test_add_ignores_unknown_actions_and_empty_text(self):
        history, _ = self._mk()
        history.add(
            b'_not_reversible', False,
            (0, 0), (0, 1),
            (0, 0), (0, 1),
            False, False,
            'x'
        )
        history.add(
            b'_key_string', False,
            (0, 0), (0, 1),
            (0, 0), (0, 1),
            False, False,
            None
        )
        self.assertEqual(len(history._stack_undo), 0)

    def test_add_clears_redo_when_adding_to_undo(self):
        history, _ = self._mk()
        history.add(
            b'_key_string', False,
            (0, 0), (0, 1),
            (0, 0), (0, 0),
            False, False,
            'a', stack_type='redo'
        )
        self.assertEqual(len(history._stack_redo), 1)

        history.add(
            b'_key_string', False,
            (0, 1), (0, 2),
            (0, 0), (0, 0),
            False, False,
            'b'
        )
        self.assertEqual(len(history._stack_redo), 0)
        self.assertEqual(len(history._stack_undo), 1)

    def test_add_honors_stack_size_limit_fifo(self):
        history, _ = self._mk(stack_size=2)
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 1), (0, 2), (0, 0), (0, 0), False, False, 'b')
        history.add(b'_key_string', False, (0, 2), (0, 3), (0, 0), (0, 0), False, False, 'c')

        self.assertEqual(len(history._stack_undo), 2)
        self.assertEqual(history._stack_undo[0].action_text, ('b',))
        self.assertEqual(history._stack_undo[1].action_text, ('c',))

    def test_clear_empties_both_stacks(self):
        history, _ = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 1), (0, 2), (0, 0), (0, 0), False, False, 'b', stack_type='redo')

        history.clear()
        self.assertEqual(history._stack_undo, [])
        self.assertEqual(history._stack_redo, [])

    def test_undo_and_redo_noop_on_empty_stack(self):
        history, editor = self._mk()
        history.undo(editor)
        history.redo(editor)
        self.assertEqual(editor.calls, [])

    def test_undo_uses_reverse_action_mapping_and_restores_state(self):
        history, editor = self._mk()
        history.add(
            b'_key_string', False,
            (1, 2), (1, 3),
            (4, 5), (6, 7),
            True, False,
            'x'
        )

        history.undo(editor)

        self.assertEqual(editor.calls[0][0], '_key_backspace')
        self.assertEqual(editor.calls[0][1], ('x',))
        self.assertEqual(editor.calls[0][2], (1, 3))
        self.assertEqual(editor.calls[0][3], (6, 7))
        self.assertEqual(editor.calls[0][4], False)
        self.assertEqual(editor.cpos.get_pos(), (1, 2))
        self.assertEqual(editor.spos.get_pos(), (4, 5))
        self.assertTrue(editor.selecting)

    def test_undo_uses_multiline_reverse_mapping_when_size_changes(self):
        history, editor = self._mk()
        history.add(
            b'_key_backspace', True,
            (2, 0), (1, 5),
            (0, 0), (0, 0),
            False, False,
            'x'
        )

        history.undo(editor)
        self.assertEqual(editor.calls[0][0], '_key_enter')

    def test_action_str_repr_contains_core_parts(self):
        history, _ = self._mk()
        history.add(
            b'_key_string', False,
            (0, 0), (0, 1),
            (0, 0), (0, 0),
            False, False,
            'x'
        )
        action = history._stack_undo[-1]
        text = str(action)
        self.assertIn("b'_key_string'", text)
        self.assertIn("('x',)", text)
        self.assertIn("False(0, 0)(0, 1)", text)

    def test_add_with_invalid_stack_type_returns_without_changes(self):
        history, _ = self._mk()
        history.add(
            b'_key_string', False,
            (0, 0), (0, 1),
            (0, 0), (0, 0),
            False, False,
            'x', stack_type='invalid'
        )
        self.assertEqual(history._stack_undo, [])
        self.assertEqual(history._stack_redo, [])

    def test_undo_asserts_when_reverse_action_missing(self):
        history, editor = self._mk()
        broken_action = curseshelper._Action(
            b'_not_mapped',
            False,
            (0, 0), (0, 1),
            (0, 0), (0, 0),
            False, False,
            'x'
        )
        with self.assertRaises(AssertionError):
            history._undo(editor, broken_action)

    def test_redo_replays_action_and_restores_post_state(self):
        history, editor = self._mk()
        history.add(
            b'_key_string', False,
            (0, 0), (0, 1),
            (0, 0), (0, 1),
            False, True,
            'a'
        )

        history.undo(editor)
        editor.calls.clear()
        history.redo(editor)

        self.assertEqual(editor.calls[0][0], '_key_string')
        self.assertEqual(editor.calls[0][1], ('a',))
        self.assertEqual(editor.calls[0][2], (0, 0))
        self.assertEqual(editor.calls[0][3], (0, 0))
        self.assertFalse(editor.calls[0][4])
        self.assertEqual(editor.cpos.get_pos(), (0, 1))
        self.assertEqual(editor.spos.get_pos(), (0, 1))
        self.assertTrue(editor.selecting)

    def test_undo_stacks_contiguous_non_whitespace_actions(self):
        history, editor = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 1), (0, 2), (0, 0), (0, 0), False, False, 'b')

        history.undo(editor)
        self.assertEqual([c[1][0] for c in editor.calls], ['b', 'a'])
        self.assertEqual(len(history._stack_undo), 0)
        self.assertEqual(len(history._stack_redo), 2)

    def test_redo_stacks_contiguous_non_whitespace_actions(self):
        history, editor = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 1), (0, 2), (0, 0), (0, 0), False, False, 'b')
        history.undo(editor)
        editor.calls.clear()

        history.redo(editor)
        self.assertEqual([c[1][0] for c in editor.calls], ['a', 'b'])
        self.assertEqual(len(history._stack_undo), 2)
        self.assertEqual(len(history._stack_redo), 0)

    def test_undo_does_not_stack_when_whitespace_class_changes(self):
        history, editor = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 1), (0, 2), (0, 0), (0, 0), False, False, ' ')

        history.undo(editor)
        self.assertEqual([c[1][0] for c in editor.calls], [' '])
        self.assertEqual(len(history._stack_undo), 1)

    def test_undo_does_not_stack_when_positions_are_not_contiguous(self):
        history, editor = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a')
        history.add(b'_key_string', False, (0, 5), (0, 6), (0, 0), (0, 0), False, False, 'b')

        history.undo(editor)
        self.assertEqual([c[1][0] for c in editor.calls], ['b'])
        self.assertEqual(len(history._stack_undo), 1)

    def test_redo_break_branch_reappends_non_stackable_action(self):
        history, editor = self._mk()
        history.add(b'_key_string', False, (0, 0), (0, 1), (0, 0), (0, 0), False, False, 'a', stack_type='redo')
        history.add(b'_key_backspace', False, (0, 2), (0, 1), (0, 0), (0, 0), False, False, 'b', stack_type='redo')

        history.redo(editor)

        self.assertEqual(editor.calls[0][0], '_key_backspace')
        self.assertEqual(len(history._stack_redo), 1)
        self.assertEqual(history._stack_redo[0].action_text, ('a',))
