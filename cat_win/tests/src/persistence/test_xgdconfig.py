from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cat_win.src.persistence import xdgconfig


class TestXdgConfig(TestCase):
    def test_config_root_uses_override_and_expands_user(self):
        with patch.dict('os.environ', {xdgconfig.ENV_OVERRIDE: '~/my_cfg'}, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.os.path.expanduser', return_value='/expanded/my_cfg') as expand_user:
                root = xdgconfig._config_root()

        expand_user.assert_called_once_with('~/my_cfg')
        self.assertEqual(root, Path('/expanded/my_cfg'))

    def test_config_root_windows_prefers_appdata(self):
        env = {
            'APPDATA': 'C:/Users/Test/AppData/Roaming',
            'LOCALAPPDATA': 'C:/Users/Test/AppData/Local',
        }
        with patch.dict('os.environ', env, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'win32'):
                root = xdgconfig._config_root()

        self.assertEqual(root, Path('C:/Users/Test/AppData/Roaming'))

    def test_config_root_windows_uses_localappdata_if_appdata_missing(self):
        env = {
            'LOCALAPPDATA': 'C:/Users/Test/AppData/Local',
        }
        with patch.dict('os.environ', env, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'win32'):
                root = xdgconfig._config_root()

        self.assertEqual(root, Path('C:/Users/Test/AppData/Local'))

    def test_config_root_windows_falls_back_to_home_appdata_roaming(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'win32'):
                with patch('cat_win.src.persistence.xdgconfig.Path.home', return_value=Path('C:/Users/Test')):
                    root = xdgconfig._config_root()

        self.assertEqual(root, Path('C:/Users/Test/AppData/Roaming'))

    def test_config_root_darwin_uses_library_application_support(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'darwin'):
                with patch('cat_win.src.persistence.xdgconfig.Path.home', return_value=Path('/Users/test')):
                    root = xdgconfig._config_root()

        self.assertEqual(root, Path('/Users/test/Library/Application Support'))

    def test_config_root_linux_uses_xdg_config_home_when_set(self):
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': '/tmp/xdg_home'}, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'linux'):
                root = xdgconfig._config_root()

        self.assertEqual(root, Path('/tmp/xdg_home'))

    def test_config_root_linux_falls_back_to_home_dot_config(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('cat_win.src.persistence.xdgconfig.sys.platform', 'linux'):
                with patch('cat_win.src.persistence.xdgconfig.Path.home', return_value=Path('/home/test')):
                    root = xdgconfig._config_root()

        self.assertEqual(root, Path('/home/test/.config'))

    def test_xdg_config_builds_path_without_creating_directory(self):
        with patch('cat_win.src.persistence.xdgconfig._config_root', return_value=Path('/base')):
            with patch('cat_win.src.persistence.xdgconfig.Path.mkdir') as mkdir:
                result = xdgconfig.xdg_config('my.file', ensure_dir=False)

        self.assertEqual(result, Path('/base/cat_win/my.file'))
        mkdir.assert_not_called()

    def test_xdg_config_ensure_dir_for_file_path_creates_parent(self):
        with patch('cat_win.src.persistence.xdgconfig._config_root', return_value=Path('/base')):
            with patch('cat_win.src.persistence.xdgconfig.Path.mkdir') as mkdir:
                result = xdgconfig.xdg_config('config.ini', ensure_dir=True)

        self.assertEqual(result, Path('/base/cat_win/config.ini'))
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        created_target = mkdir.call_args_list[0][0][0] if mkdir.call_args_list[0][0] else None
        # Path.mkdir is a bound method in runtime; no positional path arg should be passed.
        self.assertIsNone(created_target)

    def test_xdg_config_ensure_dir_for_directory_like_part_creates_full_path(self):
        with patch('cat_win.src.persistence.xdgconfig._config_root', return_value=Path('/base')):
            with patch('cat_win.src.persistence.xdgconfig.Path.mkdir') as mkdir:
                result = xdgconfig.xdg_config('subdir', ensure_dir=True)

        self.assertEqual(result, Path('/base/cat_win/subdir'))
        mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_xdg_config_ensure_dir_with_no_parts_creates_cat_win_dir(self):
        with patch('cat_win.src.persistence.xdgconfig._config_root', return_value=Path('/base')):
            with patch('cat_win.src.persistence.xdgconfig.Path.mkdir') as mkdir:
                result = xdgconfig.xdg_config(ensure_dir=True)

        self.assertEqual(result, Path('/base/cat_win'))
        mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_xdg_config_multiple_parts_join_correctly(self):
        with patch('cat_win.src.persistence.xdgconfig._config_root', return_value=Path('/base')):
            result = xdgconfig.xdg_config('nested', 'state.json')

        self.assertEqual(result, Path('/base/cat_win/nested/state.json'))
