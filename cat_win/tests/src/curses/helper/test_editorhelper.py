from unittest.mock import patch, MagicMock
from unittest import TestCase
import importlib.util
import os
import sys
import types

from cat_win.src.curses.helper import editorhelper
if not hasattr(editorhelper, 'curses'):
    setattr(editorhelper, 'curses', None)
from cat_win.src.curses.helper.editorhelper import Position, History, frepr
from cat_win.tests.mocks.edit import EditorHistoryMock

mm = MagicMock()

@patch('cat_win.src.curses.helper.editorhelper.curses', mm)
class TestEditorHelper(TestCase):
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

    def _load_editorhelper_module(self, module_name, modules):
        file_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', '..', 'src', 'curses', 'helper', 'editorhelper.py'
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
            '..', '..', '..', '..', 'src', 'curses', 'helper', 'editorhelper.py'
        ))
        spec = importlib.util.spec_from_file_location('editorhelper_cov_no_curses', file_path)
        module = importlib.util.module_from_spec(spec)
        with patch('builtins.__import__', side_effect=_fake_import):
            spec.loader.exec_module(module)

        self.assertFalse(hasattr(module, 'curses'))


@patch('cat_win.src.curses.helper.editorhelper.curses', mm)
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
        broken_action = editorhelper._Action(
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
