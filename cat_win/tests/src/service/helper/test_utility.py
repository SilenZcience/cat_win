from unittest import TestCase

from cat_win.src.const.argconstants import ARGS_EVAL, ALL_ARGS
from cat_win.src.cat import remove_ansi_codes_from_line as cleaner
from cat_win.src.service.converter import Converter
try:
    from cat_win.src.service.helper.utility import comp_eval, comp_conv
except SyntaxError: # in case of Python 3.7
    from cat_win.src.service.helper.utilityold import comp_eval, comp_conv

# import sys
# sys.path.append('../cat_win')
converter = Converter()
param_lowercase, param_uppercase = '', ''
for arg in ALL_ARGS:
    if arg.arg_id == ARGS_EVAL:
        param_lowercase = arg.short_form
        param_uppercase = arg.long_form
        break


class TestConverterComp(TestCase):
    maxDiff = None

    def test_comp_eval_lowercase(self):
        test_content_in = [
            ('', '5 +5 * 5'),
            ('', '7**2 -   1'),
            ('', 'hello2+2world'),
            ('2*2', '7//2 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-9   /2'),
            ('', 'hello 5+5 world 5-5 test'),
            ('', ' 8%  3 4'),
            ('', 'xyz 1) + (1 + 1 xyz 7+7'),
            ('', 'xyz (1 + (1)) + (1) xyz'),
            ('', 'xyz (((1 + (1)) + (1) xyz'),
            ('', 'xyz (1 + (1)) + (1))) xyz'),
        ]
        test_content_out = [
            ('', '30'),
            ('', '48'),
            ('', 'hello4world'),
            ('2*2', '3 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-4.5'),
            ('', 'hello 10 world 0 test'),
            ('', ' 2 4'),
            ('', 'xyz ??????????? xyz 14'),
            ('', 'xyz 3 xyz'),
            ('', 'xyz ((3 xyz'),
            ('', 'xyz 3)) xyz'),
        ]
        new_content = comp_eval(converter, test_content_in, param_lowercase, cleaner)
        self.assertListEqual(new_content, test_content_out)

    def test_comp_eval_uppercase(self):
        test_content_in = [
            ('', '5 +5 * 5'),
            ('', '7**2 -   1'),
            ('', 'hello2+2world'),
            ('2*2', '7//2 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-9   /2'),
            ('', 'hello 5+5 world 5-5 test'),
            ('', ' 8%  3 4'),
            ('', 'xyz 1) + (1 + 1 xyz 7+7'),
            ('', 'xyz (1 + (1)) + (1) xyz'),
            ('', 'xyz (((1 + (1)) + (1) xyz'),
            ('', 'xyz (1 + (1)) + (1))) xyz'),
        ]
        test_content_out = [
            ('', '30'),
            ('', '48'),
            ('', '4'),
            ('2*2', '3'),
            ('', '-4.5'),
            ('', '10,0'),
            ('', '2'),
            ('', '?,14'),
            ('', '3'),
            ('', '3'),
            ('', '3'),
        ]
        new_content = comp_eval(converter, test_content_in, param_uppercase, cleaner)
        self.assertListEqual(new_content, test_content_out)

    def test_comp_conv_dec(self):
        test_content_in = [
            ('', '30'),
            ('', '48'),
            ('', 'hello4world'),
            ('2*2', '3 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-4.5'),
            ('', '1001'),
            ('', '0b1001'),
            ('', '0x1001'),
        ]
        test_content_out = [
            ('', '30 [Bin: 0b11110, Oct: 0o36, Hex: 0x1e]'),
            ('', '48 [Bin: 0b110000, Oct: 0o60, Hex: 0x30]'),
            ('', '1001 [Bin: 0b1111101001, Oct: 0o1751, Hex: 0x3e9]'),
        ]
        new_content = comp_conv(converter, test_content_in, '--dec', cleaner)
        self.assertListEqual(new_content, test_content_out)

    def test_comp_conv_hex(self):
        test_content_in = [
            ('', '30'),
            ('', '48'),
            ('', 'hello4world'),
            ('2*2', '3 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-4.5'),
            ('', '1001'),
            ('', '0b1001'),
            ('', '0x1001'),
        ]
        test_content_out = [
            ('', '30 [Bin: 0b110000, Oct: 0o60, Dec: 48]'),
            ('', '48 [Bin: 0b1001000, Oct: 0o110, Dec: 72]'),
            ('5+5', 'abc [Bin: 0b101010111100, Oct: 0o5274, Dec: 2748]'),
            ('', '1001 [Bin: 0b1000000000001, Oct: 0o10001, Dec: 4097]'),
            ('', '0b1001 [Bin: 0b10110001000000000001, Oct: 0o2610001, Dec: 724993]'),
            ('', '0x1001 [Bin: 0b1000000000001, Oct: 0o10001, Dec: 4097]'),
        ]
        new_content = comp_conv(converter, test_content_in, '--hex', cleaner)
        self.assertListEqual(new_content, test_content_out)

    def test_comp_conv_oct(self):
        test_content_in = [
            ('', '30'),
            ('', '48'),
            ('', 'hello4world'),
            ('2*2', '3 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-4.5'),
            ('', '1001'),
            ('', '0b1001'),
            ('', '0x1001'),
        ]
        test_content_out = [
            ('', '30 [Bin: 0b11000, Dec: 24, Hex: 0x18]'),
            ('', '1001 [Bin: 0b1000000001, Dec: 513, Hex: 0x201]'),
        ]
        new_content = comp_conv(converter, test_content_in, '--oct', cleaner)
        self.assertListEqual(new_content, test_content_out)

    def test_comp_conv_bin(self):
        test_content_in = [
            ('', '30'),
            ('', '48'),
            ('', 'hello4world'),
            ('2*2', '3 xyz'),
            ('5+5', 'abc'),
            ('', 'abc-4.5'),
            ('', '1001'),
            ('', '0b1001'),
            ('', '0x1001'),
        ]
        test_content_out = [
            ('', '1001 [Oct: 0o11, Dec: 9, Hex: 0x9]'),
            ('', '0b1001 [Oct: 0o11, Dec: 9, Hex: 0x9]'),
        ]
        new_content = comp_conv(converter, test_content_in, '--bin', cleaner)
        self.assertListEqual(new_content, test_content_out)

# python -m unittest discover -s cat_win.tests -p test*.py
