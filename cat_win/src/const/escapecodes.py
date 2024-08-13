"""
escapecodes
"""

ESC_CODE = '\x1b'


def id_to_color_code(code: int) -> str:
    """
    converts a color id to a usable escape sequence
    """
    return f"{ESC_CODE}[{code}m"

CURSOR_INVISIBLE = f"{ESC_CODE}[?25l"
CURSOR_VISIBLE   = f"{ESC_CODE}[?25h"

LINE_MOVE_UP     = f"{ESC_CODE}[1F"
LINE_ERASE       = f"{ESC_CODE}[2K"
