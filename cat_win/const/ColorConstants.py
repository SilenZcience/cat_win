from colorama import Fore, Back, Style


class ColoramaOptions:
    C_Fore = {"BLACK": Fore.BLACK,
              "RED": Fore.RED,
              "GREEN": Fore.GREEN,
              "YELLOW": Fore.YELLOW,
              "BLUE": Fore.BLUE,
              "MAGENTA": Fore.MAGENTA,
              "CYAN": Fore.CYAN,
              "WHITE": Fore.WHITE,
              "LIGHTBLACK_EX": Fore.LIGHTBLACK_EX,
              "LIGHTRED_EX": Fore.LIGHTRED_EX,
              "LIGHTGREEN_EX": Fore.LIGHTGREEN_EX,
              "LIGHTYELLOW_EX": Fore.LIGHTYELLOW_EX,
              "LIGHTBLUE_EX": Fore.LIGHTBLUE_EX,
              "LIGHTMAGENTA_EX": Fore.LIGHTMAGENTA_EX,
              "LIGHTCYAN_EX": Fore.LIGHTCYAN_EX,
              "LIGHTWHITE_EX": Fore.LIGHTWHITE_EX
              }
    C_Back = {"BLACK": Back.BLACK,
              "RED": Back.RED,
              "GREEN": Back.GREEN,
              "YELLOW": Back.YELLOW,
              "BLUE": Back.BLUE,
              "MAGENTA": Back.MAGENTA,
              "CYAN": Back.CYAN,
              "WHITE": Back.WHITE,
              "LIGHTBLACK_EX": Back.LIGHTBLACK_EX,
              "LIGHTRED_EX": Back.LIGHTRED_EX,
              "LIGHTGREEN_EX": Back.LIGHTGREEN_EX,
              "LIGHTYELLOW_EX": Back.LIGHTYELLOW_EX,
              "LIGHTBLUE_EX": Back.LIGHTBLUE_EX,
              "LIGHTMAGENTA_EX": Back.LIGHTMAGENTA_EX,
              "LIGHTCYAN_EX": Back.LIGHTCYAN_EX,
              "LIGHTWHITE_EX": Back.LIGHTWHITE_EX
              }

    C_Fore_Reset = Fore.RESET
    C_Back_Reset = Back.RESET
    C_Style_Reset = Style.RESET_ALL


class C_KW:
    RESET_ALL = "reset_all"
    RESET_FOUND = "reset_found"
    RESET_MATCHED = "reset_matched"

    NUMBER = "line_numbers"
    LINE_LENGTH = "line_length"
    ENDS = "line_ends"
    TABS = "tab_characters"
    CONVERSION = "number_conversion"
    REPLACE = "substring_replacement"
    FOUND = "found_keyword"
    FOUND_MESSAGE = "found_keyword_message"
    MATCHED = "matched_pattern"
    MATCHED_MESSAGE = "matched_pattern_message"
    CHECKSUM = "checksum_message"
    COUNT_AND_FILES = "processed_message"
    ATTRIB = "file_attribute_message"
    ATTRIB_POSITIVE = "active_file_attributes"
    ATTRIB_NEGATIVE = "missing_file_attributes"
