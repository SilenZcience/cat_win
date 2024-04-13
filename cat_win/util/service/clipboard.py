"""
clipboard
"""

import os
import sys

class Clipboard:
    """
    implements clipboard functionality
    """

    copy_function = None

    @staticmethod
    def _copy_def(__dependency: int = 3, __clip_board_error: bool = False) -> object:
        """
        return a method to copy to the clipboard by recursively checking which module exists and
        could be used, this function should only be called by Clipboard.put()
        
        Parameters:
        __dependency (int):
            do not change!
        __clip_board_error (bool):
            do not change!
            
        Returns:
        (function):
            the method used for copying to the clipboard
            (in case we want to use this function again without another import)
        """
        if __dependency == 0:
            if __clip_board_error:
                error_msg = '\n'
                error_msg += "ClipBoardError: You can use either 'pyperclip3', "
                error_msg += "'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
                error_msg += 'Try to install a different one using '
                error_msg += f"'{os.path.basename(sys.executable)} -m pip install ...'"
            else:
                error_msg = '\n'
                error_msg += "ImportError: You need either 'pyperclip3', 'pyperclip',"
                error_msg += "or 'pyclip' in order to use the '--clip' parameter.\n"
                error_msg += 'Should you have any problem with either module, try to install a diff'
                error_msg += f"erent one using '{os.path.basename(sys.executable)} -m pip install ...'"
            print(error_msg, file=sys.stderr)
            return None
        try:
            if __dependency == 3:
                import pyperclip as pc
            elif __dependency == 2:
                import pyclip as pc
            elif __dependency == 1:
                import pyperclip3 as pc
            return pc.copy
        except ImportError:
            return Clipboard._copy_def(__dependency-1, False or __clip_board_error)
        except Exception:
            return Clipboard._copy_def(__dependency-1, True or __clip_board_error)

    @staticmethod
    def put(content: str) -> None:
        """
        entry point to recursive function _copy_to_clipboard()
        
        Parameters:
        content (str):
            the string to copy
        copy_function (function):
            the method to use for copying to the clipboard
            (in case such a method already exists we do not need to import any module (again))
        """
        if Clipboard.copy_function is None:
            Clipboard.copy_function = Clipboard._copy_def()
        Clipboard.copy_function(content)
