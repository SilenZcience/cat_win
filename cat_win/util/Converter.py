import string

class Converter():
    def is_decimal(self, v: str):
        """
        returns True if given String is a Decimal number.
        return False if it is not.
        """
        return v.isdecimal()

    def is_hex(self, v: str):
        """
        returns True if a String is a Hexadecimal number.
        returns False if it is not.
        """
        hex_digits = set(string.hexdigits)
        if v[:2] == "0x": v = v[2:]
        return all(c in hex_digits for c in v)

    def is_bin(self, v: str):
        """
        returns True if a String is a Binary number.
        returns False if it is not.
        """
        v_set = set(v)
        return v_set == {'0', '1'} or v_set == {'0'} or v_set == {'1'}

    def __dec_to_hex__(self, value: int, leading: bool = False):
        return "{0:#x}".format(value) if leading else "{0:x}".format(value)

    def __dec_to_bin__(self, value: int, leading: bool = False):
        return "{0:#b}".format(value) if leading else "{0:b}".format(value)

    def _fromDEC(self, value: int, leading: bool = False):
        """
        returns a String representation of a Decimal Int including the corresponding
        Hexadecimal and Binary number.
        """
        return str(value) + " {Hexadecimal: " + str(self.__dec_to_hex__(value, leading)) + "; Binary: " + str(self.__dec_to_bin__(value, leading)) + "}"

    def __hex_to_dec__(self, value: str):
        return int(value, 16)

    def __hex_to_bin__(self, value: str, leading:bool = False):
        return bin(int(value, 16)) if leading else bin(int(value, 16))[2:]

    def _fromHEX(self, value: str, leading: bool = False):
        """
        returns a String representation of a Hexadecimal String including the corresponding
        Decimal and Binary number.
        """
        return value + " {Decimal: " + str(self.__hex_to_dec__(value)) + "; Binary: " + str(self.__hex_to_bin__(value, leading)) + "}"

    def __bin_to_dec__(self, value: str):
        return int(value, 2)

    def __bin_to_hex__(self, value: str, leading: bool = False):
        return hex(int(value, 2)) if leading else hex(int(value, 2))[2:]

    def _fromBIN(self, value: str, leading: bool = False):
        """
        returns a String representation of a Binary String including the corresponding
        Decimal and Hexadecimal number.
        """
        return str(value) + " {Decimal: " + str(self.__bin_to_dec__(value)) + "; Hexadecimal: " + str(self.__bin_to_hex__(value, leading)) + "}"