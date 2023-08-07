from unittest import TestCase

from cat_win.util.converter import Converter
# import sys
# sys.path.append('../cat_win')


converter = Converter()
debug_converter = Converter()
debug_converter.set_params(True)

class TestConverter(TestCase):
    def test_converter_dec(self):
        expected_output = '{Hexadecimal: 0x3039; Binary: 0b11000000111001}'
        self.assertEqual(converter.c_from_dec('12345', True), expected_output)

        expected_output = '{Hexadecimal: 3039; Binary: 11000000111001}'
        self.assertEqual(converter.c_from_dec('12345', False), expected_output)

    def test_converter_hex(self):
        expected_output = '{Decimal: 12345; Binary: 0b11000000111001}'
        self.assertEqual(converter.c_from_hex('0x3039', True), expected_output)

        expected_output = '{Decimal: 12345; Binary: 11000000111001}'
        self.assertEqual(converter.c_from_hex('0x3039', False), expected_output)

        expected_output = '{Decimal: 12345; Binary: 0b11000000111001}'
        self.assertEqual(converter.c_from_hex('3039', True), expected_output)

        expected_output = '{Decimal: 12345; Binary: 11000000111001}'
        self.assertEqual(converter.c_from_hex('3039', False), expected_output)

    def test_converter_bin(self):
        expected_output = '{Decimal: 12345; Hexadecimal: 0x3039}'
        self.assertEqual(converter.c_from_bin(
            '0b11000000111001', True), expected_output)

        expected_output = '{Decimal: 12345; Hexadecimal: 3039}'
        self.assertEqual(converter.c_from_bin(
            '0b11000000111001', False), expected_output)

        expected_output = '{Decimal: 12345; Hexadecimal: 0x3039}'
        self.assertEqual(converter.c_from_bin(
            '11000000111001', True), expected_output)

        expected_output = '{Decimal: 12345; Hexadecimal: 3039}'
        self.assertEqual(converter.c_from_bin(
            '11000000111001', False), expected_output)

    def test_empty_input(self):
        expected_output = False
        self.assertEqual(converter.is_dec(''), expected_output)
        self.assertEqual(converter.is_hex(''), expected_output)
        self.assertEqual(converter.is_bin(''), expected_output)

    def test_correct_input(self):
        expected_output = True
        self.assertEqual(converter.is_dec('1'), expected_output)
        self.assertEqual(converter.is_dec('-1'), expected_output)
        self.assertEqual(converter.is_dec('999'), expected_output)

        self.assertEqual(converter.is_hex('1'), expected_output)
        self.assertEqual(converter.is_hex('-1'), expected_output)
        self.assertEqual(converter.is_hex('999'), expected_output)
        self.assertEqual(converter.is_hex('0x999'), expected_output)
        self.assertEqual(converter.is_hex('-0x999'), expected_output)

        self.assertEqual(converter.is_bin('1'), expected_output)
        self.assertEqual(converter.is_bin('-1'), expected_output)
        self.assertEqual(converter.is_bin('0101'), expected_output)
        self.assertEqual(converter.is_bin('0b0101'), expected_output)
        self.assertEqual(converter.is_bin('-0b0101'), expected_output)

    def test_wrong_input(self):
        expected_output = False
        self.assertEqual(converter.is_dec('0x1'), expected_output)
        self.assertEqual(converter.is_dec('1.5'), expected_output)

        self.assertEqual(converter.is_hex('FG'), expected_output)
        self.assertEqual(converter.is_hex('0x-999'), expected_output)

        self.assertEqual(converter.is_bin('2'), expected_output)
        self.assertEqual(converter.is_bin('0x1'), expected_output)

    def test_exception_handler(self):
        exc = ZeroDivisionError()
        group = '1/0'
        l_tokens = []
        converter._evaluate_exception_handler(exc, group, l_tokens)
        
        self.assertListEqual(l_tokens, ['???'])

    def test_exception_handler_known_exc(self):
        exc = ZeroDivisionError('TeSt')
        group = '1/0'
        l_tokens = ['5']
        debug_converter._evaluate_exception_handler(exc, group, l_tokens)
        
        self.assertListEqual(l_tokens, ['5', "???(ZeroDivisionError: TeSt in '1/0')"])

    def test_exception_handler_unknown_exc(self):
        exc = IndexError('NotGood')
        group = '1/0'
        l_tokens = ['5']
        with self.assertRaises(type(exc)) as context:
            debug_converter._evaluate_exception_handler(exc, group, l_tokens)
        self.assertIn('NotGood', context.exception.args)
        self.assertListEqual(l_tokens, ['5', "???(IndexError: NotGood in '1/0')"])
