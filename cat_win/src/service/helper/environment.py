"""
environment
"""

import os
import platform
import sys


on_pyinstaller = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
on_windows_os  = platform.system() == 'Windows'
on_mac_os      = platform.system() == 'Darwin'


def get_py_executable() -> str:
    """
    get the most likely python executable

    Returns:
    py_executable (str):
        the python executable used to start the current process
    """
    py_executable = sys.executable
    py_dirname    = os.path.normcase(os.path.normpath(os.path.dirname(py_executable)))
    environ_paths = os.environ.get('PATH', '').split(os.pathsep)

    def _paths_equal(p) -> bool:
        return os.path.normcase(os.path.normpath(p)) == py_dirname

    if any(_paths_equal(p) for p in environ_paths):
        py_executable = os.path.basename(py_executable)
        if on_windows_os and py_executable.lower().endswith('.exe'):
            py_executable = py_executable[:-4]
    elif ' ' in py_executable:
        py_executable = f'"{py_executable}"' if on_windows_os else py_executable.replace(' ', '\\ ')
    return py_executable
