from unittest import TestCase
from unittest.mock import patch
import os

from cat_win import cat
from cat_win.const.defaultconstants import DKW
from cat_win.tests.mocks.std import StdOutMock, OSAttyDefGen
from cat_win.util.argparser import ArgParser
from cat_win.util.holder import Holder
from cat_win.persistence.cconfig import CConfig
from cat_win.persistence.config import Config
# import sys
# sys.path.append('../cat_win')


ansi_pos_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'ansi-pos.txt')
ansi_neg_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'ansi-neg.txt')
ansi_base_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'ansi-base.txt')
ansi_pos_file_content = ''
ansi_neg_file_content = ''
with open(ansi_pos_file_path, 'r', encoding='utf-8') as f:
    ansi_pos_file_content = f.read()
with open(ansi_neg_file_path, 'r', encoding='utf-8') as f:
    ansi_neg_file_content = f.read()

config = CConfig(os.path.join(os.path.dirname(__file__), 'texts'))
config.load_config()

strip_color_dic_true = Config.default_dic.copy()
strip_color_dic_false = Config.default_dic.copy()
strip_color_dic_false[DKW.STRIP_COLOR_ON_PIPE] = False



@patch('cat_win.cat.default_color_dic', config.color_dic)
@patch('cat_win.cat.color_dic', config.color_dic)
@patch('os.isatty', OSAttyDefGen.get_def({1: False}))
class TestAnsiPiped(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()
        cat.arg_parser = ArgParser()
        cat.holder = Holder()

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch('cat_win.cat.const_dic', strip_color_dic_true)
    def test_cat_ansi_input_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_neg_file_content)

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch('cat_win.cat.const_dic', strip_color_dic_false)
    def test_cat_ansi_input_no_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch('cat_win.cat.const_dic', strip_color_dic_true)
    def test_cat_ansi_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_neg_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch('cat_win.cat.const_dic', strip_color_dic_false)
    def test_cat_ansi_no_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

@patch('cat_win.cat.default_color_dic', config.color_dic)
@patch('cat_win.cat.color_dic', config.color_dic)
@patch('os.isatty', OSAttyDefGen.get_def({1: True}))
class TestAnsiNotPiped(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()
        cat.arg_parser = ArgParser()
        cat.holder = Holder()

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch('cat_win.cat.const_dic', strip_color_dic_true)
    def test_cat_ansi_input_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch('cat_win.cat.const_dic', strip_color_dic_false)
    def test_cat_ansi_input_no_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch('cat_win.cat.const_dic', strip_color_dic_true)
    def test_cat_ansi_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch('cat_win.cat.const_dic', strip_color_dic_false)
    def test_cat_ansi_no_strip(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)
