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
    if os.path.dirname(py_executable) in os.environ['PATH'].split(os.pathsep):
        py_executable = os.path.basename(py_executable)
    elif ' ' in py_executable:
        py_executable = f'"{py_executable}"' if on_windows_os else py_executable.replace(' ', '\\ ')
    return py_executable
