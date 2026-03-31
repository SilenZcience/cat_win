from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import MagicMock, patch

from cat_win.src.const.argconstants import (
    ARGS_GREP,
    ARGS_GREP_ONLY,
    ARGS_MORE,
    ARGS_NOBREAK,
    ARGS_NOCOL,
    ARGS_NOKEYWORD,
    ARGS_PEEK,
    ARGS_STDIN,
)
from cat_win.src.const.colorconstants import CKW
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.processor import outputprocessor as op
from cat_win.tests.mocks.args import DummyArgs


@contextmanager
def _noop_cm(*_):
    yield


class StepperStub:
    def __init__(self):
        self.lines = []
        self.multi = []

    def add_line(self, line):
        self.lines.append(line)

    def add_lines(self, lines):
        self.multi.append(list(lines))


class TestOutputProcessor(TestCase):
    def _ctx(self, args=None):
        default_args = {
            ARGS_GREP: False,
            ARGS_GREP_ONLY: False,
            ARGS_MORE: False,
            ARGS_NOKEYWORD: False,
            ARGS_NOBREAK: False,
            ARGS_NOCOL: False,
            ARGS_STDIN: False,
            ARGS_PEEK: False,
        }
        if args:
            default_args.update(args)
        ctx = MagicMock()
        ctx.u_args = DummyArgs(default_args)
        ctx.const_dic = {
            DKW.PEEK_SIZE: 1,
            DKW.GREP_CONTEXT_LINES: 1,
            DKW.GREP_QUERY_SEPARATOR: ' | ',
        }
        ctx.color_dic = {
            CKW.NUMBER: '<NUM>',
            CKW.RESET_ALL: '<RST>',
            CKW.REPLACE: '<REP>',
            CKW.FOUND: '<F>',
            CKW.RESET_FOUND: '</F>',
            CKW.MATCHED: '<M>',
            CKW.RESET_MATCHED: '</M>',
            CKW.FOUND_MESSAGE: '<FM>',
            CKW.MATCHED_MESSAGE: '<MM>',
        }
        ctx.arg_parser = MagicMock()
        ctx.arg_parser.file_queries = []
        ctx.arg_parser.file_queries_replacement = []
        ctx.content = ContentBuffer.from_rows([
            ('l1', 'p1-', ''),
            ('l2', 'p2-', ''),
            ('l3', 'p3-', ''),
        ])
        ctx.u_files = [MagicMock(displayname='f1.txt')]
        return ctx

    def test_print_excluded_by_peek_helper_and_gate(self):
        with patch('cat_win.src.processor.outputprocessor.print') as p:
            op._print_excluded_by_peek(3, 12, {CKW.NUMBER: '<N>', CKW.RESET_ALL: '<R>'})
        self.assertEqual(p.call_count, 4)

        ctx = self._ctx()
        with patch('cat_win.src.processor.outputprocessor._print_excluded_by_peek') as pe:
            with patch('cat_win.src.processor.outputprocessor.remove_ansi_codes_from_line', return_value='abc'):
                op.print_excluded_by_peek(ctx, 3)
        pe.assert_called_once()

        ctx.u_args[ARGS_GREP] = True
        with patch('cat_win.src.processor.outputprocessor._print_excluded_by_peek') as pe2:
            op.print_excluded_by_peek(ctx, 3)
        pe2.assert_not_called()

    def test_print_raw_view_with_peek_queue(self):
        ctx = self._ctx(args={ARGS_PEEK: True})
        ctx.u_files = [MagicMock(displayname='raw.bin')]
        gen = iter(['HDR', 'L1', 'L2', 'L3', 'L4'])
        with patch('cat_win.src.processor.outputprocessor.get_raw_view_lines_gen', return_value=gen):
            with patch('cat_win.src.processor.outputprocessor._print_excluded_by_peek') as part:
                with patch('cat_win.src.processor.outputprocessor.print') as p:
                    op.print_raw_view(ctx, 0, 'hex')
        part.assert_called_once()
        self.assertGreaterEqual(p.call_count, 4)

    def test_print_file_returns_false_on_empty(self):
        ctx = self._ctx()
        ctx.content = ContentBuffer.from_lines([])
        self.assertFalse(op.print_file(ctx, StepperStub(), 0))

    def test_print_file_without_queries_plain_and_more(self):
        ctx = self._ctx(args={ARGS_MORE: False})
        with patch('cat_win.src.processor.outputprocessor.print_excluded_by_peek') as ex:
            with patch('cat_win.src.processor.outputprocessor.print') as p:
                found = op.print_file(ctx, StepperStub(), 2)
        self.assertFalse(found)
        ex.assert_called_once_with(ctx, 2)
        self.assertGreaterEqual(p.call_count, 2)

        ctx_more = self._ctx(args={ARGS_MORE: True})
        st = StepperStub()
        with patch('cat_win.src.processor.outputprocessor.print_excluded_by_peek') as ex2:
            found = op.print_file(ctx_more, st, 2)
        self.assertFalse(found)
        ex2.assert_called_once_with(ctx_more, 2)
        self.assertEqual(len(st.multi), 2)

    def test_print_file_grep_only(self):
        ctx = self._ctx(args={ARGS_GREP_ONLY: True})
        ctx.arg_parser.file_queries = ['x']
        st = StepperStub()
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.FOUND), (3, CKW.RESET_FOUND), (4, CKW.MATCHED), (7, CKW.RESET_MATCHED)],
            [('abc', (0, 3))],
            [('def', (4, 7))],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc def', 'abc def')):
                with patch('cat_win.src.processor.outputprocessor.print') as p:
                    found = op.print_file(ctx, st, 0)
        self.assertTrue(found)
        self.assertGreaterEqual(p.call_count, 1)

    def test_print_file_grep_context_flush_and_nokeyword(self):
        ctx = self._ctx(args={ARGS_GREP: True, ARGS_NOKEYWORD: True})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([
            ('aa', 'p1-', ''),
            ('bb', 'p2-', ''),
        ])
        qm = MagicMock()
        qm.find_keywords.side_effect = [
            ([], [], []),
            ([(0, CKW.FOUND), (2, CKW.RESET_FOUND)], [('bb', (0, 2))], []),
        ]
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', side_effect=[('aa', 'aa'), ('bb', 'bb')]):
                with patch('cat_win.src.processor.outputprocessor.print') as p:
                    found = op.print_file(ctx, StepperStub(), 0)
        self.assertTrue(found)
        self.assertGreaterEqual(p.call_count, 1)

    def test_print_file_color_messages_and_prompt_guard(self):
        ctx = self._ctx(args={ARGS_NOCOL: False, ARGS_NOBREAK: False, ARGS_STDIN: False})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([('abc', 'p-', '')])
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.FOUND), (3, CKW.RESET_FOUND)],
            [('abc', (0, 3))],
            [],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc', 'abc')):
                with patch('cat_win.src.processor.outputprocessor._build_ansi_restore', return_value=({}, set())):
                    with patch('cat_win.src.processor.outputprocessor._map_display_pos', side_effect=lambda line, pos: pos):
                        with patch('cat_win.src.processor.outputprocessor.IoHelper.dup_stdin', _noop_cm):
                            with patch('cat_win.src.processor.outputprocessor.input', side_effect=EOFError()) as inp:
                                with patch('cat_win.src.processor.outputprocessor.print') as p:
                                    found = op.print_file(ctx, StepperStub(), 0)
        self.assertTrue(found)
        self.assertTrue(inp.called)
        self.assertGreaterEqual(p.call_count, 1)

    def test_print_file_nobreak_skips_prompt(self):
        ctx = self._ctx(args={ARGS_NOBREAK: True})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([('abc', 'p-', '')])
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.FOUND), (3, CKW.RESET_FOUND)],
            [('abc', (0, 3))],
            [],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc', 'abc')):
                with patch('cat_win.src.processor.outputprocessor._build_ansi_restore', return_value=({}, set())):
                    with patch('cat_win.src.processor.outputprocessor._map_display_pos', side_effect=lambda line, pos: pos):
                        with patch('cat_win.src.processor.outputprocessor.print'):
                            with patch('cat_win.src.processor.outputprocessor.input') as inp:
                                op.print_file(ctx, StepperStub(), 0)
        inp.assert_not_called()

    def test_print_file_grep_only_with_more_adds_stepper_line(self):
        ctx = self._ctx(args={ARGS_GREP_ONLY: True, ARGS_MORE: True})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([('abc def', 'p-', '')])
        st = StepperStub()
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.FOUND), (3, CKW.RESET_FOUND), (4, CKW.MATCHED), (7, CKW.RESET_MATCHED)],
            [('abc', (0, 3))],
            [('def', (4, 7))],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc def', 'abc def')):
                op.print_file(ctx, st, 0)
        self.assertEqual(len(st.lines), 1)

    def test_print_file_no_intervals_with_and_without_more(self):
        ctx_more = self._ctx(args={ARGS_GREP: False, ARGS_MORE: True})
        ctx_more.arg_parser.file_queries = ['x']
        ctx_more.content = ContentBuffer.from_rows([('aa', 'p-', '')])
        qm_more = MagicMock()
        qm_more.find_keywords.return_value = ([], [], [])
        st = StepperStub()
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm_more):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('aa', 'aa')):
                op.print_file(ctx_more, st, 0)
        self.assertEqual(st.lines, ['p-aa'])

        ctx_plain = self._ctx(args={ARGS_GREP: False, ARGS_MORE: False})
        ctx_plain.arg_parser.file_queries = ['x']
        ctx_plain.content = ContentBuffer.from_rows([('aa', 'p-', '')])
        qm_plain = MagicMock()
        qm_plain.find_keywords.return_value = ([], [], [])
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm_plain):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('aa', 'aa')):
                with patch('cat_win.src.processor.outputprocessor.print') as p:
                    op.print_file(ctx_plain, StepperStub(), 0)
        self.assertGreaterEqual(p.call_count, 1)

    def test_print_file_more_path_covers_context_flush_and_messages(self):
        ctx = self._ctx(args={ARGS_GREP: False, ARGS_MORE: True, ARGS_NOCOL: False})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([('abc', 'p2-', '')])
        st = StepperStub()
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.FOUND), (1, CKW.MATCHED), (2, CKW.RESET_MATCHED), (3, CKW.RESET_FOUND)],
            [('a', (0, 1))],
            [('b', (1, 2))],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc', 'abc')):
                with patch('cat_win.src.processor.outputprocessor._build_ansi_restore', return_value=({}, {1})):
                    with patch('cat_win.src.processor.outputprocessor._map_display_pos', side_effect=lambda line, pos: pos):
                        op.print_file(ctx, st, 0)
        self.assertGreaterEqual(len(st.lines), 3)

    def test_print_file_matched_message_print_branch(self):
        ctx = self._ctx(args={ARGS_GREP: False, ARGS_MORE: False, ARGS_NOCOL: True})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([('abc', 'p-', '')])
        qm = MagicMock()
        qm.find_keywords.return_value = (
            [(0, CKW.MATCHED), (2, CKW.RESET_MATCHED)],
            [],
            [('ab', (0, 2))],
        )
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', return_value=('abc', 'abc')):
                with patch('cat_win.src.processor.outputprocessor.IoHelper.dup_stdin', _noop_cm):
                    with patch('cat_win.src.processor.outputprocessor.input', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'x')):
                        with patch('cat_win.src.processor.outputprocessor.print') as p:
                            op.print_file(ctx, StepperStub(), 0)
        self.assertGreaterEqual(p.call_count, 2)

    def test_print_file_flushes_grep_context_to_stepper_in_more_mode(self):
        ctx = self._ctx(args={ARGS_GREP: True, ARGS_MORE: True, ARGS_NOKEYWORD: True})
        ctx.arg_parser.file_queries = ['x']
        ctx.content = ContentBuffer.from_rows([
            ('pre', 'p1-', ''),
            ('hit', 'p2-', ''),
        ])
        st = StepperStub()
        qm = MagicMock()
        qm.find_keywords.side_effect = [
            ([], [], []),
            ([(0, CKW.MATCHED), (3, CKW.RESET_MATCHED)], [], [('hit', (0, 3))]),
        ]
        with patch('cat_win.src.processor.outputprocessor.QueryManager', return_value=qm):
            with patch('cat_win.src.processor.outputprocessor.replace_queries_in_line', side_effect=[('pre', 'pre'), ('hit', 'hit')]):
                op.print_file(ctx, st, 0)
        self.assertIn('p1-pre', st.lines)
