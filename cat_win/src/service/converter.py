"""
converter
"""

from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.regex import RE_EVAL


def __hex_to_dec__(value: str) -> str:
    return str(int(value, 16))

def __hex_to_oct__(value: str, leading: bool = False) -> str:
    return __dec_to_oct__(int(value, 16), leading)

def __hex_to_bin__(value: str, leading: bool = False) -> str:
    return __dec_to_bin__(int(value, 16), leading)


def __dec_to_hex__(value: int, leading: bool = False) -> str:
    return f"{value:#x}" if leading else f"{value:x}"

def __dec_to_oct__(value: int, leading: bool = False) -> str:
    return f"{value:#o}" if leading else f"{value:o}"

def __dec_to_bin__(value: int, leading: bool = False) -> str:
    return f"{value:#b}" if leading else f"{value:b}"


def __oct_to_hex__(value: str, leading: bool = False) -> str:
    return __dec_to_hex__(int(value, 8), leading)

def __oct_to_dec__(value: str) -> str:
    return str(int(value, 8))

def __oct_to_bin__(value: str, leading: bool = False) -> str:
    return __dec_to_bin__(int(value, 8), leading)


def __bin_to_hex__(value: str, leading: bool = False) -> str:
    return __dec_to_hex__(int(value, 2), leading)

def __bin_to_dec__(value: str) -> str:
    return str(int(value, 2))

def __bin_to_oct__(value: str, leading: bool = False) -> str:
    return __dec_to_oct__(int(value, 2), leading)


class Converter:
    """
    converts a binary, octal, decimal or hex number
    into the corresponding others, or evaluates an expression.
    """

    bindigits = '01'
    octdigits = '01234567'
    hexdigits = '0123456789abcdefABCDEF'

    COLOR_EVALUATION: str = ''
    COLOR_CONVERSION: str = ''
    COLOR_RESET: str      = ''

    debug_mode = False

    @staticmethod
    def set_flags(debug: bool) -> None:
        """
        set the flags to use.

        Parameters:
        debug (bool):
            indicates if debug output should be displayed
        """
        Converter.debug_mode = debug

    @staticmethod
    def set_colors(color_dic: dict) -> None:
        """
        set the colors to use.

        Parameters:
        color_dic (dict):
            color dictionary containing all configured ANSI color values
        """
        Converter.COLOR_EVALUATION = color_dic[CKW.EVALUATION]
        Converter.COLOR_CONVERSION = color_dic[CKW.CONVERSION]
        Converter.COLOR_RESET      = color_dic[CKW.RESET_ALL]

    @staticmethod
    def _evaluate_exception_handler(exc: Exception, _group: str, new_l_tokens: list) -> None:
        debug_token = ''
        if Converter.debug_mode:
            debug_token = f"({type(exc).__name__}: {exc} in {repr(_group)})"
        new_token = f"{Converter.COLOR_EVALUATION}???{debug_token}{Converter.COLOR_RESET}"
        new_l_tokens.append(new_token)

        expected_errors = [ValueError, ArithmeticError]
         # anything else should be raised again, since it is not expected here
        if not any(isinstance(exc, error) for error in expected_errors):
            raise exc

    @staticmethod
    def evaluate(_l: str, integrated: bool) -> str:
        """
        evaluate simple mathematical expression within any text

        Parameters:
        _l (str):
            the line of content to work with
        integrated (bool):
            indicates whether or not solely the not-matched
            parts should stay within the line

        Returns:
        (str):
            the new content line with the evaluated expression
        """
        new_l_tokens = []
        res = RE_EVAL.search(_l)

        while res:
            if integrated:
                new_l_tokens.append(_l[:res.start()])
            try:
                eval_call = eval(res.group(), {"__builtins__": {}})
                new_l_tokens.append(
                    f"{Converter.COLOR_EVALUATION}{eval_call}{Converter.COLOR_RESET}"
                )
            except SyntaxError as exc:
                p_diff = res.group().count('(') - res.group().count(')')
                try:
                    if p_diff > 0 and res.group()[:p_diff] == '(' * p_diff:
                        eval_call = eval(res.group()[p_diff:], {"__builtins__": {}})
                        new_l_tokens.append(
                            f"{Converter.COLOR_EVALUATION}{eval_call}{Converter.COLOR_RESET}"
                        )
                        if integrated:
                            new_l_tokens.insert(len(new_l_tokens)-1, '(' * p_diff)
                    elif p_diff < 0 and res.group()[p_diff:] == ')' * (-1 * p_diff):
                        eval_call = eval(res.group()[:p_diff], {"__builtins__": {}})
                        new_l_tokens.append(
                            f"{Converter.COLOR_EVALUATION}{eval_call}{Converter.COLOR_RESET}"
                        )
                        _l = ')' * (-1 * p_diff) + _l
                    else:
                        raise SyntaxError from exc
                except SyntaxError:
                    new_l_tokens.append(f"{Converter.COLOR_EVALUATION}" + \
                        f"{('?' * len(res.group()) if integrated else '?')}{Converter.COLOR_RESET}")
                except (NameError, ValueError, ArithmeticError) as exc_inner:
                    Converter._evaluate_exception_handler(exc_inner, res.group(), new_l_tokens)
            except (NameError, ValueError, ArithmeticError) as exc:
                Converter._evaluate_exception_handler(exc, res.group(), new_l_tokens)
            _l = _l[res.end():]
            res = RE_EVAL.search(_l)

        if integrated:
            new_l_tokens.append(_l)

        if not new_l_tokens:
            return '' if integrated else None
        return (',' * (not integrated)).join(new_l_tokens)

    @staticmethod
    def is_hex(_v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check

        Returns:
        (bool):
            True if v is a Hexadecimal number.
            False if it is not.
        """
        if _v.startswith('-'):
            _v = _v[1:]
        if _v.startswith('0x'):
            _v = _v[2:]
        return all(c in Converter.hexdigits for c in _v) and _v != ''

    @staticmethod
    def is_dec(_v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check

        Returns:
        (bool):
            True if v is a Decimal number.
            False if it is not.
        """
        if _v.startswith('-'):
            _v = _v[1:]
        return _v.isdecimal() and _v != ''

    @staticmethod
    def is_oct(_v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check

        Returns:
        (bool):
            True if v is a Octal number.
            False if it is not.
        """
        if _v.startswith('-'):
            _v = _v[1:]
        if _v.startswith('0o'):
            _v = _v[2:]
        return all(c in Converter.octdigits for c in _v) and _v != ''

    @staticmethod
    def is_bin(_v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check

        Returns:
        (bool):
            True if v is a Binary number.
            False if it is not.
        """
        if _v.startswith('-'):
            _v = _v[1:]
        if _v.startswith('0b'):
            _v = _v[2:]
        return all(c in Converter.bindigits for c in set(_v)) and _v != ''

    @staticmethod
    def c_from_hex(value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Hexadecimal String including the corresponding
        Binary, Octal and Decimal number.

        Parameters:
        value (str):
            the value to convert to hex
        leading (bool):
            should prefix be displayed

        Returns:
        (str):
            the converted string
        """
        return f"{Converter.COLOR_CONVERSION}[Bin: {__hex_to_bin__(value, leading)}, Oct: " + \
            f"{__hex_to_oct__(value, leading)}, Dec: {__hex_to_dec__(value)}]" + \
                f"{Converter.COLOR_RESET}"


    @staticmethod
    def c_from_dec(value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Decimal Int including the corresponding
        Binary, Octal and Hexadecimal number.

        Parameters:
        value (str):
            the value to convert to dec
        leading (bool):
            should prefix be displayed

        Returns:
        (str):
            the converted string
        """
        value = int(value)
        return f"{Converter.COLOR_CONVERSION}[Bin: {__dec_to_bin__(value, leading)}, Oct: " + \
            f"{__dec_to_oct__(value, leading)}, Hex: " + \
                f"{__dec_to_hex__(value, leading)}]{Converter.COLOR_RESET}"

    @staticmethod
    def c_from_oct(value: str, leading: bool = False) -> str:
        """
        returns a String representation of an Octal String including the corresponding
        Binary, Decimal and Hexadecimal number.

        Parameters:
        value (str):
            the value to convert to oct
        leading (bool):
            should prefix be displayed

        Returns:
        (str):
            the converted string
        """
        return f"{Converter.COLOR_CONVERSION}[Bin: {__oct_to_bin__(value, leading)}, Dec: " + \
            f"{__oct_to_dec__(value)}, Hex: {__oct_to_hex__(value, leading)}]" + \
                f"{Converter.COLOR_RESET}"

    @staticmethod
    def c_from_bin(value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Binary String including the corresponding
        Octal, Decimal and Hexadecimal number.

        Parameters:
        value (str):
            the value to convert to bin
        leading (bool):
            should prefix be displayed

        Returns:
        (str):
            the converted string
        """
        return f"{Converter.COLOR_CONVERSION}[Oct: {__bin_to_oct__(value, leading)}, Dec: " + \
            f"{__bin_to_dec__(value)}, Hex: {__bin_to_hex__(value, leading)}]" + \
                f"{Converter.COLOR_RESET}"
