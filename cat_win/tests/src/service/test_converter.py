from unittest import TestCase

from cat_win.src.service.converter import Converter
# import sys
# sys.path.append('../cat_win')


converter = Converter()
debug_converter = Converter()
debug_converter.set_params(True)

class TestConverter(TestCase):
    def test_converter_dec(self):
        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Hex: 0x3039]'
        self.assertEqual(converter.c_from_dec('12345', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Hex: 3039]'
        self.assertEqual(converter.c_from_dec('12345', False), expected_output)

    def test_converter_hex(self):
        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Dec: 12345]'
        self.assertEqual(converter.c_from_hex('0x3039', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Dec: 12345]'
        self.assertEqual(converter.c_from_hex('0x3039', False), expected_output)

        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Dec: 12345]'
        self.assertEqual(converter.c_from_hex('3039', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Dec: 12345]'
        self.assertEqual(converter.c_from_hex('3039', False), expected_output)

    def test_converter_bin(self):
        expected_output = '[Oct: 0o30071, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(converter.c_from_bin('0b11000000111001', True), expected_output)

        expected_output = '[Oct: 30071, Dec: 12345, Hex: 3039]'
        self.assertEqual(converter.c_from_bin('0b11000000111001', False), expected_output)

        expected_output = '[Oct: 0o30071, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(converter.c_from_bin('11000000111001', True), expected_output)

        expected_output = '[Oct: 30071, Dec: 12345, Hex: 3039]'
        self.assertEqual(converter.c_from_bin('11000000111001', False), expected_output)

    def test_converter_oct(self):
        expected_output = '[Bin: 0b11000000111001, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(converter.c_from_oct('0o30071', True), expected_output)

        expected_output = '[Bin: 11000000111001, Dec: 12345, Hex: 3039]'
        self.assertEqual(converter.c_from_oct('0o30071', False), expected_output)

        expected_output = '[Bin: 0b11000000111001, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(converter.c_from_oct('30071', True), expected_output)

        expected_output = '[Bin: 11000000111001, Dec: 12345, Hex: 3039]'
        self.assertEqual(converter.c_from_oct('30071', False), expected_output)

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

    def test_evaluate_integrated(self):
        self.assertEqual(converter.evaluate('test11**2test', True), 'test121test')
        self.assertEqual(converter.evaluate('test(5/(3-0x3))test', True), 'test???test')

    def test_evaluate_not_integrated(self):
        self.assertEqual(converter.evaluate('test11**2test', False), '121')
        self.assertEqual(converter.evaluate('test(5/(3-0x3))test', False), '???')

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
