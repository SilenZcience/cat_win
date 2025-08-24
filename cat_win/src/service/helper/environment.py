"""
environment
"""

import os
import platform
import sys


on_windows_os = platform.system() == 'Windows'

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

    def _paths_equal(p):
        return os.path.normcase(os.path.normpath(p)) == py_dirname

    if any(_paths_equal(p) for p in environ_paths):
        py_executable = os.path.basename(py_executable)
        if on_windows_os and py_executable.lower().endswith('.exe'):
            py_executable = py_executable[:-4]
    elif ' ' in py_executable:
        py_executable = f'"{py_executable}"' if on_windows_os else py_executable.replace(' ', '\\ ')
    return py_executable
