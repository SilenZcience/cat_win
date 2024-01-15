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


class TestConfig(TestCase):
    maxDiff = None

    def test_convert_config_element(self):
        self.assertEqual(Config.convert_config_element('15', int), 15)
        self.assertEqual(Config.convert_config_element('7.4', float), 7.4)
        self.assertEqual(Config.convert_config_element('15', list), ['1', '5'])
        self.assertEqual(Config.convert_config_element('false', bool), False)
        self.assertEqual(Config.convert_config_element('FALSE', bool), False)
        self.assertEqual(Config.convert_config_element('no', bool), False)
        self.assertEqual(Config.convert_config_element('n', bool), False)
        self.assertEqual(Config.convert_config_element('0', bool), False)
        self.assertEqual(Config.convert_config_element('nfalse', bool), True)
        self.assertEqual(Config.convert_config_element('1', bool), True)

    def test_is_valid_value(self):
        self.assertEqual(Config.is_valid_value('', int), False)
        self.assertEqual(Config.is_valid_value('a', int), False)
        self.assertEqual(Config.is_valid_value('a', str), True)
        self.assertEqual(Config.is_valid_value(5, float), True)
        self.assertEqual(Config.is_valid_value(5, int), True)
        self.assertEqual(Config.is_valid_value('True', bool), True)
        self.assertEqual(Config.is_valid_value('TrUe', bool), True)
        self.assertEqual(Config.is_valid_value('FaLSe', bool), True)
        self.assertEqual(Config.is_valid_value('Yes', bool), True)
        self.assertEqual(Config.is_valid_value('y', bool), True)
        self.assertEqual(Config.is_valid_value('nO', bool), True)
        self.assertEqual(Config.is_valid_value('n', bool), True)
        self.assertEqual(Config.is_valid_value('0', bool), True)
        self.assertEqual(Config.is_valid_value('1', bool), True)
        self.assertEqual(Config.is_valid_value('tru', bool), False)

    def test_load_config(self):
        config.const_dic[DKW.DEFAULT_COMMAND_LINE] = '-nl "find= "'
        self.assertListEqual(config.get_cmd(), ['-nl', 'find= '])

    def test__print_all_available_elements(self):
        all_elements = list(config.default_dic.keys())

        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            config._print_all_available_elements()
            for i, k in enumerate(all_elements, start=1):
                self.assertIn(str(i), fake_out.getvalue())
                self.assertIn(k, fake_out.getvalue())
