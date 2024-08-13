"""
escapecodes
"""

ESC_CODE = '\x1b'


def color_code_8_16(c_id: int) -> str:
    """
    converts a 8-16 color id to a usable escape sequence
    """
    return f"{ESC_CODE}[{c_id}m"

def color_code_256(c_id: int, fg: bool = True) -> str:
    """
    converts a 256(8bit) color id to a usable escape sequence
    """
    return f"{ESC_CODE}[{38 if fg else 48};5;{c_id}m"

def color_code_truecolor(r: int, g: int, b: int, fg: bool = True) -> str:
    """
    converts a truecolor(24bit) color def to a usable escape sequence
    """
    return f"{ESC_CODE}[{38 if fg else 48};2;{r};{g};{b}m"

def cursor_set_x_y(row: int, col: int) -> str:
    """
    set cursor to line row and column col
    """
    return f"{ESC_CODE}[{row};{col}H"

def cursor_move_x(x: int, direction: str) -> str:
    """
    move cursor by x in direction
    """
    map_direction = {
        'up':    'A',
        'down':  'B',
        'right': 'C',
        'left':  'D',
    }
    return f"{ESC_CODE}[{x}{map_direction.get(direction, 'A')}"

def cursor_start_x(x: int, direction: str = 'up') -> str:
    """
    move cursor by x to beginning of line
    """
    return f"{ESC_CODE}[{x}{'F' if direction == 'up' else 'E'}"


CURSOR_INVISIBLE = f"{ESC_CODE}[?25l"
CURSOR_VISIBLE   = f"{ESC_CODE}[?25h"

CURSOR_MOVE_HOME = f"{ESC_CODE}[H"
CURSOR_START_ABOVE_1     = cursor_start_x(1, 'up')

ERASE_SCREEN_FROM_CURSOR = f"{ESC_CODE}[0J"
ERASE_SCREEN_TO_CURSOR   = f"{ESC_CODE}[1J"
ERASE_SCREEN             = f"{ESC_CODE}[2J"
ERASE_LINE_FROM_CURSOR   = f"{ESC_CODE}[0K"
ERASE_LINE_TO_CURSOR     = f"{ESC_CODE}[1K"
ERASE_LINE               = f"{ESC_CODE}[2K"
