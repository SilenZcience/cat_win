from unittest.mock import patch
from unittest import TestCase
import os

from cat_win.src.const.colorconstants import ColorOptions, CKW
from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.persistence.cconfig import CConfig
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
config = CConfig(test_file_dir)
config.load_config()


@patch('os.get_terminal_size', lambda: (120, 30))
class TestCConfig(TestCase):
    maxDiff = None

    def test__print_get_all_available_colors(self):
        all_color_options = list(ColorOptions.Fore.keys()) + list(ColorOptions.Back.keys())
        all_color_options = [k for k in all_color_options if k != 'RESET']

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            config._print_get_all_available_colors()
            for i, k in enumerate(all_color_options, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(k, fake_out.getvalue())

    def test__print_all_available_elements(self):
        class_members = [attr for attr in dir(CKW) if not (
            callable(getattr(CKW, attr)) or attr.startswith('__') or attr.startswith('RESET')
        )]

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            config._print_all_available_elements()
            for i, k in enumerate(class_members, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(getattr(CKW, k), fake_out.getvalue())
