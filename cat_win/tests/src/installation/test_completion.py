"""
test_completion
"""

import os
import sys
from unittest import TestCase
from unittest.mock import patch

from cat_win.src.installation import completion as cpl
from cat_win.src.installation.completion import (
    SUPPORTED_SHELLS,
    build_completion,
    completion_path,
    detect_shell,
    generate_bash,
    generate_fish,
    generate_zsh,
    install_hint,
    show_completion,
)
from cat_win.tests.mocks.args import DummyArgConstant
from cat_win.tests.mocks.logger import LoggerStub


class TestDetectShell(TestCase):
    def test_env_versions_are_checked_first(self):
        with patch.dict(os.environ, {}, clear=True):
            for env_var, expected in (
                ('ZSH_VERSION', 'zsh'),
                ('BASH_VERSION', 'bash'),
                ('FISH_VERSION', 'fish'),
            ):
                with self.subTest(env_var=env_var):
                    with patch.dict(os.environ, {}, clear=True):
                        os.environ[env_var] = '1'
                        self.assertEqual(detect_shell(), expected)

    def test_falls_back_to_process_name(self):
        with patch.dict(os.environ, {}, clear=True):
            for proc_name, expected in (
                ('/usr/bin/bash', 'bash'),
                ('/usr/bin/fish', 'fish'),
                ('/bin/zsh', 'zsh'),
            ):
                with self.subTest(proc_name=proc_name):
                    with patch.object(sys, 'argv', [proc_name]):
                        self.assertEqual(detect_shell(), expected)

    def test_falls_back_to_configured_login_shell(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, 'argv', ['python']):
                os.environ['SHELL'] = '/usr/bin/fish'
                self.assertEqual(detect_shell(), 'fish')

    def test_defaults_to_bash_when_nothing_matches(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, 'argv', ['python']):
                os.environ['SHELL'] = '/bin/sh'
                self.assertEqual(detect_shell(), 'bash')

    def test_defaults_to_bash_when_no_shell_is_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, 'argv', ['']):
                self.assertEqual(detect_shell(), 'bash')


class TestGenerateBash(TestCase):
    def test_default_arguments_shell_is_generated(self):
        script = generate_bash()
        self.assertIn('# bash completion for cat_win', script)
        self.assertIn('complete -F _cat_win_completion catw', script)
        self.assertIn('complete -F _cat_win_completion cats', script)

    def test_skips_hidden_and_placeholder_options(self):
        fake_args = [
            DummyArgConstant('-x', '', 'hidden', -1),
            DummyArgConstant('-y[1]', '', 'placeholder', 0),
            DummyArgConstant('-n', '--number', 'number', 0),
            DummyArgConstant('-l', '--length', 'length', -1, metavar='metavar'),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_bash()
        self.assertIn('-n', script)
        self.assertIn('--number', script)
        self.assertIn('-x ', script)
        self.assertIn('-y[1] ', script)
        self.assertNotIn('--length', script)

    def test_skips_empty_forms(self):
        fake_args = [
            DummyArgConstant('', '-w', 'long only', 0),
            DummyArgConstant('', '', 'nothing', 0),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_bash()
        self.assertIn('-w', script)

    def test_adds_value_options_without_duplicates(self):
        fake_args = [
            DummyArgConstant('-c', '--generate-completion', 'completion', 100, takes_value='SHELL'),
            DummyArgConstant('--eq', '--eq', 'self duplicate', 101, takes_value='SHELL'),
            DummyArgConstant('mode=x', '', 'operand with value', 102, takes_value='SHELL'),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_bash()
        self.assertIn('opt=""', script)
        self.assertIn('compgen -W "bash fish zsh"', script)
        self.assertIn('-c)', script)
        self.assertIn('--eq)', script)
        # short_form and long_form are the same string, so the pair must
        # only end up in the case block once (and not be doubled in choices)
        self.assertEqual(script.count('            --eq)\n'), 1)
        self.assertNotIn('|--eq|--eq', script)

    def test_omits_the_value_block_when_no_option_takes_a_value(self):
        fake_args = [DummyArgConstant('-a', '--alpha', 'alpha', 0)]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_bash()
        self.assertNotIn('opt=""', script)
        self.assertNotIn('case "$opt" in', script)


class TestGenerateZsh(TestCase):
    def test_default_arguments_shell_is_generated(self):
        script = generate_zsh()
        self.assertIn('#compdef catw cats', script)
        self.assertIn('_arguments -s -S : $args', script)

    def test_merges_operand_forms_and_excludes_colon_forms_from_message(self):
        fake_args = [
            DummyArgConstant('find=X', 'find:X', 'find/query', -1),
            DummyArgConstant('fg', '', 'background', 100),
            DummyArgConstant('-y[1]', '', 'placeholder', 0),
            DummyArgConstant('-x', '', 'hidden', -1),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_zsh()
        self.assertIn("'*:find=X, fg:(find=X find:X fg)'", script)
        self.assertNotIn('find:X:', script)

    def test_renders_value_and_plain_options_diffently(self):
        fake_args = [
            DummyArgConstant('-c', '--generate-completion', 'completion', 200, takes_value='SHELL'),
            DummyArgConstant('-n', '--number', 'number', 201),
            DummyArgConstant('', '-w', 'long only', 0),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_zsh()
        self.assertIn("'-c=-[completion]:the target shell:(bash fish zsh)'", script)
        self.assertIn("'-n[number]'", script)
        self.assertIn("'-w[long only]'", script)


class TestGenerateFish(TestCase):
    def test_default_arguments_shell_is_generated(self):
        script = generate_fish()
        self.assertIn('# fish completion for cat_win', script)
        for name in ('catw', 'cats'):
            self.assertIn(f'complete -c {name}', script)

    def test_renders_long_and_short_options_and_values(self):
        fake_args = [
            DummyArgConstant('-n', '--number', 'number all lines', 0),
            DummyArgConstant('-r', '', 'reverse', 1),
            DummyArgConstant('', '--nick', 'nickname', 2),
            DummyArgConstant('-c', '--generate-completion', 'completion', 200, takes_value='SHELL'),
        ]
        with patch.object(cpl, 'ALL_ARGS', fake_args):
            script = generate_fish()
        self.assertIn("-s 'n' -l 'number' -d 'number all lines'", script)
        self.assertIn("-s 'r' -d 'reverse'", script)
        self.assertIn("-l 'nick' -d 'nickname'", script)
        self.assertIn('--no-files -a "bash fish zsh"', script)


class TestBuildCompletion(TestCase):
    def test_dispatches_to_the_matching_generator(self):
        self.assertIn('catw --generate-completion=bash', build_completion('bash'))
        self.assertIn('#compdef catw cats', build_completion('zsh'))
        self.assertIn('# fish completion for cat_win', build_completion('fish'))

    def test_unknown_shell_raises_exit_3(self):
        with self.assertRaises(SystemExit) as ex:
            build_completion('powershell')
        self.assertEqual(ex.exception.code, 3)


class TestCompletionPath(TestCase):
    def test_resolves_known_shell_paths_under_home(self):
        for shell in SUPPORTED_SHELLS:
            with self.subTest(shell=shell):
                path = completion_path(shell)
                self.assertTrue(path.endswith(cpl.COMPLETION_PATHS[shell]))
                self.assertTrue(path.startswith(os.path.expanduser('~')))

    def test_unknown_shell_raises_exit_2(self):
        with self.assertRaises(SystemExit) as ex:
            completion_path('powershell')
        self.assertEqual(ex.exception.code, 2)


class TestInstallHint(TestCase):
    def test_explains_the_install_commands_for_a_shell(self):
        hint = install_hint('bash')
        self.assertIn('to install the completion script for bash, run:', hint)
        self.assertIn('catw --generate-completion=bash ', hint)
        self.assertIn('mkdir -p', hint)

    def test_zsh_gets_the_extra_fpath_hint(self):
        hint = install_hint('zsh')
        self.assertIn('fpath', hint)

    def test_non_zsh_shells_do_not_mention_fpath(self):
        hint = install_hint('fish')
        self.assertNotIn('fpath', hint)


class TestShowCompletion(TestCase):
    def test_noop_on_windows(self):
        with patch.object(cpl, 'on_windows_os', True):
            with patch.object(cpl, 'logger', LoggerStub()) as log:
                self.assertEqual(show_completion(), 0)
        self.assertIn('windows', log.output())

    def test_unknown_shell_reports_an_error_and_returns_one(self):
        with patch.object(cpl, 'on_windows_os', False):
            with patch.object(cpl, 'logger', LoggerStub()) as log:
                self.assertEqual(show_completion('powershell'), 1)
        out = log.output()
        self.assertIn('unknown shell', out)
        self.assertIn('expected one of', out)

    def test_prints_the_script_and_logs_the_hint(self):
        with patch.object(cpl, 'on_windows_os', False):
            with patch.object(cpl, 'build_completion', return_value='SCRIPT') as build:
                with patch.object(cpl, 'install_hint', return_value='HINT') as hint:
                    with patch.object(cpl, 'logger', LoggerStub()):
                        with patch('builtins.print') as print_mock:
                            self.assertEqual(show_completion('fish'), 0)
        build.assert_called_once_with('fish')
        hint.assert_called_once_with('fish')
        print_mock.assert_called_once_with('SCRIPT', end='')

    def test_detects_the_shell_when_none_is_given(self):
        with patch.object(cpl, 'on_windows_os', False):
            with patch.object(cpl, 'detect_shell', return_value='BASH') as detect:
                with patch.object(cpl, 'build_completion', return_value='SCRIPT') as build:
                    with patch.object(cpl, 'install_hint', return_value='HINT'):
                        with patch.object(cpl, 'logger', LoggerStub()):
                            with patch('builtins.print'):
                                self.assertEqual(show_completion(), 0)
        detect.assert_called_once_with()
        build.assert_called_once_with('bash')
