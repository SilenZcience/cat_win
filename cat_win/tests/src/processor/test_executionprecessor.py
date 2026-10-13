from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_COMPLETION,
    ARGS_CONFIG_REMOVE,
    ARGS_DEBUG,
    ARGS_HELP,
    ARGS_SUDO_ALLOW,
    ARGS_VERSION,
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.processor import executionprecessor
from cat_win.src.processor.executionprecessor import (
    _show_sudoshim,
    _remove_config,
    _reset_color_config,
    _reset_config,
    _save_color_config,
    _save_config,
    _show_completion,
    _show_debug,
    _show_help,
    _show_man,
    _show_version,
    run_startup_actions,
)
from cat_win.tests.mocks.argparser import DummyArgParser
from cat_win.tests.mocks.args import DummyArgConstant, DummyStartupArgs
from cat_win.tests.mocks.ctx import DummyCtx
from cat_win.tests.mocks.logger import LoggerStub


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
        color_dic = {
            CKW.RESET_ALL: '\x1b[0m',
            'cyan': '\x1b[36m',
            'yellow': '\x1b[33m',
            'magenta': '\x1b[35m',
            'green': '\x1b[32m',
        }
        ctx = DummyCtx(
            u_args=u_args if u_args is not None else DummyStartupArgs(),
            color_dic=color_dic,
            arg_parser=DummyArgParser(),
        )
        ctx.known_files = []
        ctx.unknown_files = []
        ctx.known_dirs = []
        ctx.valid_urls = []
        ctx.echo_args = ''
        ctx.config = MagicMock()
        ctx.cconfig = MagicMock()
        return ctx

    def test_show_help_uses_more_and_prints_update_non_repl(self):
        fake_args = [
            DummyArgConstant('-a', '--alpha', 'alpha help', 0, section=0),
            DummyArgConstant('-b', '--beta', 'beta help', 1, section=1),
            DummyArgConstant('-x', '--hidden', 'hidden help', -1),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                    _show_help(self._mk_ctx(), False)

        more_cls.assert_called_once()
        more_cls.return_value.step_through.assert_called_once()
        update.assert_called_once()

    def test_show_help_repl_filters_repl_only_entries(self):
        fake_args = [
            DummyArgConstant('-a', '--alpha', 'alpha help', 0, section=0),
            DummyArgConstant('-b', '--beta', 'beta help', 0, show_arg_on_repl=False, section=0),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(self._mk_ctx(), True)

        help_lines = more_cls.call_args[0][0]
        rendered = '\n'.join(help_lines)
        self.assertIn('Interactively manipulate standard input.', rendered)
        self.assertIn('--alpha', rendered)
        self.assertNotIn('--beta', rendered)

    def test_show_help_truncates_long_argument_descriptor(self):
        fake_args = [
            DummyArgConstant('-x', '--' + 'verylongargumentname' * 3, 'desc', 0, section=0),
        ]
        with patch.object(executionprecessor, 'ALL_ARGS', fake_args):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(self._mk_ctx(), False)

        rendered = '\n'.join(more_cls.call_args[0][0])
        self.assertIn('...', rendered)

    def test_show_help_renders_metavar_with_value_description(self):
        arg = DummyArgConstant('-R', '--R', 'reconfigure streams', 0, section=0)
        arg.metavar = 'STREAM'
        with patch.object(executionprecessor, 'ALL_ARGS', [arg]):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(self._mk_ctx(), False)

        rendered = '\n'.join(more_cls.call_args[0][0])
        self.assertIn('\x1b[35m<STREAM>', rendered)
        self.assertIn('the target stream (default: stdin & stdout)', rendered)

    def test_show_help_metavar_follows_double_dash_short_form(self):
        arg = DummyArgConstant('--vis', '--visualize', 'visualize', 0, section=0)
        arg.metavar = 'CURVE'
        with patch.object(executionprecessor, 'ALL_ARGS', [arg]):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(self._mk_ctx(), False)

        rendered = '\n'.join(more_cls.call_args[0][0])
        marker = '\x1b[35m<CURVE>\x1b[0m'
        # the metavar follows both the '--' short form and the long form
        self.assertEqual(rendered.count(marker), 2)
        # yellow must be restored for the long form after the magenta metavar
        self.assertIn(f'{marker}\x1b[3m\x1b[33m, --visualize', rendered)

    def test_show_help_truncation_preserves_value_placeholder_color(self):
        # name is long enough that truncation cuts into the magenta '[=SHELL]' marker
        arg = DummyArgConstant('--' + 'x' * 24, '', 'completion', 0, section=0)
        arg.takes_value = 'SHELL'
        with patch.object(executionprecessor, 'ALL_ARGS', [arg]):
            with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
                with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                    _show_help(self._mk_ctx(), False)

        rendered = '\n'.join(more_cls.call_args[0][0])
        self.assertIn('...', rendered)
        # the marker is cut off, but the magenta opening code must survive
        self.assertNotIn('[=SHELL]', rendered)
        self.assertIn('\x1b[35m[=', rendered)

    def test_show_help_always_prints_update_even_if_more_fails(self):
        with patch('cat_win.src.processor.executionprecessor.More') as more_cls:
            more_cls.return_value.step_through.side_effect = RuntimeError('stop')
            with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                with self.assertRaises(RuntimeError):
                    _show_help(self._mk_ctx(), False)
        update.assert_called_once()

    def test_show_version_with_install_time(self):
        with patch('cat_win.src.processor.executionprecessor.get_file_ctime', return_value=0):
            with patch('cat_win.src.processor.executionprecessor.print_update_information') as update:
                with patch('builtins.print') as p:
                    _show_version(repl=True)

        printed = self._printed_text(p)
        self.assertIn('REPL', printed)
        self.assertIn('Install time', printed)
        update.assert_called_once()

    def test_show_version_handles_ctime_oserror(self):
        with patch('cat_win.src.processor.executionprecessor.get_file_ctime', side_effect=OSError):
            with patch('cat_win.src.processor.executionprecessor.print_update_information'):
                with patch('builtins.print') as p:
                    _show_version(repl=False)

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
        show_help.assert_called_once_with(ctx, False)

    def test_run_startup_actions_help_flag(self):
        ctx = self._mk_ctx(u_args=DummyStartupArgs(overrides={ARGS_HELP: True}, ordered_args=[(ARGS_HELP, '--help')]))
        with patch('cat_win.src.processor.executionprecessor._show_help') as show_help:
            with self.assertRaises(SystemExit):
                run_startup_actions(ctx, repl=True, arg_suggestions=[])
        show_help.assert_called_once_with(ctx, True)

    def test_run_startup_actions_version_flag(self):
        ctx = self._mk_ctx(u_args=DummyStartupArgs(overrides={ARGS_VERSION: True}, ordered_args=[(ARGS_VERSION, '--version')]))
        with patch('cat_win.src.processor.executionprecessor._show_version') as show_version:
            with self.assertRaises(SystemExit):
                run_startup_actions(ctx, repl=False, arg_suggestions=[])
        show_version.assert_called_once_with(False)

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

    def test_show_man_raises_system_exit_with_the_exit_code(self):
        ctx = self._mk_ctx()
        with patch('cat_win.src.processor.executionprecessor.show_man', return_value=1) as show_man:
            with self.assertRaises(SystemExit) as ex:
                _show_man(ctx)
        show_man.assert_called_once_with()
        self.assertEqual(ex.exception.code, 1)

    def test_show_completion_passes_the_shell_argument(self):
        ctx = self._mk_ctx(u_args=MagicMock())
        ctx.u_args.find_arg_value.return_value = 'fish'
        with patch('cat_win.src.processor.executionprecessor.show_completion', return_value=2) as show_completion:
            with self.assertRaises(SystemExit) as ex:
                _show_completion(ctx)
        ctx.u_args.find_arg_value.assert_called_once_with(ARGS_COMPLETION)
        show_completion.assert_called_once_with('fish')
        self.assertEqual(ex.exception.code, 2)

    def test_show_sudoshim_passes_the_script_argument(self):
        ctx = self._mk_ctx(u_args=MagicMock())
        ctx.u_args.find_arg_value.return_value = 'cats'
        with patch('cat_win.src.processor.executionprecessor.show_shim', return_value=3) as show_shim:
            with self.assertRaises(SystemExit) as ex:
                _show_sudoshim(ctx)
        ctx.u_args.find_arg_value.assert_called_once_with(ARGS_SUDO_ALLOW)
        show_shim.assert_called_once_with('cats')
        self.assertEqual(ex.exception.code, 3)
