from unittest.mock import patch
from unittest import TestCase

from cat_win.src.service.helper.progressbar import PBar
from cat_win.tests.mocks.std import StdOutMock, OSAttyDefGen
# import sys
# sys.path.append('../cat_win')


class TestPBar(TestCase):
    maxDiff = None

    @patch('os.isatty', OSAttyDefGen.get_def({1: False}))
    def test_pbar_not_atty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with PBar(100, prefix='PREFIX', suffix='SUFFIX',
                  length=50, fill_l='━', fill_r='╺').init() as p_bar:
                for i in range(101):
                    p_bar(i)
            self.assertEqual(fake_out.getvalue(), '')

    @patch('os.isatty', OSAttyDefGen.get_def({1: True}))
    def test_pbar_atty(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with PBar(2, prefix='PREFIX', suffix='SUFFIX',
                  length=2, fill_l='X', fill_r='_').init() as p_bar:
                for i in range(3):
                    p_bar(i)
            self.assertEqual(fake_out.getvalue().startswith('\x1b[?25l'), True)
            self.assertEqual(fake_out.getvalue().endswith('\x1b[?25h\n'), True)
            self.assertIn('__', fake_out.getvalue())
            self.assertIn('XX', fake_out.getvalue())
            self.assertNotIn('\b \b', fake_out.getvalue())

    @patch('os.isatty', OSAttyDefGen.get_def({1: True}))
    @patch('cat_win.src.service.helper.progressbar.CURSOR_VISIBLE', '')
    @patch('cat_win.src.service.helper.progressbar.CURSOR_INVISIBLE', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_DONE', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_MISSING', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_RESET', '')
    def test_pbar_atty_out_of_bound(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with PBar(2, prefix='', suffix='',
                  length=2, fill_l='X', fill_r='_').init() as p_bar:
                for i in range(-1, 4):
                    p_bar(i)
            self.assertEqual(fake_out.getvalue(), '\r XX 100.0%\r __   0.0%\r X_  50.0%\r XX 100.0%\r XX 100.0%\n')

    @patch('os.isatty', OSAttyDefGen.get_def({1: True}))
    @patch('cat_win.src.service.helper.progressbar.CURSOR_VISIBLE', '')
    @patch('cat_win.src.service.helper.progressbar.CURSOR_INVISIBLE', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_DONE', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_MISSING', '')
    @patch('cat_win.src.service.helper.progressbar.PBar.COLOR_RESET', '')
    def test_pbar_atty_with_suffix(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with PBar(2, prefix='', suffix='SUFFIX',
                  length=2, fill_l='X', fill_r='_').init() as p_bar:
                for i in range(0, 3):
                    p_bar(i)
            self.assertEqual(fake_out.getvalue(), '\r __   0.0% SUFFIX\r X_  50.0% SUFFIX\r XX 100.0% SUFFIX\n')

    @patch('os.isatty', OSAttyDefGen.get_def({1: True}))
    def test_pbar_atty_erase(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            with PBar(2, prefix='PREFIX', suffix='SUFFIX',
                  length=2, fill_l='X', fill_r='_', erase=True).init() as p_bar:
                for i in range(3):
                    p_bar(i)
            self.assertEqual(fake_out.getvalue().startswith('\x1b[?25l'), True)
            self.assertEqual(fake_out.getvalue().endswith('\x1b[?25h'), True)
            self.assertIn('__', fake_out.getvalue())
            self.assertIn('XX', fake_out.getvalue())
            self.assertIn('\b \b', fake_out.getvalue())
