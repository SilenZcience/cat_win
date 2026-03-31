from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_CCONFIG,
    ARGS_CCONFIG_FLUSH,
    ARGS_CONFIG,
    ARGS_CONFIG_FLUSH,
    ARGS_CONFIG_REMOVE,
    ARGS_DEBUG,
    ARGS_HELP,
    ARGS_VERSION,
)
from cat_win.src.processor import executionprecessor
from cat_win.src.processor.executionprecessor import (
    _remove_config,
    _reset_color_config,
    _reset_config,
    _save_color_config,
    _save_config,
    _show_debug,
    _show_help,
    _show_version,
    run_startup_actions,
)
from cat_win.tests.mocks.argparser import DummyArgParser
from cat_win.tests.mocks.args import DummyStartupArgs
from cat_win.tests.mocks.ctx import DummyCtx
from cat_win.tests.mocks.logger import LoggerStub


class _Arg:
    def __init__(self, section, show_arg, show_arg_on_repl, short_form, long_form, arg_help):
        self.section = section
        self.show_arg = show_arg
        self.show_arg_on_repl = show_arg_on_repl
        self.short_form = short_form
        self.long_form = long_form
        self.arg_help = arg_help


class TestExecutionPrecessor(TestCase):
    @staticmethod
    def _printed_text(print_mock) -> str:
        # Python 3.6 compatibility: call.args may not be usable as in newer versions.
        parts = []
        for call_ in print_mock.call_args_list:
            args = call_[0] if len(call_) > 0 else ()
            if args:
                parts.append(str(args[0]))
        return ''.join(parts)

    def _mk_ctx(self, u_args=None):
        ctx = DummyCtx(u_args=u_args if u_args is not None else DummyStartupArgs(), arg_parser=DummyArgParser())
        ctx.known_files = []
        ctx.unknown_files = []
        ctx.known_dirs = []
        ctx.valid_urls = []
        ctx.echo_args = ''
        ctx.working_dir = '/tmp/work'
        ctx.config = MagicMock()
        ctx.cconfig = MagicMock()
        return ctx

    def test_show_help_uses_more_and_prints_update_non_repl(self):
        fake_args = [
            _Arg(0, True, True, '-a', '--alpha', 'alpha help'),
            _Arg(1, True, True, '-b', '--beta', 'beta help'),
            _Arg(-1, True, True, '-x', '--hidden', 'hidden help'),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                    _show_help(False)

        more_cls.assert_called_once()
        more_cls.return_value.step_through.assert_called_once()
        update.assert_called_once()

    def test_show_help_repl_filters_repl_only_entries(self):
        fake_args = [
            _Arg(0, True, True, '-a', '--alpha', 'alpha help'),
            _Arg(0, True, False, '-b', '--beta', 'beta help'),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(True)

        help_lines = more_cls.call_args[0][0]
        rendered = '\n'.join(help_lines)
        self.assertIn('cats [OPTION]', rendered)
        self.assertIn('--alpha', rendered)
        self.assertNotIn('--beta', rendered)

    def test_show_help_truncates_long_argument_descriptor(self):
        fake_args = [
            _Arg(0, True, True, '-x', '--' + 'verylongargumentname' * 3, 'desc'),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(False)

        rendered = '\n'.join(more_cls.call_args[0][0])
        self.assertIn('...', rendered)

    def test_show_help_always_prints_update_even_if_more_fails(self):
        with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
            more_cls.return_value.step_through.side_effect = RuntimeError('stop')
            with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                with self.assertRaises(RuntimeError):
                    _show_help(False)
        update.assert_called_once()

    def test_show_version_with_install_time(self):
        ctx = self._mk_ctx()
        with patch('cat_win.src.processor.executionprecessor.get_file_ctime', return_value=0):
            with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                with patch('builtins.print') as p:
                    _show_version(ctx, repl=True)

        printed = self._printed_text(p)
        self.assertIn('REPL', printed)
        self.assertIn('Install time', printed)
        update.assert_called_once()

    def test_show_version_handles_ctime_oserror(self):
        ctx = self._mk_ctx()
        with patch('cat_win.src.processor.executionprecessor.get_file_ctime', side_effect=OSError):
            with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                with patch('builtins.print') as p:
                    _show_version(ctx, repl=False)

        printed = self._printed_text(p)
        self.assertIn('Installtime:\t-', printed.replace(' ', ''))

    def test_show_debug_logs_all_sections(self):
        logger_stub = LoggerStub()
        ctx = self._mk_ctx(u_args=DummyStartupArgs(overrides={ARGS_DEBUG: True}, ordered_args=[(ARGS_DEBUG, '-d')]))
        ctx.arg_parser.file_queries = [('abc', False)]
        ctx.arg_parser.file_queries_replacement = ['x']
        ctx.arg_parser.file_truncate = [1, 2, 3]
        ctx.known_files = ['f1']
        ctx.unknown_files = ['u1']
        ctx.known_dirs = ['d1']
        ctx.valid_urls = ['url']
        ctx.echo_args = 'echo'

        with patch('cat_win.src.processor.executionprecessor.logger', logger_stub):
            _show_debug(ctx, ['--weird'])

        out = logger_stub.output()
        self.assertIn('DEBUG', out)
        self.assertIn('unknown_args', out)
        self.assertIn('known_files', out)
        self.assertIn('replace queries', out)

    def test_config_startup_actions_call_expected_targets(self):
        ctx = self._mk_ctx()
        _remove_config(ctx)
        _reset_config(ctx)
        _reset_color_config(ctx)
        _save_config(ctx)
        _save_color_config(ctx)

        ctx.config.remove_config.assert_called_once()
        ctx.config.reset_config.assert_called_once()
        ctx.cconfig.reset_config.assert_called_once()
        ctx.config.save_config.assert_called_once()
        ctx.cconfig.save_config.assert_called_once()

    def test_run_startup_actions_help_when_no_inputs_non_repl(self):
        ctx = self._mk_ctx(u_args=DummyStartupArgs())
        with patch('cat_win.src.processor.executionprecessor._show_help') as show_help:
            with self.assertRaises(SystemExit) as ex:
                run_startup_actions(ctx, repl=False, arg_suggestions=[])
        self.assertEqual(ex.exception.code, 0)
        show_help.assert_called_once_with(False)

    def test_run_startup_actions_help_flag(self):
        ctx = self._mk_ctx(u_args=DummyStartupArgs(overrides={ARGS_HELP: True}, ordered_args=[(ARGS_HELP, '--help')]))
        with patch('cat_win.src.processor.executionprecessor._show_help') as show_help:
            with self.assertRaises(SystemExit):
                run_startup_actions(ctx, repl=True, arg_suggestions=[])
        show_help.assert_called_once_with(True)

    def test_run_startup_actions_version_flag(self):
        ctx = self._mk_ctx(u_args=DummyStartupArgs(overrides={ARGS_VERSION: True}, ordered_args=[(ARGS_VERSION, '--version')]))
        with patch('cat_win.src.processor.executionprecessor._show_version') as show_version:
            with self.assertRaises(SystemExit):
                run_startup_actions(ctx, repl=False, arg_suggestions=[])
        show_version.assert_called_once_with(ctx, False)

    def test_run_startup_actions_debug_then_return_when_no_handlers(self):
        args = DummyStartupArgs(overrides={ARGS_DEBUG: True}, ordered_args=[(999999, '--noop')])
        ctx = self._mk_ctx(u_args=args)
        ctx.known_files = ['file']
        with patch('cat_win.src.processor.executionprecessor._show_debug') as show_debug:
            run_startup_actions(ctx, repl=False, arg_suggestions=['--bad'])
        show_debug.assert_called_once_with(ctx, ['--bad'])

    def test_run_startup_actions_executes_registered_handler_and_exits(self):
        args = DummyStartupArgs(overrides={ARGS_CONFIG_REMOVE: True}, ordered_args=[(ARGS_CONFIG_REMOVE, '--rmcfg')])
        ctx = self._mk_ctx(u_args=args)
        ctx.known_files = ['file']
        with self.assertRaises(SystemExit) as ex:
            run_startup_actions(ctx, repl=False, arg_suggestions=[])
        self.assertEqual(ex.exception.code, 0)
        ctx.config.remove_config.assert_called_once()

    def test_run_startup_actions_ignores_unknown_startup_ids(self):
        args = DummyStartupArgs(ordered_args=[(123456, '--unknown')])
        ctx = self._mk_ctx(u_args=args)
        ctx.known_files = ['file']
        run_startup_actions(ctx, repl=False, arg_suggestions=[])
