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
    def setup(ansi_cleaner = None, step_length: int = 0):
        """
        setup the configuration
        
        Parameters:
        ansi_cleaner (function):
            remove_ansi_codes_from_line
        step_length (int):
            defines how many lines should be displayed before pausing.
            a value of 0 is equivalent to the size of the terminal window
        """
        if ansi_cleaner is not None:
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
        if not os.isatty(sys.stdout.fileno()):
            print(*self.lines, sep='\n')
            return

        def pause_output(percentage: int, info: str, t_width: int, clear_size: int = 0) -> str:
            print() # move to bottom line
            # print bottom line:
            if t_width < 7:
                print('=' * t_width)
            else:
                padding = '-' * ((t_width-7)//2)
                print(padding + 'cat_win' + '-' * (t_width-7-len(padding)), end='')
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

        try:
            t_width, t_height = os.get_terminal_size()
            t_width, t_height = max(t_width, 1), max(t_height-2, 1)
        except OSError: # PyPy-Error: "Inappropriate ioctl for device"
            t_width, t_height = 120, 28
        step_length = t_height

        i_length = len(self.lines)
        first_chunk, chunk_s = True, 1
        current_line, skip_to_line = 0, 0

        while current_line < i_length:
            if (current_line+1) < skip_to_line:
                current_line += 1
                continue

            # potentially the offset is wrong when the last line is too long for the terminal size
            # and wraps around to the next line. in this case the first line will not be visible
            # in the current frame ...
            # it is however not possible to pre-cut the lines to the correct lengths, because the
            # lines may very likely contain color/ANSI-codes
            print(self.lines[current_line])

            if len(More.ansi_cleaner(self.lines[current_line])) > t_width:
                chunk_s += ceil(len(More.ansi_cleaner(self.lines[current_line])) / t_width)-1

            if chunk_s >= step_length and (current_line+1) < i_length:
                chunk_s = 0
                if first_chunk:
                    first_chunk = False
                    step_length = More.step_length if More.step_length > 0 else t_height

                info, clear_size = '', 0
                while True:
                    user_input = pause_output((current_line+1)*100//i_length,
                                              info,
                                              t_width,
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
                        info = f"Line: {current_line+1}"
                        continue
                    if user_input.startswith('D') or user_input.startswith('DOWN'):
                        idown = user_input[4:] if user_input.startswith('DOWN') else user_input[1:]
                        idown = '1' if not idown else idown
                        try:
                            step_length = int(idown)
                            first_chunk = True
                        except ValueError:
                            info = f"invalid input: {idown}"
                            user_input = '?'
                            continue
                        break
                    if user_input.startswith('S') or user_input.startswith('SKIP'):
                        iskip = user_input[4:] if user_input.startswith('SKIP') else user_input[1:]
                        iskip = '1' if not iskip else iskip
                        try:
                            skip_to_line = current_line+int(iskip)+2
                        except ValueError:
                            info = f"invalid input: {iskip}"
                            user_input = '?'
                            continue
                        break
                    if user_input.startswith('J') or user_input.startswith('JUMP'):
                        ijump = user_input[4:] if user_input.startswith('JUMP') else user_input[1:]
                        ijump = str(current_line+1) if not ijump else ijump
                        try:
                            current_line = int(ijump)-2
                            skip_to_line = 1
                        except ValueError:
                            info = f"invalid input: {ijump}"
                            user_input = '?'
                            continue
                        break
                    break

            chunk_s += 1
            current_line += 1
