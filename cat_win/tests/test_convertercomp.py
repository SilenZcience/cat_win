from unittest import TestCase

from cat_win.const.argconstants import ARGS_EVAL, ALL_ARGS
from cat_win.cat import remove_ansi_codes_from_line as cleaner
from cat_win.util.converter import Converter
try:
    from cat_win.util.convertercomp import comp_eval, comp_conv
except SyntaxError: # in case of Python 3.7
    from cat_win.util.convertercompold import comp_eval, comp_conv

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
        ]
        new_content = comp_eval(converter, test_content_in, param_lowercase)
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
        ]
        test_content_out = [
            ('', '30'),
            ('', '48'),
            ('', '4'),
            ('2*2', '3'),
            ('', '-4.5'),
            ('', '10,0'),
            ('', '2'),
        ]
        new_content = comp_eval(converter, test_content_in, param_uppercase)
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
            ('', '30 {Hexadecimal: 0x1e; Binary: 0b11110}'),
            ('', '48 {Hexadecimal: 0x30; Binary: 0b110000}'),
            ('', '1001 {Hexadecimal: 0x3e9; Binary: 0b1111101001}'),
        ]
        new_content = comp_conv(converter, test_content_in, '--dec', cleaner, ['', ''])
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
            ('', '30 {Decimal: 48; Binary: 0b110000}'),
            ('', '48 {Decimal: 72; Binary: 0b1001000}'),
            ('5+5', 'abc {Decimal: 2748; Binary: 0b101010111100}'),
            ('', '1001 {Decimal: 4097; Binary: 0b1000000000001}'),
            ('', '0b1001 {Decimal: 724993; Binary: 0b10110001000000000001}'),
            ('', '0x1001 {Decimal: 4097; Binary: 0b1000000000001}'),
        ]
        new_content = comp_conv(converter, test_content_in, '--hex', cleaner, ['', ''])
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
            ('', '1001 {Decimal: 9; Hexadecimal: 0x9}'),
            ('', '0b1001 {Decimal: 9; Hexadecimal: 0x9}'),
        ]
        new_content = comp_conv(converter, test_content_in, '--bin', cleaner, ['', ''])
        self.assertListEqual(new_content, test_content_out)

# python -m unittest discover -s cat_win.tests -p test*.py
