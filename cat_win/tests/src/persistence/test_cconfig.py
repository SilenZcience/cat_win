from unittest.mock import patch, mock_open
from unittest import TestCase
import os

from cat_win.src.const.colorconstants import ColorOptions, CKW
from cat_win.src.persistence.cconfig import CConfig
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.std import StdOutMock
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
config = CConfig(test_file_dir)
config.load_config()
logger = LoggerStub()


@patch('sys.stdout', new=StdOutMock())
@patch('shutil.get_terminal_size', lambda: (120, 30))
class TestCConfig(TestCase):
    maxDiff = None

    def test__save_config_writes_value(self):
        config_ = CConfig(test_file_dir)
        config_.config_parser.add_section('COLORS')

        with patch('builtins.open', mock_open()) as m_open:
            with patch.object(config_.config_parser, 'write') as m_write:
                config_._save_config(CKW.FOUND, 'Fore.RED')

        self.assertEqual(config_.config_parser.get('COLORS', CKW.FOUND), 'Fore.RED')
        m_open.assert_called_once_with(config_.config_file, 'w', encoding='utf-8')
        m_write.assert_called_once_with(m_open())

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test__save_config_oserror_logs(self):
        logger.clear()
        config_ = CConfig(test_file_dir)

        with patch('builtins.open', side_effect=OSError('Mocked Error')):
            config_._save_config(None)

        self.assertIn('Could not write to config file', logger.output())

    def test_convert_config_element_fore_back(self):
        config_ = CConfig(test_file_dir)
        self.assertEqual(
            config_.convert_config_element('Fore.RED', CKW.FOUND),
            ColorOptions.Fore['RED']
        )
        self.assertEqual(
            config_.convert_config_element('Back.CYAN', CKW.MATCHED),
            ColorOptions.Back['CYAN']
        )

    def test_convert_config_element_ansi(self):
        config_ = CConfig(test_file_dir)
        self.assertEqual(
            config_.convert_config_element('[31m', CKW.FOUND),
            '\033[31m'
        )

    def test_convert_config_element_8bit(self):
        config_ = CConfig(test_file_dir)
        self.assertEqual(
            config_.convert_config_element('f196', CKW.FOUND),
            '\033[38;5;196m'
        )

    def test_convert_config_element_truecolor(self):
        config_ = CConfig(test_file_dir)
        self.assertEqual(
            config_.convert_config_element('b1;2;3', CKW.MATCHED),
            '\033[48;2;1;2;3m'
        )

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_convert_config_element_invalid_resets_and_exits(self):
        logger.clear()
        config_ = CConfig(test_file_dir)

        with patch.object(config_, '_save_config') as mock_save:
            with self.assertRaises(SystemExit):
                config_.convert_config_element('not-a-color', CKW.FOUND)

        mock_save.assert_called_once_with(CKW.FOUND, config_.default_dic[CKW.FOUND][1:])
        self.assertIn('invalid config value', logger.output())
        self.assertIn('resetting to', logger.output())

    def test_load_config_without_colors_section_uses_defaults(self):
        config_ = CConfig(test_file_dir)
        with patch.object(config_.config_parser, 'read') as mock_read:
            colors = config_.load_config()

        mock_read.assert_called_once_with(config_.config_file, encoding='utf-8')
        self.assertIn('COLORS', config_.config_parser.sections())
        self.assertEqual(colors[CKW.RESET_ALL], ColorOptions.Style['RESET'])
        self.assertEqual(colors[CKW.RESET_FOUND], ColorOptions.Fore['RESET'])
        self.assertEqual(colors[CKW.RESET_MATCHED], ColorOptions.Back['RESET'])
        self.assertEqual(colors[CKW.FOUND], config_.default_dic[CKW.FOUND])
        self.assertIsNot(colors, config_.default_dic)

    def test_load_config_with_colors_section_parses_values(self):
        config_ = CConfig(test_file_dir)
        config_.config_parser.add_section('COLORS')
        config_.config_parser.set('COLORS', CKW.FOUND, 'f196')
        config_.config_parser.set('COLORS', CKW.MATCHED, 'Back.YELLOW')

        colors = config_.load_config()

        self.assertEqual(colors[CKW.FOUND], '\033[38;5;196m')
        self.assertEqual(colors[CKW.MATCHED], ColorOptions.Back['YELLOW'])
        self.assertEqual(colors[CKW.RESET_ALL], ColorOptions.Style['RESET'])
        self.assertEqual(colors[CKW.RESET_FOUND], ColorOptions.Fore['RESET'])
        self.assertEqual(colors[CKW.RESET_MATCHED], ColorOptions.Back['RESET'])

    def test_load_config_with_invalid_entry_falls_back_to_default(self):
        config_ = CConfig(test_file_dir)
        config_.config_parser.add_section('COLORS')
        config_.config_parser.set('COLORS', CKW.FOUND, 'Fore.NOT_A_REAL_COLOR')

        colors = config_.load_config()

        self.assertEqual(colors[CKW.FOUND], config_.default_dic[CKW.FOUND])
        self.assertEqual(colors[CKW.RESET_ALL], ColorOptions.Style['RESET'])

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
        config_ = CConfig(test_file_dir)
        config_.load_config()
        config_.color_dic[CKW.FOUND] = ColorOptions.Fore['BLACK']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            config_._print_all_available_elements()
            for i, k in enumerate(class_members, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(getattr(CKW, k), fake_out.getvalue())

    def test_save_config_selects_keyword_by_name(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED', 'Back.CYAN']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.FOUND, 'Fore.RED']):
                        config_.save_config()

        mock_save.assert_called_once_with(CKW.FOUND, 'Fore.RED')

    def test_save_config_unknown_keyword_then_valid(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=['unknown-keyword', CKW.FOUND, 'Fore.RED']):
                        with patch('sys.stdout', new=StdOutMock()) as fake_out:
                            config_.save_config()

        self.assertIn("Unknown keyword 'unknown-keyword'", fake_out.getvalue())
        mock_save.assert_called_once_with(CKW.FOUND, 'Fore.RED')

    def test_save_config_selects_keyword_and_color_by_id(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()
        first_keyword = config_.elements[0]

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED', 'Back.CYAN']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=['1', '1']):
                        config_.save_config()

        mock_save.assert_called_once_with(first_keyword, 'Fore.RED')

    def test_save_config_accepts_higher_bit_color(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED', 'Back.CYAN']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.LINE_LENGTH, 'f196']):
                        config_.save_config()

        mock_save.assert_called_once_with(CKW.LINE_LENGTH, 'f196')

    def test_save_config_accepts_custom_ansi_color(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED', 'Back.CYAN']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.LINE_LENGTH, '[31m']):
                        config_.save_config()

        mock_save.assert_called_once_with(CKW.LINE_LENGTH, '[31m')

    def test_save_config_unknown_option_then_valid(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.FOUND, 'invalid-option', 'Fore.RED']):
                        with patch('sys.stdout', new=StdOutMock()) as fake_out:
                            config_.save_config()

        self.assertIn("Unknown option 'invalid-option'", fake_out.getvalue())
        mock_save.assert_called_once_with(CKW.FOUND, 'Fore.RED')

    def test_save_config_truecolor_path(self):
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.LINE_LENGTH, 'b1;2;3']):
                        config_.save_config()

        mock_save.assert_called_once_with(CKW.LINE_LENGTH, 'b1;2;3')

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_save_config_rejects_back_for_fore_exclusive(self):
        logger.clear()
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Back.CYAN']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.FOUND, 'Back.CYAN']):
                        self.assertIsNone(config_.save_config())

        mock_save.assert_not_called()
        self.assertIn("can only be of style 'Fore'", logger.output())

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_save_config_rejects_fore_for_back_exclusive(self):
        logger.clear()
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.MATCHED, 'Fore.RED']):
                        self.assertIsNone(config_.save_config())

        mock_save.assert_not_called()
        self.assertIn("can only be of style 'Back'", logger.output())

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_save_config_keyword_input_eof(self):
        logger.clear()
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch('builtins.input', side_effect=EOFError):
                self.assertIsNone(config_.save_config())

        self.assertIn('End-of-File', logger.output())

    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_save_config_color_input_eof(self):
        logger.clear()
        config_ = CConfig(test_file_dir)
        config_.color_dic = config_.default_dic.copy()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_print_get_all_available_colors', return_value=['Fore.RED']):
                with patch.object(config_, '_save_config') as mock_save:
                    with patch('builtins.input', side_effect=[CKW.LINE_LENGTH, EOFError]):
                        self.assertIsNone(config_.save_config())

        mock_save.assert_not_called()
        self.assertIn('End-of-File', logger.output())


    @patch('cat_win.src.persistence.cconfig.logger', logger)
    def test_reset_config(self):
        config_ = CConfig(test_file_dir)
        config_.config_parser.add_section('COLORS')
        with patch.object(config_, '_save_config') as mock_save:
            config_.reset_config()
        self.assertNotIn('COLORS', config_.config_parser.sections())
        mock_save.assert_called_once_with(None)
