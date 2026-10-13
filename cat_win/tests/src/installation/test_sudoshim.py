"""
test_sudoshim
"""

import ast
import io
import subprocess
import tokenize
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cat_win.src.installation import sudoshim as sh
from cat_win.src.installation.sudoshim import (
    CONSOLE_SCRIPTS,
    SHIM_DIR,
    build_shim,
    install_hint,
    show_shim
)


class TestBuildShim(TestCase):
    def test_is_valid_posix_shell(self):
        #check syntax errors with 'sh -n'
        result = subprocess.run(
            ['sh', '-n'], input=build_shim(), text=True,
            capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_starts_with_shebang(self):
        self.assertTrue(build_shim().startswith('#!/bin/sh\n'))

    def test_dispatches_on_the_name_it_was_invoked_as(self):
        shim = build_shim()
        self.assertIn('basename "$0"', shim)
        self.assertIn('"$_cw_dir/$_cw_script"', shim)
        # no Script Name may be baked into the payload at all
        for name in CONSOLE_SCRIPTS:
            self.assertNotIn('_cw_dir/' + name, shim)

    def test_pins_config_dir_to_the_invoking_user(self):
        # sudo resets HOME to root's, so without this the caller would get
        # root's config instead of their own
        shim = build_shim()
        self.assertIn('SUDO_USER', shim)
        self.assertIn('CAT_WIN_CONFIG_DIR="$_cw_home/.config"', shim)

    def test_respects_an_explicit_config_dir(self):
        shim = build_shim()
        self.assertIn('if [ -z "${CAT_WIN_CONFIG_DIR:-}" ]', shim)

    def test_searches_user_bin_dirs(self):
        shim = build_shim()
        self.assertIn('"$_cw_home/.local/bin"', shim)
        self.assertIn('"$_cw_home/bin"', shim)

    def test_does_not_search_its_own_directory(self):
        # would make the shim exec itself forever
        self.assertNotIn(SHIM_DIR, build_shim())

    def test_generation_is_deterministic(self):
        self.assertEqual(build_shim(), build_shim())


class TestInstallHint(TestCase):
    def test_names_every_target_path(self):
        hint = install_hint()
        for name in CONSOLE_SCRIPTS:
            self.assertIn(name, hint)
        self.assertIn(SHIM_DIR, hint)

    def test_sets_the_executable_bit(self):
        self.assertIn('chmod 755', install_hint())

    def test_installs_under_both_names(self):
        for name in CONSOLE_SCRIPTS:
            self.assertIn(name, install_hint().split('to remove')[0])

    def test_tells_the_user_how_to_remove_it(self):
        self.assertIn('sudo rm -f', install_hint())

    def test_never_runs_sudo_itself(self):
        self.assertNotIn('subprocess', install_hint())


class TestShowShim(TestCase):
    def test_exits_zero(self):
        with patch.object(sh, 'on_windows_os', False):
            self.assertEqual(show_shim(), 0)

    def test_noop_on_windows(self):
        with patch.object(sh, 'on_windows_os', True):
            self.assertEqual(show_shim(), 0)


class TestNoEscalation(TestCase):
    def test_never_escalates(self):
        source = Path(sh.__file__).read_text()
        code_lines = set()
        for token in tokenize.generate_tokens(
                io.StringIO(source).readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            code_lines.update(range(token.start[0], token.end[0] + 1))
        code = '\n'.join(
            line for number, line in enumerate(source.split('\n'), 1)
            if number in code_lines
        )
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    code = code.replace(doc, '')
        for forbidden in ('subprocess', 'setuid', 'os.system', 'popen',
                          'geteuid', 'doas'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, code)
