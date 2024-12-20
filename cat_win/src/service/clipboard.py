"""
clipboard
"""

from cat_win.src.service.helper.environment import get_py_executable
from cat_win.src.service.helper.iohelper import err_print


class Clipboard:
    """
    implements clipboard functionality
    """

    clipboard = ''
    copy_function = None
    paste_function = None

    @staticmethod
    def clear() -> None:
        """
        clear the clipboard
        """
        Clipboard.clipboard = ''

    @staticmethod
    def _copy(content: str, __dependency: int = 3, __clip_board_error: bool = False) -> bool:
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

        Returns:
        (bool):
            indicates if the clipboard function went successfull
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
            error_msg += f"'{get_py_executable()} -m pip install ...'"
            err_print('\n', error_msg, sep='')
            return False
        try:
            if __dependency == 3:
                import pyperclip as pc
            elif __dependency == 2:
                import pyclip as pc
            elif __dependency == 1:
                import pyperclip3 as pc
            Clipboard.copy_function = pc.copy
            Clipboard.put(content)
            return True
        except ImportError:
            Clipboard._copy(content, __dependency-1, False or __clip_board_error)
        except Exception:
            Clipboard._copy(content, __dependency-1, True or __clip_board_error)

    @staticmethod
    def put(content: str) -> bool:
        """
        entry point to recursive function _copy()

        Parameters:
        content (str):
            the string to copy

        Returns:
        (bool):
            indicates if the clipboard function went successfull
        """
        if Clipboard.copy_function is not None:
            Clipboard.copy_function(content)
            return True

        return Clipboard._copy(content)

    @staticmethod
    def _paste(__dependency: int = 3, __clip_board_error: bool = False):
        """
        import the clipboard by recursively checking which module exists and
        could be used, this function should only be called by Clipboard.get() and will only
        be called once.

        Parameters:
        __dependency (int):
            do not change!
        __clip_board_error (bool):
            do not change!

        Returns:
        (str|bytes):
            the content of the clipboard
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
            error_msg += f"'{get_py_executable()} -m pip install ...'"
            err_print('\n', error_msg, sep='')
            return
        try:
            if __dependency == 3:
                import pyperclip as pc
            elif __dependency == 2:
                import pyclip as pc
            elif __dependency == 1:
                import pyperclip3 as pc
            Clipboard.paste_function = pc.paste
        except ImportError:
            Clipboard._paste(__dependency-1, False or __clip_board_error)
        except Exception:
            Clipboard._paste(__dependency-1, True or __clip_board_error)

    @staticmethod
    def get():
        """
        entry point to recursive function _paste()

        Returns:
        (str):
            the content of the clipboard or None
        """
        if Clipboard.paste_function is None:
            Clipboard._paste()
        if Clipboard.paste_function is None:
            return None
        clipboard = Clipboard.paste_function()
        if isinstance(clipboard, bytes):
            return clipboard.decode(errors='ignore')
        return clipboard
