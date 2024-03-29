"""
more
"""

from math import ceil
import os
import sys

class More:
    """
    implements 'more' behaviour
    """
    ansi_cleaner = lambda x: x
    step_length = 0

    @staticmethod
    def setup(ansi_cleaner = lambda x: x, step_length: int = 0):
        """
        setup the configuration
        
        Parameters:
        ansi_cleaner (function):
            remove_ansi_codes_from_line
        step_length (int):
            defines how many lines should be displayed before pausing.
            a value of 0 is equivalent to the size of the terminal window
        """
        More.ansi_cleaner = ansi_cleaner
        More.step_length = step_length

    def __init__(self, lines: list = None) -> None:
        self.lines = lines if lines else []

    def add_line(self, line: str) -> None:
        """
        add a single line.

        Parameters:
        line (str):
            the line to append
        """
        self.lines.append(line)

    def add_lines(self, lines: list) -> None:
        """
        add multiple lines.
        
        Parameters:
        lines (list):
            the list of lines to append
        """
        self.lines += lines

    def step_through(self) -> None:
        """
        step through the lines and wait for user input.
        """
        def pause_output(percentage: int) -> str:
            try:
                user_input = input(f"-- More ({percentage: >2}%) -- ").upper()
            except EOFError:
                user_input = ''
            if not os.isatty(sys.stdin.fileno()):
                print() # emulate enter-press on piped input
            print('\x1b[1F\x1b[2K', end='', flush=True) # clear input() line
            return user_input

        try:
            t_width, t_height = os.get_terminal_size()
            t_width, t_height = max(t_width-1, 1), max(t_height-1, 1)
        except OSError: # PyPy-Error: "Inappropriate ioctl for device"
            t_width, t_height = 119, 29

        i_length = len(self.lines)
        first_chunk, chunk_s = True, 1
        for nr, line in enumerate(self.lines, start=1):
            print(line)

            if len(More.ansi_cleaner(line)) > t_width:
                chunk_s += ceil(len(More.ansi_cleaner(line)) / t_width)-1
            if chunk_s >= t_height and nr < i_length:
                user_input = '?'
                while user_input in ['?', 'H', 'HELP']:
                    user_input = pause_output(nr*100//i_length)
                    if user_input in ['?', 'H', 'HELP']:
                        print('Q QUIT       quit')
                        print('N NEXT       skip to next file')
                        continue
                    if user_input in ['N', 'NEXT']:
                        return
                    if user_input in ['\x11', 'Q', 'QUIT']: # '\x11' = ^Q
                        sys.exit(0)
                if first_chunk:
                    first_chunk = False
                    if More.step_length > 0:
                        t_height = More.step_length
                chunk_s = 0
            chunk_s += 1
