"""
progressbar
"""

import contextlib
import os
import sys
from cat_win.src.const.colorconstants import ColorOptions
from cat_win.src.const.escapecodes import CURSOR_VISIBLE, CURSOR_INVISIBLE


class PBar:
    """
    ProgressBar
    """
    COLOR_DONE: str    = ColorOptions.Fore['LIGHTGREEN']
    COLOR_MISSING: str = ColorOptions.Fore['LIGHTMAGENTA']
    COLOR_RESET: str   = ColorOptions.Style['RESET']

    @staticmethod
    def set_colors(color_done: str, color_missing: str, color_reset: str) -> None:
        """
        setup the colors to use in the progress bar.
        
        Parameters:
        color_done (str):
            the color to use for the done progress (ansi escape)
        color_missing (str):
            the color to use for the missing progress (ansi escape)
        color_reset (str)
            the ansi esacpe to reset the color
        """
        PBar.COLOR_DONE = color_done
        PBar.COLOR_MISSING = color_missing
        PBar.COLOR_RESET = color_reset

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
        """
        initialize the progress bar
        """
        try:
            if os.isatty(sys.stdout.fileno()):
                print(CURSOR_INVISIBLE, end='')
                yield self.print_progress_bar
            else:
                yield lambda _: None
        finally:
            if os.isatty(sys.stdout.fileno()):
                if self.erase:
                    self.erase_progress_bar()
                print(CURSOR_VISIBLE, end='\n'*(not self.erase), flush=True)

    def print_progress_bar(self, iteration: int) -> None:
        """
        print the current state of the progress bar
        
        Parameters:
        iteration (int):
            the current progress iteration
        """
        if iteration < 0 or iteration > self.total:
            iteration = self.total
        percentage = min(100 * (iteration / float(self.total)), 100.0)
        percent_color = PBar.COLOR_DONE if percentage == 100.0 else PBar.COLOR_MISSING
        percent = f"{percentage:5.{self.decimals}f}"
        length_l = int(self.length * iteration // self.total)
        bars = f"{PBar.COLOR_DONE}{self.fill_l * length_l}{PBar.COLOR_MISSING}{self.fill_r * (self.length - length_l)}"
        progress = f"\r{self.prefix} {bars} {percent_color}{percent}%{PBar.COLOR_RESET} {self.suffix}"
        print(progress, end='', flush=True)

    def erase_progress_bar(self) -> None:
        """
        erase the progress bar from screen
        """
        length = len(self.prefix) + len(self.suffix) + self.length + 9
        print('\b \b' * length, end='')
