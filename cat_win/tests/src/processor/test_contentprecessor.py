from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_CCHARCOUNT,
    ARGS_CHECKSUM,
    ARGS_DATA,
    ARGS_DDIRECTORIES,
    ARGS_DIFF,
    ARGS_DOTFILES,
    ARGS_ECHO,
    ARGS_EDITOR,
    ARGS_FFILES,
    ARGS_HEX_EDITOR,
    ARGS_LESS,
    ARGS_ONELINE,
    ARGS_PLAIN_ONLY,
    ARGS_RAW,
    ARGS_RECONFIGURE,
    ARGS_RECONFIGURE_ERR,
    ARGS_RECONFIGURE_IN,
    ARGS_RECONFIGURE_OUT,
    ARGS_SSUM,
    ARGS_STDIN,
    ARGS_URI,
    ARGS_VISUALIZE_B,
    ARGS_WWORDCOUNT,
)
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.processor import contentprecessor as pre
from cat_win.tests.mocks.args import DummyStartupArgs


@contextmanager
def _noop_cm(*_):
    yield


class TestContentPrecessor(TestCase):
    def _ctx(self):
        ctx = MagicMock()
        ctx.echo_args = 'echo-body'
        ctx.valid_urls = ['https://example.test/a']
        ctx.known_files = []
        ctx.unknown_files = ['u1.txt']
        ctx.known_dirs = ['d1']
        ctx.const_dic = {DKW.IGNORE_UNKNOWN_BYTES: False}
        ctx.color_dic = {'x': 'y'}
        ctx.arg_parser = MagicMock()
        ctx.arg_parser.file_encoding = 'utf-8'
        ctx.arg_parser.file_truncate = (None, None, None)
        ctx.arg_parser.get_arguments.return_value = ([('a', True)], ['--bad'], 'echo')
        ctx.arg_parser.get_files.return_value = ['k.txt']
        ctx.arg_parser.filter_urls.return_value = (['u2.txt'], ['https://example'])
        ctx.arg_parser.get_dirs.return_value = ['dir']
        ctx.config = MagicMock()
        ctx.config.get_args.return_value = ['catw']
        ctx.u_files = MagicMock()
        ctx.u_args = DummyStartupArgs(
            {
                ARGS_RAW: False,
                ARGS_ONELINE: False,
                ARGS_STDIN: False,
                ARGS_EDITOR: False,
                ARGS_HEX_EDITOR: False,
                ARGS_PLAIN_ONLY: False,
                ARGS_DIFF: False,
                ARGS_FFILES: False,
                ARGS_DDIRECTORIES: False,
                ARGS_DATA: False,
                ARGS_CHECKSUM: False,
                ARGS_SSUM: False,
                ARGS_WWORDCOUNT: False,
                ARGS_CCHARCOUNT: False,
                ARGS_RECONFIGURE: False,
                ARGS_RECONFIGURE_IN: False,
                ARGS_RECONFIGURE_OUT: False,
                ARGS_RECONFIGURE_ERR: False,
                ARGS_URI: False,
                ARGS_ECHO: False,
                ARGS_DOTFILES: False,
            }
        )
        return ctx

    def test_preprocess_context_populates_ctx(self):
        ctx = self._ctx()
        with patch('cat_win.src.processor.contentprecessor._reconfigure_streams') as rc:
            pre.preprocess_context(ctx)
        self.assertEqual(ctx.args, [('a', True)])
        self.assertEqual(ctx.unknown_args, ['--bad'])
        self.assertEqual(ctx.echo_args, 'echo')
        self.assertEqual(ctx.known_files, ['k.txt'])
        self.assertEqual(ctx.unknown_files, ['u2.txt'])
        self.assertEqual(ctx.valid_urls, ['https://example'])
        self.assertEqual(ctx.known_dirs, ['dir'])
        rc.assert_called_once_with(ctx)

    def test_reconfigure_streams_calls_selected_handlers(self):
        ctx = self._ctx()
        ctx.u_args[ARGS_RECONFIGURE_IN] = True
        ctx.u_args[ARGS_RECONFIGURE_ERR] = True
        with patch('cat_win.src.processor.contentprecessor._reconfigure_stream') as rcs:
            pre._reconfigure_streams(ctx)
        self.assertEqual(rcs.call_count, 2)

    def test_reconfigure_stream_calls_reconfigure_only_when_supported(self):
        stream = MagicMock()
        pre._reconfigure_stream(stream, 'utf-8')
        stream.reconfigure.assert_called_once_with(encoding='utf-8')

        stream_no_method = object()
        pre._reconfigure_stream(stream_no_method, 'utf-8')
        pre._reconfigure_stream(None, 'utf-8')

    def test_materialize_context_sources_invokes_enabled_handlers(self):
        ctx = self._ctx()
        tmp = MagicMock()
        ctx.u_args[ARGS_ECHO] = True
        ctx.u_args[ARGS_URI] = True
        ctx.u_args[ARGS_STDIN] = True
        with patch('cat_win.src.processor.contentprecessor._materialize_echo') as me:
            with patch('cat_win.src.processor.contentprecessor._materialize_urls') as mu:
                with patch('cat_win.src.processor.contentprecessor._materialize_stdin') as ms:
                    with patch('cat_win.src.processor.contentprecessor._resolve_unknown_files') as ru:
                        pre.materialize_context_sources(ctx, tmp)
        me.assert_called_once_with(ctx, tmp)
        mu.assert_called_once_with(ctx, tmp)
        ms.assert_called_once_with(ctx, tmp)
        ru.assert_called_once_with(ctx)

    def test_materialize_echo_writes_temp_file(self):
        ctx = self._ctx()
        tmp = MagicMock()
        tmp.generate_temp_file_name.return_value = 'tmp1.txt'
        with patch('cat_win.src.processor.contentprecessor.IoHelper.write_file', return_value='tf') as wf:
            pre._materialize_echo(ctx, tmp)
        wf.assert_called_once_with('tmp1.txt', 'echo-body', 'utf-8')
        self.assertEqual(ctx.known_files, ['tf'])
        ctx.u_files.set_temp_file_echo.assert_called_once_with('tf')

    def test_materialize_urls_writes_all_urls(self):
        ctx = self._ctx()
        tmp = MagicMock()
        tmp.generate_temp_file_name.side_effect = ['t1', 't2']
        ctx.valid_urls = ['u1', 'u2']
        with patch('cat_win.src.processor.contentprecessor.read_url', side_effect=['c1', 'c2']):
            with patch('cat_win.src.processor.contentprecessor.IoHelper.write_file', side_effect=['f1', 'f2']):
                pre._materialize_urls(ctx, tmp)
        self.assertIn('f1', ctx.known_files)
        self.assertIn('f2', ctx.known_files)
        ctx.u_files.set_temp_files_url.assert_called_once_with({'f1': 'u1', 'f2': 'u2'})

    def test_materialize_stdin_writes_temp_and_unknown_files(self):
        ctx = self._ctx()
        tmp = MagicMock()
        tmp.generate_temp_file_name.return_value = 'std.tmp'
        with patch('cat_win.src.processor.contentprecessor.IoHelper.get_stdin_content', return_value=['A', 'B']):
            with patch('cat_win.src.processor.contentprecessor.IoHelper.write_file', return_value='sfile'):
                with patch('cat_win.src.processor.contentprecessor.IoHelper.write_files', return_value=['u-out']) as wr:
                    pre._materialize_stdin(ctx, tmp)
        self.assertIn('sfile', ctx.known_files)
        self.assertEqual(ctx.unknown_files, ['u-out'])
        wr.assert_called_once_with(['u1.txt'], 'AB', 'utf-8')
        ctx.u_files.set_temp_file_stdin.assert_called_once_with('sfile')

    def test_resolve_unknown_files_respects_skip_conditions(self):
        ctx = self._ctx()
        ctx.u_args[ARGS_STDIN] = True
        with patch('cat_win.src.processor.contentprecessor.IoHelper.read_write_files_from_stdin') as rw:
            pre._resolve_unknown_files(ctx)
        rw.assert_not_called()

    def test_resolve_unknown_files_returns_when_editor_flags_present(self):
        ctx = self._ctx()
        ctx.u_args.find_first = MagicMock(side_effect=[(ARGS_EDITOR, True), None])
        with patch('cat_win.src.processor.contentprecessor.IoHelper.read_write_files_from_stdin') as rw:
            pre._resolve_unknown_files(ctx)
        rw.assert_not_called()

    def test_resolve_unknown_files_reads_when_allowed(self):
        ctx = self._ctx()
        ctx.u_args[ARGS_STDIN] = False
        ctx.u_args[ARGS_EDITOR] = False
        ctx.u_args[ARGS_HEX_EDITOR] = False
        with patch('cat_win.src.processor.contentprecessor.IoHelper.read_write_files_from_stdin', return_value=['rw']) as rw:
            pre._resolve_unknown_files(ctx)
        rw.assert_called_once_with(['u1.txt'], 'utf-8', False)
        self.assertEqual(ctx.unknown_files, ['rw'])

    def test_open_editors_editor_and_hex_paths(self):
        ctx = self._ctx()
        ctx.unknown_files = ['u1']
        ctx.known_files = ['k1']
        ctx.u_args[ARGS_EDITOR] = True
        with patch('cat_win.src.processor.contentprecessor.Editor.open') as eo:
            with patch('cat_win.src.processor.contentprecessor.IoHelper.dup_stdstreams', _noop_cm):
                handled = pre._open_editors(ctx)
        self.assertTrue(handled)
        self.assertEqual(eo.call_count, 2)

        ctx2 = self._ctx()
        ctx2.unknown_files = ['u1']
        ctx2.known_files = ['k1']
        ctx2.u_args.find_first = MagicMock(side_effect=[None, (ARGS_HEX_EDITOR, True)])
        with patch('cat_win.src.processor.contentprecessor.Editor.open'):
            with patch('cat_win.src.processor.contentprecessor.HexEditor.open') as ho:
                with patch('cat_win.src.processor.contentprecessor.IoHelper.dup_stdstreams', _noop_cm):
                    handled = pre._open_editors(ctx2)
        self.assertTrue(handled)
        self.assertEqual(ho.call_count, 2)

    def test_open_diff_view_and_summary_helpers(self):
        ctx = self._ctx()
        self.assertFalse(pre._open_diff_view(ctx))
        ctx.known_files = ['k1']
        with patch('cat_win.src.processor.contentprecessor.IoHelper.dup_stdstreams', _noop_cm):
            with patch('cat_win.src.processor.contentprecessor.DiffViewer.open') as dv:
                self.assertTrue(pre._open_diff_view(ctx))
        dv.assert_called_once()

        ctx.u_args[ARGS_FFILES] = True
        ctx.u_args[ARGS_DDIRECTORIES] = True
        with patch('cat_win.src.processor.contentprecessor.Summary.show_files') as sf:
            with patch('cat_win.src.processor.contentprecessor.Summary.show_dirs') as sd:
                self.assertTrue(pre._show_files_only(ctx))
        sf.assert_called_once()
        sd.assert_called_once_with(['d1'])

    def test_open_editors_returns_false_when_no_editor_args(self):
        ctx = self._ctx()
        ctx.u_args.find_first = MagicMock(return_value=None)
        self.assertFalse(pre._open_editors(ctx))

    def test_meta_checksum_visualize_less_sum_word_char(self):
        ctx = self._ctx()
        ctx.u_files = [MagicMock(path='p1')]
        ctx.u_args[ARGS_DATA] = True
        ctx.u_args[ARGS_CHECKSUM] = True
        with patch('cat_win.src.processor.contentprecessor.print_meta') as pm:
            with patch('cat_win.src.processor.contentprecessor.print_checksum') as pc:
                self.assertTrue(pre._show_meta_and_checksum(ctx))
        pm.assert_called_once_with('p1', ctx.color_dic)
        pc.assert_called_once_with('p1', ctx.color_dic)

        run_vis = pre._visualize_files('ByteView')
        with patch('cat_win.src.processor.contentprecessor.Visualizer') as vis:
            self.assertTrue(run_vis(ctx))
        vis.return_value.visualize_files.assert_called_once()

        with patch('cat_win.src.processor.contentprecessor.More') as more_cls:
            stepper = more_cls.return_value
            stepper.step_through.side_effect = SystemExit()
            self.assertTrue(pre._page_files_lazily(ctx))

        ctx.u_files = MagicMock()
        ctx.u_files.files = ['f']
        ctx.u_files.all_files_lines = 12
        ctx.u_files.all_line_number_place_holder = 3
        with patch('cat_win.src.processor.contentprecessor.Summary.show_sum') as ss:
            self.assertTrue(pre._show_sum_only(ctx))
        ss.assert_called_once()

        with patch('cat_win.src.processor.contentprecessor.Summary.show_wordcount') as sw:
            self.assertTrue(pre._show_wordcount_only(ctx))
        sw.assert_called_once_with(['f'], 'utf-8')

        with patch('cat_win.src.processor.contentprecessor.Summary.show_charcount') as sc:
            self.assertTrue(pre._show_charcount_only(ctx))
        sc.assert_called_once_with(['f'], 'utf-8')

    def test_run_pre_content_actions_deduplicates_handlers(self):
        ctx = self._ctx()
        ctx.u_args = DummyStartupArgs({}, ordered_args=[(1, True), (2, True), (3, True)])
        h = MagicMock(return_value=True)
        with patch.object(pre, 'PRE_CONTENT_ACTIONS', {1: h, 2: h, 3: MagicMock(return_value=False)}):
            handled = pre.run_pre_content_actions(ctx)
        self.assertTrue(handled)
        h.assert_called_once_with(ctx)
