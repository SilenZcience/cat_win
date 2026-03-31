from collections import namedtuple
from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_CHARCOUNT,
    ARGS_CLIP,
    ARGS_DEBUG,
    ARGS_DIRECTORIES,
    ARGS_FFILES,
    ARGS_FILES,
    ARGS_SSUM,
    ARGS_SUM,
    ARGS_WORDCOUNT,
)
from cat_win.src.processor import contentpostessor as post
from cat_win.tests.mocks.args import DummyStartupArgs


def _cache_stub(name, hits=1, misses=2, maxsize=10, currsize=3):
    info_cls = namedtuple('CacheInfo', 'hits misses maxsize currsize')

    def fn(*_):
        return None

    fn.__name__ = name
    fn.cache_info = lambda: info_cls(hits, misses, maxsize, currsize)
    return fn


class TestContentPostessor(TestCase):
    def _ctx(self):
        ctx = MagicMock()
        ctx.arg_parser = MagicMock()
        ctx.arg_parser.file_encoding = 'utf-8'
        ctx.known_dirs = ['d1']
        ctx.u_files = MagicMock()
        ctx.u_files.files = ['f1']
        ctx.u_files.all_files_lines = 7
        ctx.u_files.all_line_number_place_holder = 2
        ctx.u_files._get_file_lines_sum_ = _cache_stub('_get_file_lines_sum_')
        ctx.u_files._calc_max_line_length_ = _cache_stub('_calc_max_line_length_')
        ctx.u_args = DummyStartupArgs(
            {
                ARGS_FILES: False,
                ARGS_FFILES: False,
                ARGS_DIRECTORIES: False,
                ARGS_SUM: False,
                ARGS_SSUM: False,
                ARGS_WORDCOUNT: False,
                ARGS_CHARCOUNT: False,
                ARGS_CLIP: False,
                ARGS_DEBUG: False,
            },
            ordered_args=[],
        )
        return ctx

    def test_print_cache_debug_info(self):
        ctx = self._ctx()
        logger_stub = MagicMock()
        with patch.object(post, 'logger', logger_stub):
            with patch.object(post, 'remove_ansi_codes_from_line', _cache_stub('remove_ansi_codes_from_line')):
                with patch.object(post, '_calculate_line_prefix_spacing', _cache_stub('_calculate_line_prefix_spacing')):
                    with patch.object(post, '_calculate_line_length_prefix_spacing', _cache_stub('_calculate_line_length_prefix_spacing')):
                        with patch.object(post.Visualizer, 'get_color_byte_view', _cache_stub('get_color_byte_view')):
                            with patch.object(post.Visualizer, 'get_color_entropy', _cache_stub('get_color_entropy')):
                                with patch.object(post, 'is_special_character', _cache_stub('is_special_character')):
                                    post._print_cache_debug_info(ctx)
        self.assertGreaterEqual(logger_stub.call_count, 2)

    def test_cleanup_temp_files_success_and_error(self):
        logger_stub = MagicMock()
        helper = MagicMock()
        helper.get_generated_temp_files.return_value = ['a.tmp', 'b.tmp']
        with patch.object(post, 'logger', logger_stub):
            with patch('cat_win.src.processor.contentpostessor.os.remove', side_effect=[None, OSError('x')]) as rm:
                post._cleanup_temp_files(helper)
        self.assertEqual(rm.call_count, 2)
        self.assertGreaterEqual(logger_stub.call_count, 3)

    def test_show_summary_actions(self):
        ctx = self._ctx()
        ctx.u_args[ARGS_FILES] = True
        ctx.u_args[ARGS_DIRECTORIES] = True
        with patch('cat_win.src.processor.contentpostessor.print'):
            with patch('cat_win.src.processor.contentpostessor.Summary.show_files') as sf:
                with patch('cat_win.src.processor.contentpostessor.Summary.show_dirs') as sd:
                    post._show_files_and_directories(ctx)
        sf.assert_called_once_with(['f1'], False)
        sd.assert_called_once_with(['d1'])

        ctx.u_args[ARGS_SSUM] = True
        with patch('cat_win.src.processor.contentpostessor.print'):
            with patch('cat_win.src.processor.contentpostessor.Summary.show_sum') as ss:
                post._show_sum(ctx)
        ss.assert_called_once()

        with patch('cat_win.src.processor.contentpostessor.print'):
            with patch('cat_win.src.processor.contentpostessor.Summary.show_wordcount') as sw:
                post._show_wordcount(ctx)
        sw.assert_called_once_with(['f1'], 'utf-8')

        with patch('cat_win.src.processor.contentpostessor.print'):
            with patch('cat_win.src.processor.contentpostessor.Summary.show_charcount') as sc:
                post._show_charcount(ctx)
        sc.assert_called_once_with(['f1'], 'utf-8')

    def test_copy_to_clipboard(self):
        with patch.object(post.Clipboard, 'clipboard', '\x1b[31mabc\x1b[0m'):
            with patch('cat_win.src.processor.contentpostessor.remove_ansi_codes_from_line', return_value='abc'):
                with patch.object(post.Clipboard, 'put') as put:
                    post._copy_to_clipboard(MagicMock())
        put.assert_called_once_with('abc')

    def test_run_post_content_actions_deduplicates(self):
        ctx = self._ctx()
        ctx.u_args = DummyStartupArgs({}, ordered_args=[(1, True), (2, True), (3, True)])
        h = MagicMock()
        with patch.object(post, 'POST_CONTENT_ACTIONS', {1: h, 2: h, 3: MagicMock()}):
            post.run_post_content_actions(ctx)
        h.assert_called_once_with(ctx)

    def test_finalize_context_runs_debug_cleanup_and_close(self):
        ctx = self._ctx()
        ctx.u_args[ARGS_DEBUG] = True
        tmp = MagicMock()
        with patch('cat_win.src.processor.contentpostessor._print_cache_debug_info') as dbg:
            with patch('cat_win.src.processor.contentpostessor._cleanup_temp_files') as clean:
                with patch.object(post, 'logger') as logger_m:
                    post.finalize_context(ctx, tmp)
        dbg.assert_called_once_with(ctx)
        clean.assert_called_once_with(tmp)
        logger_m.close.assert_called_once()
