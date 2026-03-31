from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_B64E,
    ARGS_BLANK,
    ARGS_CHR,
    ARGS_CLIP,
    ARGS_CUT,
    ARGS_ENDS,
    ARGS_FILE_PREFIX,
    ARGS_FFILE_PREFIX,
    ARGS_LLENGTH,
    ARGS_MORE,
    ARGS_NUMBER,
    ARGS_PEEK,
    ARGS_REPLACE,
    ARGS_SPECIFIC_FORMATS,
    ARGS_SQUEEZE,
    ARGS_STDIN,
    ARGS_STRINGS,
    ARGS_EOL,
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.processor import contentprocessor as pro
from cat_win.tests.mocks.argparser import DummyArgParser
from cat_win.tests.mocks.args import DummyStartupArgs
from cat_win.tests.mocks.ctx import DummyCtx, DummyFile, DummyFiles


class TestContentProcessor(TestCase):
    def _ctx(self, args=None, ordered=None):
        defaults = {
            ARGS_STRINGS: False,
            ARGS_B64E: False,
            ARGS_CLIP: False,
            ARGS_NUMBER: False,
            ARGS_LLENGTH: False,
            ARGS_FILE_PREFIX: False,
            ARGS_FFILE_PREFIX: False,
            ARGS_PEEK: False,
            ARGS_MORE: False,
            ARGS_STDIN: False,
            ARGS_CHR: False,
            ARGS_BLANK: False,
            ARGS_ENDS: False,
            ARGS_REPLACE: False,
            ARGS_CUT: False,
            ARGS_SQUEEZE: False,
            ARGS_SPECIFIC_FORMATS: False,
            ARGS_EOL: False,
        }
        if args:
            defaults.update(args)

        arg_parser = DummyArgParser(file_encoding='utf-8')
        arg_parser.file_truncate = (None, None, None)

        u_args = DummyStartupArgs(overrides=defaults, ordered_args=ordered or [])

        ctx = DummyCtx(
            u_args=u_args,
            u_files=DummyFiles([DummyFile('a.txt')]),
            const_dic={
            DKW.STRINGS_MIN_SEQUENCE_LENGTH: 3,
            DKW.STRINGS_DELIMETER: b'\x00',
            DKW.PEEK_SIZE: 1,
            DKW.BLANK_REMOVE_WS_LINES: False,
            DKW.END_MARKER_SYMBOL: '$',
            DKW.SQUEEZE_COLLAPSE_SUFFIXES: True,
            },
            color_dic={
            CKW.RESET_ALL: '<RST>',
            CKW.ENDS: '<E>',
            CKW.CHARS: '<C>',
            CKW.SQUEEZE: '<S>',
            CKW.REPLACE: '<R>',
            },
            arg_parser=arg_parser,
            content=ContentBuffer.from_lines(['line1', 'line2']),
        )
        return ctx

    def test_ansi_aware_slice_line_and_apply_cut(self):
        sl = pro._ansi_aware_slice_line((0, 2, 1), '<RST>')
        out = sl('\x1b[31mabc\x1b[0m')
        self.assertIn('a', out)
        self.assertIn('b', out)

        ctx = self._ctx()
        ctx.content = ContentBuffer.from_lines(['abcd'])
        pro._apply_cut((1, 3, 1), ctx)
        self.assertEqual(ctx.content.lines, ['bc'])

    def test_ansi_aware_slice_line_empty_and_reset_transition(self):
        sl_empty = pro._ansi_aware_slice_line((2, 2, 1), '<RST>')
        self.assertEqual(sl_empty('abc'), '')

        with patch('cat_win.src.processor.contentprocessor.remove_ansi_codes_from_line', return_value='ab'):
            with patch('cat_win.src.processor.contentprocessor._map_display_pos', side_effect=[0, 1]):
                with patch('cat_win.src.processor.contentprocessor._build_ansi_restore', return_value=({0: '<RED>', 1: ''}, None)):
                    sl = pro._ansi_aware_slice_line((0, 2, 1), '<RST>')
                    out = sl('ab')
        self.assertIn('<RST>', out)

    def test_apply_ends_chr_blank_reverse_sort_replace_and_squeeze(self):
        ctx = self._ctx()
        ctx.content = ContentBuffer.from_rows([('A', 'p', 's'), ('A', 'p2', 's2'), ('', 'p3', 's3')])

        pro._apply_ends(None, ctx)
        self.assertTrue(ctx.content.suffixes[0].endswith('<E>$<RST>'))

        with patch.object(pro, 'SPECIAL_CHARS', [(9, 'I', None, True)]):
            ctx.content = ContentBuffer.from_lines(['a\tb'])
            pro._apply_chr(None, ctx)
            self.assertIn('^I', ctx.content.lines[0])

        with patch.object(pro, 'SPECIAL_CHARS', [(9, 'I', None, False)]):
            ctx.content = ContentBuffer.from_lines(['a\tb'])
            pro._apply_chr(None, ctx)
            self.assertEqual(ctx.content.lines, ['a\tb'])

        ctx.content = ContentBuffer.from_rows([('z', '1', ''), ('a', '2', ''), ('a', '3', ''), ('', '4', '')])
        pro._apply_blank(None, ctx)
        self.assertNotIn('', ctx.content.lines)
        pro._apply_squeeze(None, ctx)
        self.assertEqual(ctx.content.lines, ['z', 'a'])
        self.assertIn('[x2]', ''.join(ctx.content.suffixes))
        pro._apply_reverse(None, ctx)
        self.assertEqual(ctx.content.lines, ['a', 'z'])
        pro._apply_sort_alpha(None, ctx)
        self.assertEqual(ctx.content.lines, ['a', 'z'])
        pro._apply_sort_length(None, ctx)
        self.assertEqual(ctx.content.lines[0], 'a')

        ctx.const_dic[DKW.SQUEEZE_COLLAPSE_SUFFIXES] = False
        ctx.content = ContentBuffer.from_rows([('k', '1', 's1'), ('k', '2', 's2')])
        pro._apply_squeeze(None, ctx)
        self.assertEqual(ctx.content.suffixes, ['s1'])

        ctx.content = ContentBuffer.from_lines(['hello there'])
        pro._apply_replace(('there', 'world'), ctx)
        self.assertIn('world', ctx.content.lines[0])
        self.assertIn('<R>', ctx.content.lines[0])

    def test_apply_eval_and_convert(self):
        ctx = self._ctx()
        with patch('cat_win.src.processor.contentprocessor.comp_eval', return_value=ContentBuffer.from_lines(['E'])) as ce:
            pro._apply_eval('expr', ctx)
        ce.assert_called_once()
        self.assertEqual(ctx.content.lines, ['E'])

        with patch('cat_win.src.processor.contentprocessor.comp_conv', return_value=ContentBuffer.from_lines(['C'])) as cc:
            pro._apply_convert('hex', ctx)
        cc.assert_called_once()
        self.assertEqual(ctx.content.lines, ['C'])

    def test__apply_eol_suffixes(self):
        ctx = self._ctx(args={ARGS_EOL: True})
        ctx.content = ContentBuffer.from_lines(['line2\r', 'line3\n', 'line4\r\n', 'line5'])
        pro._apply_eol_suffixes(ctx)
        self.assertListEqual(ctx.content.lines, ['line2', 'line3', 'line4', 'line5'])
        self.assertListEqual(ctx.content.suffixes, ['<C><CR><RST>', '<C><LF><RST>', '<C><CRLF><RST>', '<C><EOF-noeol><RST>'])

    def test_edit_raw_content_branches(self):
        ctx = self._ctx(args={ARGS_STRINGS: True})
        with patch('cat_win.src.processor.contentprocessor.edit_content') as ec:
            pro.edit_raw_content(b'abc', 0, ctx)
        ec.assert_called_once_with(0, 0, ctx)

        ctx = self._ctx(args={ARGS_B64E: True, ARGS_CLIP: True})
        with patch('cat_win.src.processor.contentprocessor.encode_base64', return_value='ENC'):
            with patch('cat_win.src.processor.contentprocessor.print'):
                pro.edit_raw_content(b'abc', 0, ctx)
        self.assertIn('ENC', pro.Clipboard.clipboard)

        ctx = self._ctx()
        with patch('cat_win.src.processor.contentprocessor.sys.stdout.buffer.write') as wr:
            pro.edit_raw_content(b'raw', 0, ctx)
        wr.assert_called_once_with(b'raw')

    def test_edit_content_self_pipe_warning_early_return(self):
        ctx = self._ctx()
        ctx.content = ContentBuffer.from_lines([])
        logger_stub = MagicMock()
        now_ts = pro.datetime.timestamp(pro.datetime.now())
        with patch('cat_win.src.processor.contentprocessor.os.isatty', return_value=False):
            with patch('cat_win.src.processor.contentprocessor.get_file_mtime', return_value=now_ts):
                with patch.object(pro, 'logger', logger_stub):
                    pro.edit_content(0, 0, ctx)
        self.assertGreaterEqual(logger_stub.call_count, 1)

    def test_edit_content_full_flow_prefixes_peek_more_clip_and_b64(self):
        ordered = [(ARGS_CUT, (0, 4, 1))]
        ctx = self._ctx(
            args={
                ARGS_NUMBER: True,
                ARGS_LLENGTH: True,
                ARGS_FILE_PREFIX: True,
                ARGS_PEEK: True,
                ARGS_MORE: True,
                ARGS_CLIP: True,
                ARGS_EOL: True,
            },
            ordered=ordered,
        )
        ctx.content = ContentBuffer.from_lines(['lineA', 'lineB', 'lineC', 'lineD'])
        with patch('cat_win.src.processor.contentprocessor.get_line_prefix', side_effect=['1:', '2:', '3:', '4:']):
            with patch('cat_win.src.processor.contentprocessor.get_line_length_prefix', side_effect=lambda _c, p, _l: 'L' + p):
                with patch('cat_win.src.processor.contentprocessor.get_file_prefix', side_effect=lambda _c, p, _i, hyper=False: ('H' if hyper else 'F') + p):
                    with patch('cat_win.src.processor.contentprocessor.print_file', return_value=True):
                        with patch('cat_win.src.processor.contentprocessor.More') as more_cls:
                            pro.edit_content(0, 0, ctx)
        self.assertEqual(ctx.u_files[0].contains_queried, True)
        self.assertGreaterEqual(more_cls.return_value.step_through.call_count, 1)
        self.assertIn('F', pro.Clipboard.clipboard)
        self.assertEqual(ctx.content.prefixes, ['FL1:', 'FL4:'])
        self.assertEqual(ctx.content.lines, ['line', 'line'])
        self.assertEqual(ctx.content.suffixes, ['<C><EOF-noeol><RST>', '<C><EOF-noeol><RST>'])

        ctx = self._ctx(args={ARGS_B64E: True})
        with patch('cat_win.src.processor.contentprocessor.print_file', return_value=False):
            with patch('cat_win.src.processor.contentprocessor.encode_base64', return_value='ENCODED'):
                pro.edit_content(0, 0, ctx)
        self.assertEqual(ctx.content.lines, ['ENCODED'])

    def test_edit_content_strings_specific_formats_slice_and_ffile_prefix(self):
        ctx = self._ctx(
            args={
                ARGS_STRINGS: True,
                ARGS_SPECIFIC_FORMATS: True,
                ARGS_FFILE_PREFIX: True,
                ARGS_FILE_PREFIX: False,
            },
        )
        ctx.content = ContentBuffer.from_rows([
            ('a1', 'p1', ''),
            ('a2', 'p2', ''),
            ('a3', 'p3', ''),
        ])
        ctx.arg_parser.file_truncate = (0, 2, 1)
        with patch('cat_win.src.processor.contentprocessor.get_strings', return_value=ctx.content) as gs:
            with patch('cat_win.src.processor.contentprocessor.Formatter.format', return_value=ctx.content) as ff:
                with patch('cat_win.src.processor.contentprocessor.get_file_prefix', side_effect=lambda _c, p, _i, hyper=False: ('H' if hyper else 'F') + p) as gfp:
                    with patch('cat_win.src.processor.contentprocessor.print_file', return_value=False):
                        with patch('cat_win.src.processor.contentprocessor.More'):
                            pro.edit_content(0, 0, ctx)
        gs.assert_called_once()
        ff.assert_called_once()
        self.assertEqual(len(ctx.content), 2)
        self.assertTrue(all(p.startswith('H') for p in ctx.content.prefixes))
        self.assertTrue(gfp.called)
