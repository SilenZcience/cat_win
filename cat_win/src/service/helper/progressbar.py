
import contextlib
import os
import sys
from cat_win.src.const.colorconstants import CPB


class PBar:
    def __init__(self, total: int, prefix: str = '', suffix: str = '',
                    decimals: int = 1, length: int = 100,
                    fill_l: str = '█', fill_r: str = '-', erase: bool = False) -> None:
        # x━x x╺x x╸x x-x
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill_l = fill_l
        self.fill_r = fill_r
        self.erase = erase

    @contextlib.contextmanager
    def init(self):
        try:
            if os.isatty(sys.stdout.fileno()):
                print('\x1b[?25l', end='')
                yield self.print_progress_bar
            else:
                yield lambda _: None
        finally:
            if os.isatty(sys.stdout.fileno()):
                if self.erase:
                    self.erase_progress_bar()
                print('\x1b[?25h', end='\n'*(not self.erase))

    def print_progress_bar(self, iteration: int) -> None:
        if iteration < 0:
            iteration = self.total
        percentage = min(100 * (iteration / float(self.total)), 100.0)
        percent_color = CPB.COLOR_FULL if percentage == 100.0 else CPB.COLOR_EMPTY
        percent = f"{percentage:5.{self.decimals}f}"
        length_l = int(self.length * iteration // self.total)
        bars = f"{CPB.COLOR_FULL}{self.fill_l * length_l}{CPB.COLOR_EMPTY}{self.fill_r * (self.length - length_l)}"
        progress = f"\r{self.prefix} {bars} {percent_color}{percent}%{CPB.COLOR_RESET} {self.suffix}"
        print(progress, end='')

    def erase_progress_bar(self) -> None:
        length = len(self.prefix) + len(self.suffix) + self.length + 9
        print('\b \b' * length, end='')
