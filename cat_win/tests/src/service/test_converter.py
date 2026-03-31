from unittest import TestCase

from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.converter import Converter
# import sys
# sys.path.append('../cat_win')


class TestConverter(TestCase):
    def test_converter_dec(self):
        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Hex: 0x3039]'
        self.assertEqual(Converter.c_from_dec('12345', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Hex: 3039]'
        self.assertEqual(Converter.c_from_dec('12345', False), expected_output)

    def test_converter_hex(self):
        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Dec: 12345]'
        self.assertEqual(Converter.c_from_hex('0x3039', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Dec: 12345]'
        self.assertEqual(Converter.c_from_hex('0x3039', False), expected_output)

        expected_output = '[Bin: 0b11000000111001, Oct: 0o30071, Dec: 12345]'
        self.assertEqual(Converter.c_from_hex('3039', True), expected_output)

        expected_output = '[Bin: 11000000111001, Oct: 30071, Dec: 12345]'
        self.assertEqual(Converter.c_from_hex('3039', False), expected_output)

    def test_converter_bin(self):
        expected_output = '[Oct: 0o30071, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(Converter.c_from_bin('0b11000000111001', True), expected_output)

        expected_output = '[Oct: 30071, Dec: 12345, Hex: 3039]'
        self.assertEqual(Converter.c_from_bin('0b11000000111001', False), expected_output)

        expected_output = '[Oct: 0o30071, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(Converter.c_from_bin('11000000111001', True), expected_output)

        expected_output = '[Oct: 30071, Dec: 12345, Hex: 3039]'
        self.assertEqual(Converter.c_from_bin('11000000111001', False), expected_output)

    def test_converter_oct(self):
        expected_output = '[Bin: 0b11000000111001, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(Converter.c_from_oct('0o30071', True), expected_output)

        expected_output = '[Bin: 11000000111001, Dec: 12345, Hex: 3039]'
        self.assertEqual(Converter.c_from_oct('0o30071', False), expected_output)

        expected_output = '[Bin: 0b11000000111001, Dec: 12345, Hex: 0x3039]'
        self.assertEqual(Converter.c_from_oct('30071', True), expected_output)

        expected_output = '[Bin: 11000000111001, Dec: 12345, Hex: 3039]'
        self.assertEqual(Converter.c_from_oct('30071', False), expected_output)

    def test_empty_input(self):
        expected_output = False
        self.assertEqual(Converter.is_dec(''), expected_output)
        self.assertEqual(Converter.is_hex(''), expected_output)
        self.assertEqual(Converter.is_bin(''), expected_output)

    def test_correct_input(self):
        expected_output = True
        self.assertEqual(Converter.is_dec('1'), expected_output)
        self.assertEqual(Converter.is_dec('-1'), expected_output)
        self.assertEqual(Converter.is_dec('999'), expected_output)

        self.assertEqual(Converter.is_hex('1'), expected_output)
        self.assertEqual(Converter.is_hex('-1'), expected_output)
        self.assertEqual(Converter.is_hex('999'), expected_output)
        self.assertEqual(Converter.is_hex('0x999'), expected_output)
        self.assertEqual(Converter.is_hex('-0x999'), expected_output)

        self.assertEqual(Converter.is_bin('1'), expected_output)
        self.assertEqual(Converter.is_bin('-1'), expected_output)
        self.assertEqual(Converter.is_bin('0101'), expected_output)
        self.assertEqual(Converter.is_bin('0b0101'), expected_output)
        self.assertEqual(Converter.is_bin('-0b0101'), expected_output)

        self.assertEqual(Converter.is_oct('1'), expected_output)
        self.assertEqual(Converter.is_oct('-1'), expected_output)
        self.assertEqual(Converter.is_oct('-0o0101'), expected_output)
        self.assertEqual(Converter.is_oct('0o777'), expected_output)

    def test_wrong_input(self):
        expected_output = False
        self.assertEqual(Converter.is_dec('0x1'), expected_output)
        self.assertEqual(Converter.is_dec('1.5'), expected_output)

        self.assertEqual(Converter.is_hex('FG'), expected_output)
        self.assertEqual(Converter.is_hex('0x-999'), expected_output)

        self.assertEqual(Converter.is_bin('2'), expected_output)
        self.assertEqual(Converter.is_bin('0x1'), expected_output)

        self.assertEqual(Converter.is_bin('8'), expected_output)
        self.assertEqual(Converter.is_bin('0x1'), expected_output)

    def test_evaluate_integrated(self):
        self.assertEqual(Converter.evaluate('test11**2test', True), 'test121test')
        self.assertEqual(Converter.evaluate('test(5/(3-0x3))test', True), 'test???test')
        self.assertEqual(Converter.evaluate('', True), '')

    def test_evaluate_not_integrated(self):
        self.assertEqual(Converter.evaluate('test11**2test', False), '121')
        self.assertEqual(Converter.evaluate('test(5/(3-0x3))test', False), '???')
        self.assertEqual(Converter.evaluate('', False), None)

    def test_evaluate_syntaxerror_leading_paren_recovery_integrated(self):
        # Triggers p_diff > 0 branch and integrated insertion of unmatched opening parenthesis.
        self.assertEqual(Converter.evaluate('A((1+2)B', True), 'A(3B')

    def test_evaluate_syntaxerror_trailing_paren_recovery_integrated(self):
        # Triggers p_diff < 0 branch and keeps unmatched closing parenthesis in remaining text.
        self.assertEqual(Converter.evaluate('A1+2))B', True), 'A3))B')

    def test_evaluate_syntaxerror_unrecoverable_marks_unknown(self):
        # Triggers the fallback SyntaxError marker branch (p_diff does not match recoverable shapes).
        self.assertEqual(Converter.evaluate('A1+(2*3B', True), 'A??????B')

    def test_evaluate_syntaxerror_inner_arithmetic_error_handler(self):
        # Triggers p_diff > 0 branch where inner eval raises ArithmeticError and is routed to handler.
        self.assertEqual(Converter.evaluate('A((1/0)B', True), 'A???B')

    def test_exception_handler(self):
        exc = ZeroDivisionError()
        group = '1/0'
        l_tokens = []
        Converter._evaluate_exception_handler(exc, group, l_tokens)

        self.assertListEqual(l_tokens, ['???'])

    def test_exception_handler_known_exc(self):
        exc = ZeroDivisionError('TeSt')
        group = '1/0'
        l_tokens = ['5']
        backup = Converter.debug_mode
        Converter.debug_mode = True
        Converter._evaluate_exception_handler(exc, group, l_tokens)
        Converter.debug_mode = backup

        self.assertListEqual(l_tokens, ['5', "???(ZeroDivisionError: TeSt in '1/0')"])

    def test_exception_handler_unknown_exc(self):
        exc = IndexError('NotGood')
        group = '1/0'
        l_tokens = ['5']
        backup = Converter.debug_mode
        Converter.debug_mode = True
        with self.assertRaises(type(exc)) as context:
            Converter._evaluate_exception_handler(exc, group, l_tokens)
        Converter.debug_mode = backup
        self.assertIn('NotGood', context.exception.args)
        self.assertListEqual(l_tokens, ['5', "???(IndexError: NotGood in '1/0')"])

    def test_set_flags(self):
        backup = Converter.debug_mode
        Converter.set_flags(True)
        self.assertTrue(Converter.debug_mode)
        Converter.set_flags(False)
        self.assertFalse(Converter.debug_mode)
        Converter.set_flags(backup)

    def test_set_colors(self):
        old_evaluation = Converter.COLOR_EVALUATION
        old_conversion = Converter.COLOR_CONVERSION
        old_reset = Converter.COLOR_RESET

        color_dic = {
            CKW.EVALUATION: '\033[91m',
            CKW.CONVERSION: '\033[92m',
            CKW.RESET_ALL: '\033[0m',
        }
        Converter.set_colors(color_dic)
        self.assertEqual(Converter.COLOR_EVALUATION, '\033[91m')
        self.assertEqual(Converter.COLOR_CONVERSION, '\033[92m')
        self.assertEqual(Converter.COLOR_RESET, '\033[0m')

        color_dic = {
            CKW.EVALUATION: old_evaluation,
            CKW.CONVERSION: old_conversion,
            CKW.RESET_ALL: old_reset,
        }
        Converter.set_colors(color_dic)
        self.assertEqual(Converter.COLOR_EVALUATION, old_evaluation)
        self.assertEqual(Converter.COLOR_CONVERSION, old_conversion)
        self.assertEqual(Converter.COLOR_RESET, old_reset)
