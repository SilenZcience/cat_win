"""
clipboard
"""

import os
import sys

from cat_win.src.service.helper.iohelper import err_print


class Clipboard:
    """
    implements clipboard functionality
    """

    clipboard = ''
    copy_function = None

    @staticmethod
    def _copy(content: str, __dependency: int = 3, __clip_board_error: bool = False) -> None:
        """
        import the clipboard by recursively checking which module exists and
        could be used, this function should only be called by Clipboard.put() and will only
        be called once.
        
        Parameters:
        content (str):
            the content to copy to the clipboard
        __dependency (int):
            do not change!
        __clip_board_error (bool):
            do not change!
        """
        if __dependency == 0:
            if __clip_board_error:
                error_msg = "ClipBoardError: You can use"
            else:
                error_msg = "ImportError: You need"
            error_msg += " either 'pyperclip3', 'pyperclip', or 'pyclip' "
            error_msg += "in order to use the '--clip' parameter.\n"
            error_msg += 'Should you have any problem with either module, '
            error_msg += 'try to install a different one using '
            error_msg += f"'{os.path.basename(sys.executable)} -m pip install ...'"
            return err_print('\n', error_msg, sep='')
        try:
            if __dependency == 3:
                import pyperclip as pc
            elif __dependency == 2:
                import pyclip as pc
            elif __dependency == 1:
                import pyperclip3 as pc
            Clipboard.copy_function = pc.copy
            Clipboard.put(content)
            return
        except ImportError:
            Clipboard._copy(content, __dependency-1, False or __clip_board_error)
        except Exception:
            Clipboard._copy(content, __dependency-1, True or __clip_board_error)

    @staticmethod
    def put(content: str) -> None:
        """
        entry point to recursive function _copy_to_clipboard()
        
        Parameters:
        content (str):
            the string to copy
        """
        if Clipboard.copy_function is not None:
            Clipboard.copy_function(content)
            return

        Clipboard._copy(content)
