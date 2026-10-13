"""
test_manpage
"""

from unittest import TestCase
from unittest.mock import patch

from cat_win.src.installation import manpage as mp
from cat_win.src.installation.manpage import (
    MAN_DIR,
    _roff_escape,
    build_man,
    install_hint,
    show_man,
)
from cat_win.tests.mocks.args import DummyArgConstant
from cat_win.tests.mocks.logger import LoggerStub


class TestRoffEscape(TestCase):
    def test_escapes_formats_groff_could_swallow(self):
        self.assertEqual(_roff_escape('-h'), '\\&-h')
        self.assertEqual(_roff_escape("'x"), "\\&'x")
        self.assertEqual(_roff_escape('[A,B]'), '\\&[A,B]')
        self.assertEqual(_roff_escape('&'), '\\&&')

    def test_leaves_plain_parameters_untouched(self):
        self.assertEqual(_roff_escape('find=X'), 'find=X')


class TestBuildMan(TestCase):
    def test_default_arguments_build_a_complete_man_page(self):
        page = build_man()
        self.assertIn('.TH CATW 1', page)
        self.assertIn('.SH OPTIONS', page)
        self.assertIn('.SH EXIT STATUS', page)
        self.assertIn('.B 0', page)
        self.assertIn('.B >= 1', page)
        self.assertIn('.SH AUTHOR', page)
        self.assertIn('find=X', page)
        self.assertIn('--Rin', page)

    def test_renders_placeholder_arguments_escaped(self):
        fake_args = [
            DummyArgConstant('[A,B]', '', 'replace', -1, section=16),
            DummyArgConstant('-n', '--number', 'number', 0, section=1),
        ]
        with patch.object(mp, 'ALL_ARGS', fake_args):
            page = build_man()
        self.assertIn('.B \\&[A,B]', page)
        self.assertIn('.B \\&-n, \\&--number', page)

    def test_emits_section_headings_and_groups_arguments(self):
        fake_args = [
            DummyArgConstant('-a', '', 'alpha', 0, section=0),
            DummyArgConstant('-W', '--wordcount', 'word count', 1, section=0),
            DummyArgConstant('-z', '', 'zeta', 2, section=999),
        ]
        with patch.object(mp, 'ALL_ARGS', fake_args):
            page = build_man()
        self.assertIn('.SS General Information', page)
        self.assertIn('.SS Other', page)

    def test_does_not_duplicate_same_long_and_short_form(self):
        fake_args = [DummyArgConstant('--Rin', '--Rin', 'stdin encoding', 1401, section=14)]
        with patch.object(mp, 'ALL_ARGS', fake_args):
            page = build_man()
        self.assertEqual(page.count('--Rin'), 1)

    def test_places_the_help_on_its_own_roff_line(self):
        fake_args = [DummyArgConstant('fg', '', 'background session', 100, section=0)]
        with patch.object(mp, 'ALL_ARGS', fake_args):
            page = build_man()
        self.assertIn('.B fg\n.br\nBackground session.', page)

    def test_appends_the_takes_value_suffix_to_every_form(self):
        fake_args = [DummyArgConstant('-c', '--generate-completion', 'completion', 200,
                          section=15, takes_value='SHELL')]
        with patch.object(mp, 'ALL_ARGS', fake_args):
            page = build_man()
        self.assertIn('.B \\&-c=SHELL, \\&--generate-completion=SHELL', page)


class TestInstallHint(TestCase):
    def test_explains_the_install_and_removal_commands(self):
        hint = install_hint()
        self.assertIn('to install the man page, run:', hint)
        self.assertIn('catw --generate-man > ', hint)
        self.assertIn(MAN_DIR, hint)
        self.assertIn('rm -f', hint)
        self.assertIn('man catw', hint)


class TestShowMan(TestCase):
    def test_noop_on_windows(self):
        with patch.object(mp, 'on_windows_os', True):
            with patch.object(mp, 'logger', LoggerStub()) as log:
                self.assertEqual(show_man(), 0)
        self.assertIn('windows', log.output())

    def test_prints_the_page_and_logs_the_hint(self):
        with patch.object(mp, 'on_windows_os', False):
            with patch.object(mp, 'build_man', return_value='MANPAGE') as build:
                with patch.object(mp, 'install_hint', return_value='HINT') as hint:
                    with patch.object(mp, 'logger', LoggerStub()):
                        with patch('builtins.print') as print_mock:
                            self.assertEqual(show_man(), 0)
        build.assert_called_once_with()
        hint.assert_called_once_with()
        print_mock.assert_called_once_with('MANPAGE', end='')
