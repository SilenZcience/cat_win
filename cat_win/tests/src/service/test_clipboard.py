from unittest import TestCase
from unittest.mock import patch
import os
from types import SimpleNamespace

from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.src.service.clipboard import Clipboard
# import sys
# sys.path.append('../cat_win')


test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')
logger = LoggerStub()


@patch('cat_win.src.service.clipboard.get_py_executable', lambda *_: 'python')
class TestClipboard(TestCase):
    maxDiff = None

    def setUp(self):
        logger.clear()
        Clipboard.clipboard = ''
        Clipboard.copy_function = None
        Clipboard.paste_function = None

    def test_clipabord_clear(self):
        Clipboard.clipboard = '42'
        Clipboard.clear()
        self.assertEqual(Clipboard.clipboard, '')

    def test_put_cached(self):
        # the patch makes the copy_function not None
        with patch.object(Clipboard, 'copy_function') as mocka, patch.object(Clipboard, '_copy') as mockb:
            Clipboard.put('42')
        mocka.assert_called_once_with('42')
        mockb.assert_not_called()

    def test_put_not_cached(self):
        with patch.object(Clipboard, '_copy') as mockb:
            Clipboard.put('42')
        mockb.assert_called_once_with('42')

    @patch('cat_win.src.service.clipboard.get_py_executable', lambda *_: 'python')
    def test__copy_clipboarderror(self):
        with patch('cat_win.src.service.clipboard.logger', logger) as fake_out:
            Clipboard._copy('', 0, True)
            self.assertIn('ClipBoardError', fake_out.output())
            self.assertNotIn('ImportError', fake_out.output())
            self.assertIn("'--clip'", fake_out.output())

    def test__copy_importerror(self):
        with patch('cat_win.src.service.clipboard.logger', logger) as fake_out:
            Clipboard._copy('', 0, False)
            self.assertNotIn('ClipBoardError', fake_out.output())
            self.assertIn('ImportError', fake_out.output())
            self.assertIn("'--clip'", fake_out.output())

    def test__copy_recursive_importerror_fallback(self):
        copied = []
        fake_module = SimpleNamespace(copy=lambda content: copied.append(content))
        real_import = __import__

        def import_side_effect(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError('missing pyperclip')
            if name == 'pyclip':
                raise ImportError('missing pyclip')
            if name == 'pyperclip3':
                return fake_module
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_side_effect):
            self.assertTrue(Clipboard._copy('42'))

        self.assertEqual(copied, ['42'])

    def test__copy_recursive_exception_fallback(self):
        copied = []
        fake_module = SimpleNamespace(copy=lambda content: copied.append(content))
        real_import = __import__

        def import_side_effect(name, *args, **kwargs):
            if name == 'pyperclip':
                raise RuntimeError('clipboard backend error')
            if name == 'pyclip':
                raise ImportError('missing pyclip')
            if name == 'pyperclip3':
                return fake_module
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_side_effect):
            self.assertTrue(Clipboard._copy('99'))

        self.assertEqual(copied, ['99'])

    def test_get_cached(self):
        # the patch makes the copy_function not None
        with patch.object(Clipboard, 'paste_function') as mocka, patch.object(Clipboard, '_paste') as mockb:
            Clipboard.get()
        mocka.assert_called_once()
        mockb.assert_not_called()

    def test_get_not_cached(self):
        with patch.object(Clipboard, '_paste') as mockb:
            self.assertEqual(Clipboard.get(), None)
        mockb.assert_called_once()

    def test__paste_clipboarderror(self):
        with patch('cat_win.src.service.clipboard.logger', logger) as fake_out:
            Clipboard._paste(0, True)
            self.assertIn('ClipBoardError', fake_out.output())
            self.assertNotIn('ImportError', fake_out.output())
            self.assertIn("'--clip'", fake_out.output())

    def test__paste_importerror(self):
        with patch('cat_win.src.service.clipboard.logger', logger) as fake_out:
            Clipboard._paste(0, False)
            self.assertNotIn('ClipBoardError', fake_out.output())
            self.assertIn('ImportError', fake_out.output())
            self.assertIn("'--clip'", fake_out.output())

    def test__paste_recursive_importerror_fallback(self):
        fake_module = SimpleNamespace(paste=lambda: 'OK')
        real_import = __import__

        def import_side_effect(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError('missing pyperclip')
            if name == 'pyclip':
                raise ImportError('missing pyclip')
            if name == 'pyperclip3':
                return fake_module
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_side_effect):
            self.assertIsNone(Clipboard._paste())

        self.assertEqual(Clipboard.paste_function(), 'OK')

    def test__paste_recursive_exception_fallback(self):
        fake_module = SimpleNamespace(paste=lambda: 'OK2')
        real_import = __import__

        def import_side_effect(name, *args, **kwargs):
            if name == 'pyperclip':
                raise RuntimeError('clipboard backend error')
            if name == 'pyclip':
                raise ImportError('missing pyclip')
            if name == 'pyperclip3':
                return fake_module
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_side_effect):
            self.assertIsNone(Clipboard._paste())

        self.assertEqual(Clipboard.paste_function(), 'OK2')

    def test_get_decodes_bytes(self):
        Clipboard.paste_function = lambda: b'\xffABC'
        self.assertEqual(Clipboard.get(), 'ABC')
