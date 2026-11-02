"""
test_mods
"""

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cat_win.src.argparser import ArgParser
from cat_win.src.const.argconstants import ALL_ARGS
from cat_win.src.modding.mods import MODS_DIR, load_mods
from cat_win.tests.mocks.std import StdOutMock


def _save_all_args():
    return list(ALL_ARGS)

def _restore_all_args(saved):
    ALL_ARGS.clear()
    ALL_ARGS.extend(saved)


class TestLoadMods(TestCase):
    def test_no_mods_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'nonexistent_mods'
            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()
                self.assertEqual(loaded, [])
                self.assertEqual(failed, [])

    def test_empty_mods_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()
            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()
                self.assertEqual(loaded, [])
                self.assertEqual(failed, [])

    def test_loads_valid_mod(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()

            mod_file = fake_mods_dir / 'my_valid_mod.py'
            mod_file.write_text('# valid mod\nx = 42\nprint("MOD IS LOADED!")\n')

            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                with patch('sys.stdout', new=StdOutMock()) as fake_out:
                    loaded, failed = load_mods()
                    self.assertEqual(fake_out.getvalue(), "MOD IS LOADED!\n")

                self.assertEqual(len(failed), 0)
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0], 'cat_win.mods.my_valid_mod')

    def test_handles_broken_mod(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()

            mod_file = fake_mods_dir / 'broken_mod.py'
            mod_file.write_text('raise RuntimeError("boom")\n')

            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()

                self.assertEqual(len(loaded), 0)
                self.assertEqual(len(failed), 1)
                self.assertEqual(failed[0][0], 'cat_win.mods.broken_mod')
                self.assertIn('RuntimeError', failed[0][1])

    def test_loads_multiple_mods_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()

            (fake_mods_dir / 'zebra_mod.py').write_text('# zebra\n')
            (fake_mods_dir / 'apple_mod.py').write_text('# apple\n')

            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()

                self.assertEqual(len(loaded), 2)
                self.assertEqual(loaded[0], 'cat_win.mods.apple_mod')
                self.assertEqual(loaded[1], 'cat_win.mods.zebra_mod')
                self.assertEqual(failed, [])

    def test_skips_underscore_prefixed_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()

            (fake_mods_dir / '_private_mod.py').write_text('# private\n')
            (fake_mods_dir / 'public_mod.py').write_text('# public\n')

            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()

                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0], 'cat_win.mods.public_mod')
                self.assertEqual(failed, [])

    def test_mods_dir_uses_xdg_config(self):
        self.assertEqual(MODS_DIR.name, '~mods')
        self.assertIn('cat_win', str(MODS_DIR))


class TestModCustomCommandIntegration(TestCase):
    def setUp(self):
        self._saved_args = _save_all_args()

    def tearDown(self):
        _restore_all_args(self._saved_args)

    def test_load_mod_file_that_appends_arg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_mods_dir = Path(tmpdir) / 'mods'
            fake_mods_dir.mkdir()

            mod_file = fake_mods_dir / 'adds_flag_mod.py'
            mod_file.write_text(
                'from cat_win.src.modding import *\n'
                'ALL_ARGS.append(ArgConstant(\n'
                '    "--mod-sum-flag", "--mod-sum-flag",\n'
                '    "mod sum flag", 99998\n'
                '))\n'
            )

            with patch('cat_win.src.modding.mods.MODS_DIR', fake_mods_dir):
                loaded, failed = load_mods()

                self.assertEqual(len(failed), 0)
                self.assertEqual(len(loaded), 1)

                # The new ArgConstant is now in ALL_ARGS.
                new_args = [a for a in ALL_ARGS if a.arg_id == 99998]
                self.assertEqual(len(new_args), 1)
                self.assertEqual(new_args[0].short_form, '--mod-sum-flag')

                # ArgParser recognizes it as a known arg, not unknown.
                parser = ArgParser()
                args, unknown_args, echo_args = parser.get_arguments(
                    ['catw', '--mod-sum-flag']
                )
                self.assertNotIn('--mod-sum-flag', unknown_args)
                self.assertGreaterEqual(len(args), 1)
