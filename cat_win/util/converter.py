from re import compile as re_compile, search as re_search
from string import hexdigits


class Converter():
    """
    converts a decimal, hex, binary number
    to the two corresponding others, or
    evaluate an expression.
    """
    # matches a mathematical expression consisting of either hex-numbers = (0x...), binary-numbers (0b...) or
    # default decimal numbers (these are not allowed to have a leading zero before the decimal point, yet something like "-.06" is allowed).
    # between every number has to be a valid operator (*,/,+,-,%,**,//)
    # before every number there may be opening parenthesis, after every number there may be closing parenthesis
    # (it is not validated that all parenthesis match each other to a valid expression ...)
    _eval_regex = re_compile(r'(?:\(\s*)*(?:(?:0(?:(?:x[0-9a-fA-F]+)|b[01]+)|(?:\-?(?:(?:0|[1-9][0-9]*)?\.[0-9]*|0|[1-9][0-9]*)))[\)\s]*[%\-\/\+\*][\/\*]?[\(\s]*)+(?:0(?:(?:x[0-9a-fA-F]+)|b[01]+)|(?:\-?(?:(?:0|[1-9][0-9]*)?\.[0-9]*|0|[1-9][0-9]*)))(?:\s*\))*')

    def __init__(self) -> None:
        self.colors = ['', '', '']
        self.debug = False

    def set_params(self, debug: bool, colors = None) -> None:
        """
        set the colors to use.
        
        Parameters:
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
        new_token = f"{self.colors[0]}???{debug_token if self.debug else ''}{self.colors[2]}"
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
        res = re_search(self._eval_regex, _l)

        while (res):
            if integrated:
                new_l_tokens.append(_l[:res.start()])
            try:
                new_l_tokens.append(f"{self.colors[0]}{eval(res.group())}{self.colors[2]}")
            except SyntaxError:
                p_diff = res.group().count('(') - res.group().count(')')
                try:
                    if p_diff > 0 and res.group()[:p_diff] == '(' * p_diff:
                        new_l_tokens.append(f"{self.colors[0]}{eval(res.group()[p_diff:])}{self.colors[2]}")
                        if integrated:
                            new_l_tokens.insert(len(new_l_tokens)-1, '(' * p_diff)
                    elif p_diff < 0 and res.group()[p_diff:] == ')' * (-1 * p_diff):
                        new_l_tokens.append(f"{self.colors[0]}{eval(res.group()[:p_diff])}{self.colors[2]}")
                        _l = ')' * (-1 * p_diff) + _l
                    else:
                        raise SyntaxError()
                except SyntaxError:
                    new_l_tokens.append(f"{self.colors[0]}{('?' * len(res.group()) if integrated else '?')}{self.colors[2]}")
                except Exception as e:
                    self._evaluate_exception_handler(e, res.group(), new_l_tokens)
            except Exception as e:
                self._evaluate_exception_handler(e, res.group(), new_l_tokens)
            _l = _l[res.end():]
            res = re_search(self._eval_regex, _l)

        if integrated:
            new_l_tokens.append(_l)

        if not new_l_tokens:
            return '' if integrated else None
        return (',' * (not integrated)).join(new_l_tokens)

    def is_dec(self, _v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check
            
        Returns:
            True if v is a Decimal number.
            False if it is not.
        """
        if _v[:1] == '-':
            _v = _v[1:]
        return _v.isdecimal() and _v != ""

    def is_hex(self, _v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check
            
        Returns:
            True if v is a Hexadecimal number.
            False if it is not.
        """
        if _v[:1] == '-':
            _v = _v[1:]
        hex_digits = set(hexdigits)
        if _v[:2] == '0x':
            _v = _v[2:]
        return all(c in hex_digits for c in _v) and _v != ""

    def is_bin(self, _v: str) -> bool:
        """
        Parameters:
        v (str):
            the string to check
            
        Returns:
            True if v is a Binary number.
            False if it is not.
        """
        if _v[:1] == '-':
            _v = _v[1:]
        if _v[:2] == '0b':
            _v = _v[2:]
        v_set = set(_v)
        return v_set in [{'0', '1'}, {'0'}, {'1'}] and _v != ""

    def __dec_to_hex__(self, value: int, leading: bool = False) -> str:
        return f"{value:#x}" if leading else f"{value:x}"

    def __dec_to_bin__(self, value: int, leading: bool = False) -> str:
        return f"{value:#b}" if leading else f"{value:b}"

    def c_from_dec(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Decimal Int including the corresponding
        Hexadecimal and Binary number.
        """
        value = int(value)
        return self.colors[1] + '{Hexadecimal: ' + self.__dec_to_hex__(value, leading) + '; Binary: ' + \
            self.__dec_to_bin__(value, leading) + '}' + self.colors[2]

    def __hex_to_dec__(self, value: str) -> str:
        return str(int(value, 16))

    def __hex_to_bin__(self, value: str, leading: bool = False) -> str:
        return bin(int(value, 16)) if leading else bin(int(value, 16))[2:]

    def c_from_hex(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Hexadecimal String including the corresponding
        Decimal and Binary number.
        """
        return self.colors[1] + '{Decimal: ' + self.__hex_to_dec__(value) + '; Binary: ' + \
            self.__hex_to_bin__(value, leading) + '}' + self.colors[2]

    def __bin_to_dec__(self, value: str) -> str:
        return str(int(value, 2))

    def __bin_to_hex__(self, value: str, leading: bool = False) -> str:
        return hex(int(value, 2)) if leading else hex(int(value, 2))[2:]

    def c_from_bin(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Binary String including the corresponding
        Decimal and Hexadecimal number.
        """
        return self.colors[1] + '{Decimal: ' + self.__bin_to_dec__(value) + '; Hexadecimal: ' + \
            self.__bin_to_hex__(value, leading) + '}' + self.colors[2]
