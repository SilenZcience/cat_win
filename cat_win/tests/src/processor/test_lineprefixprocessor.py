from unittest import TestCase
from unittest.mock import patch

from cat_win.src.const.argconstants import ARGS_FILE_PREFIX, ARGS_NOCOL, ARGS_NUMBER
from cat_win.src.processor.lineprefixprocessor import (
    _calculate_line_length_prefix_spacing,
    _calculate_line_prefix_spacing,
    get_file_prefix,
    get_line_length_prefix,
    get_line_prefix,
)
from cat_win.tests.mocks.ctx import DummyCtx, DummyFile, DummyFiles


class TestLinePrefixProcessor(TestCase):
    def setUp(self):
        _calculate_line_prefix_spacing.cache_clear()
        _calculate_line_length_prefix_spacing.cache_clear()

    def test_calculate_line_prefix_spacing_default(self):
        fmt = _calculate_line_prefix_spacing(2, 4, 0, '<N>', '<R>')
        self.assertEqual(fmt, '<N>  %i)<R> ')

    def test_calculate_line_prefix_spacing_file_name_prefix(self):
        fmt = _calculate_line_prefix_spacing(1, 3, 0, '<N>', '<R>', file_name_prefix=True)
        self.assertEqual(fmt, '<N>%i  <R> ')

    def test_calculate_line_prefix_spacing_with_file_index(self):
        fmt = _calculate_line_prefix_spacing(
            1,
            3,
            2,
            '<N>',
            '<R>',
            include_file_prefix=True,
            file_char_length=1,
        )
        self.assertEqual(fmt, '<N> %i.  %i)<R> ')

    def test_calculate_line_length_prefix_spacing(self):
        fmt = _calculate_line_length_prefix_spacing(2, 4, '<L>', '<R>')
        self.assertEqual(fmt, '%s<L>[  %i]<R> ')

    def test_get_line_prefix_with_file_prefix_flag(self):
        ctx = DummyCtx(u_args={ARGS_FILE_PREFIX: True}, u_files=DummyFiles([DummyFile('a')], all_line=4))
        self.assertEqual(get_line_prefix(ctx, 7, 3), '<NUM>7   <RST> ')

    def test_get_line_prefix_with_multiple_files(self):
        files = DummyFiles([DummyFile('a'), DummyFile('b')], all_line=3, file_num=3)
        ctx = DummyCtx(u_files=files)
        self.assertEqual(get_line_prefix(ctx, 12, 4), '<NUM>  4. 12)<RST> ')

    def test_get_line_prefix_single_file_default(self):
        files = DummyFiles([DummyFile('a')], all_line=3)
        ctx = DummyCtx(u_files=files)
        self.assertEqual(get_line_prefix(ctx, 5, 1), '<NUM>  5)<RST> ')

    def test_get_line_length_prefix_strips_ansi_for_strings(self):
        ctx = DummyCtx(u_files=DummyFiles([DummyFile('a')], line_len=3))
        with patch('cat_win.src.processor.lineprefixprocessor.remove_ansi_codes_from_line', return_value='abcd') as strip_ansi:
            result = get_line_length_prefix(ctx, 'P:', '\x1b[31mabcd\x1b[0m')
        strip_ansi.assert_called_once()
        self.assertEqual(result, 'P:<LEN>[  4]<RST> ')

    def test_get_line_length_prefix_skips_ansi_strip_for_non_string(self):
        ctx = DummyCtx(u_files=DummyFiles([DummyFile('a')], line_len=3))
        with patch('cat_win.src.processor.lineprefixprocessor.remove_ansi_codes_from_line') as strip_ansi:
            result = get_line_length_prefix(ctx, 'P:', ['a', 'b'])
        strip_ansi.assert_not_called()
        self.assertEqual(result, 'P:<LEN>[  2]<RST> ')

    def test_get_line_length_prefix_skips_ansi_strip_with_nocol(self):
        ctx = DummyCtx(u_args={ARGS_NOCOL: True}, u_files=DummyFiles([DummyFile('a')], line_len=3))
        with patch('cat_win.src.processor.lineprefixprocessor.remove_ansi_codes_from_line') as strip_ansi:
            result = get_line_length_prefix(ctx, 'P:', 'abcd')
        strip_ansi.assert_not_called()
        self.assertEqual(result, 'P:<LEN>[  4]<RST> ')

    def test_get_file_prefix_negative_index_returns_prefix(self):
        ctx = DummyCtx()
        self.assertEqual(get_file_prefix(ctx, 'P:', -1), 'P:')

    def test_get_file_prefix_appends_when_not_numbered(self):
        files = DummyFiles([DummyFile('alpha.txt')])
        ctx = DummyCtx(u_args={ARGS_NUMBER: False}, u_files=files)
        self.assertEqual(get_file_prefix(ctx, 'P:', 0), 'P:<FP>alpha.txt<RST> ')

    def test_get_file_prefix_prepends_when_numbered(self):
        files = DummyFiles([DummyFile('alpha.txt')])
        ctx = DummyCtx(u_args={ARGS_NUMBER: True}, u_files=files)
        self.assertEqual(get_file_prefix(ctx, 'P:', 0), '<FP>alpha.txt<RST>:P:')

    def test_get_file_prefix_hyperlink_forces_append_and_slashes(self):
        files = DummyFiles([DummyFile(r'C:\\tmp\\x.txt')])
        ctx = DummyCtx(u_args={ARGS_NUMBER: True}, u_files=files)
        result = get_file_prefix(ctx, 'P:', 0, hyper=True)
        self.assertTrue(result.startswith('P:<FP>file://'))
        self.assertIn('C:', result)
        self.assertNotIn('\\', result)
        self.assertTrue(result.endswith('<RST> '))
