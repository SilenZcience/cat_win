from unittest.mock import patch
from unittest import TestCase

from cat_win.src.service.helper.vishelper import get_fit_terminal_square, \
    SpaceFilling, Entropy
from cat_win.tests.mocks.pbar import PBarMock
# import sys
# sys.path.append('../cat_win')


class TestVisHelper(TestCase):
    maxDiff = None

    def test_get_fit_terminal_square(self):
        self.assertEqual(get_fit_terminal_square(1200,  120),  32)
        self.assertEqual(get_fit_terminal_square(120000, 64),  64)
        self.assertEqual(get_fit_terminal_square(120000, 63),  32)
        self.assertEqual(get_fit_terminal_square(120,   300),   8)
        self.assertEqual(get_fit_terminal_square(64,   300),    8)
        self.assertEqual(get_fit_terminal_square(63,   300),    4)
        self.assertEqual(get_fit_terminal_square(62,   300),    4)

    def test_get_scan_curve(self):
        scan_curve = [p for p in SpaceFilling.get_scan_curve(b'ab'*600, 120)]
        for p in scan_curve:
            self.assertEqual(len(p), 32)
        self.assertEqual(scan_curve[0], b'ab'*16)
        self.assertListEqual(scan_curve[1], [98, 97] * 16)
        self.assertEqual(scan_curve[2], b'ab'*16)
        self.assertListEqual(scan_curve[3], [98, 97] * 16)

    def test__get_zorder_index(self):
        self.assertEqual(SpaceFilling._get_zorder_index(0, 0), 0)
        self.assertEqual(SpaceFilling._get_zorder_index(1, 0), 2)
        self.assertEqual(SpaceFilling._get_zorder_index(1, 1), 3)
        self.assertEqual(SpaceFilling._get_zorder_index(0, 2), 4)
        self.assertEqual(SpaceFilling._get_zorder_index(0, 3), 5)
        self.assertEqual(SpaceFilling._get_zorder_index(1, 2), 6)
        self.assertEqual(SpaceFilling._get_zorder_index(1, 3), 7)
        self.assertEqual(SpaceFilling._get_zorder_index(2, 0), 8)

        self.assertEqual(SpaceFilling._get_zorder_index(7, 7),63)

    def test_get_zorder_curve(self):
        in_ = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?!.'
        out_ = [
            [97, 98, 101, 102, 113, 114, 117, 118],
            [99, 100, 103, 104, 115, 116, 119, 120],
            [105, 106, 109, 110, 121, 122, 67, 68],
            [107, 108, 111, 112, 65, 66, 69, 70],
            [71, 72, 75, 76, 87, 88, 48, 49],
            [73, 74, 77, 78, 89, 90, 50, 51],
            [79, 80, 83, 84, 52, 53, 56, 57],
            [81, 82, 85, 86, 54, 55, 63, 33],
            [46, -1, -1, -1, -1, -1, -1, -1]
            ]
        out = [p for p in SpaceFilling.get_zorder_curve(in_, 120)]
        self.assertEqual(out, out_)

    def test__get_hilbert_index(self):
        self.assertEqual(SpaceFilling._get_hilbert_index(2, 0, 0), 0)
        self.assertEqual(SpaceFilling._get_hilbert_index(2, 1, 0), 1)
        self.assertEqual(SpaceFilling._get_hilbert_index(2, 1, 1), 2)
        self.assertEqual(SpaceFilling._get_hilbert_index(2, 0, 1), 3)

        self.assertEqual(SpaceFilling._get_hilbert_index(4, 0, 0), 0)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 0, 1), 1)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 1, 1), 2)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 1, 0), 3)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 2, 0), 4)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 3, 0), 5)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 3, 1), 6)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 2, 1), 7)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 2, 2), 8)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 3, 2), 9)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 3, 3),10)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 2, 3),11)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 1, 3),12)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 1, 2),13)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 0, 2),14)
        self.assertEqual(SpaceFilling._get_hilbert_index(4, 0, 3),15)

    def test_get_hilbert_curve(self):
        in_ = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?!.'
        out_ = [
            [97, 100, 101, 102, 54, 55, 56, 33],
            [98, 99, 104, 103, 53, 52, 57, 63],
            [111, 110, 105, 106, 50, 51, 89, 88],
            [112, 109, 108, 107, 49, 48, 90, 87],
            [113, 114, 69, 70, 71, 72, 85, 86],
            [116, 115, 68, 67, 74, 73, 84, 83],
            [117, 120, 121, 66, 75, 78, 79, 82],
            [118, 119, 122, 65, 76, 77, 80, 81],
            [46, -1, -1, -1, -1, -1, -1, -1]
            ]
        out = [p for p in SpaceFilling.get_hilbert_curve(in_, 120)]
        self.assertEqual(out, out_)

    @patch('cat_win.src.service.helper.vishelper.PBar', PBarMock)
    def test_normalized_shannon_entropy(self):
        self.assertListEqual(Entropy.normalized_shannon_entropy(b'a'*128), [0] * 128)
        self.assertListEqual(Entropy.normalized_shannon_entropy(list(range(128))), [100] * 128)
        self.assertListEqual(Entropy.normalized_shannon_entropy(b'ab'*64), [14] * 128)
        self.assertListEqual(Entropy.normalized_shannon_entropy(b'abc'*64), [22] * 192)
        self.assertListEqual(Entropy.normalized_shannon_entropy(b'abcd'*64), [28] * 256)
