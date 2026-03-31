from unittest import TestCase
from unittest.mock import patch

from cat_win.src.curses.helper import diffviewerhelper
from cat_win.src.curses.helper.diffviewerhelper import (
    CustomDiffer,
    DifflibID,
    DifflibItem,
    DifflibParser,
    is_special_character,
)


class TestDiffViewerHelper(TestCase):
    def test_is_special_character_variants(self):
        self.assertFalse(is_special_character('a'))
        self.assertTrue(is_special_character('界'))
        self.assertTrue(is_special_character('\x00'))
        self.assertTrue(is_special_character('\u0301'))

    def test_custom_differ_plain_replace_when_no_close_or_equal(self):
        differ = CustomDiffer(best_ratio=0.99, cutoff=0.995)
        result = list(differ._fancy_replace(['alpha'], 0, 1, ['beta'], 0, 1))
        self.assertEqual(result, ['- alpha', '+ beta'])

    def test_custom_differ_synchs_on_identical_pair_when_no_close(self):
        differ = CustomDiffer(best_ratio=0.99, cutoff=0.995)
        result = list(
            differ._fancy_replace(
                ['left', 'same', 'tail-a'],
                0,
                3,
                ['same', 'right', 'tail-b'],
                0,
                3,
            )
        )
        self.assertIn('  same', result)

    def test_custom_differ_safety_fallback_when_best_indices_are_none(self):
        # cutoff below default best_ratio (0.6) forces the else-path.
        differ = CustomDiffer(cutoff=0.5)
        with patch.object(differ, '_plain_replace', return_value=iter(['P'])) as plain_replace:
            result = list(differ._fancy_replace(['same'], 0, 1, ['same'], 0, 1))
        self.assertEqual(result, ['P'])
        plain_replace.assert_called_once_with(['same'], 0, 1, ['same'], 0, 1)

    def test_custom_differ_intraline_opcodes_cover_all_tag_branches(self):
        class FakeMatcher:
            def __init__(self, *_):
                pass

            def set_seq2(self, *_):
                return None

            def set_seq1(self, *_):
                return None

            def real_quick_ratio(self):
                return 1.0

            def quick_ratio(self):
                return 1.0

            def ratio(self):
                return 1.0

            def set_seqs(self, *_):
                return None

            def get_opcodes(self):
                return [
                    ('replace', 0, 1, 0, 1),
                    ('delete', 1, 2, 1, 1),
                    ('insert', 2, 2, 1, 2),
                    ('equal', 2, 3, 2, 3),
                ]

        differ = CustomDiffer(best_ratio=0.1, cutoff=0.2)
        with patch.object(diffviewerhelper.difflib, 'SequenceMatcher', FakeMatcher):
            with patch.object(differ, '_fancy_helper', side_effect=[iter(['PRE']), iter(['POST'])]) as helper:
                with patch.object(differ, '_qformat', return_value=iter(['Q'])):
                    result = list(differ._fancy_replace(['abc'], 0, 1, ['xyz'], 0, 1))

        self.assertEqual(result, ['PRE', 'Q', 'POST'])
        self.assertEqual(helper.call_count, 2)

    def test_custom_differ_raises_on_unknown_opcode_tag(self):
        class FakeMatcher:
            def __init__(self, *_):
                pass

            def set_seq2(self, *_):
                return None

            def set_seq1(self, *_):
                return None

            def real_quick_ratio(self):
                return 1.0

            def quick_ratio(self):
                return 1.0

            def ratio(self):
                return 1.0

            def set_seqs(self, *_):
                return None

            def get_opcodes(self):
                return [('weird', 0, 1, 0, 1)]

        differ = CustomDiffer(best_ratio=0.1, cutoff=0.2)
        with patch.object(diffviewerhelper.difflib, 'SequenceMatcher', FakeMatcher):
            with self.assertRaises(ValueError):
                list(differ._fancy_replace(['a'], 0, 1, ['b'], 0, 1))

    def _parser_with_ndiff(self, ndiff_lines):
        with patch.object(CustomDiffer, 'compare', return_value=ndiff_lines):
            return DifflibParser([], [])

    def test_parser_advance_insert_and_delete(self):
        parser = self._parser_with_ndiff(['+ \t界', '- gone'])
        diff = parser.get_diff()

        self.assertEqual(len(diff), 2)
        self.assertEqual(diff[0].code, DifflibID.INSERT)
        self.assertEqual(diff[0].line1, '')
        self.assertEqual(diff[1].code, DifflibID.DELETE)
        self.assertEqual(diff[1].line2, '')
        self.assertEqual(parser.count_insert, 1)
        self.assertEqual(parser.count_delete, 1)

    def test_try_get_changed_line_quad_format(self):
        parser = self._parser_with_ndiff(['- old', '? -^', '+ new', '? +^'])
        item = parser.get_diff()[0]

        self.assertEqual(item.code, DifflibID.CHANGED)
        self.assertEqual(item.line1, 'old')
        self.assertEqual(item.line2, 'new')
        self.assertEqual(item.changes1, [0, 1])
        self.assertEqual(item.changes2, [0, 1])

    def test_try_get_changed_line_minus_plus_qmark(self):
        parser = self._parser_with_ndiff(['- old', '+ n\tew', '? +^'])
        item = parser.get_diff()[0]

        self.assertEqual(item.code, DifflibID.CHANGED)
        self.assertEqual(item.changes1, [])
        self.assertEqual(item.changes2, [0, 1])
        self.assertEqual(item.line2, 'n ew')

    def test_try_get_changed_line_minus_qmark_plus(self):
        parser = self._parser_with_ndiff(['- old', '? -^', '+ ne\tw'])
        item = parser.get_diff()[0]

        self.assertEqual(item.code, DifflibID.CHANGED)
        self.assertEqual(item.changes1, [0, 1])
        self.assertEqual(item.changes2, [])
        self.assertEqual(item.line2, 'ne w')

    def test_try_get_changed_line_returns_zero_when_no_pattern_matches(self):
        parser = self._parser_with_ndiff(['  keep'])
        cmp_line = DifflibItem('x', 'x')

        self.assertEqual(parser._tryGetChangedLine(cmp_line), 0)

    def test_parse_sets_counts_and_right_justified_line_numbers(self):
        parser = self._parser_with_ndiff(['  a', '+ b', '- c'])
        diff = parser.get_diff()

        self.assertEqual(parser.count_equal, 1)
        self.assertEqual(parser.last_lineno, 2)
        self.assertEqual(diff[0].lineno, '1')
        self.assertEqual(diff[1].lineno, ' ')
        self.assertEqual(diff[2].lineno, '2')
