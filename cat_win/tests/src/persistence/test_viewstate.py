from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.tests.mocks.logger import LoggerStub
from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor
from cat_win.src.persistence import viewstate


class DummyView:
    pass


class _DummyPath:
    def __init__(self):
        self.open = MagicMock()


logger = LoggerStub()


class TestViewState(TestCase):
    def setUp(self):
        logger.clear()
        self._class_state_backup = {
            DiffViewer: {
                'debug_mode': DiffViewer.debug_mode,
                'watch_mode': DiffViewer.watch_mode,
                'file_encoding': DiffViewer.file_encoding,
            },
            Editor: {
                'debug_mode': Editor.debug_mode,
                'special_indentation': Editor.special_indentation,
                'auto_indent': Editor.auto_indent,
                'file_encoding': Editor.file_encoding,
            },
            HexEditor: {
                'debug_mode': HexEditor.debug_mode,
                'columns': HexEditor.columns,
                'unicode_escaped_insert': HexEditor.unicode_escaped_insert,
            },
        }

    def tearDown(self):
        for cls, attrs in self._class_state_backup.items():
            for key, value in attrs.items():
                setattr(cls, key, value)

    @staticmethod
    def _make_view(cls, **kwargs):
        obj = cls.__new__(cls)
        obj.__dict__.update(kwargs)
        return obj

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_save_view_state_payload_no_real_file_io(self):
        fake_path = _DummyPath()
        fake_handle = MagicMock()
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = fake_handle
        fake_cm.__exit__.return_value = None
        fake_path.open.return_value = fake_cm

        editor = self._make_view(Editor, sample='ok', curse_window=object())

        with patch('cat_win.src.persistence.viewstate.xdg_config', return_value=fake_path) as xdg, \
             patch('cat_win.src.persistence.viewstate.pickle.dump') as dump_mock:
            viewstate.save_view_state(editor)

        xdg.assert_called_once_with('viewstate_obj.bin', ensure_dir=True)
        fake_path.open.assert_called_once_with('wb')
        dump_mock.assert_called_once()

        payload = dump_mock.call_args[0][0]
        self.assertEqual(payload['view_type'], 'Editor')
        self.assertEqual(payload['view_module'], 'cat_win.src.curses.editor')
        self.assertIn('state', payload)
        self.assertIn('class_state', payload)
        self.assertIsNone(payload['state']['curse_window'])
        self.assertEqual(payload['state']['sample'], 'ok')
        self.assertIn("Collected attribute 'sample'", logger.output())

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_save_unsupported_view_type_raises(self):
        self.assertFalse(viewstate.save_view_state(DummyView()))
        self.assertIn('Error saving view state', logger.output())

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_load_view_state_restores_instance_and_class_state_no_real_file_io(self):
        fake_path = _DummyPath()
        fake_handle = MagicMock()
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = fake_handle
        fake_cm.__exit__.return_value = None
        fake_path.open.return_value = fake_cm

        payload = {
            'view_type': 'DiffViewer',
            'view_module': 'cat_win.src.curses.diffviewer',
            'state': {
                'curse_window': None,
                'marker': 123,
            },
            'class_state': {
                'debug_mode': True,
                'watch_mode': True,
                'file_encoding': 'cp1252',
                '__ignored': 'x',
                'not_existing': 99,
            },
        }

        module_mock = MagicMock()
        module_mock.DiffViewer = DiffViewer

        with patch('cat_win.src.persistence.viewstate.xdg_config', return_value=fake_path) as xdg, \
             patch('cat_win.src.persistence.viewstate.pickle.load', return_value=payload) as load_mock, \
             patch('cat_win.src.persistence.viewstate.importlib.import_module', return_value=module_mock) as import_mock:
            restored = viewstate.load_view_state()

        xdg.assert_called_once_with('viewstate_obj.bin', ensure_dir=True)
        fake_path.open.assert_called_once_with('rb')
        load_mock.assert_called_once_with(fake_handle)
        import_mock.assert_called_once_with('cat_win.src.curses.diffviewer')

        self.assertIsInstance(restored, DiffViewer)
        self.assertEqual(restored.marker, 123)
        self.assertIsNone(restored.curse_window)
        self.assertTrue(DiffViewer.debug_mode)
        self.assertTrue(DiffViewer.watch_mode)
        self.assertEqual(DiffViewer.file_encoding, 'cp1252')

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_load_invalid_view_type_raises(self):
        fake_path = _DummyPath()
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = MagicMock()
        fake_cm.__exit__.return_value = None
        fake_path.open.return_value = fake_cm

        payload = {
            'view_type': 'NotAView',
            'view_module': 'cat_win.src.curses.editor',
            'state': {},
            'class_state': {},
        }

        with patch('cat_win.src.persistence.viewstate.xdg_config', return_value=fake_path), \
             patch('cat_win.src.persistence.viewstate.pickle.load', return_value=payload):
            self.assertIsNone(viewstate.load_view_state())
        self.assertIn('Error loading view state', logger.output())

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_load_invalid_state_payload_shapes_raise(self):
        fake_path = _DummyPath()
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = MagicMock()
        fake_cm.__exit__.return_value = None
        fake_path.open.return_value = fake_cm

        payload_bad_state = {
            'view_type': 'Editor',
            'view_module': 'cat_win.src.curses.editor',
            'state': 'not-a-dict',
            'class_state': {},
        }
        payload_bad_class_state = {
            'view_type': 'Editor',
            'view_module': 'cat_win.src.curses.editor',
            'state': {},
            'class_state': 'not-a-dict',
        }

        with patch('cat_win.src.persistence.viewstate.xdg_config', return_value=fake_path), \
             patch('cat_win.src.persistence.viewstate.pickle.load', return_value=payload_bad_state):
            self.assertIsNone(viewstate.load_view_state())

        with patch('cat_win.src.persistence.viewstate.xdg_config', return_value=fake_path), \
             patch('cat_win.src.persistence.viewstate.pickle.load', return_value=payload_bad_class_state):
            self.assertIsNone(viewstate.load_view_state())
        self.assertIn('Error loading view state', logger.output())

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_collect_state_skips_non_pickleable_value(self):
        class NonPickleable:
            def __getstate__(self):
                raise TypeError('cannot pickle')

        dv = self._make_view(DiffViewer, ok=1, nope=NonPickleable(), curse_window='x')
        state = viewstate._collect_state(dv)

        self.assertEqual(state['ok'], 1)
        self.assertIsNone(state['nope'])
        self.assertIsNone(state['curse_window'])
        out = logger.output()
        self.assertIn("Collected attribute 'ok'", out)
        self.assertIn("Skipping non-serializable attribute 'nope'", out)

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_collect_class_state_skips_non_pickleable_class_attribute(self):
        class NonPickleable:
            def __getstate__(self):
                raise TypeError('cannot pickle')

        old_marker = getattr(Editor, 'test_non_pickleable_marker', None)
        had_marker = hasattr(Editor, 'test_non_pickleable_marker')
        try:
            Editor.test_non_pickleable_marker = NonPickleable()
            editor = self._make_view(Editor)
            class_state = viewstate._collect_class_state(editor)
            self.assertNotIn('test_non_pickleable_marker', class_state)
            self.assertIn(
                "Skipping non-serializable class attribute 'test_non_pickleable_marker'",
                logger.output()
            )
        finally:
            if had_marker:
                Editor.test_non_pickleable_marker = old_marker
            else:
                delattr(Editor, 'test_non_pickleable_marker')

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_apply_class_state_skips_callable_attribute(self):
        callable_key = next(
            key for key, value in vars(Editor).items()
            if (not key.startswith('__')) and callable(value)
        )
        before = getattr(Editor, callable_key)
        viewstate._apply_class_state(Editor, {callable_key: 'mutated'})
        self.assertIs(getattr(Editor, callable_key), before)

    @patch('cat_win.src.persistence.viewstate.logger', logger)
    def test_load_view_state_corrupted_payload_returns_none(self):
        with patch('cat_win.src.persistence.viewstate.ViewStateLoader.load', side_effect=EOFError('bad')):
            self.assertIsNone(viewstate.load_view_state())
        self.assertIn('file may be corrupted', logger.output())
