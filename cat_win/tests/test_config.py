from unittest.mock import patch
from unittest import TestCase
import os

from cat_win.const.defaultconstants import DKW
from cat_win.tests.mocks.std import StdOutMock
from cat_win.persistence.config import Config
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
config = Config(test_file_dir)
config.load_config()


@patch('os.get_terminal_size', lambda: (120, 30))
class TestConfig(TestCase):
    maxDiff = None

    def test_convert_config_element(self):
        self.assertEqual(config.convert_config_element('"15"', DKW.LARGE_FILE_SIZE), 15)
        self.assertEqual(config.convert_config_element('"7"', DKW.LARGE_FILE_SIZE), 7)
        self.assertEqual(config.convert_config_element('"15"', DKW.DEFAULT_COMMAND_LINE), "15")
        self.assertEqual(config.convert_config_element('"false"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config.convert_config_element('"FALSE"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config.convert_config_element('"no"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config.convert_config_element('"n"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config.convert_config_element('"0"', DKW.STRIP_COLOR_ON_PIPE), False)
        self.assertEqual(config.convert_config_element('"1"', DKW.STRIP_COLOR_ON_PIPE), True)

    def test_is_valid_value(self):
        self.assertEqual(config.is_valid_value('', DKW.DEFAULT_COMMAND_LINE), True)
        self.assertEqual(config.is_valid_value('', DKW.LARGE_FILE_SIZE), False)
        self.assertEqual(config.is_valid_value('a', DKW.LARGE_FILE_SIZE), False)
        self.assertEqual(config.is_valid_value('a', DKW.EDITOR_INDENTATION), True)
        self.assertEqual(config.is_valid_value("5", DKW.STRINGS_MIN_SEQUENCE_LENGTH), True)
        self.assertEqual(config.is_valid_value("5", DKW.LARGE_FILE_SIZE), True)
        self.assertEqual(config.is_valid_value('True', DKW.BINARY_HEX_VIEW), True)
        self.assertEqual(config.is_valid_value('TrUe', DKW.EDITOR_AUTO_INDENT), True)
        self.assertEqual(config.is_valid_value('FaLSe', DKW.EDITOR_AUTO_INDENT), True)
        self.assertEqual(config.is_valid_value('Yes', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('y', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('nO', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('n', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('0', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('1', DKW.STRIP_COLOR_ON_PIPE), True)
        self.assertEqual(config.is_valid_value('tru', DKW.STRIP_COLOR_ON_PIPE), False)

    def test_load_config(self):
        config.const_dic[DKW.DEFAULT_COMMAND_LINE] = '-nl "find= "'
        self.assertListEqual(config.get_cmd(), ['-nl', 'find= '])

    def test__print_all_available_elements(self):
        all_elements = list(config.default_dic.keys())

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            config._print_all_available_elements()
            for i, k in enumerate(all_elements, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(k, fake_out.getvalue())
