"""
colorconstants
"""

ESC_CODE = '\x1b'


def id_to_code(code: int) -> str:
    """
    converts a color id to a usable escape sequence
    """
    return f"{ESC_CODE}[{code}m"


class ColorOptions:
    """
    Holds the dictionaries mapping colors to ANSI-Escape codes.
    """
    __Fore = {
        'RESET': 39,

        'BLACK':   30,
        'RED':     31,
        'GREEN':   32,
        'YELLOW':  33,
        'BLUE':    34,
        'MAGENTA': 35,
        'CYAN':    36,
        'WHITE':   37,

        'LIGHTBLACK':   90,
        'LIGHTRED':     91,
        'LIGHTGREEN':   92,
        'LIGHTYELLOW':  93,
        'LIGHTBLUE':    94,
        'LIGHTMAGENTA': 95,
        'LIGHTCYAN':    96,
        'LIGHTWHITE':   97
        }
    __Back = {
        'RESET': 49,

        'BLACK':   40,
        'RED':     41,
        'GREEN':   42,
        'YELLOW':  43,
        'BLUE':    44,
        'MAGENTA': 45,
        'CYAN':    46,
        'WHITE':   47,

        'LIGHTBLACK':   100,
        'LIGHTRED':     101,
        'LIGHTGREEN':   102,
        'LIGHTYELLOW':  103,
        'LIGHTBLUE':    104,
        'LIGHTMAGENTA': 105,
        'LIGHTCYAN':    106,
        'LIGHTWHITE':   107
        }
    __Style = {
        'RESET': 0
        }

    Fore  = {'NONE': ''}
    Back  = {'NONE': ''}
    Style = {'NONE': ''}

    for key, _ in __Fore.items():
        Fore[key]  = id_to_code(__Fore[key])
    for key, _ in __Back.items():
        Back[key]  = id_to_code(__Back[key])
    for key, _ in __Style.items():
        Style[key] = id_to_code(__Style[key])

    del __Fore
    del __Back
    del __Style


class CVis:
    """
    the colors for the visualizer
    """
    DIGRAPH_VIEW_CONTROL = ColorOptions.Fore['GREEN']

    BYTE_VIEW_0          = ColorOptions.Fore['BLACK']
    BYTE_VIEW_CONTROL    = ColorOptions.Fore['GREEN']
    BYTE_VIEW_PRINTABLE  = ColorOptions.Fore['BLUE']
    BYTE_VIEW_EXTENDED   = ColorOptions.Fore['RED']
    BYTE_VIEW_256        = ColorOptions.Fore['WHITE']

    ENTROPY_VERY_HIGH    = ColorOptions.Fore['WHITE']
    ENTROPY_HIGH         = ColorOptions.Fore['YELLOW']
    ENTROPY_MEDIUM       = ColorOptions.Fore['RED']
    ENTROPY_LOW          = ColorOptions.Fore['BLUE']
    ENTROPY_VERY_LOW     = ColorOptions.Fore['BLACK']

    COLOR_RESET          = ColorOptions.Style['RESET']


class CPB:
    """
    the colors for the progress bar
    """
    COLOR_FULL  = ColorOptions.Fore['LIGHTGREEN']
    COLOR_EMPTY = ColorOptions.Fore['LIGHTMAGENTA']
    # COLOR_EMPTY = '\x1b[38;2;255;71;156m'
    COLOR_RESET = ColorOptions.Style['RESET']


class CKW:
    """
    The collection of all different color options
    """
    RESET_ALL = 'reset_all'
    RESET_FOUND = 'reset_found'
    RESET_MATCHED = 'reset_matched'

    LINE_LENGTH = 'line_length'
    NUMBER = 'line_numbers'
    FILE_PREFIX = 'file_prefix'
    ENDS = 'line_ends'
    CHARS = 'special_chars'
    SUMMARY = 'summary_message'
    EVALUATION = 'number_evaluation'
    CONVERSION = 'number_conversion'
    ATTRIB = 'file_attribute_message'
    ATTRIB_POSITIVE = 'active_file_attributes'
    ATTRIB_NEGATIVE = 'missing_file_attributes'
    CHECKSUM = 'checksum_message'
    RAWVIEWER = 'raw_viewer'
    FOUND = 'found_keyword'
    FOUND_MESSAGE = 'found_keyword_message'
    MATCHED = 'matched_pattern'
    MATCHED_MESSAGE = 'matched_pattern_message'
    REPLACE = 'substring_replacement'

    MESSAGE_INFORMATION = 'message_information'
    MESSAGE_IMPORTANT = 'message_important'
    MESSAGE_WARNING = 'message_warning'
