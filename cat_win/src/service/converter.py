"""
converter
"""

from cat_win.src.const.regex import RE_EVAL


class Converter:
    """
    converts a binary, octal, decimal or hex number
    into the corresponding others, or evaluates an expression.
    """

    bindigits = '01'
    octdigits = '01234567'
    hexdigits = '0123456789abcdefABCDEF'

    def __init__(self) -> None:
        self.colors = ['', '', '']
        self.debug = False

    def set_params(self, debug: bool, colors = None) -> None:
        """
        set the colors to use.
        
        Parameters:
        debug (bool):
            indicates if debug output should be displayed
        colors (list[str]):
            the colors to use, 3 elements needed:
            Index 0 -> EVALULATION
            Index 1 -> CONVERSION
            INDEX 2 -> RESET
        """
        if colors is None or len(colors) < 3:
            colors = ['', '', '']

        self.colors = colors
        self.debug = debug

    def _evaluate_exception_handler(self, exc: Exception, _group: str, new_l_tokens: list) -> None:
        debug_token = ''
        if self.debug:
            debug_token = f"({type(exc).__name__}: {exc} in {repr(_group)})"
        new_token = f"{self.colors[0]}???{debug_token}{self.colors[2]}"
        new_l_tokens.append(new_token)

        expected_errors = [ValueError, ArithmeticError]
         # anything else should be raised again, since it is not expected here
        if not any([isinstance(exc, error) for error in expected_errors]):
            raise exc

    def evaluate(self, _l: str, integrated: bool) -> str:
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
                new_l_tokens.append(f"{self.colors[0]}{eval(res.group())}{self.colors[2]}")
            except SyntaxError as exc:
                p_diff = res.group().count('(') - res.group().count(')')
                try:
                    if p_diff > 0 and res.group()[:p_diff] == '(' * p_diff:
                        new_l_tokens.append(f"{self.colors[0]}" + \
                            f"{eval(res.group()[p_diff:])}{self.colors[2]}")
                        if integrated:
                            new_l_tokens.insert(len(new_l_tokens)-1, '(' * p_diff)
                    elif p_diff < 0 and res.group()[p_diff:] == ')' * (-1 * p_diff):
                        new_l_tokens.append(f"{self.colors[0]}" + \
                            f"{eval(res.group()[:p_diff])}{self.colors[2]}")
                        _l = ')' * (-1 * p_diff) + _l
                    else:
                        raise SyntaxError from exc
                except SyntaxError:
                    new_l_tokens.append(f"{self.colors[0]}" + \
                        f"{('?' * len(res.group()) if integrated else '?')}{self.colors[2]}")
                except (NameError, ValueError, ArithmeticError) as exc_inner:
                    self._evaluate_exception_handler(exc_inner, res.group(), new_l_tokens)
            except (NameError, ValueError, ArithmeticError) as exc:
                self._evaluate_exception_handler(exc, res.group(), new_l_tokens)
            _l = _l[res.end():]
            res = RE_EVAL.search(_l)

        if integrated:
            new_l_tokens.append(_l)

        if not new_l_tokens:
            return '' if integrated else None
        return (',' * (not integrated)).join(new_l_tokens)

    def is_hex(self, _v: str) -> bool:
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
        return all(c in self.hexdigits for c in _v) and _v != ''

    def is_dec(self, _v: str) -> bool:
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

    def is_oct(self, _v: str) -> bool:
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
        return all(c in self.octdigits for c in _v) and _v != ''

    def is_bin(self, _v: str) -> bool:
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
        return all(c in self.bindigits for c in set(_v)) and _v != ''


    def __hex_to_dec__(self, value: str) -> str:
        return str(int(value, 16))

    def __hex_to_oct__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_oct__(int(value, 16), leading)

    def __hex_to_bin__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_bin__(int(value, 16), leading)

    def c_from_hex(self, value: str, leading: bool = False) -> str:
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
        return f"{self.colors[1]}[Bin: {self.__hex_to_bin__(value, leading)}, Oct: " + \
            f"{self.__hex_to_oct__(value, leading)}, Dec: {self.__hex_to_dec__(value)}]" + \
                f"{self.colors[2]}"


    def __dec_to_hex__(self, value: int, leading: bool = False) -> str:
        return f"{value:#x}" if leading else f"{value:x}"

    def __dec_to_oct__(self, value: int, leading: bool = False) -> str:
        return f"{value:#o}" if leading else f"{value:o}"

    def __dec_to_bin__(self, value: int, leading: bool = False) -> str:
        return f"{value:#b}" if leading else f"{value:b}"

    def c_from_dec(self, value: str, leading: bool = False) -> str:
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
        return f"{self.colors[1]}[Bin: {self.__dec_to_bin__(value, leading)}, Oct: " + \
            f"{self.__dec_to_oct__(value, leading)}, Hex: " + \
                f"{self.__dec_to_hex__(value, leading)}]{self.colors[2]}"


    def __oct_to_hex__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_hex__(int(value, 8), leading)

    def __oct_to_dec__(self, value: str) -> str:
        return str(int(value, 8))

    def __oct_to_bin__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_bin__(int(value, 8), leading)

    def c_from_oct(self, value: str, leading: bool = False) -> str:
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
        return f"{self.colors[1]}[Bin: {self.__oct_to_bin__(value, leading)}, Dec: " + \
            f"{self.__oct_to_dec__(value)}, Hex: {self.__oct_to_hex__(value, leading)}]" + \
                f"{self.colors[2]}"


    def __bin_to_hex__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_hex__(int(value, 2), leading)

    def __bin_to_dec__(self, value: str) -> str:
        return str(int(value, 2))

    def __bin_to_oct__(self, value: str, leading: bool = False) -> str:
        return self.__dec_to_oct__(int(value, 2), leading)

    def c_from_bin(self, value: str, leading: bool = False) -> str:
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
        return f"{self.colors[1]}[Oct: {self.__bin_to_oct__(value, leading)}, Dec: " + \
            f"{self.__bin_to_dec__(value)}, Hex: {self.__bin_to_hex__(value, leading)}]" + \
                f"{self.colors[2]}"
