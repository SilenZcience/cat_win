from unittest.mock import patch, mock_open
from unittest import TestCase
import os

from cat_win.src.const.argconstants import ALL_ARGS
from cat_win.src.const.defaultconstants import DKW
from cat_win.tests.mocks.error import ErrorDefGen
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.std import StdOutMock
from cat_win.src.persistence.config import (
    Config,
    validator_string,
    validator_int,
    validator_int_pos,
    validator_bool,
    validator_encoding
)
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
logger = LoggerStub()


@patch('sys.stdout', new=StdOutMock())
@patch('shutil.get_terminal_size', lambda: (120, 30))
@patch(
    'cat_win.src.persistence.config.xdg_config',
    lambda fname, ensure_dir=False: os.path.join(test_file_dir, f'__test_{fname}')
)
class TestConfig(TestCase):
    maxDiff = None

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_validator_string(self):
        logger.clear()
        self.assertTrue(validator_string("test"))
        self.assertTrue(validator_string(""))
        self.assertFalse(validator_string("", True))
        self.assertIn('String', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_validator_int(self):
        logger.clear()
        self.assertTrue(validator_int("123"))
        self.assertTrue(validator_int("0"))
        self.assertFalse(validator_int("-1"))
        self.assertFalse(validator_int("abc"))
        self.assertFalse(validator_int("12a"))
        self.assertFalse(validator_int("", True))
        self.assertIn('Integer', logger.output())
        self.assertIn('or Zero', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_validator_int_pos(self):
        logger.clear()
        self.assertTrue(validator_int_pos("123"))
        self.assertTrue(validator_int_pos("1"))
        self.assertFalse(validator_int_pos("0"))
        self.assertFalse(validator_int_pos("-1"))
        self.assertFalse(validator_int_pos("abc"))
        self.assertFalse(validator_int_pos("12a"))
        self.assertFalse(validator_int_pos("", True))
        self.assertIn('Integer', logger.output())
        self.assertIn('greater than Zero', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_validator_bool(self):
        logger.clear()
        self.assertTrue(validator_bool("trUe"))
        self.assertTrue(validator_bool("yES"))
        self.assertTrue(validator_bool("y"))
        self.assertTrue(validator_bool("1"))
        self.assertTrue(validator_bool("FAlse"))
        self.assertTrue(validator_bool("nO"))
        self.assertTrue(validator_bool("n"))
        self.assertTrue(validator_bool("0"))
        self.assertFalse(validator_bool("nope"))
        self.assertFalse(validator_bool("ja"))
        self.assertFalse(validator_bool("", True))
        self.assertIn('FALSE', logger.output())
        self.assertIn('TRUE', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_validator_encoding(self):
        logger.clear()
        self.assertTrue(validator_encoding("utf-8"))
        self.assertTrue(validator_encoding("ascii"))
        self.assertFalse(validator_encoding("invalid-encoding"))
        self.assertFalse(validator_encoding("", True))
        self.assertIn('Valid Encoding', logger.output())

    def test_convert_config_element(self):
        config_ = Config()
        self.assertEqual(config_.convert_config_element('"15"', DKW.LARGE_FILE_SIZE), 15)
        self.assertEqual(config_.convert_config_element('"7"', DKW.LARGE_FILE_SIZE), 7)
        self.assertEqual(config_.convert_config_element('"15"', DKW.DEFAULT_COMMAND_LINE), "15")
        self.assertEqual(config_.convert_config_element('"false"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.convert_config_element('"FALSE"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.convert_config_element('"no"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.convert_config_element('"n"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.convert_config_element('"0"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.convert_config_element('"1"', DKW.STRIP_COLOR_ON_PIPE), True)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_convert_config_element_invalid_value_resets_and_exits(self):
        logger.clear()
        config_ = Config()

        with patch.object(config_, '_save_config') as mock_save:
            with self.assertRaises(SystemExit):
                config_.convert_config_element('"abc"', DKW.LARGE_FILE_SIZE)

        mock_save.assert_called_once_with(DKW.LARGE_FILE_SIZE, config_.default_dic[DKW.LARGE_FILE_SIZE])
        self.assertIn("invalid config value 'abc'", logger.output())
        self.assertIn('resetting to', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_convert_config_element_unicode_error_resets_and_exits(self):
        logger.clear()
        config_ = Config()

        with patch.object(config_, '_save_config') as mock_save:
            with self.assertRaises(SystemExit):
                config_.convert_config_element('"\\ud800"', DKW.DEFAULT_COMMAND_LINE)

        mock_save.assert_called_once_with(
            DKW.DEFAULT_COMMAND_LINE,
            config_.default_dic[DKW.DEFAULT_COMMAND_LINE]
        )
        self.assertIn("invalid config value", logger.output())

    def test_convert_config_element_unicode_escape_conversion(self):
        config_ = Config()
        self.assertEqual(
            config_.convert_config_element('"\\n"', DKW.STRINGS_DELIMETER),
            '\n'
        )

    def test_is_valid_value(self):
        config_ = Config()
        self.assertEqual(config_.is_valid_value('', DKW.DEFAULT_COMMAND_LINE), True)
        self.assertEqual(config_.is_valid_value('', DKW.LARGE_FILE_SIZE), False)
        self.assertEqual(config_.is_valid_value('a', DKW.LARGE_FILE_SIZE), False)
        self.assertEqual(config_.is_valid_value('a', DKW.EDITOR_INDENTATION), True)
        self.assertEqual(config_.is_valid_value("5", DKW.STRINGS_MIN_SEQUENCE_LENGTH), True)
        self.assertEqual(config_.is_valid_value("5", DKW.LARGE_FILE_SIZE), True)
        self.assertEqual(config_.is_valid_value('TrUe', DKW.EDITOR_AUTO_INDENT), True)
        self.assertEqual(config_.is_valid_value('FaLSe', DKW.EDITOR_AUTO_INDENT), True)
        self.assertEqual(config_.is_valid_value('Yes', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('y', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('nO', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('n', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('0', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('1', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config_.is_valid_value('tru', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.is_valid_value(None, DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.is_valid_value('a\0b', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config_.is_valid_value(r'\\\xawd', DKW.STRIP_COLOR_ON_PIPE), False)

    def test_load_config_without_sections_uses_defaults(self):
        config_ = Config()
        with patch.object(config_.config_parser, 'read') as mock_read:
            consts = config_.load_config()

        mock_read.assert_called_once_with(config_.config_file, encoding='utf-8')
        self.assertEqual(config_.custom_commands, {})
        self.assertIn('COMMANDS', config_.config_parser.sections())
        self.assertIn('CONSTS', config_.config_parser.sections())
        self.assertDictEqual(consts, config_.default_dic)
        self.assertIsNot(consts, config_.default_dic)

    def test_load_config_with_sections_parses_values(self):
        config_ = Config()
        config_.config_parser.add_section('COMMANDS')
        config_.config_parser.set('COMMANDS', '-x', '"-a -b"')
        config_.config_parser.add_section('CONSTS')
        config_.config_parser.set('CONSTS', DKW.LARGE_FILE_SIZE, '"123"')
        config_.config_parser.set('CONSTS', DKW.STRIP_COLOR_ON_PIPE, '"false"')

        consts = config_.load_config()

        self.assertDictEqual(config_.custom_commands, {'-x': ['-a', '-b']})
        self.assertEqual(consts[DKW.LARGE_FILE_SIZE], 123)
        self.assertEqual(consts[DKW.STRIP_COLOR_ON_PIPE], False)
        self.assertEqual(consts[DKW.DEFAULT_FILE_ENCODING], config_.default_dic[DKW.DEFAULT_FILE_ENCODING])

    def test_load_config_missing_const_key_falls_back_to_default(self):
        config_ = Config()
        config_.config_parser.add_section('COMMANDS')
        config_.config_parser.add_section('CONSTS')
        config_.config_parser.set('CONSTS', DKW.DEFAULT_COMMAND_LINE, '"-n"')

        consts = config_.load_config()

        self.assertEqual(consts[DKW.DEFAULT_COMMAND_LINE], '-n')
        self.assertEqual(consts[DKW.LARGE_FILE_SIZE], config_.default_dic[DKW.LARGE_FILE_SIZE])

    def test_get_cmd(self):
        config_ = Config()
        config_.const_dic[DKW.DEFAULT_COMMAND_LINE] = '-nl "find= "'
        with patch('sys.argv', ['cat_win', '--existing', 'arg']):
            self.assertListEqual(
                config_.get_cmd(),
                ['cat_win', '-nl', 'find= ', '--existing', 'arg']
            )

    def test__print_all_available_elements(self):
        config_ = Config()
        config_.load_config()
        for i in range(1, 11):
            config_.custom_commands[f'custom{i}'] = ['-a', '-b']
        all_elements = list(config_.default_dic.keys())

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            config_._print_all_available_elements()
            for i, k in enumerate(all_elements, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(k, fake_out.getvalue())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config(self):
        logger.clear()
        config_ = Config()
        config_.config_parser.add_section('CONSTS')
        with patch('builtins.open', ErrorDefGen.get_def(OSError("Mocked Error"))):
            config_._save_config('test', 'val ue')
        self.assertEqual(config_.config_parser.get('CONSTS', 'test', fallback=None), '"val ue"')
        self.assertIn('Could not write', logger.output())



    def test_save_config_selects_element_by_name(self):
        config_ = Config()
        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_element') as mock_save_element:
                with patch('builtins.input', side_effect=[DKW.DEFAULT_COMMAND_LINE]):
                    config_.save_config()
        mock_save_element.assert_called_once_with(DKW.DEFAULT_COMMAND_LINE)

    def test_save_config_selects_element_by_id(self):
        config_ = Config()
        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_element') as mock_save_element:
                with patch('builtins.input', side_effect=['1']):
                    config_.save_config()
        mock_save_element.assert_called_once_with(config_.elements[0])

    def test_save_config_selects_custom_command_by_name(self):
        config_ = Config()
        config_.custom_commands['-x'] = ['-a', '-b']
        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                with patch('builtins.input', side_effect=['-x']):
                    config_.save_config()
        mock_save_custom.assert_called_once_with('-x')

    def test_save_config_selects_custom_command_by_id(self):
        config_ = Config()
        config_.custom_commands['-x'] = ['-a', '-b']
        custom_id = str(len(config_.elements) + 1)

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                with patch('builtins.input', side_effect=[custom_id]):
                    config_.save_config()
        mock_save_custom.assert_called_once_with('-x')

    def test_save_config_selects_new_custom_command(self):
        config_ = Config()
        new_custom_id = str(len(config_.elements) + 1)

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_add_custom_command') as mock_save_new_custom:
                with patch('builtins.input', side_effect=[new_custom_id]):
                    config_.save_config()
        mock_save_new_custom.assert_called_once_with()

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_save_config_unknown_keyword_then_valid(self):
        logger.clear()
        config_ = Config()

        with patch.object(config_, '_print_all_available_elements'):
            with patch.object(config_, '_save_config_element') as mock_save_element:
                with patch('builtins.input', side_effect=['unknown-keyword', DKW.DEFAULT_COMMAND_LINE]):
                    config_.save_config()

        self.assertIn("Unknown keyword 'unknown-keyword'", logger.output())
        mock_save_element.assert_called_once_with(DKW.DEFAULT_COMMAND_LINE)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_save_config_eof(self):
        logger.clear()
        config_ = Config()

        with patch.object(config_, '_print_all_available_elements'):
            with patch('builtins.input', side_effect=EOFError):
                result = config_.save_config()

        self.assertIsNone(result)
        self.assertIn('End-of-File', logger.output())

    def test__save_config_element_valid_input(self):
        config_ = Config()
        keyword = DKW.LARGE_FILE_SIZE
        config_.const_dic[keyword] = config_.default_dic[keyword]

        with patch('builtins.input', side_effect=['10']):
            with patch.object(config_, '_save_config') as mock_save:
                config_._save_config_element(keyword)

        mock_save.assert_called_once_with(keyword, '10')

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_element_retries_on_invalid_value(self):
        logger.clear()
        config_ = Config()
        keyword = DKW.LARGE_FILE_SIZE
        config_.const_dic[keyword] = config_.default_dic[keyword]

        with patch('builtins.input', side_effect=['abc', '10']):
            with patch.object(config_, '_save_config') as mock_save:
                config_._save_config_element(keyword)

        self.assertIn("Invalid option: 'abc'", logger.output())
        mock_save.assert_called_once_with(keyword, '10')

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_element_eof(self):
        logger.clear()
        config_ = Config()
        keyword = DKW.LARGE_FILE_SIZE
        config_.const_dic[keyword] = config_.default_dic[keyword]

        with patch('builtins.input', side_effect=EOFError):
            with patch.object(config_, '_save_config') as mock_save:
                self.assertIsNone(config_._save_config_element(keyword))

        mock_save.assert_not_called()
        self.assertIn('End-of-File', logger.output())

    def test__save_config_custom_command_with_value(self):
        config_ = Config()
        config_.custom_commands['-mycmd'] = ['-a', '-b']

        with patch('builtins.input', side_effect=['-n 10']):
            with patch.object(config_, '_save_config') as mock_save:
                config_._save_config_custom_command('-mycmd')

        mock_save.assert_called_once_with('-mycmd', '-n 10', 'COMMANDS')

    def test__save_config_custom_command_empty_value_removes(self):
        config_ = Config()
        config_.custom_commands['-mycmd'] = ['-a', '-b']
        config_.config_parser.add_section('COMMANDS')
        config_.config_parser.set('COMMANDS', '-mycmd', '"-a -b"')

        with patch('builtins.input', side_effect=['']):
            with patch.object(config_, '_save_config') as mock_save:
                config_._save_config_custom_command('-mycmd')

        self.assertFalse(config_.config_parser.has_option('COMMANDS', '-mycmd'))
        mock_save.assert_called_once_with(None)

    def test__save_config_custom_command_forwarded(self):
        config_ = Config()

        with patch('builtins.input', side_effect=['-n 10']):
            with patch.object(config_, '_save_config') as mock_save:
                config_._save_config_custom_command('-mycmd', True)

        mock_save.assert_called_once_with('-mycmd', '-n 10', 'COMMANDS')

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_custom_command_eof(self):
        logger.clear()
        config_ = Config()
        config_.custom_commands['-mycmd'] = ['-a', '-b']

        with patch('builtins.input', side_effect=EOFError):
            with patch.object(config_, '_save_config') as mock_save:
                self.assertIsNone(config_._save_config_custom_command('-mycmd'))

        mock_save.assert_not_called()
        self.assertIn('End-of-File', logger.output())

    def test__save_config_add_custom_command_valid(self):
        config_ = Config()

        with patch('builtins.input', side_effect=['-my-new-cmd']):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                config_._save_config_add_custom_command()

        mock_save_custom.assert_called_once_with('-my-new-cmd', True)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_add_custom_command_invalid_then_valid(self):
        logger.clear()
        config_ = Config()

        with patch('builtins.input', side_effect=['not-a-command', '-my-new-cmd']):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                config_._save_config_add_custom_command()

        self.assertIn("Invalid option: 'not-a-command'", logger.output())
        mock_save_custom.assert_called_once_with('-my-new-cmd', True)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_add_custom_command_rejects_duplicates(self):
        config_ = Config()
        config_.custom_commands['-my-new-cmd'] = ['-a']

        with patch('builtins.input', side_effect=['-my-new-cmd', '-my-other-cmd']):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                config_._save_config_add_custom_command()

        mock_save_custom.assert_called_once_with('-my-other-cmd', True)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_add_custom_command_rejects_existing_arg(self):
        config_ = Config()
        existing_arg = ALL_ARGS[0].short_form

        with patch('builtins.input', side_effect=[existing_arg, '-my-new-cmd']):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                config_._save_config_add_custom_command()

        mock_save_custom.assert_called_once_with('-my-new-cmd', True)

    @patch('cat_win.src.persistence.config.logger', logger)
    def test__save_config_add_custom_command_eof(self):
        logger.clear()
        config_ = Config()

        with patch('builtins.input', side_effect=EOFError):
            with patch.object(config_, '_save_config_custom_command') as mock_save_custom:
                self.assertIsNone(config_._save_config_add_custom_command())

        mock_save_custom.assert_not_called()
        self.assertIn('End-of-File', logger.output())

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_reset_config(self):
        config_ = Config()
        with patch('builtins.open', ErrorDefGen.get_def(OSError("Mocked Error"))):
            config_.reset_config()
        self.assertIn('Could not write', logger.output())
        self.assertListEqual(config_.config_parser.sections(), [])

        config_.config_parser.add_section('CONSTS')
        config_.config_parser.add_section('COMMANDS')
        with patch('builtins.open', mock_open()) as m_open:
            with patch.object(config_.config_parser, 'write') as m_write:
                config_.reset_config()
                m_open.assert_called_once_with(config_.config_file, 'w', encoding='utf-8')
                m_write.assert_called_once()
                file_handle = m_open()
                self.assertIs(file_handle, m_write.call_args[0][0])
        self.assertListEqual(config_.config_parser.sections(), [])

    @patch('cat_win.src.persistence.config.logger', logger)
    def test_remove_config(self):
        logger.clear()
        config_ = Config()
        with patch('os.remove', ErrorDefGen.get_def(FileNotFoundError("Mocked Error"))):
            config_.remove_config()
            self.assertIn('No active config file has been found.', logger.output())

        logger.clear()
        with patch('os.remove', ErrorDefGen.get_def(PermissionError("Mocked Error"))):
            config_.remove_config()
            self.assertIn('Permission denied', logger.output())

        logger.clear()
        with patch('os.remove', ErrorDefGen.get_def(OSError("Mocked Error"))):
            config_.remove_config()
            self.assertIn('unexpected error', logger.output())

        logger.clear()
        with patch('os.remove', lambda x: None):
            with patch('sys.stdout', new=StdOutMock()) as fake_out:
                config_.remove_config()
                self.assertIn('Successfull', fake_out.getvalue())
