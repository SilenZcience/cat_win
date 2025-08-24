from unittest import TestCase
from unittest.mock import patch

from cat_win.src.service.helper.environment import get_py_executable


class TestEnvironment(TestCase):
    maxDiff = None

    @patch('sys.executable', '/usr/bin/python')
    @patch('os.environ', {'PATH': '/usr/bin'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', False)
    def test_get_py_executable_linux_path_a(self):
        self.assertEqual(get_py_executable(), 'python')

    @patch('sys.executable', '/usr/bin/python')
    @patch('os.environ', {'PATH': '/usr/bin/'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', False)
    def test_get_py_executable_linux_path_b(self):
        self.assertEqual(get_py_executable(), 'python')

    @patch('sys.executable', '/usr/bin/python3')
    @patch('os.environ', {'PATH': '/usr/bin/'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', False)
    def test_get_py_executable_linux_path_c(self):
        self.assertEqual(get_py_executable(), 'python3')


    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/python.exe')
    @patch('os.environ', {'PATH': '/Users/user/AppData/Local/Programs/Python/Python39'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_path_a(self):
        self.assertEqual(get_py_executable(), 'python')

    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/python.exe')
    @patch('os.environ', {'PATH': '/Users/user/AppData/Local/Programs/Python/Python39/'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_path_b(self):
        self.assertEqual(get_py_executable(), 'python')

    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/python.exe')
    @patch('os.environ', {'PATH': '/Users/user/AppData/Local/Programs/Python/Python39\\'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_path_c(self):
        self.assertEqual(get_py_executable(), 'python')

    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/python3.exe')
    @patch('os.environ', {'PATH': '/Users/user/AppData/Local/Programs/Python/Python39\\'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_path_d(self):
        self.assertEqual(get_py_executable(), 'python3')

    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/py')
    @patch('os.environ', {'PATH': '/Users/user/AppData/Local/Programs/Python/Python39\\'})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_path_e(self):
        self.assertEqual(get_py_executable(), 'py')


    @patch('sys.executable', '/usr/bin/python4?')
    @patch('os.environ', {})
    @patch('cat_win.src.service.helper.environment.on_windows_os', False)
    def test_get_py_executable_linux_nopath_a(self):
        self.assertEqual(get_py_executable(), '/usr/bin/python4?')

    @patch('sys.executable', '/Users/user/AppData/Local/Programs/Python/Python39/python4.exe?')
    @patch('os.environ', {})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_nopath_a(self):
        self.assertEqual(get_py_executable(), '/Users/user/AppData/Local/Programs/Python/Python39/python4.exe?')


    @patch('sys.executable', '/usr/bin/spa ce/python4?')
    @patch('os.environ', {})
    @patch('cat_win.src.service.helper.environment.on_windows_os', False)
    def test_get_py_executable_linux_nopath_space_a(self):
        self.assertEqual(get_py_executable(), '/usr/bin/spa\\ ce/python4?')

    @patch('sys.executable', '/Program Files/Python/Python39/python4.exe?')
    @patch('os.environ', {})
    @patch('cat_win.src.service.helper.environment.on_windows_os', True)
    def test_get_py_executable_windows_nopath_space_a(self):
        self.assertEqual(get_py_executable(), '"/Program Files/Python/Python39/python4.exe?"')
