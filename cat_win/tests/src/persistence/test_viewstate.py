from tempfile import TemporaryDirectory
from unittest import TestCase

from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor
from cat_win.src.persistence.viewstate import (
    ViewStateLoader,
    ViewStateWriter,
    load_view_state,
    save_view_state,
)


class TestViewState(TestCase):
    def _write_file(self, path: str, content: bytes) -> None:
        with open(path, 'wb') as f_handle:
            f_handle.write(content)

    def test_save_and_load_diffviewer_state(self):
        with TemporaryDirectory() as tmp_dir:
            file_1 = f'{tmp_dir}/left.txt'
            file_2 = f'{tmp_dir}/right.txt'
            state_file = f'{tmp_dir}/diff.state'

            self._write_file(file_1, b'a\nline\n')
            self._write_file(file_2, b'a\nline changed\n')

            obj = DiffViewer([(file_1, 'left.txt'), (file_2, 'right.txt')])
            obj.search = 'line'
            obj.rpos.row = 1

            ViewStateWriter.save(state_file, obj)
            loaded = ViewStateLoader.load(state_file)

            self.assertIsInstance(loaded, DiffViewer)
            self.assertEqual(loaded.search, obj.search)
            self.assertEqual(loaded.rpos.row, obj.rpos.row)
            self.assertEqual(loaded.diff_files, obj.diff_files)
            self.assertIsNone(loaded.curse_window)

    def test_save_and_load_editor_state(self):
        with TemporaryDirectory() as tmp_dir:
            file_1 = f'{tmp_dir}/edit.txt'
            state_file = f'{tmp_dir}/editor.state'

            self._write_file(file_1, b'hello\nworld\n')

            obj = Editor([(file_1, 'edit.txt')])
            obj.search = 'world'
            obj.replace = 'planet'
            obj.cpos.row = 1
            obj.cpos.col = 2
            obj.unsaved_progress = True

            save_view_state(state_file, obj)
            loaded = load_view_state(state_file)

            self.assertIsInstance(loaded, Editor)
            self.assertEqual(loaded.search, obj.search)
            self.assertEqual(loaded.replace, obj.replace)
            self.assertEqual(loaded.cpos.row, obj.cpos.row)
            self.assertEqual(loaded.cpos.col, obj.cpos.col)
            self.assertEqual(loaded.window_content, obj.window_content)
            self.assertIsNone(loaded.curse_window)
            self.assertIsNone(loaded.get_char)

    def test_save_and_load_hexeditor_state(self):
        with TemporaryDirectory() as tmp_dir:
            file_1 = f'{tmp_dir}/hex.bin'
            state_file = f'{tmp_dir}/hex.state'

            self._write_file(file_1, bytes(range(32)))

            obj = HexEditor([(file_1, 'hex.bin')])
            obj.search = '0A'
            obj.cpos.row = 1
            obj.cpos.col = 3
            obj.hex_array_edit[0][0] = 'FF'

            ViewStateWriter.save(state_file, obj)
            loaded = ViewStateLoader.load(state_file)

            self.assertIsInstance(loaded, HexEditor)
            self.assertEqual(loaded.search, obj.search)
            self.assertEqual(loaded.cpos.row, obj.cpos.row)
            self.assertEqual(loaded.cpos.col, obj.cpos.col)
            self.assertEqual(loaded.hex_array, obj.hex_array)
            self.assertEqual(loaded.hex_array_edit, obj.hex_array_edit)
            self.assertIsNone(loaded.curse_window)
            self.assertIsNone(loaded.decode_char)

    def test_save_rejects_unsupported_object(self):
        with TemporaryDirectory() as tmp_dir:
            state_file = f'{tmp_dir}/invalid.state'
            with self.assertRaises(TypeError):
                ViewStateWriter.save(state_file, object())
