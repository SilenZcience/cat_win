from unittest import TestCase

from cat_win.src.const.escapecodes import *


class TestRegex(TestCase):
    maxDiff = None


    def test_color_code_8_16(self):
        self.assertEqual(color_code_8_16(33), '\x1b[33m')

    def test_color_code_256(self):
        self.assertEqual(color_code_256(33), '\x1b[38;5;33m')
        self.assertEqual(color_code_256(33, False), '\x1b[48;5;33m')

    def test_color_code_truecolor(self):
        self.assertEqual(color_code_truecolor(1, 2, 3), '\x1b[38;2;1;2;3m')
        self.assertEqual(color_code_truecolor(1, 2, 3, False), '\x1b[48;2;1;2;3m')

    def test_cursor_set_x_y(self):
        self.assertEqual(cursor_set_x_y(1, 2), '\x1b[1;2H')

    def test_cursor_move_x(self):
        self.assertEqual(cursor_move_x(7, 'up'), '\x1b[7A')
        self.assertEqual(cursor_move_x(8, 'down'), '\x1b[8B')
        self.assertEqual(cursor_move_x(9, 'right'), '\x1b[9C')
        self.assertEqual(cursor_move_x(10, 'left'), '\x1b[10D')

    def test_cursor_start_x(self):
        self.assertEqual(cursor_start_x(4), '\x1b[4F')
        self.assertEqual(cursor_start_x(4, 'down'), '\x1b[4E')
