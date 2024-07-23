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
