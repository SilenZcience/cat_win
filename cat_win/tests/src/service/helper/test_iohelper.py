from unittest import TestCase
from unittest.mock import patch
import inspect
import io
import logging
import os
from types import SimpleNamespace

from cat_win.tests.mocks.std import StdInMock
from cat_win.tests.mocks.logger import LoggerStub
from cat_win.tests.mocks.pbar import PBarMock
from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.helper.iohelper import IoHelper, StatusLogger, create_file, path_parts


test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'texts')
test_file_path  = os.path.join(test_file_dir, 'test.txt')
test_file_path_empty = os.path.join(test_file_dir, 'test_empty.txt')
test_file_path_oneline = os.path.join(test_file_dir, 'test_oneline.txt')

stdin_mock = StdInMock()


@patch('sys.stdin', stdin_mock)
class TestStdInHelper(TestCase):
    def test_status_logger_formatter_and_get_color(self):
        sl = StatusLogger()
        try:
            sl.colors['info'] = '[I]'
            sl.colors['reset'] = '[/]'
            formatter = sl._Formatter(sl)
            record = logging.LogRecord('cat_win', logging.INFO, __file__, 1, 'msg', (), None)
            record.line_end = ''
            self.assertEqual(formatter.format(record), '[I]msg[/]')
            self.assertEqual(sl.get_color(sl.INFO), '[I]')
            self.assertEqual(sl.get_color(123456), '')
        finally:
            sl.close()

    def test_status_logger_set_and_clear_colors(self):
        sl = StatusLogger()
        try:
            color_dic = {
                CKW.DEBUG: 'd',
                CKW.INFO: 'i',
                CKW.WARNING: 'w',
                CKW.ERROR: 'e',
                CKW.CRITICAL: 'c',
                CKW.RESET_ALL: 'r',
            }
            with patch.object(sl, 'refresh_formatter') as mock_refresh:
                sl.set_colors(color_dic)
                self.assertEqual(sl.colors['debug'], 'd')
                self.assertEqual(sl.colors['info'], 'i')
                self.assertEqual(sl.colors['warning'], 'w')
                self.assertEqual(sl.colors['error'], 'e')
                self.assertEqual(sl.colors['critical'], 'c')
                self.assertEqual(sl.colors['reset'], 'r')
                mock_refresh.assert_called_once_with()

            with patch.object(sl, 'refresh_formatter') as mock_refresh:
                sl.clear_colors()
                self.assertEqual(sl.colors['debug'], '')
                self.assertEqual(sl.colors['info'], '')
                self.assertEqual(sl.colors['warning'], '')
                self.assertEqual(sl.colors['error'], '')
                self.assertEqual(sl.colors['critical'], '')
                self.assertEqual(sl.colors['reset'], '')
                mock_refresh.assert_called_once_with()
        finally:
            sl.close()

    def test_status_logger_reconfigure_file_handler_path(self):
        sl = StatusLogger()

        class FakeFileHandler(logging.Handler):
            def __init__(self, *_args, **_kwargs):
                super().__init__()
                self.closed_called = False

            def emit(self, _record):
                return

            def close(self):
                self.closed_called = True
                super().close()

        try:
            with patch('cat_win.src.service.helper.iohelper.logging.FileHandler', FakeFileHandler):
                old_handler = FakeFileHandler()
                sl.handler = old_handler
                sl.logger.addHandler(old_handler)
                with patch.object(sl.logger, 'removeHandler', wraps=sl.logger.removeHandler) as mock_remove:
                    with patch.object(old_handler, 'close', wraps=old_handler.close) as mock_close:
                        sl.log_to_file = True
                        sl._reconfigure_handler()
            self.assertTrue(mock_remove.called)
            self.assertTrue(mock_close.called)
            self.assertIsInstance(sl.handler, FakeFileHandler)
        finally:
            sl.close()

    def test_status_logger_set_level_set_log_to_file_and_call(self):
        sl = StatusLogger()
        try:
            sl.set_level(logging.CRITICAL)
            self.assertEqual(sl.logger.level, logging.CRITICAL)

            with patch.object(sl, '_reconfigure_handler') as mock_reconf:
                sl.set_log_to_file(True)
                self.assertTrue(sl.log_to_file)
                mock_reconf.assert_called_once_with()

            with patch.object(sl.logger, 'log') as mock_log:
                sl('a', 'b', sep='-', end='!')
                mock_log.assert_called_once_with(sl.ERROR, 'a-b', extra={'line_end': '!'})

            with self.assertRaises(TypeError):
                sl('x', unknown_kw=1)
        finally:
            sl.close()

    def test_status_logger_close_branches_and_del(self):
        sl = StatusLogger()

        class FakeFileHandler(logging.Handler):
            def __init__(self, *_args, **_kwargs):
                super().__init__()

            def emit(self, _record):
                return

        try:
            sl.handler = None
            sl.close()

            with patch('cat_win.src.service.helper.iohelper.logging.FileHandler', FakeFileHandler):
                fh = FakeFileHandler()
                sl.handler = fh
                sl.logger.addHandler(fh)
                with patch.object(sl.logger, 'removeHandler', wraps=sl.logger.removeHandler) as mock_remove:
                    with patch.object(fh, 'close', wraps=fh.close) as mock_close:
                        with patch.object(sl, '_reconfigure_handler') as mock_reconf:
                            sl.close()
                self.assertTrue(mock_remove.called)
                self.assertTrue(mock_close.called)
                self.assertTrue(mock_reconf.called)

            sh = logging.StreamHandler(io.StringIO())
            sl.handler = sh
            with patch.object(sh, 'flush', wraps=sh.flush) as mock_flush:
                sl.close()
            self.assertTrue(mock_flush.called)

            with patch.object(sl, 'close') as mock_close:
                sl.__del__()
                mock_close.assert_called_once_with()
        finally:
            sl.close()

    def test_path_parts(self):
        expected_output_win = ['C:/', 'a', 'b', 'c', 'd.txt']
        expected_output_unix_mac = ['a', 'b', 'c', 'd.txt']

        self.assertIn(path_parts('C:/a/b/c/d.txt'), [expected_output_win, expected_output_unix_mac])

    def test_read_file_text(self):
        self.assertEqual(IoHelper.read_file(test_file_path_empty, False), '')

    def test_read_file_binary(self):
        self.assertEqual(IoHelper.read_file(test_file_path_empty, True), b'')

    def test_read_file_with_progress_bar_mode(self):
        class DummyBinaryFile:
            def __init__(self):
                self.pos = 0

            def read(self, size=-1):
                if self.pos > 0:
                    return b''
                self.pos += 1
                return b'abc'

            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

        with patch('cat_win.src.service.helper.iohelper.PBar', PBarMock):
            with patch('builtins.open', return_value=DummyBinaryFile()):
                with patch('cat_win.src.service.helper.iohelper.io.BufferedReader', lambda f, buffer_size: f):
                    self.assertEqual(IoHelper.read_file('dummy.txt', binary=False, file_length=3), 'abc')

    def test_yield_file(self):
        gen = IoHelper.yield_file(__file__)
        for line in gen:
            self.assertNotIn('\n', line)

    def test_yield_file_close_early(self):
        gen = IoHelper.yield_file(__file__)
        self.assertEqual(inspect.getgeneratorstate(gen), 'GEN_CREATED')
        next(gen)
        self.assertEqual(inspect.getgeneratorstate(gen), 'GEN_SUSPENDED')
        gen.close()
        self.assertEqual(inspect.getgeneratorstate(gen), 'GEN_CLOSED')

        gen = IoHelper.yield_file(__file__)
        self.assertEqual(inspect.getgeneratorstate(gen), 'GEN_CREATED')
        gen.close()
        self.assertEqual(inspect.getgeneratorstate(gen), 'GEN_CLOSED')

    def test_yield_file_stop_iteration_paths(self):
        class StopIterFile:
            def __init__(self):
                self.closed = False

            def __iter__(self):
                raise StopIteration

            def close(self):
                self.closed = True

        txt_file = StopIterFile()
        with patch('builtins.open', return_value=txt_file):
            self.assertEqual(list(IoHelper.yield_file('dummy', binary=False)), [])
        self.assertTrue(txt_file.closed)

        bin_file = StopIterFile()
        with patch('builtins.open', return_value=bin_file):
            self.assertEqual(list(IoHelper.yield_file('dummy', binary=True)), [])
        self.assertTrue(bin_file.closed)

    def test_yield_file_binary_yields_bytes(self):
        data = b'AB'
        with patch('builtins.open', return_value=io.BytesIO(data)):
            self.assertEqual(list(IoHelper.yield_file('dummy', binary=True)), [65, 66])

    def test_get_newline(self):
        self.assertEqual(IoHelper.get_newline(test_file_path), '\r\n')
        self.assertEqual(IoHelper.get_newline(test_file_path_empty), '\n')
        self.assertEqual(IoHelper.get_newline(test_file_path_oneline), '\n')
        self.assertEqual(IoHelper.get_newline(test_file_path, 'x'), '\r\n')
        self.assertEqual(IoHelper.get_newline(test_file_path_empty, 'x'), 'x')
        self.assertEqual(IoHelper.get_newline(test_file_path_oneline, 'x'), 'x')

    def test_get_newline_error(self):
        self.assertEqual(IoHelper.get_newline('randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|', 'DEFAULT'), 'DEFAULT')

    def test_get_stdin_content_oneline(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(IoHelper.get_stdin_content(True)), 'hello')

    def test_get_stdin_content_oneline_eof(self):
        stdin_mock.set_content(f"hello{chr(26)}\n")
        self.assertEqual(''.join(IoHelper.get_stdin_content(True)), 'hello')

    def test_get_stdin_content(self):
        stdin_mock.set_content('hello\nworld')
        self.assertEqual(''.join(IoHelper.get_stdin_content(False)), 'hello\nworld\n')

    def test_get_stdin_content_eof(self):
        stdin_mock.set_content(f"hello\nworld{chr(26)}\n")
        self.assertEqual(''.join(IoHelper.get_stdin_content(False)), 'hello\nworld')

    def test_create_file_success_and_error_paths(self):
        logger_stub = LoggerStub()
        file_path = os.path.join('X:/', 'a', 'b', 'f.txt')

        with patch('cat_win.src.service.helper.iohelper.path_parts', return_value=['X:/', 'a', 'b']):
            with patch('cat_win.src.service.helper.iohelper.os.path.exists', return_value=False):
                with patch('cat_win.src.service.helper.iohelper.os.makedirs', side_effect=OSError('nope')):
                    with patch('cat_win.src.service.helper.iohelper.os.rmdir', side_effect=OSError('cleanup-fail')) as mock_rmdir:
                        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
                            self.assertFalse(create_file(file_path, 'x', 'utf-8'))
                self.assertTrue(mock_rmdir.called)

        logger_stub.clear()
        with patch('cat_win.src.service.helper.iohelper.path_parts', return_value=['X:/', 'a', 'b']):
            with patch('cat_win.src.service.helper.iohelper.os.path.exists', return_value=False):
                with patch('cat_win.src.service.helper.iohelper.os.makedirs'):
                    with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', side_effect=OSError('nope')):
                        with patch('cat_win.src.service.helper.iohelper.os.rmdir', side_effect=OSError('cleanup-fail')) as mock_rmdir:
                            with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
                                self.assertFalse(create_file(file_path, 'x', 'utf-8'))
                self.assertTrue(mock_rmdir.called)

        with patch('cat_win.src.service.helper.iohelper.os.makedirs'):
            with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file'):
                self.assertTrue(create_file(file_path, 'x', 'utf-8'))

    def test_write_file_short_writes_raise(self):
        class Ctx:
            def __init__(self, writer):
                self.writer = writer

            def __enter__(self):
                return self.writer

            def __exit__(self, *_):
                return False

        class ShortWriter:
            def write(self, _):
                return 0

        with patch('builtins.open', return_value=Ctx(ShortWriter())):
            with self.assertRaises(OSError):
                IoHelper.write_file('dummy.txt', 'abc', 'utf-8')

        with patch('builtins.open', return_value=Ctx(ShortWriter())):
            with self.assertRaises(OSError):
                IoHelper.write_file('dummy.bin', b'abc', 'utf-8')

    def test_write_file_returns_src_file_on_success(self):
        class Ctx:
            def __init__(self, writer):
                self.writer = writer

            def __enter__(self):
                return self.writer

            def __exit__(self, *_):
                return False

        class FullWriter:
            def __init__(self, count):
                self.count = count

            def write(self, _):
                return self.count

        with patch('builtins.open', return_value=Ctx(FullWriter(3))):
            self.assertEqual(IoHelper.write_file('dummy.txt', 'abc', 'utf-8'), 'dummy.txt')
        with patch('builtins.open', return_value=Ctx(FullWriter(3))):
            self.assertEqual(IoHelper.write_file('dummy.bin', b'abc', 'utf-8'), 'dummy.bin')

    def test_write_files_branches(self):
        logger_stub = LoggerStub()
        self.assertEqual(IoHelper.write_files([], 'x', 'utf-8'), [])

        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('builtins.input', return_value='N'):
                files = ['a.txt']
                self.assertEqual(IoHelper.write_files(files, '', 'utf-8'), [])

        logger_stub.clear()
        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('builtins.input', side_effect=UnicodeError('bad-input')):
                files = ['a.txt']
                self.assertEqual(IoHelper.write_files(files, '', 'utf-8'), [])
                self.assertIn('Aborting...', logger_stub.output())

        logger_stub.clear()
        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('builtins.input', return_value='Y'):
                with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', return_value='a.txt'):
                    self.assertEqual(IoHelper.write_files(['a.txt'], '', 'ascii'), ['a.txt'])
        self.assertIn('[Y/ENTER] Yes, Continue', logger_stub.output())

        # Force the explicit raise branch at iohelper.py:446
        # (encode succeeds but encoded length is not 3)
        logger_stub.clear()
        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('builtins.input', return_value='Y'):
                with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', return_value='a.txt'):
                    self.assertEqual(IoHelper.write_files(['a.txt'], '', 'utf-16'), ['a.txt'])
        self.assertIn('[Y/ENTER] Yes, Continue', logger_stub.output())

        logger_stub.clear()
        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('builtins.input', side_effect=EOFError):
                with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', return_value='a.txt'):
                    self.assertEqual(IoHelper.write_files(['a.txt'], '', 'utf-8'), ['a.txt'])

        calls = {'n': 0}

        def write_side_effect(file, _content, _enc):
            calls['n'] += 1
            if calls['n'] == 2:
                raise FileNotFoundError('missing')
            if calls['n'] == 3:
                raise OSError('write-fail')
            return file

        logger_stub.clear()
        files = ['ok.txt', 'missing.txt', 'bad.txt']
        with patch('cat_win.src.service.helper.iohelper.IoHelper.write_file', side_effect=write_side_effect):
            with patch('cat_win.src.service.helper.iohelper.create_file', return_value=True):
                with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
                    success = IoHelper.write_files(files, 'content', 'utf-8')
        self.assertEqual(success, ['ok.txt', 'missing.txt'])
        self.assertIn("could not be written", logger_stub.output())

    def test_read_write_files_from_stdin_paths(self):
        self.assertEqual(IoHelper.read_write_files_from_stdin([], 'utf-8'), [])

        logger_stub = LoggerStub()
        with patch('cat_win.src.service.helper.iohelper.logger', logger_stub):
            with patch('cat_win.src.service.helper.iohelper.IoHelper.get_stdin_content', return_value=iter(['a', 'b'])):
                with patch('cat_win.src.service.helper.iohelper.IoHelper.write_files', return_value=['f1']) as mock_write:
                    result = IoHelper.read_write_files_from_stdin(['f1'], 'utf-8', one_line=True)
        self.assertEqual(result, ['f1'])
        mock_write.assert_called_once_with(['f1'], 'ab', 'utf-8')
        self.assertIn('The given FILE(s)', logger_stub.output())

    def test_dup_stdin_internal_paths(self):
        with patch('cat_win.src.service.helper.iohelper.os.dup', return_value=11) as mock_dup:
            with patch('cat_win.src.service.helper.iohelper.os.open', return_value=22) as mock_open:
                with patch('cat_win.src.service.helper.iohelper.os.dup2') as mock_dup2:
                    with IoHelper.dup_stdin(True):
                        pass

        mock_dup.assert_called_once()
        self.assertTrue(mock_open.called)
        self.assertGreaterEqual(mock_dup2.call_count, 2)

    def test_dup_stdin_pyinstaller_windows_branch(self):
        fake_kernel = SimpleNamespace()
        fake_kernel.CreateFileW = lambda *args: 123
        fake_kernel.SetStdHandle = lambda *_args: 1
        fake_ctypes = SimpleNamespace(windll=SimpleNamespace(kernel32=fake_kernel))

        with patch('cat_win.src.service.helper.iohelper.on_windows_os', True):
            with patch('cat_win.src.service.helper.iohelper.ctypes', fake_ctypes):
                with patch('cat_win.src.service.helper.iohelper.getattr', side_effect=lambda obj, name, default=None: True if name == 'frozen' else getattr(obj, name, default)):
                    with patch('cat_win.src.service.helper.iohelper.hasattr', return_value=True):
                        with patch('cat_win.src.service.helper.iohelper.os.dup', return_value=11):
                            with patch('cat_win.src.service.helper.iohelper.os.open', return_value=22):
                                with patch('cat_win.src.service.helper.iohelper.os.dup2'):
                                    with IoHelper.dup_stdin(True):
                                        pass

    def test_dup_stdin_do_not_dup(self):
        with IoHelper.dup_stdin(False) as dup:
            self.assertEqual(dup, None)
