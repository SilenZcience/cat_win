"""Tests for ANSI color handling in piped and terminal environments."""
from unittest import TestCase
from unittest.mock import patch
import os
from cat_win.src.domain.appcontext import AppContext

from cat_win.src import cat
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.persistence.cconfig import CConfig
from cat_win.src.persistence.config import Config
from cat_win.tests.mocks.std import StdOutMock, OSAttyDefGen


def _clear_caches():
    """Clear cached formatting state and reset app context between tests."""
    from cat_win.src.processor.lineprefixprocessor import _calculate_line_prefix_spacing, _calculate_line_length_prefix_spacing
    _calculate_line_prefix_spacing.cache_clear()
    _calculate_line_length_prefix_spacing.cache_clear()
    cat._ctx = AppContext(cat.working_dir)


# Load test files with ANSI codes
test_texts_dir = os.path.join(os.path.dirname(__file__), '..', 'texts')
ansi_pos_file_path = os.path.join(test_texts_dir, 'ansi-pos.txt')
ansi_neg_file_path = os.path.join(test_texts_dir, 'ansi-neg.txt')
ansi_base_file_path = os.path.join(test_texts_dir, 'ansi-base.txt')

ansi_pos_file_content = ''
ansi_neg_file_content = ''
with open(ansi_pos_file_path, 'r', encoding='utf-8') as f:
    ansi_pos_file_content = f.read()
with open(ansi_neg_file_path, 'r', encoding='utf-8') as f:
    ansi_neg_file_content = f.read()


# Concrete config dictionaries used by patched Config.load_config
strip_color_dic_true = Config.default_dic.copy()
strip_color_dic_false = Config.default_dic.copy()
strip_color_dic_false[DKW.STRIP_COLOR_ON_PIPE] = False


@patch('cat_win.src.domain.appcontext.CConfig.load_config', lambda self: CConfig.default_dic.copy())
@patch('cat_win.src.const.colorconstants.CVis.remove_colors', lambda: None)
@patch('os.isatty', OSAttyDefGen.get_def({1: False}))
class TestAnsiPiped(TestCase):
    maxDiff = None

    def tearDown(self):
        _clear_caches()

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_true)
    def test_cat_ansi_input_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_neg_file_content)

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_false)
    def test_cat_ansi_input_no_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_true)
    def test_cat_ansi_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_neg_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_false)
    def test_cat_ansi_no_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)


@patch('cat_win.src.domain.appcontext.CConfig.load_config', lambda self: CConfig.default_dic.copy())
@patch('cat_win.src.const.colorconstants.CVis.remove_colors', lambda: None)
@patch('os.isatty', OSAttyDefGen.get_def({1: True}))
class TestAnsiNotPiped(TestCase):
    maxDiff = None

    def tearDown(self):
        _clear_caches()

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_true)
    def test_cat_ansi_input_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_pos_file_path])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_false)
    def test_cat_ansi_input_no_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_true)
    def test_cat_ansi_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)

    @patch('sys.argv', ['<CAT>', ansi_base_file_path, '-ln'])
    @patch.object(Config, 'load_config', return_value=strip_color_dic_false)
    def test_cat_ansi_no_strip(self, mock_load):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.main()
            self.assertEqual(fake_out.getvalue(), ansi_pos_file_content)
