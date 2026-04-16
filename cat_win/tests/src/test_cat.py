from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ALL_ARGS,
    ARGS_B64D,
    ARGS_DEBUG,
    ARGS_DEBUG_LOG,
    ARGS_LLENGTH,
    ARGS_NOCOL,
    ARGS_NUMBER,
    ARGS_SSUM,
    ARGS_STDIN,
    ARGS_SUM,
    ARGS_WATCH,
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.defaultconstants import DKW
from cat_win.src import cat as cat_module
from cat_win.tests.mocks.argparser import DummyArgParser
from cat_win.tests.mocks.args import DummyStartupArgs
from cat_win.tests.mocks.ctx import DummyCtx
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.ufiles import DummyUFiles


class _ArgDef:
    def __init__(self, arg_id, short_form, long_form, show_arg_on_repl=True):
        self.arg_id = arg_id
        self.short_form = short_form
        self.long_form = long_form
        self.show_arg_on_repl = show_arg_on_repl


class TestCat(TestCase):
    def _mk_handle_args(self, overrides=None):
        args = {
            ARGS_B64D: False,
            ARGS_SUM: False,
            ARGS_SSUM: False,
            ARGS_NUMBER: False,
            ARGS_LLENGTH: False,
            ARGS_DEBUG: False,
            ARGS_DEBUG_LOG: False,
            ARGS_NOCOL: False,
            ARGS_STDIN: False,
            ARGS_WATCH: False,
        }
        if overrides:
            args.update(overrides)
        return args

    def _mk_base_ctx(self, u_args=None):
        if u_args is None:
            u_args = DummyStartupArgs()
        color_map = {
            CKW.RESET_ALL: '<RST>',
            CKW.NUMBER: '<NUM>',
            CKW.LINE_LENGTH: '<LEN>',
            CKW.FILE_PREFIX: '<FP>',
            CKW.REPL_PREFIX: '<RP>',
        }
        ctx = DummyCtx(
            u_args=u_args,
            color_dic=dict(color_map),
            const_dic={
                DKW.STRIP_COLOR_ON_PIPE: False,
                DKW.LARGE_FILE_SIZE: 100,
                DKW.EDITOR_INDENTATION: '  ',
                DKW.EDITOR_AUTO_INDENT: True,
                DKW.UNICODE_ESCAPED_EDITOR_SEARCH: True,
                DKW.UNICODE_ESCAPED_EDITOR_REPLACE: True,
                DKW.UNICODE_ESCAPED_EDITOR_INSERT: True,
                DKW.HEX_EDITOR_COLUMNS: 16,
                DKW.MORE_STEP_LENGTH: 20,
                DKW.SUMMARY_UNIQUE_ELEMENTS: False,
                DKW.IGNORE_UNKNOWN_BYTES: False,
            },
            arg_parser=DummyArgParser(),
        )
        ctx.default_color_dic = dict(color_map)
        ctx.init = MagicMock()
        ctx.known_files = []
        ctx.unknown_files = []
        ctx.known_dirs = []
        ctx.valid_urls = []
        ctx.echo_args = ''
        ctx.u_files = DummyUFiles([])
        return ctx

    def test_exception_handler_debug_mode_calls_debug_hook(self):
        ctx = self._mk_base_ctx(u_args=DummyStartupArgs(overrides={ARGS_DEBUG: True}, ordered_args=[(ARGS_DEBUG, '-d')]))
        debug_hook = MagicMock()
        logger_stub = LoggerStub()
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'logger', logger_stub):
                cat_module.exception_handler(ValueError, ValueError('x'), None, debug_hook=debug_hook)
        debug_hook.assert_called_once()

    def test_exception_handler_non_debug_logs_and_exits_zero(self):
        ctx = self._mk_base_ctx()
        logger_stub = LoggerStub()
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'logger', logger_stub):
                with patch('cat_win.src.cat.sys.exit', side_effect=SystemExit(0)):
                    with self.assertRaises(SystemExit):
                        cat_module.exception_handler(ValueError, ValueError('oops'), None)
        out = logger_stub.output()
        self.assertIn('ValueError', out)
        self.assertIn('issues', out)

    def test_exception_handler_broken_pipe_redirects_stdout(self):
        ctx = self._mk_base_ctx()
        err = OSError()
        err.errno = 22
        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.os.open', return_value=11) as os_open:
                with patch('cat_win.src.cat.os.dup2') as dup2:
                    with patch('cat_win.src.cat.sys.stdout.fileno', return_value=1):
                        with patch('cat_win.src.cat.sys.exit', side_effect=SystemExit(1)) as sys_exit:
                            with self.assertRaises(SystemExit):
                                cat_module.exception_handler(OSError, err, None)
        os_open.assert_called_once()
        dup2.assert_called_once_with(11, 1)
        sys_exit.assert_called_once_with(1)

    def test_exception_handler_broken_pipe_during_logging_redirects_stderr(self):
        ctx = self._mk_base_ctx()
        logger_mock = MagicMock()
        logger_mock.side_effect = BrokenPipeError()
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'logger', logger_mock):
                with patch('cat_win.src.cat.os.open', return_value=13) as os_open:
                    with patch('cat_win.src.cat.os.dup2') as dup2:
                        with patch('cat_win.src.cat.sys.stderr.fileno', return_value=2):
                            with patch('cat_win.src.cat.sys.exit', side_effect=SystemExit(1)) as sys_exit:
                                with self.assertRaises(SystemExit):
                                    cat_module.exception_handler(ValueError, ValueError('x'), None)
        os_open.assert_called_once()
        dup2.assert_called_once_with(13, 2)
        sys_exit.assert_called_once_with(1)

    def test_exception_handler_generic_failure_calls_debug_hook(self):
        ctx = self._mk_base_ctx()
        debug_hook = MagicMock()
        logger_mock = MagicMock()
        logger_mock.side_effect = RuntimeError('logger failed')
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'logger', logger_mock):
                cat_module.exception_handler(ValueError, ValueError('x'), None, debug_hook=debug_hook)
        debug_hook.assert_called_once()

    def test_show_unknown_args_suggestions_logs_warnings(self):
        ctx = self._mk_base_ctx()
        ctx.arg_parser._unknown_args = ['--x']
        logger_stub = LoggerStub()
        fake_args = [_ArgDef(1, '-a', '--alpha', True), _ArgDef(2, '-b', '--beta', False)]
        suggestions = [('--x', [('--alpha', 1)])]
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'ALL_ARGS', fake_args):
                with patch.object(cat_module, 'calculate_suggestions', return_value=suggestions):
                    with patch.object(cat_module, 'logger', logger_stub):
                        out = cat_module.show_unknown_args_suggestions(repl=True)
        self.assertEqual(out, suggestions)
        self.assertIn('Unknown argument', logger_stub.output())

    def test_show_unknown_args_suggestions_non_repl_uses_all_args(self):
        ctx = self._mk_base_ctx()
        ctx.arg_parser._unknown_args = ['--x']
        fake_args = [_ArgDef(1, '-a', '--alpha', True), _ArgDef(2, '-b', '--beta', False)]
        with patch.object(cat_module, '_ctx', ctx):
            with patch.object(cat_module, 'ALL_ARGS', fake_args):
                with patch.object(cat_module, 'calculate_suggestions', return_value=[]) as calc:
                    cat_module.show_unknown_args_suggestions(repl=False)
        calc.assert_called_once_with(['--x'], [('-a', '--alpha'), ('-b', '--beta')])

    def test_init_colors_nocol_clears_colors_and_logger(self):
        args = DummyStartupArgs(overrides={ARGS_NOCOL: True, ARGS_DEBUG_LOG: False}, ordered_args=[(ARGS_NOCOL, '--nocol')])
        ctx = self._mk_base_ctx(u_args=args)
        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.CVis.remove_colors') as rm_colors:
                with patch.object(cat_module, 'logger') as logger_m:
                    cat_module.init_colors()
        self.assertTrue(all(v == '' for v in ctx.color_dic.values()))
        rm_colors.assert_called_once()
        logger_m.clear_colors.assert_called_once()

    def test_init_colors_uses_default_and_sets_logger_colors(self):
        args = self._mk_handle_args({ARGS_NOCOL: False, ARGS_DEBUG_LOG: False})
        ctx = self._mk_base_ctx(u_args=args)
        ctx.color_dic = {CKW.NUMBER: 'x', CKW.RESET_ALL: 'y'}
        ctx.default_color_dic = {CKW.NUMBER: '<NUM>', CKW.RESET_ALL: '<RST>'}
        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.os.isatty', return_value=True):
                with patch('cat_win.src.cat.sys.stdout.fileno', return_value=1):
                    with patch('cat_win.src.cat.sys.stderr.fileno', return_value=2):
                        with patch.object(cat_module, 'logger') as logger_m:
                            cat_module.init_colors()
        self.assertEqual(ctx.color_dic, ctx.default_color_dic)
        logger_m.set_colors.assert_called_once_with(ctx.default_color_dic)

    def test_init_calls_all_subsystem_setups(self):
        args = DummyStartupArgs(overrides={ARGS_DEBUG: True, ARGS_DEBUG_LOG: True, ARGS_STDIN: False, ARGS_WATCH: False}, ordered_args=[(ARGS_DEBUG, '-d')])
        ctx = self._mk_base_ctx(u_args=args)
        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.preprocess_context') as pre:
                with patch('cat_win.src.cat.init_colors') as init_colors:
                    with patch('cat_win.src.cat.show_unknown_args_suggestions', return_value=['s']) as sugg:
                        with patch('cat_win.src.cat.run_startup_actions') as startup:
                            with patch('cat_win.src.cat.DiffViewer.set_flags') as diff_flags:
                                with patch('cat_win.src.cat.Editor.set_indentation') as ed_indent:
                                    with patch('cat_win.src.cat.Editor.set_flags') as ed_flags:
                                        with patch('cat_win.src.cat.HexEditor.set_flags') as hex_flags:
                                            with patch('cat_win.src.cat.More.set_flags') as more_flags:
                                                with patch('cat_win.src.cat.More.set_colors') as more_colors:
                                                    with patch('cat_win.src.cat.Visualizer.set_flags') as vis_flags:
                                                        with patch('cat_win.src.cat.Summary.set_flags') as sum_flags:
                                                            with patch('cat_win.src.cat.Summary.set_colors') as sum_colors:
                                                                with patch('cat_win.src.cat.PBar.set_colors') as pbar_colors:
                                                                    with patch('cat_win.src.cat.Converter.set_flags') as conv_flags:
                                                                        with patch('cat_win.src.cat.Converter.set_colors') as conv_colors:
                                                                            with patch.object(cat_module, 'logger') as logger_m:
                                                                                cat_module.init(repl=False)
        pre.assert_called_once_with(ctx)
        logger_m.set_log_to_file.assert_called_once_with(True)
        logger_m.set_level.assert_called_once_with(logger_m.DEBUG)
        init_colors.assert_called_once()
        sugg.assert_called_once_with(False)
        startup.assert_called_once_with(ctx, False, ['s'])
        diff_flags.assert_called_once()
        ed_indent.assert_called_once()
        ed_flags.assert_called_once()
        hex_flags.assert_called_once()
        more_flags.assert_called_once()
        more_colors.assert_called_once_with(ctx.color_dic)
        # Signatures.init() uses lazy loading and is only called when signatures are needed, not during init
        vis_flags.assert_called_once()
        sum_flags.assert_called_once()
        sum_colors.assert_called_once_with(ctx.color_dic)
        pbar_colors.assert_called_once_with(ctx.color_dic)
        conv_flags.assert_called_once()
        conv_colors.assert_called_once_with(ctx.color_dic)

    def test_handle_args_full_flow(self):
        args = self._mk_handle_args({ARGS_B64D: True, ARGS_SUM: True, ARGS_SSUM: False, ARGS_NUMBER: False, ARGS_LLENGTH: True})
        ctx = self._mk_base_ctx(u_args=args)
        f1 = MagicMock()
        f1.path = 'a.txt'
        f1.file_size = 0
        f1.set_file_size.side_effect = lambda size: setattr(f1, 'file_size', size)
        f2 = MagicMock()
        f2.path = 'b.txt'
        f2.file_size = 0
        f2.set_file_size.side_effect = lambda size: setattr(f2, 'file_size', size)
        ctx.known_files = [f1]
        ctx.unknown_files = [f2]
        ctx.u_files = DummyUFiles([])
        tmp_helper = MagicMock()
        logger_stub = LoggerStub()

        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.init') as init_m:
                with patch('cat_win.src.cat.materialize_context_sources') as materialize:
                    with patch('cat_win.src.cat.get_file_size', side_effect=[60, 60]):
                        with patch('cat_win.src.cat._fp_decode_files_base64') as dec_b64:
                            with patch('cat_win.src.cat.run_pre_content_actions', return_value=False):
                                with patch('cat_win.src.cat._fp_edit_files') as edit_files:
                                    with patch('cat_win.src.cat.run_post_content_actions') as post:
                                        with patch.object(cat_module, 'logger', logger_stub):
                                            cat_module.handle_args(tmp_helper)

        init_m.assert_called_once_with(repl=False)
        materialize.assert_called_once_with(ctx, tmp_helper)
        self.assertEqual(len(ctx.u_files.set_files_calls), 1)
        self.assertEqual(ctx.u_files.generate_values_calls, [(True, True)])
        dec_b64.assert_called_once_with(ctx, tmp_helper)
        edit_files.assert_called_once_with(ctx)
        post.assert_called_once_with(ctx)
        self.assertIn('large amount of data', logger_stub.output())

    def test_handle_args_returns_early_when_no_files_or_pre_action(self):
        ctx = self._mk_base_ctx(u_args=self._mk_handle_args())
        tmp_helper = MagicMock()

        with patch.object(cat_module, '_ctx', ctx):
            with patch('cat_win.src.cat.init'):
                with patch('cat_win.src.cat.materialize_context_sources'):
                    with patch('cat_win.src.cat.run_pre_content_actions', return_value=True):
                        with patch('cat_win.src.cat._fp_edit_files') as edit_files:
                            cat_module.handle_args(tmp_helper)
        edit_files.assert_not_called()

    def test_managed_tmp_file_helper_finalizes(self):
        with patch('cat_win.src.cat.TmpFileHelper') as helper_cls:
            helper = helper_cls.return_value
            with patch('cat_win.src.cat.finalize_context') as finalize:
                with cat_module.managed_tmp_file_helper() as yielded:
                    self.assertIs(yielded, helper)
            finalize.assert_called_once_with(cat_module._ctx, helper)

    def test_main_calls_handle_args_inside_context(self):
        helper = MagicMock()

        class _CM:
            def __enter__(self):
                return helper

            def __exit__(self, *_):
                return False

        with patch('cat_win.src.cat.managed_tmp_file_helper', return_value=_CM()):
            with patch('cat_win.src.cat.handle_args') as handle_args:
                cat_module.main()
        handle_args.assert_called_once_with(helper)

    def test_repl_main_calls_repl_module(self):
        class _CM:
            def __enter__(self):
                return MagicMock()

            def __exit__(self, *_):
                return False

        with patch('cat_win.src.cat.managed_tmp_file_helper', return_value=_CM()):
            with patch('cat_win.src.cat.init') as init_m:
                with patch('cat_win.src.cat.repl_module.repl_main') as repl_main_m:
                    cat_module.repl_main()
        init_m.assert_called_once_with(repl=True)
        repl_main_m.assert_called_once_with(cat_module._ctx, cat_module.init_colors, cat_module.show_unknown_args_suggestions)
