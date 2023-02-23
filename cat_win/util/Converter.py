import string


class Converter():
    def is_dec(self, v: str) -> bool:
        """
        returns True if given String is a Decimal number.
        return False if it is not.
        """
        if v[:1] == '-':
            v = v[1:]
        return v.isdecimal() and v != ""

    def is_hex(self, v: str) -> bool:
        """
        returns True if a String is a Hexadecimal number.
        returns False if it is not.
        """
        if v[:1] == '-':
            v = v[1:]
        hex_digits = set(string.hexdigits)
        if v[:2] == '0x':
            v = v[2:]
        return all(c in hex_digits for c in v) and v != ""

    def is_bin(self, v: str) -> bool:
        """
        returns True if a String is a Binary number.
        returns False if it is not.
        """
        if v[:1] == '-':
            v = v[1:]
        if v[:2] == '0b':
            v = v[2:]
        v_set = set(v)
        return (v_set == {'0', '1'} or v_set == {'0'} or v_set == {'1'}) and v != ""

    def __dec_to_hex__(self, value: int, leading: bool = False) -> str:
        return '{0:#x}'.format(value) if leading else '{0:x}'.format(value)

    def __dec_to_bin__(self, value: int, leading: bool = False) -> str:
        return '{0:#b}'.format(value) if leading else '{0:b}'.format(value)

    def _fromDEC(self, value: int, leading: bool = False) -> str:
        """
        returns a String representation of a Decimal Int including the corresponding
        Hexadecimal and Binary number.
        """
        return '{Hexadecimal: ' + self.__dec_to_hex__(value, leading) + '; Binary: ' + self.__dec_to_bin__(value, leading) + '}'

    def __hex_to_dec__(self, value: str) -> str:
        return str(int(value, 16))

    def __hex_to_bin__(self, value: str, leading: bool = False) -> str:
        return bin(int(value, 16)) if leading else bin(int(value, 16))[2:]

    def _fromHEX(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Hexadecimal String including the corresponding
        Decimal and Binary number.
        """
        return '{Decimal: ' + self.__hex_to_dec__(value) + '; Binary: ' + self.__hex_to_bin__(value, leading) + '}'

    def __bin_to_dec__(self, value: str) -> str:
        return str(int(value, 2))

    def __bin_to_hex__(self, value: str, leading: bool = False) -> str:
        return hex(int(value, 2)) if leading else hex(int(value, 2))[2:]

    def _fromBIN(self, value: str, leading: bool = False) -> str:
        """
        returns a String representation of a Binary String including the corresponding
        Decimal and Hexadecimal number.
        """
        return '{Decimal: ' + self.__bin_to_dec__(value) + '; Hexadecimal: ' + self.__bin_to_hex__(value, leading) + '}'
