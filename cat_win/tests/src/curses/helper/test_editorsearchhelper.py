from unittest import TestCase
from unittest.mock import MagicMock
import re

from cat_win.src.curses.helper import editorsearchhelper as esh
from cat_win.tests.mocks.editorsearch import (
    PosMock,
    EditorSearchMock,
    HexEditorSearchMock,
    DiffViewerSearchMock,
)


class TestEditorSearchHelper(TestCase):
    def test_base_iter_and_notimplemented(self):
        e = EditorSearchMock(['abc'])
        base = esh._SearchIterBase(e, 0)
        self.assertIs(iter(base), base)
        with self.assertRaises(NotImplementedError):
            base._stop_if_past_original(0, 0)
        with self.assertRaises(NotImplementedError):
            next(base)

    def test_factory_returns_expected_types(self):
        e = EditorSearchMock(['abc'])
        self.assertIsInstance(esh.search_iter_factory(e, 0, downwards=True), esh._SearchIterDown)
        self.assertIsInstance(esh.search_iter_factory(e, 0, downwards=False), esh._SearchIterUp)

        h = HexEditorSearchMock([b'\xAB'])
        self.assertIsInstance(esh.search_iter_hex_factory(h, 0, downwards=True), esh._SearchIterHexDown)
        self.assertIsInstance(esh.search_iter_hex_factory(h, 0, downwards=False), esh._SearchIterHexUp)

        dv = DiffViewerSearchMock([('a', 'a')])
        self.assertIsInstance(esh.search_iter_diff_factory(dv, 0, downwards=True), esh._SearchIterDiffDown)
        self.assertIsInstance(esh.search_iter_diff_factory(dv, 0, downwards=False), esh._SearchIterDiffUp)

    def test_search_up_get_next_pos_string_and_multiline(self):
        e = EditorSearchMock(['abc aaa', 'bbb', 'ccc'], row=0, col=6, search='aaa')
        it = esh._SearchIterUp(e, 0)
        self.assertEqual(it._get_next_pos(e.window_content[0], 6, 0), 4)

        e2 = EditorSearchMock(['pre hello', 'middle', 'tailZ'], row=0, col=8, search='hello\nmiddle\ntail')
        it2 = esh._SearchIterUp(e2, 0)
        self.assertEqual(it2._get_next_pos(e2.window_content[0], 8, 0), 4)
        self.assertEqual(it2.s_rows, [((1, 0), 6), ((2, 0), 4)])
        self.assertEqual(it2._get_next_pos(e2.window_content[0], None, None), -1)

    def test_search_up_get_next_pos_regex_and_error_fallback(self):
        e = EditorSearchMock(['ab ab'], row=0, col=5, search=re.compile('ab'), replace='X')
        it = esh._SearchIterUp(e, 0)
        self.assertEqual(it._get_next_pos(e.window_content[0], 5, 0), 3)
        self.assertEqual(it.replace, 'X')

        e_err = EditorSearchMock(['ab'], row=0, col=1, search=re.compile('ab'), replace='\\g<1>')
        it_err = esh._SearchIterUp(e_err, 0)
        self.assertEqual(it_err._get_next_pos('ab', 1, 0), 0)
        self.assertEqual(it_err.replace, '\\g<1>')

        e_empty = EditorSearchMock(['ab'], row=0, col=1, search=re.compile(''), replace='R')
        it_empty = esh._SearchIterUp(e_empty, 0)
        it_empty.offset = 0
        it_empty._get_next_pos('ab', 1, 0)
        self.assertEqual(it_empty.empty_match_offset, 1)

    def test_search_up_stop_if_past_original_and_replacing_updates(self):
        e = EditorSearchMock(['abc'], row=0, col=2, search='a', replace='LONG')
        it = esh._SearchIterUp(e, 0, replacing=True)
        e.search_items = {(0, 2): 1, (1, 0): 2}
        it.s_len = 1
        it.r_len = 4
        res = it._stop_if_past_original(0, 1)
        self.assertEqual(res, (0, 1))
        self.assertTrue(it.yielded_result)
        self.assertEqual(it._start_x, 5)

        it.wrapped = True
        with self.assertRaises(StopIteration):
            it._stop_if_past_original(-1, 0)

        e.selecting = True
        e.selected_area = ((1, 0), (2, 0))
        with self.assertRaises(StopIteration):
            it._stop_if_past_original(0, 0)

    def test_search_up_next_found_wrap_and_stop(self):
        e = EditorSearchMock(['nomatch', 'zzz aaa'], row=1, col=6, search='aaa')
        it = esh._SearchIterUp(e, 0)
        self.assertEqual(next(it), (1, 4))

        e2 = EditorSearchMock(['aaa start', 'nomatch'], row=1, col=3, search='aaa')
        it2 = esh._SearchIterUp(e2, 0)
        self.assertEqual(next(it2), (0, 0))

        e3 = EditorSearchMock(['nomatch'], row=0, col=0, search='aaa', selecting=True)
        it3 = esh._SearchIterUp(e3, 0)
        with self.assertRaises(StopIteration):
            next(it3)

    def test_search_down_get_next_pos_string_multiline_and_regex(self):
        e = EditorSearchMock(['abc aaa'], row=0, col=0, search='aaa')
        it = esh._SearchIterDown(e, 0)
        self.assertEqual(it._get_next_pos(e.window_content[0], 0, 0), 4)
        self.assertEqual(it._get_next_pos(e.window_content[0], 999, 0), -1)

        e2 = EditorSearchMock(['pre hello', 'middle', 'tailZ'], row=0, col=0, search='hello\nmiddle\ntail')
        it2 = esh._SearchIterDown(e2, 0)
        self.assertEqual(it2._get_next_pos(e2.window_content[0], 4, 0), 0)

        e3 = EditorSearchMock(['ab ab'], row=0, col=0, search=re.compile('ab'), replace='X')
        it3 = esh._SearchIterDown(e3, 0)
        self.assertEqual(it3._get_next_pos('ab ab', 0, 0), 0)

        e4 = EditorSearchMock(['ab'], row=0, col=0, search=re.compile('ab'), replace='\\g<1>')
        it4 = esh._SearchIterDown(e4, 0)
        self.assertEqual(it4._get_next_pos('ab', 0, 0), 0)
        self.assertEqual(it4.replace, '\\g<1>')

    def test_search_down_stop_if_and_next_paths(self):
        e = EditorSearchMock(['aaa', 'bbb aaa'], row=0, col=0, search='aaa', replace='ZZ')
        it = esh._SearchIterDown(e, 0, replacing=True)
        e.search_items = {(0, 0): 1, (0, 2): 2}
        it.s_len = 3
        it.r_len = 2
        self.assertEqual(it._stop_if_past_original(0, 0), (0, 0))

        it.wrapped = True
        with self.assertRaises(StopIteration):
            it._stop_if_past_original(1, 0)

        e.selecting = True
        e.selected_area = ((0, 0), (0, 1))
        with self.assertRaises(StopIteration):
            it._stop_if_past_original(0, 1)

        e2 = EditorSearchMock(['aaa', 'bbb'], row=0, col=0, search='aaa')
        it2 = esh._SearchIterDown(e2, 0)
        self.assertEqual(next(it2), (0, 0))

        e3 = EditorSearchMock(['nomatch'], row=0, col=0, search='zzz')
        e3._next_extend_lines = ['zzz now']
        it3 = esh._SearchIterDown(e3, 0)
        self.assertEqual(next(it3), (1, 0))

    def test_search_down_next_selecting_stop(self):
        e = EditorSearchMock(['nomatch'], row=0, col=0, search='x', selecting=True)
        it = esh._SearchIterDown(e, 0)
        with self.assertRaises(StopIteration):
            next(it)

    def test_hex_base_conversions(self):
        h = HexEditorSearchMock([b'\xAA\xBB', b'\xCC'], row=0, col=0, search='AABB')
        it = esh._SearchIterHexBase(h, 0)
        self.assertEqual(it._flat_to_pos(2), (1, 0))
        self.assertEqual(it._pos_to_flat(1, 0), 2)
        self.assertEqual(it._pos_to_nibble(1, 0), 4)
        self.assertEqual(it._nibble_to_pos(5), (1, 0, 1))
        self.assertEqual(it._set_match_start(2), (0, 1))

    def test_hex_up_and_down_next_and_boundaries(self):
        h = HexEditorSearchMock([b'\xAA\xBB', b'\xCC\xDD'], row=0, col=0, search='BBCC')
        up = esh._SearchIterHexUp(h, 0)
        up.editor.cpos = PosMock(1, 1)
        self.assertEqual(next(up), (0, 1))

        h2 = HexEditorSearchMock([b'\xAA\xBB', b'\xCC\xDD'], row=1, col=1, search='DD')
        down = esh._SearchIterHexDown(h2, 0)
        down.editor.cpos = PosMock(1, 1)
        self.assertEqual(next(down), (1, 1))

        h3 = HexEditorSearchMock([b'\xAA\xBB'], row=0, col=0, search='FFFF')
        u3 = esh._SearchIterHexUp(h3, 0)
        with self.assertRaises(StopIteration):
            next(u3)

    def test_hex_selecting_and_wrapped_stop_conditions(self):
        h = HexEditorSearchMock([b'\xAA\xBB', b'\xCC'], row=0, col=0, search='AA')
        up = esh._SearchIterHexUp(h, 0)
        up.wrapped = True
        with self.assertRaises(StopIteration):
            up._stop_if_past_original(-1, 0)

        down = esh._SearchIterHexDown(h, 0)
        down.wrapped = True
        with self.assertRaises(StopIteration):
            down._stop_if_past_original(1, 0)

        h.selecting = True
        h.selected_area = ((0, 1), (0, 1))
        with self.assertRaises(StopIteration):
            up._stop_if_past_original(0, 0)
        with self.assertRaises(StopIteration):
            down._stop_if_past_original(1, 0)

    def test_diff_base_iter_and_notimplemented(self):
        dv = DiffViewerSearchMock([('abc', 'abc')])
        base = esh._SearchIterDiffBase(dv, 0)
        self.assertIs(iter(base), base)
        with self.assertRaises(NotImplementedError):
            base._stop_if_past_original(0, 0)
        with self.assertRaises(NotImplementedError):
            next(base)

    def test_diff_up_get_next_pos_variants_and_buffer(self):
        dv = DiffViewerSearchMock([('xabc', 'abc')], row=0, col=3, search='abc')
        up = esh._SearchIterDiffUp(dv, 0)
        self.assertEqual(up._get_next_pos(0, 3), 1)
        self.assertFalse(up.line2_matched)

        dv2 = DiffViewerSearchMock([('abc', 'xabc')], row=0, col=3, search='abc')
        up2 = esh._SearchIterDiffUp(dv2, 0)
        self.assertEqual(up2._get_next_pos(0, 3), 1)
        self.assertTrue(up2.line2_matched)

        dv3 = DiffViewerSearchMock([('abc', 'abc')], row=0, col=3, search='abc')
        up3 = esh._SearchIterDiffUp(dv3, 0)
        self.assertEqual(up3._get_next_pos(0, 3), 0)
        self.assertEqual(up3.match_buffer, (0, 0))

    def test_diff_up_next_and_wrap(self):
        dv = DiffViewerSearchMock([('abc', 'abc'), ('zzz', 'zzz')], row=1, col=2, search='abc')
        up = esh._SearchIterDiffUp(dv, 0)
        self.assertEqual(next(up), (0, 0))
        self.assertFalse(up.line2_matched)
        self.assertEqual(next(up), (0, 0))
        self.assertTrue(up.line2_matched)

        dv2 = DiffViewerSearchMock([('no', 'no')], row=0, col=0, search='abc')
        up2 = esh._SearchIterDiffUp(dv2, 0)
        with self.assertRaises(StopIteration):
            next(up2)

    def test_diff_down_get_next_pos_and_next(self):
        dv = DiffViewerSearchMock([('xab', 'ab'), ('none', 'zzab')], row=0, col=0, search='ab')
        down = esh._SearchIterDiffDown(dv, 0)
        self.assertEqual(down._get_next_pos(0, 0), 0)
        self.assertTrue(down.line2_matched)
        self.assertEqual(down._get_next_pos(1, 0), 2)
        self.assertTrue(down.line2_matched)

        dv2 = DiffViewerSearchMock([('ab', 'ab')], row=0, col=0, search='ab')
        down2 = esh._SearchIterDiffDown(dv2, 0)
        self.assertEqual(down2._get_next_pos(0, 0), 0)
        self.assertEqual(next(down2), (0, 0))
        self.assertTrue(down2.line2_matched)

    def test_diff_down_stop_and_wrapped(self):
        dv = DiffViewerSearchMock([('ab', 'ab')], row=0, col=0, search='ab')
        down = esh._SearchIterDiffDown(dv, 0)
        down.wrapped = True
        with self.assertRaises(StopIteration):
            down._stop_if_past_original(1, 0)

        dv2 = DiffViewerSearchMock([('xx', 'yy')], row=0, col=0, search='ab')
        down2 = esh._SearchIterDiffDown(dv2, 0)
        with self.assertRaises(StopIteration):
            next(down2)

    def test_search_up_additional_negative_branches(self):
        it = esh._SearchIterUp(EditorSearchMock(['x'], search='x'), 0)
        self.assertEqual(it._get_next_pos('x', -1, 0), -1)

        multi = esh._SearchIterUp(EditorSearchMock(['a'], search='a\nb'), 0)
        self.assertEqual(multi._get_next_pos('a', 0, 0), -1)

        multi2 = esh._SearchIterUp(EditorSearchMock(['abcd', 'xx', 'yy'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi2._get_next_pos('abcd', 0, 0), -1)

        multi3 = esh._SearchIterUp(EditorSearchMock(['zzab', 'DIFF', 'yy'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi3._get_next_pos('zzab', 2, 0), -1)

        multi4 = esh._SearchIterUp(EditorSearchMock(['zzab', 'xx', 'BAD'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi4._get_next_pos('zzab', 2, 0), -1)

        regex_it = esh._SearchIterUp(EditorSearchMock(['abc'], search=re.compile('z')), 0)
        self.assertEqual(regex_it._get_next_pos('abc', None, 0), -1)

    def test_search_up_next_wrapped_paths(self):
        e = EditorSearchMock(['aaa', 'bbb'], row=0, col=0, search='aaa')
        it = esh._SearchIterUp(e, 0)
        e.cpos = PosMock(1, 0)
        it.wrapped = True
        self.assertEqual(next(it), (0, 0))

        e2 = EditorSearchMock(['bbb', 'aaa'], row=0, col=0, search='aaa')
        it2 = esh._SearchIterUp(e2, 0)
        self.assertEqual(next(it2), (1, 0))

        e3 = EditorSearchMock(['none', 'none'], row=0, col=0, search='zzz')
        it3 = esh._SearchIterUp(e3, 0)
        with self.assertRaises(StopIteration):
            next(it3)

    def test_search_down_additional_negative_branches(self):
        multi = esh._SearchIterDown(EditorSearchMock(['a'], search='a\nb'), 0)
        self.assertEqual(multi._get_next_pos('a', 0, None), -1)

        multi2 = esh._SearchIterDown(EditorSearchMock(['a'], search='a\nb'), 0)
        self.assertEqual(multi2._get_next_pos('a', 0, 0), -1)

        multi3 = esh._SearchIterDown(EditorSearchMock(['zz', 'xx', 'yy'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi3._get_next_pos('zz', 0, 0), -1)

        multi4 = esh._SearchIterDown(EditorSearchMock(['ab', 'DIFF', 'yy'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi4._get_next_pos('ab', 0, 0), -1)

        multi5 = esh._SearchIterDown(EditorSearchMock(['ab', 'xx', 'BAD'], search='ab\nxx\nyy'), 0)
        self.assertEqual(multi5._get_next_pos('ab', 0, 0), -1)

        regex_none = esh._SearchIterDown(EditorSearchMock(['abc'], search=re.compile('z')), 0)
        self.assertEqual(regex_none._get_next_pos('abc', 0, 0), -1)

    def test_search_down_replacing_wrapped_and_next_wrapped(self):
        e = EditorSearchMock(['aaa'], row=0, col=0, search='aaa', replace='ZZ')
        it = esh._SearchIterDown(e, 1, replacing=True)
        e.search_items = {(0, 0): 1}
        it.s_len = 3
        it.r_len = 2
        it.wrapped = True
        it._stop_if_past_original(0, 0)
        self.assertEqual(it._start_x, -1)

        e2 = EditorSearchMock(['none', 'aaa'], row=1, col=0, search='aaa')
        it2 = esh._SearchIterDown(e2, 1)
        e2.cpos = PosMock(0, 0)
        it2.wrapped = True
        self.assertEqual(next(it2), (1, 0))

        e3 = EditorSearchMock(['zzz'], row=0, col=0, search='aaa')
        it3 = esh._SearchIterDown(e3, 0)
        with self.assertRaises(StopIteration):
            next(it3)

    def test_hex_base_iter_and_notimplemented(self):
        base = esh._SearchIterHexBase(HexEditorSearchMock([b'\xAA']), 0)
        self.assertIs(iter(base), base)
        with self.assertRaises(NotImplementedError):
            base._stop_if_past_original(0, 0)
        with self.assertRaises(NotImplementedError):
            next(base)

    def test_hex_additional_paths(self):
        h_wrap = HexEditorSearchMock([b'\xAA\xBB'], row=0, col=0, search='AA')
        up_wrap = esh._SearchIterHexUp(h_wrap, 0)
        up_wrap.editor.cpos = PosMock(0, 1)
        up_wrap.wrapped = True
        self.assertEqual(next(up_wrap), (0, 0))

        h_sel = HexEditorSearchMock([b'\xAA\xBB'], row=0, col=1, search='AA')
        h_sel.selecting = True
        h_sel.selected_area = ((0, 0), (0, 1))
        up_sel = esh._SearchIterHexUp(h_sel, 0)
        self.assertEqual(next(up_sel), (0, 0))

        h_down_wrap = HexEditorSearchMock([b'\xAA\xBB'], row=0, col=2, search='BB')
        down_wrap = esh._SearchIterHexDown(h_down_wrap, 0)
        down_wrap.editor.cpos = PosMock(0, 0)
        down_wrap.wrapped = True
        self.assertEqual(next(down_wrap), (0, 1))

        h_down_sel = HexEditorSearchMock([b'\xAA\xBB'], row=0, col=0, search='AA')
        h_down_sel.selecting = True
        h_down_sel.selected_area = ((0, 0), (0, 1))
        down_sel = esh._SearchIterHexDown(h_down_sel, 0)
        self.assertEqual(next(down_sel), (0, 0))

        h_none = HexEditorSearchMock([b'\xAA'], row=0, col=0, search='FFFF')
        down_none = esh._SearchIterHexDown(h_none, 0)
        with self.assertRaises(StopIteration):
            next(down_none)

    def test_diff_additional_paths(self):
        dv_up = DiffViewerSearchMock([('abc', 'def'), ('abc', 'def')], row=0, col=0, search='abc')
        up = esh._SearchIterDiffUp(dv_up, 0)
        self.assertEqual(next(up), (0, 0))

        up.wrapped = True
        with self.assertRaises(StopIteration):
            up._stop_if_past_original(-1, 0)

        dv_up2 = DiffViewerSearchMock([('none', 'none')], row=0, col=0, search='abc')
        up2 = esh._SearchIterDiffUp(dv_up2, 0)
        up2.wrapped = True
        with self.assertRaises(StopIteration):
            next(up2)

        dv_up3 = DiffViewerSearchMock([('none', 'none'), ('none', 'abc')], row=0, col=0, search='abc')
        up3 = esh._SearchIterDiffUp(dv_up3, 0)
        self.assertEqual(next(up3), (1, 0))

        dv_down = DiffViewerSearchMock([('abc', 'zz'), ('none', 'none')], row=0, col=0, search='abc')
        down = esh._SearchIterDiffDown(dv_down, 0)
        self.assertEqual(next(down), (0, 0))

        self.assertEqual(down._get_next_pos(0, 999), -1)

        down.wrapped = True
        with self.assertRaises(StopIteration):
            down._stop_if_past_original(1, 0)

        dv_down2 = DiffViewerSearchMock([('none', 'none'), ('abc', 'none')], row=1, col=0, search='abc')
        down2 = esh._SearchIterDiffDown(dv_down2, 1)
        dv_down2.cpos = PosMock(0, 0)
        down2.wrapped = True
        self.assertEqual(next(down2), (1, 0))

        dv_down3 = DiffViewerSearchMock([('none', 'none'), ('abc', 'none')], row=0, col=0, search='abc')
        down3 = esh._SearchIterDiffDown(dv_down3, 0)
        self.assertEqual(next(down3), (1, 0))

        dv_down4 = DiffViewerSearchMock([('none', 'none'), ('none', 'abc')], row=0, col=0, search='abc')
        down4 = esh._SearchIterDiffDown(dv_down4, 0)
        self.assertEqual(next(down4), (1, 0))

        dv_down5 = DiffViewerSearchMock([('none', 'none'), ('none', 'none')], row=0, col=0, search='abc')
        down5 = esh._SearchIterDiffDown(dv_down5, 0)
        with self.assertRaises(StopIteration):
            next(down5)

    def test_remaining_edge_branches(self):
        up_mismatch = esh._SearchIterUp(EditorSearchMock(['zzab', 'xx', 'yy'], search='cd\nxx\nyy'), 0)
        self.assertEqual(up_mismatch._get_next_pos('zzab', 2, 0), -1)

        up_sel = esh._SearchIterUp(EditorSearchMock(['abc'], row=0, col=0, search='a', selecting=True), 0)
        up_sel.editor.selected_area = ((1, 0), (2, 0))
        with self.assertRaises(StopIteration):
            up_sel._stop_if_past_original(0, 0)

        down_sel = esh._SearchIterDown(EditorSearchMock(['abc'], row=0, col=0, search='a', selecting=True), 0)
        down_sel.editor.selected_area = ((0, 0), (0, 0))
        with self.assertRaises(StopIteration):
            down_sel._stop_if_past_original(0, 0)

        e = EditorSearchMock(['hit', 'none'], row=1, col=0, search='hit')
        it = esh._SearchIterDown(e, 0)
        self.assertEqual(next(it), (0, 0))

        hd = HexEditorSearchMock([b'\xAA'], row=0, col=0, search='AA')
        hd.selecting = True
        hd.selected_area = ((0, 0), (-1, 0))
        down_h = esh._SearchIterHexDown(hd, 0)
        with self.assertRaises(StopIteration):
            down_h._stop_if_past_original(0, 0)

        class _ToggleSelectingHex(HexEditorSearchMock):
            def __init__(self):
                super().__init__([b'\xAA'], row=0, col=0, search='FFFF')
                self._reads = 0

            @property
            def selecting(self):
                self._reads += 1
                return self._reads > 1

            @selecting.setter
            def selecting(self, _value):
                return

        hx_up = _ToggleSelectingHex()
        with self.assertRaises(StopIteration):
            next(esh._SearchIterHexUp(hx_up, 0))

        hx_down = _ToggleSelectingHex()
        with self.assertRaises(StopIteration):
            next(esh._SearchIterHexDown(hx_down, 0))

        dv_up = DiffViewerSearchMock([('abc', 'abc')], row=0, col=0, search='abc')
        up_d = esh._SearchIterDiffUp(dv_up, 0)
        self.assertEqual(up_d._get_next_pos(0, -1), -1)

        dv_wrap = DiffViewerSearchMock([('none', 'none'), ('abc', 'none'), ('none', 'none')], row=0, col=0, search='abc')
        up_wrap = esh._SearchIterDiffUp(dv_wrap, 0)
        up_wrap.diffviewer.cpos = PosMock(2, 0)
        up_wrap.wrapped = True
        self.assertEqual(next(up_wrap), (1, 0))

        dv_down_wrap = DiffViewerSearchMock([('abc', 'none'), ('none', 'none')], row=1, col=0, search='abc')
        down_wrap = esh._SearchIterDiffDown(dv_down_wrap, 0)
        self.assertEqual(next(down_wrap), (0, 0))
