from unittest import TestCase

from cat_win.src.const.argconstants import ARGS_EVAL, ALL_ARGS
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.service.querymanager import remove_ansi_codes_from_line as cleaner
try:
    from cat_win.src.service.helper.utility import comp_eval, comp_conv
except SyntaxError: # in case of Python 3.7
    from cat_win.src.service.helper.utilityold import comp_eval, comp_conv

# import sys
# sys.path.append('../cat_win')
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
            ('5 +5 * 5'),
            ('7**2 -   1'),
            ('hello2+2world'),
            ('7//2 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-9   /2'),
            ('hello 5+5 world 5-5 test'),
            (' 8%  3 4'),
            ('xyz 1) + (1 + 1 xyz 7+7'),
            ('xyz (1 + (1)) + (1) xyz'),
            ('xyz (((1 + (1)) + (1) xyz'),
            ('xyz (1 + (1)) + (1))) xyz'),
        ]
        test_content_out = [
            ('30'),
            ('48'),
            ('hello4world'),
            ('3 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-4.5'),
            ('hello 10 world 0 test'),
            (' 2 4'),
            ('xyz ??????????? xyz 14'),
            ('xyz 3 xyz'),
            ('xyz ((3 xyz'),
            ('xyz 3)) xyz'),
        ]
        new_content = comp_eval(ContentBuffer.from_rows(test_content_in), param_lowercase, cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

    def test_comp_eval_uppercase(self):
        test_content_in = [
            ('5 +5 * 5'),
            ('7**2 -   1'),
            ('hello2+2world'),
            ('7//2 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-9   /2'),
            ('hello 5+5 world 5-5 test'),
            (' 8%  3 4'),
            ('xyz 1) + (1 + 1 xyz 7+7'),
            ('xyz (1 + (1)) + (1) xyz'),
            ('xyz (((1 + (1)) + (1) xyz'),
            ('xyz (1 + (1)) + (1))) xyz'),
        ]
        test_content_out = [
            ('30'),
            ('48'),
            ('4'),
            ('3', '2*2'),
            ('-4.5'),
            ('10,0'),
            ('2'),
            ('?,14'),
            ('3'),
            ('3'),
            ('3'),
        ]
        new_content = comp_eval(ContentBuffer.from_rows(test_content_in), param_uppercase, cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

    def test_comp_conv_dec(self):
        test_content_in = [
            ('30'),
            ('48'),
            ('hello4world'),
            ('3 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-4.5'),
            ('1001'),
            ('0b1001'),
            ('0x1001'),
        ]
        test_content_out = [
            ('30', '', r" [Bin 0b00011110; Oct 0o36; Int8 30/30; Hex 0x1E; Utf8 \x1e]"),
            ('48', '', ' [Bin 0b00110000; Oct 0o60; Int8 48/48; Hex 0x30; Utf8 0]'),
            ('1001', '', r" [Bin 0b0000001111101001; Oct 0o1751; Int16 1001/1001; Hex 0x3E9; Utf8 \x03�]"),
        ]
        new_content = comp_conv(ContentBuffer.from_rows(test_content_in), '--dec', cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

    def test_comp_conv_hex(self):
        test_content_in = [
            ('30'),
            ('48', '', 'test'),
            ('hello4world'),
            ('3 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-4.5'),
            ('1001'),
            ('0b1001'),
            ('0x1001'),
        ]
        test_content_out = [
            ('30', '', ' [Bin 0b00110000; Oct 0o60; Int8 48/48; Hex 0x30; Utf8 0]'),
            ('48', '', 'test [Bin 0b01001000; Oct 0o110; Int8 72/72; Hex 0x48; Utf8 H]'),
            ('abc', '5+5', r" [Bin 0b0000101010111100; Oct 0o5274; Int16 2748/2748; Hex 0xABC; Utf8 \n�]"),
            ('1001', '', r" [Bin 0b0001000000000001; Oct 0o10001; Int16 4097/4097; Hex 0x1001; Utf8 \x10\x01]"),
            ('0b1001', '', r" [Bin 0b00000000000010110001000000000001; Oct 0o2610001; Int32 724993/724993; Hex 0xB1001; Utf8 \x00\x0b\x10\x01]"),
            ('0x1001', '', r" [Bin 0b0001000000000001; Oct 0o10001; Int16 4097/4097; Hex 0x1001; Utf8 \x10\x01]"),
        ]
        new_content = comp_conv(ContentBuffer.from_rows(test_content_in), '--hex', cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

    def test_comp_conv_oct(self):
        test_content_in = [
            ('30'),
            ('48'),
            ('hello4world'),
            ('3 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-4.5'),
            ('1001'),
            ('0b1001'),
            ('0x1001'),
        ]
        test_content_out = [
            ('30', '', r" [Bin 0b00011000; Oct 0o30; Int8 24/24; Hex 0x18; Utf8 \x18]"),
            ('1001', '', r" [Bin 0b0000001000000001; Oct 0o1001; Int16 513/513; Hex 0x201; Utf8 \x02\x01]"),
        ]
        new_content = comp_conv(ContentBuffer.from_rows(test_content_in), '--oct', cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

    def test_comp_conv_bin(self):
        test_content_in = [
            ('30'),
            ('48'),
            ('hello4world'),
            ('3 xyz', '2*2'),
            ('abc', '5+5'),
            ('abc-4.5'),
            ('1001'),
            ('0b1001'),
            ('0x1001'),
        ]
        test_content_out = [
            ('1001', '', r" [Bin 0b00001001; Oct 0o11; Int8 9/9; Hex 0x9; Utf8 \t]"),
            ('0b1001', '', r" [Bin 0b00001001; Oct 0o11; Int8 9/9; Hex 0x9; Utf8 \t]"),
        ]
        new_content = comp_conv(ContentBuffer.from_rows(test_content_in), '--bin', cleaner)
        self.assertEqual(new_content, ContentBuffer.from_rows(test_content_out))

# python -m unittest discover -s cat_win.tests -p test*.py
