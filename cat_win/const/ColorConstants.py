
ESC_CODE = '\x1b'


def idToCode(code: int) -> str:
    return f'{ESC_CODE}[{code}m'


class ColorOptions:
    Fore = {
        "RESET": 39,
            
        "BLACK":   30,
        "RED":     31,
        "GREEN":   32,
        "YELLOW":  33,
        "BLUE":    34,
        "MAGENTA": 35,
        "CYAN":    36,
        "WHITE":   37,
        
        "LIGHTBLACK":   90,
        "LIGHTRED":     91,
        "LIGHTGREEN":   92,
        "LIGHTYELLOW":  93,
        "LIGHTBLUE":    94,
        "LIGHTMAGENTA": 95,
        "LIGHTCYAN":    96,
        "LIGHTWHITE":   97
        }
    Back = {
        "RESET": 49,
            
        "BLACK":   40,
        "RED":     41,
        "GREEN":   42,
        "YELLOW":  43,
        "BLUE":    44,
        "MAGENTA": 45,
        "CYAN":    46,
        "WHITE":   47,
          
        "LIGHTBLACK":   100,
        "LIGHTRED":     101,
        "LIGHTGREEN":   102,
        "LIGHTYELLOW":  103,
        "LIGHTBLUE":    104,
        "LIGHTMAGENTA": 105,
        "LIGHTCYAN":    106,
        "LIGHTWHITE":   107
        }
    Style = {
        "RESET": 0
        }

    for key in Fore:
        Fore[key] = idToCode(Fore[key])
    for key in Back:
        Back[key] = idToCode(Back[key])
    for key in Style:
        Style[key] = idToCode(Style[key])


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
    
    MESSAGE_INFORMATION = "message_information"
    MESSAGE_IMPORTANT = "message_important"
    MESSAGE_WARNING = "message_warning"
