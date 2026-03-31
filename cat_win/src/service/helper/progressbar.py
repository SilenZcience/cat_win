"""
progressbar
"""

import contextlib
import os
import shutil
import sys

from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.escapecodes import CURSOR_VISIBLE, CURSOR_INVISIBLE


class PBar:
    """
    ProgressBar
    """
    COLOR_DONE: str    = ''
    COLOR_MISSING: str = ''
    COLOR_RESET: str   = ''

    @staticmethod
    def set_colors(color_dic: dict) -> None:
        """
        setup the colors to use in the progress bar.

        Parameters:
        color_dic (dict):
            color dictionary containing all configured ANSI color values
        """
        PBar.COLOR_DONE    = color_dic[CKW.PROGRESSBAR_DONE]
        PBar.COLOR_MISSING = color_dic[CKW.PROGRESSBAR_MISSING]
        PBar.COLOR_RESET   = color_dic[CKW.RESET_ALL]

    def __init__(self, total: int, prefix: str = '', suffix: str = '',
                    decimals: int = 1, length: int = -1,
                    fill_l: str = '█', fill_r: str = '-', erase: bool = False) -> None:
        # x━x x╺x x╸x x-x
        self.total = total
        self.prefix = prefix
        if suffix and suffix[0] != ' ':
            suffix = ' ' + suffix
        self.suffix = suffix
        self.decimals = decimals

        length_  = shutil.get_terminal_size()[0]
        length_ -= len(self.prefix)
        length_ -= len(self.suffix)
        length_ -= 4 # 2 spaces and 1 '%' and 1 buffer at the end
        length_ -= (4+decimals) # '100.' -> 4 + decimals
        length_  = max(0, min(length_, length))
        self.length = length_
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
        percent = f"{percentage:{4+self.decimals}.{self.decimals}f}"
        length_l = int(self.length * iteration // self.total)
        bars = f"{PBar.COLOR_DONE}{self.fill_l * length_l}{PBar.COLOR_MISSING}{self.fill_r * (self.length - length_l)}"
        progress = f"\r{self.prefix} {bars} {percent_color}{percent}%{PBar.COLOR_RESET}{self.suffix}"
        print(progress, end='', flush=True)

    def erase_progress_bar(self) -> None:
        """
        erase the progress bar from screen
        """
        length = self.length + len(self.prefix) + len(self.suffix) + 4 + (4+self.decimals)
        print('\b \b' * length, end='')
