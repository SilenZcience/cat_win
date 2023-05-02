import string


class Converter():
    """
    converts a decimal, hex, binary number
    to the two corresponding others.
    """
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
        hex_digits = set(string.hexdigits)
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

    def c_from_dec(self, value: int, leading: bool = False) -> str:
        """
        returns a String representation of a Decimal Int including the corresponding
        Hexadecimal and Binary number.
        """
        return '{Hexadecimal: ' + self.__dec_to_hex__(value, leading) + '; Binary: ' + \
            self.__dec_to_bin__(value, leading) + '}'

    def __hex_to_dec__(self, value: str) -> str:
        return str(int(value, 16))

    def __hex_to_bin__(self, value: str, leading: bool = False) -> str:
        return bin(int(value, 16)) if leading else bin(int(value, 16))[2:]

    def c_from_hex(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Hexadecimal String including the corresponding
        Decimal and Binary number.
        """
        return '{Decimal: ' + self.__hex_to_dec__(value) + '; Binary: ' + \
            self.__hex_to_bin__(value, leading) + '}'

    def __bin_to_dec__(self, value: str) -> str:
        return str(int(value, 2))

    def __bin_to_hex__(self, value: str, leading: bool = False) -> str:
        return hex(int(value, 2)) if leading else hex(int(value, 2))[2:]

    def c_from_bin(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Binary String including the corresponding
        Decimal and Hexadecimal number.
        """
        return '{Decimal: ' + self.__bin_to_dec__(value) + '; Hexadecimal: ' + \
            self.__bin_to_hex__(value, leading) + '}'
