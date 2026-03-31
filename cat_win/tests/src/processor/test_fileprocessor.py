from unittest import TestCase
from unittest.mock import call, patch

from cat_win.src.const.argconstants import ARGS_BINVIEW, ARGS_EOL, ARGS_HEXVIEW, ARGS_PLAIN_ONLY, ARGS_RAW, ARGS_REVERSE, ARGS_WATCH
from cat_win.src.const.defaultconstants import DKW

from cat_win.src.processor.fileprocessor import (
    decode_files_base64,
    edit_file,
    edit_files,
)
from cat_win.tests.mocks.argparser import DummyArgParser
from cat_win.tests.mocks.args import DummyArgs
from cat_win.tests.mocks.ctx import DummyCtx, DummyFile
from cat_win.tests.mocks.tmpfile import DummyTmpFileHelper

class TestFileProcessor(TestCase):
    def _mk_ctx(self, files, args=None, const_dic=None):
        if const_dic is None:
            const_dic = {
                DKW.LARGE_FILE_SIZE: 1024,
                DKW.STRIP_COLOR_ON_PIPE: False,
                DKW.IGNORE_UNKNOWN_BYTES: False,
            }
        return DummyCtx(
            u_files=files,
            u_args=args if args is not None else DummyArgs(),
            const_dic=const_dic,
            arg_parser=DummyArgParser(),
            content=None,
        )

    def test_edit_file_raw_mode_calls_edit_raw_content(self):
        ctx = self._mk_ctx([DummyFile('a.txt', path='a.txt')], args=DummyArgs({ARGS_RAW: True}))
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value=b'raw') as read_file:
            with patch('cat_win.src.processor.fileprocessor.edit_raw_content') as edit_raw:
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        read_file.assert_called_once_with('a.txt', True)
        edit_raw.assert_called_once_with(b'raw', 0, ctx)
        edit_content.assert_not_called()

    def test_edit_file_regular_flow_sets_content_and_calls_edit_content(self):
        ctx = self._mk_ctx([DummyFile('a.txt', path='a.txt')])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value='A\nB') as read_file:
            with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=True):
                with patch('cat_win.src.processor.fileprocessor.ContentBuffer.from_lines', return_value='BUF') as from_lines:
                    with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                        edit_file(0, ctx)

        read_file.assert_called_once_with('a.txt', file_encoding='utf-8', file_length=-1)
        from_lines.assert_called_once_with(['A', 'B'])
        self.assertEqual(ctx.content, 'BUF')
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_edit_file_strips_ansi_on_pipe_when_configured(self):
        ctx = self._mk_ctx([DummyFile('a.txt', path='a.txt')], const_dic={DKW.LARGE_FILE_SIZE: 1024, DKW.STRIP_COLOR_ON_PIPE: True, DKW.IGNORE_UNKNOWN_BYTES: False})
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value='ANSI'):
            with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.remove_ansi_codes_from_line', return_value='STRIPPED') as strip_ansi:
                    with patch('cat_win.src.processor.fileprocessor.ContentBuffer.from_lines', return_value='BUF'):
                        with patch('cat_win.src.processor.fileprocessor.edit_content'):
                            edit_file(0, ctx)
        strip_ansi.assert_called_once_with('ANSI')

    def test_edit_file_permission_error_logs_and_returns(self):
        ctx = self._mk_ctx([DummyFile('X', path='x.txt')])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=PermissionError):
            with patch('cat_win.src.processor.fileprocessor.logger') as log:
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        self.assertIn('Permission denied', log.call_args[0][0])
        edit_content.assert_not_called()

    def test_edit_file_blocking_or_notfound_logs_and_returns(self):
        ctx = self._mk_ctx([DummyFile('X', path='x.txt')])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=FileNotFoundError):
            with patch('cat_win.src.processor.fileprocessor.logger') as log:
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        self.assertIn('Resource blocked/unavailable', log.call_args[0][0])
        edit_content.assert_not_called()

    def test_edit_file_plain_only_stops_after_binary_detection(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], args=DummyArgs({ARGS_PLAIN_ONLY: True}))
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=UnicodeError):
            with patch('cat_win.src.processor.fileprocessor.display_archive') as disp_archive:
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        self.assertEqual(ctx.u_files[0].plaintext_calls, [False])
        disp_archive.assert_not_called()
        edit_content.assert_not_called()

    def test_edit_file_archive_display_success_stops_processing(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=UnicodeError):
            with patch('cat_win.src.processor.fileprocessor.display_archive', return_value=True) as disp_archive:
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        disp_archive.assert_called_once()
        edit_content.assert_not_called()

    def test_edit_file_fallback_read_uses_ignore_when_configured(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], const_dic={DKW.LARGE_FILE_SIZE: 1024, DKW.STRIP_COLOR_ON_PIPE: False, DKW.IGNORE_UNKNOWN_BYTES: True})
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=[UnicodeError, 'FALLBACK']) as read_file:
            with patch('cat_win.src.processor.fileprocessor.display_archive', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=True):
                    with patch('cat_win.src.processor.fileprocessor.ContentBuffer.from_lines', return_value='BUF'):
                        with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                            edit_file(0, ctx)
        self.assertEqual(read_file.call_args_list[1], call('x.txt', file_encoding='utf-8', errors='ignore', file_length=-1))
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_edit_file_fallback_read_strips_ansi_on_pipe(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], const_dic={DKW.LARGE_FILE_SIZE: 1024, DKW.STRIP_COLOR_ON_PIPE: True, DKW.IGNORE_UNKNOWN_BYTES: False})
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=[UnicodeError, 'ANSI']) as read_file:
            with patch('cat_win.src.processor.fileprocessor.display_archive', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=False):
                    with patch('cat_win.src.processor.fileprocessor.remove_ansi_codes_from_line', return_value='CLEAN') as strip_ansi:
                        with patch('cat_win.src.processor.fileprocessor.ContentBuffer.from_lines', return_value='BUF'):
                            with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                                edit_file(0, ctx)
        self.assertEqual(read_file.call_args_list[1], call('x.txt', file_encoding='utf-8', errors='replace', file_length=-1))
        strip_ansi.assert_called_once_with('ANSI')
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_edit_file_fallback_oserror_logs_and_returns(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=[OSError, OSError]):
            with patch('cat_win.src.processor.fileprocessor.display_archive', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.logger') as log:
                    with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                        edit_file(0, ctx)
        self.assertIn('Operation failed', log.call_args[0][0])
        edit_content.assert_not_called()

    def test_edit_file_no_args_eol(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], args=DummyArgs({ARGS_EOL: False}))
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value='a\rb\nc\r\nd'):
            with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        self.assertEqual(ctx.content.lines, ['a', 'b', 'c', 'd'])
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_edit_file_args_eol(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], args=DummyArgs({ARGS_EOL: True}))
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value='a\rb\nc\r\nd'):
            with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                    edit_file(0, ctx)
        self.assertEqual(ctx.content.lines, ['a\r', 'b\n', 'c\r\n', 'd'])
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_edit_file_args_eol_fail_first(self):
        ctx = self._mk_ctx([DummyFile('x.txt', path='x.txt')], args=DummyArgs({ARGS_EOL: True}))
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=[OSError, 'a\rb\nc\r\nd']):
            with patch('cat_win.src.processor.fileprocessor.display_archive', return_value=False):
                with patch('cat_win.src.processor.fileprocessor.os.isatty', return_value=False):
                    with patch('cat_win.src.processor.fileprocessor.edit_content') as edit_content:
                        edit_file(0, ctx)
        self.assertEqual(ctx.content.lines, ['a\r', 'b\n', 'c\r\n', 'd'])
        edit_content.assert_called_once_with(0, 0, ctx)

    def test_decode_files_base64_raw_mode(self):
        files = [DummyFile('A', path='a.b64'), DummyFile('B', path='b.b64')]
        ctx = self._mk_ctx(files, args=DummyArgs({ARGS_RAW: True}))
        tmp = DummyTmpFileHelper(['tmp1', 'tmp2'])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=['d1', 'd2']):
            with patch('cat_win.src.processor.fileprocessor.decode_base64', side_effect=[b'x1', b'x2']) as b64:
                with patch('cat_win.src.processor.fileprocessor.IoHelper.write_file') as write_file:
                    decode_files_base64(tmp, ctx)

        self.assertEqual(files[0].path, 'tmp1')
        self.assertEqual(files[1].path, 'tmp2')
        self.assertEqual(b64.call_args_list, [call('d1'), call('d2')])
        self.assertEqual(write_file.call_args_list, [call('tmp1', b'x1'), call('tmp2', b'x2')])

    def test_decode_files_base64_text_mode(self):
        files = [DummyFile('A', path='a.b64')]
        ctx = self._mk_ctx(files, args=DummyArgs({ARGS_RAW: False}))
        tmp = DummyTmpFileHelper(['tmp1'])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', return_value='d1'):
            with patch('cat_win.src.processor.fileprocessor.decode_base64', return_value='decoded') as b64:
                with patch('cat_win.src.processor.fileprocessor.IoHelper.write_file') as write_file:
                    decode_files_base64(tmp, ctx)

        b64.assert_called_once_with('d1', True, 'utf-8')
        write_file.assert_called_once_with('tmp1', 'decoded', 'utf-8')

    def test_decode_files_base64_logs_failures_and_continues(self):
        files = [DummyFile('A', path='a.b64'), DummyFile('B', path='b.b64')]
        ctx = self._mk_ctx(files)
        tmp = DummyTmpFileHelper(['tmp1', 'tmp2'])
        with patch('cat_win.src.processor.fileprocessor.IoHelper.read_file', side_effect=[UnicodeError, 'ok']):
            with patch('cat_win.src.processor.fileprocessor.decode_base64', return_value='decoded'):
                with patch('cat_win.src.processor.fileprocessor.IoHelper.write_file'):
                    with patch('cat_win.src.processor.fileprocessor.logger') as log:
                        decode_files_base64(tmp, ctx)

        self.assertIn('Base64 decoding failed for file: A', log.call_args_list[0][0][0])
        self.assertEqual(files[0].path, 'a.b64')
        self.assertEqual(files[1].path, 'tmp2')

    def test_edit_files_processes_in_forward_order(self):
        files = [DummyFile('a', path='a'), DummyFile('b', path='b'), DummyFile('c', path='c')]
        ctx = self._mk_ctx(files)
        with patch('cat_win.src.processor.fileprocessor.edit_file') as edit_file_m:
            edit_files(ctx)
        self.assertEqual(edit_file_m.call_args_list, [call(0, ctx), call(1, ctx), call(2, ctx)])

    def test_edit_files_processes_in_reverse_order(self):
        files = [DummyFile('a', path='a'), DummyFile('b', path='b'), DummyFile('c', path='c')]
        ctx = self._mk_ctx(files, args=DummyArgs({ARGS_REVERSE: True}))
        with patch('cat_win.src.processor.fileprocessor.edit_file') as edit_file_m:
            edit_files(ctx)
        self.assertEqual(edit_file_m.call_args_list, [call(2, ctx), call(1, ctx), call(0, ctx)])

    def test_edit_files_raw_view_modes_bin_hex_upper_hex_lower(self):
        files = [DummyFile('a', path='a')]

        ctx_b = self._mk_ctx(files, args=DummyArgs({ARGS_BINVIEW: True}))
        with patch('cat_win.src.processor.fileprocessor.print_raw_view') as prv:
            edit_files(ctx_b)
        prv.assert_called_once_with(ctx_b, 0, 'b')

        ctx_xu = self._mk_ctx(files, args=DummyArgs({ARGS_HEXVIEW: 'X'}))
        with patch('cat_win.src.processor.fileprocessor.print_raw_view') as prv:
            edit_files(ctx_xu)
        prv.assert_called_once_with(ctx_xu, 0, 'X')

        ctx_xl = self._mk_ctx(files, args=DummyArgs({ARGS_HEXVIEW: 'x'}))
        with patch('cat_win.src.processor.fileprocessor.print_raw_view') as prv:
            edit_files(ctx_xl)
        prv.assert_called_once_with(ctx_xl, 0, 'x')

    def test_edit_files_watch_mode_reloads_modified_file_and_stops_on_interrupt(self):
        files = [DummyFile('A', path='a'), DummyFile('B', path='b')]
        ctx = self._mk_ctx(files, args=DummyArgs({ARGS_WATCH: True}))

        mtime_values = [1, 2, 1, 3, 4]
        with patch('cat_win.src.processor.fileprocessor.get_file_mtime', side_effect=mtime_values):
            with patch('cat_win.src.processor.fileprocessor.edit_file') as edit_file_m:
                with patch('cat_win.src.processor.fileprocessor.sleep', side_effect=[None, KeyboardInterrupt]):
                    with patch('cat_win.src.processor.fileprocessor.logger') as log:
                        edit_files(ctx)

        self.assertEqual(edit_file_m.call_args_list[0:2], [call(0, ctx), call(1, ctx)])
        self.assertIn(call(1, ctx), edit_file_m.call_args_list)
        self.assertTrue(any("File 'B' has been modified. Reloading" in c[0][0] for c in log.call_args_list if c[0]))
