from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import ARGS_B64D, ARGS_CLIP, ARGS_ONELINE
from cat_win.src.const.colorconstants import CKW
from cat_win.src.cats import ReplCommandHandler, repl_main
from cat_win.tests.mocks.argparser import DummyReplArgParser
from cat_win.tests.mocks.args import DummyReplArgs
from cat_win.tests.mocks.ctx import DummyCtx


class TestReplCommandHandler(TestCase):
    def _mk_handler(self, u_args=None, parser=None):
        if u_args is None:
            u_args = DummyReplArgs(active_args=[(1, '-a')])
        if parser is None:
            parser = DummyReplArgParser()

        ctx = DummyCtx(
            u_args=u_args,
            arg_parser=parser,
            color_dic={CKW.REPL_PREFIX: '<RP>', CKW.RESET_ALL: '<RST>'},
        )
        refresh_colors = MagicMock()
        show_unknown_args = MagicMock()
        handler = ReplCommandHandler(ctx, refresh_colors, show_unknown_args)
        return handler, parser, u_args, refresh_colors, show_unknown_args

    def test_exec_non_command_returns_false(self):
        handler, _, _, _, _ = self._mk_handler()
        self.assertFalse(handler.exec('hello'))

    def test_exec_unknown_command(self):
        handler, _, _, _, _ = self._mk_handler()
        with patch('builtins.print') as p:
            self.assertTrue(handler.exec('!idontexist'))
        self.assertEqual(handler.last_cmd, 'idontexist')
        self.assertIn("unknown", str(p.call_args_list[0]))

    def test_command_help_windows_and_non_windows(self):
        handler, _, _, _, _ = self._mk_handler()
        with patch('cat_win.src.cats.on_windows_os', True):
            with patch('builtins.print') as p:
                handler._command_help([])
        self.assertIn('^Z', str(p.call_args_list[0]))

        with patch('cat_win.src.cats.on_windows_os', False):
            with patch('builtins.print') as p:
                handler._command_help([])
        self.assertIn('^D', str(p.call_args_list[0]))

    def test_command_cat_prints_elapsed_time(self):
        handler, _, _, _, _ = self._mk_handler()
        handler._session_start = 100.0
        with patch('cat_win.src.cats.monotonic', return_value=100.0 + 3661.0):
            with patch('builtins.print') as p:
                handler._command_cat([])
        self.assertIn('01:01:01', str(p.call_args_list[0]))

    def test_command_add_and_del(self):
        handler, parser, u_args, refresh_colors, show_unknown_args = self._mk_handler()
        parser.set_args([(10, '--x')])

        with patch('builtins.print'):
            handler._command_add(['--x'])
        self.assertEqual(parser.gen_calls[0], (['', '--x'], False))
        self.assertIn((10, '--x'), u_args.args)
        refresh_colors.assert_called_once()
        show_unknown_args.assert_called_once()

        with patch('builtins.print'):
            handler._command_del(['--x'])
        self.assertEqual(parser.gen_calls[1], (['', '--x'], True))
        self.assertNotIn((10, '--x'), u_args.args)

    def test_command_clear_resets_and_deletes_all_active(self):
        handler, parser, u_args, _, _ = self._mk_handler(u_args=DummyReplArgs(active_args=[(1, '-a'), (2, '-b')]))

        def _gen(argv, delete=False):
            if delete:
                parser.set_args([(1, '-a'), (2, '-b')])
        parser.gen_arguments = _gen

        with patch('builtins.print'):
            handler._command_clear([])
        self.assertTrue(parser.reset_called)
        self.assertEqual(u_args.args, [])

    def test_command_see_prints_queries_and_replacements(self):
        handler, parser, _, _, _ = self._mk_handler()
        parser.file_queries = [('abc', False)]
        parser.file_queries_replacement = ['xyz']
        with patch('builtins.print') as p:
            handler._command_see([])
        rendered = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('Active Args', rendered)
        self.assertIn('Queries', rendered)
        self.assertIn('Replacement', rendered)

    def test_command_exit_sets_flag(self):
        handler, _, _, _, _ = self._mk_handler()
        handler._command_exit([])
        self.assertTrue(handler.exit_repl)


class TestReplMain(TestCase):
    def _mk_ctx(self, u_args=None):
        if u_args is None:
            u_args = DummyReplArgs(overrides={ARGS_ONELINE: False, ARGS_B64D: False, ARGS_CLIP: False})
        return DummyCtx(
            u_args=u_args,
            arg_parser=DummyReplArgParser(),
            color_dic={CKW.REPL_PREFIX: '<RP>', CKW.RESET_ALL: '<RST>'},
        )

    def test_repl_main_command_and_text_flow(self):
        ctx = self._mk_ctx()
        lines = ['!help\n', 'hello\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content') as edit_content:
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())

        from_lines.assert_called_once_with(['hello'])
        edit_content.assert_called_once_with(ctx, -1, 0)
        self.assertEqual(ctx.content, 'BUF')

    def test_repl_main_b64_clip_and_pipe_echo(self):
        ctx = self._mk_ctx(u_args=DummyReplArgs(overrides={ARGS_B64D: True, ARGS_CLIP: True, ARGS_ONELINE: True}))
        lines = ['ZGF0YQ==\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=False):
                    with patch('cat_win.src.cats.decode_base64', return_value='decoded') as b64:
                        with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF'):
                            with patch('cat_win.src.cats.edit_content') as edit_content:
                                with patch('cat_win.src.cats.remove_ansi_codes_from_line', return_value='clean') as strip_ansi:
                                    with patch('cat_win.src.cats.Clipboard.put') as cb_put:
                                        with patch('cat_win.src.cats.Clipboard.clear') as cb_clear:
                                            with patch('cat_win.src.cats.Clipboard.clipboard', 'ansi'):
                                                with patch('builtins.print') as p:
                                                    repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())

        b64.assert_called_once_with('ZGF0YQ==', True, 'utf-8')
        edit_content.assert_called_once_with(ctx, -1, 0)
        strip_ansi.assert_called_once_with('ansi')
        cb_put.assert_called_once_with('clean')
        cb_clear.assert_called_once()
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn("'ZGF0YQ=='", printed)

    def test_repl_main_escaped_leading_bang_is_treated_as_text(self):
        ctx = self._mk_ctx()
        lines = ['\\!help\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content') as edit_content:
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())

        from_lines.assert_called_once_with(['!help'])
        edit_content.assert_called_once_with(ctx, -1, 0)

    def test_repl_main_refreshes_color_caches_on_add_command(self):
        ctx = self._mk_ctx()

        def _gen(argv, delete=False):
            ctx.arg_parser.set_args([(99, '--num')])
        ctx.arg_parser.gen_arguments = _gen

        with patch('cat_win.src.cats._calculate_line_prefix_spacing.cache_clear') as clear_lp:
            with patch('cat_win.src.cats._calculate_line_length_prefix_spacing.cache_clear') as clear_ll:
                with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(['!add --num\n', '!exit\n'])):
                    with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                        with patch('cat_win.src.cats.os.isatty', return_value=True):
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())

        clear_lp.assert_called_once()
        clear_ll.assert_called_once()

    def test_repl_main_output_unchanged(self):
        """Adapted from test_cat_repl_output_unchanged: basic text input should pass through unchanged."""
        ctx = self._mk_ctx()
        lines = ['abc\n', 'xyz\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        # Each line is processed individually, so check both were processed
        from_lines.assert_any_call(['abc'])
        from_lines.assert_any_call(['xyz'])

    def test_repl_main_unknown_param(self):
        """Adapted from test_cat_repl_unknown_param: unknown command should be reported."""
        ctx = self._mk_ctx()
        wrong_cmd = '!xyz'
        lines = [wrong_cmd + '\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('builtins.print') as p:
                        repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn(wrong_cmd, printed)

    def test_repl_main_help_param(self):
        """Adapted from test_cat_repl_help_param: !help should display help info."""
        ctx = self._mk_ctx()
        lines = ['!help\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('builtins.print') as p:
                        repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('!add', printed)
        self.assertIn('!del', printed)
        self.assertIn('!see', printed)

    def test_repl_main_add_param(self):
        """Adapted from test_cat_repl_add_param: !add command should apply parameters."""
        ctx = self._mk_ctx()
        ctx.arg_parser.set_args([(1, '-l'), (2, '-n')])
        lines = ['abc\n', '!add -ln\n', 'abc\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF'):
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print') as p:
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('successfully added', printed)

    def test_repl_main_delete_param(self):
        """Adapted from test_cat_repl_delete_param: !del command should remove parameters."""
        ctx = self._mk_ctx(u_args=DummyReplArgs(overrides={ARGS_ONELINE: False, ARGS_B64D: False, ARGS_CLIP: False},
                                               active_args=[(1, '-l'), (2, '-n')]))
        ctx.arg_parser.set_args([(1, '-l')])
        lines = ['abc\n', '!del -l\n', 'abc\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF'):
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print') as p:
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('successfully removed', printed)

    def test_repl_main_see_param(self):
        """Adapted from test_cat_repl_see_param: !see command should display active args and queries."""
        ctx = self._mk_ctx()
        ctx.arg_parser.file_queries = [('test', False)]
        ctx.arg_parser.set_args([(1, '-l'), (2, '-n')])
        lines = ['!see\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('builtins.print') as p:
                        repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('Active Args', printed)
        self.assertIn('Queries', printed)

    def test_repl_main_clear_param(self):
        """Adapted from test_cat_repl_clear_param: !clear command should remove all active parameters."""
        ctx = self._mk_ctx(u_args=DummyReplArgs(overrides={ARGS_ONELINE: False, ARGS_B64D: False, ARGS_CLIP: False},
                                               active_args=[(1, '-l'), (2, '-n')]))

        def _gen(argv, delete=False):
            if delete:
                ctx.arg_parser.set_args([(1, '-l'), (2, '-n')])
        ctx.arg_parser.gen_arguments = _gen

        lines = ['!clear\n', '!see\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('builtins.print') as p:
                        repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        printed = '\n'.join(str(c) for c in p.call_args_list)
        self.assertIn('successfully removed', printed)
        self.assertIn('Active Args: []', printed)

    def test_repl_main_exit(self):
        """Adapted from test_cat_repl_exit: !exit command should stop processing input."""
        ctx = self._mk_ctx()
        lines = ['abc\n', '!exit\n', 'abc\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        # Only first 'abc' should be processed, not the second one after !exit
        from_lines.assert_called_once_with(['abc'])

    def test_repl_main_cmd_escape(self):
        """Adapted from test_cat_repl_cmd_escape: escaped ! should be treated as text, not command."""
        ctx = self._mk_ctx()
        lines = ['\\!exit\n', 'test\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        # Escaped !exit should be treated as text
        from_lines.assert_any_call(['!exit'])
        from_lines.assert_any_call(['test'])

    def test_repl_main_cmd_escape_backslash(self):
        """Adapted from test_cat_repl_cmd_escape: multiple backslashes should be handled correctly."""
        ctx = self._mk_ctx()
        lines = ['\\' * 5 + 'test\n', '!exit\n']
        with patch('cat_win.src.cats.IoHelper.get_stdin_content', return_value=iter(lines)):
            with patch('cat_win.src.cats.sys.stdin.fileno', return_value=0):
                with patch('cat_win.src.cats.os.isatty', return_value=True):
                    with patch('cat_win.src.cats.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                        with patch('cat_win.src.cats.edit_content'):
                            with patch('builtins.print'):
                                repl_main(ctx, init_colors=MagicMock(), show_unknown_args=MagicMock())
        from_lines.assert_called_once_with(['\\' * 4 + 'test'])
