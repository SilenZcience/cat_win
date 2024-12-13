from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.service.clipboard import Clipboard
# import sys
# sys.path.append('../cat_win')


test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')


class TestClipboard(TestCase):
    maxDiff = None

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

    def test__copy_clipboarderror(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            Clipboard._copy('', 0, True)
            self.assertIn('ClipBoardError', fake_out.getvalue())
            self.assertNotIn('ImportError', fake_out.getvalue())
            self.assertIn("'--clip'", fake_out.getvalue())

    def test__copy_importerror(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            Clipboard._copy('', 0, False)
            self.assertNotIn('ClipBoardError', fake_out.getvalue())
            self.assertIn('ImportError', fake_out.getvalue())
            self.assertIn("'--clip'", fake_out.getvalue())

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
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            Clipboard._paste(0, True)
            self.assertIn('ClipBoardError', fake_out.getvalue())
            self.assertNotIn('ImportError', fake_out.getvalue())
            self.assertIn("'--clip'", fake_out.getvalue())

    def test__paste_importerror(self):
        with patch('sys.stderr', new=StdOutMock()) as fake_out:
            Clipboard._paste( 0, False)
            self.assertNotIn('ClipBoardError', fake_out.getvalue())
            self.assertIn('ImportError', fake_out.getvalue())
            self.assertIn("'--clip'", fake_out.getvalue())
