"""
more
"""

import os
import sys

from cat_win.src.service.helper.iohelper import IoHelper


class More:
    """
    implements 'more' behaviour
    """
    on_windows_os = True
    step_length = 0
    t_width = 120
    t_height = 28

    @staticmethod
    def setup(on_windows_os: bool, step_length: int = 0) -> None:
        """
        setup the configuration
        
        Parameters:
        on_windows_os (bool):
            indicates if the current system is Windows
        step_length (int):
            defines how many lines should be displayed before pausing.
            a value of 0 is equivalent to the size of the terminal window
        """
        More.on_windows_os = on_windows_os
        More.step_length = step_length
        try:
            t_width, t_height = os.get_terminal_size()
            More.t_width, More.t_height = max(t_width, 1), max(t_height-2, 1)
        except OSError: # PyPy-Error: "Inappropriate ioctl for device"
            pass

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

    @staticmethod
    def _pause_output(percentage: int, info: str, clear_size: int = 0) -> str:
        print() # move to bottom line
        # print bottom line:
        if More.t_width < 7:
            print('-' * More.t_width)
        else:
            padding = '-' * ((More.t_width-7)//2)
            print(padding + 'cat_win' + '-' * (More.t_width-7-len(padding)), end='')
        print('\x1b[1F', end='', flush=True) # move up to input() line
        try:
            user_input = input(
                f"-- More ({percentage: >2}%){('['+info+']') if info else ''} -- "
                ).strip().upper()
        except EOFError:
            user_input = ''
        except KeyboardInterrupt:
            user_input = 'INTERRUPT'
        if not os.isatty(sys.stdin.fileno()) or user_input == 'INTERRUPT':
            print() # emulate enter-press on piped input
        print('\x1b[2K\x1b[1F\x1b[2K', end='') # clear bottom & input() line
        print('\x1b[1F\x1b[2K' * clear_size, end='', flush=True) # clear lines above
        return user_input

    @staticmethod
    def _yield_parts(line: str):
        if not line:
            yield line
            return

        escape_sequence = False
        sub_string, sub_length = '', 0
        for char in line:
            sub_string += char
            if escape_sequence:
                escape_sequence = not char.isalpha()
                continue
            if char == '\x1b':
                escape_sequence = True
                continue
            sub_length += 1
            if sub_length >= More.t_width:
                yield sub_string
                sub_string, sub_length = '', 0

        if sub_string:
            yield sub_string

    def _step_through(self) -> None:
        i_length, line_index = len(self.lines), 0
        step_length = More.t_height

        first_chunk, chunk_size = True, 0
        skip_line_parts = 0

        while line_index < i_length:
            for line_part in More._yield_parts(self.lines[line_index]):
                if skip_line_parts > 0:
                    skip_line_parts -= 1
                    continue

                print(line_part)

                chunk_size += 1
                if chunk_size >= step_length:
                    chunk_size = 0
                    if first_chunk:
                        first_chunk = False
                        step_length = More.step_length if More.step_length > 0 else More.t_height

                    break_line = False
                    info, clear_size = '', 0
                    while True:
                        user_input = More._pause_output((line_index+1)*100//i_length,
                                                  info,
                                                  clear_size)
                        info, clear_size = '', 0

                        if user_input == 'INTERRUPT':
                            raise KeyboardInterrupt
                        if user_input in ['?', 'H', 'HELP']:
                            print('H HELP       display this help message')
                            print('Q QUIT       quit')
                            print('N NEXT       skip to next file')
                            print('L LINE       display current line number')
                            print('D DOWN <x>   step x lines down')
                            print('S SKIP <x>   skip x lines')
                            print('J JUMP <x>   jump to line x')
                            clear_size = 7
                            continue
                        if user_input in ['\x11', 'Q', 'QUIT']: # '\x11' = ^Q
                            sys.exit(0)
                        if user_input in ['N', 'NEXT']:
                            return
                        if user_input in ['L', 'LINE']:
                            info = f"Line: {line_index+1}"
                            continue
                        if user_input.startswith('D') or user_input.startswith('DOWN'):
                            idown = user_input[4:] if user_input.startswith('DOWN') else user_input[1:]
                            idown = '1' if not idown else idown
                            try:
                                step_length = int(idown)
                                first_chunk = True
                            except ValueError:
                                info = f"invalid input: {idown}"
                                continue
                            break
                        if user_input.startswith('S') or user_input.startswith('SKIP'):
                            iskip = user_input[4:] if user_input.startswith('SKIP') else user_input[1:]
                            iskip = '1' if not iskip else iskip
                            try:
                                skip_line_parts = int(iskip)
                            except ValueError:
                                info = f"invalid input: {iskip}"
                                continue
                            break
                        if user_input.startswith('J') or user_input.startswith('JUMP'):
                            ijump = user_input[4:] if user_input.startswith('JUMP') else user_input[1:]
                            ijump = str(line_index+1) if not ijump else ijump
                            try:
                                # will be incremented again after the for-loop
                                line_index = int(ijump)-2
                                # user entered '0' -> mapped to line 1
                                # just like entering '1' ...
                                if line_index == -2:
                                    line_index = -1
                                # map negative numbers to positive ones, so the
                                # percentage is correct
                                elif line_index < -2:
                                    line_index = i_length+line_index+1
                            except ValueError:
                                info = f"invalid input: {ijump}"
                                continue
                            break_line = True
                            break
                        break

                    if break_line:
                        break

            line_index += 1

    def step_through(self, dup_needed: bool = False) -> None:
        """
        step through the lines and wait for user input.
        
        Parameters:
        dup_needed (bool):
            indicates if the stdin-dup is needed
        """
        if not os.isatty(sys.stdout.fileno()):
            print(*self.lines, sep='\n')
            return

        with IoHelper.dup_stdin(More.on_windows_os, dup_needed):
            self._step_through()
