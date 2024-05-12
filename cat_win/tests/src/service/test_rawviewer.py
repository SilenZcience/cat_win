from unittest import TestCase
import os

from cat_win.src.service.rawviewer import get_display_char_gen, get_raw_view_lines_gen


test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')


class TestRawViewer(TestCase):
    maxDiff = None

    def test_get_display_char_gen(self):
        gen_no_encoding_error = get_display_char_gen()
        self.assertEqual(gen_no_encoding_error(128), '·')
        self.assertEqual(gen_no_encoding_error(65), 'A')
        self.assertEqual(gen_no_encoding_error(10), '␤')
        gen_encoding_error = get_display_char_gen('utf-16')
        self.assertEqual(gen_encoding_error(128), '.')
        self.assertEqual(gen_encoding_error(65), 'A')
        self.assertEqual(gen_encoding_error(10), '.')

    def test_get_display_char_gen_base(self):
        gen_hex = get_display_char_gen(base=16)
        self.assertEqual(gen_hex('0A'), '␤')
        gen_hex = get_display_char_gen(base=8)
        self.assertEqual(gen_hex('12'), '␤')

    def test_mode_x_upper(self):
        expected_result = """\
Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text                   
00000000 53 61 6D 70 6C 65 20 54 65 78 74 3A 0D 0A 54 68 # S a m p l e   T e x t : ␍ ␤ T h
00000010 69 73 20 69 73 20 61 20 54 61 62 2D 43 68 61 72 # i s   i s   a   T a b - C h a r
00000020 61 63 74 65 72 3A 20 3E 09 3C 0D 0A 54 68 65 73 # a c t e r :   > ␉ < ␍ ␤ T h e s
00000030 65 20 61 72 65 20 53 70 65 63 69 61 6C 20 43 68 # e   a r e   S p e c i a l   C h
00000040 61 72 73 3A 20 C3 A4 C3 B6 C3 BC C3 84 C3 96 C3 # a r s :   · · · · · · · · · · ·
00000050 9C 0D 0A 4E 2D 41 72 79 20 53 75 6D 6D 61 74 69 # · ␍ ␤ N - A r y   S u m m a t i
00000060 6F 6E 3A 20 E2 88 91 0D 0A 54 68 65 20 66 6F 6C # o n :   · · · ␍ ␤ T h e   f o l
00000070 6C 6F 77 69 6E 67 20 4C 69 6E 65 20 69 73 20 45 # l o w i n g   L i n e   i s   E
00000080 6D 70 74 79 3A 0D 0A 0D 0A 54 68 69 73 20 4C 69 # m p t y : ␍ ␤ ␍ ␤ T h i s   L i
00000090 6E 65 20 69 73 20 61 20 44 75 70 6C 69 63 61 74 # n e   i s   a   D u p l i c a t
000000A0 65 21 0D 0A 54 68 69 73 20 4C 69 6E 65 20 69 73 # e ! ␍ ␤ T h i s   L i n e   i s
000000B0 20 61 20 44 75 70 6C 69 63 61 74 65 21          #   a   D u p l i c a t e !"""

        self.assertEqual('\n'.join(get_raw_view_lines_gen(test_file_path, 'X')), expected_result)

    def test_mode_x(self):
        expected_result = """\
Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text                   
00000000 53 61 6d 70 6c 65 20 54 65 78 74 3a 0d 0a 54 68 # S a m p l e   T e x t : ␍ ␤ T h
00000010 69 73 20 69 73 20 61 20 54 61 62 2d 43 68 61 72 # i s   i s   a   T a b - C h a r
00000020 61 63 74 65 72 3a 20 3e 09 3c 0d 0a 54 68 65 73 # a c t e r :   > ␉ < ␍ ␤ T h e s
00000030 65 20 61 72 65 20 53 70 65 63 69 61 6c 20 43 68 # e   a r e   S p e c i a l   C h
00000040 61 72 73 3a 20 c3 a4 c3 b6 c3 bc c3 84 c3 96 c3 # a r s :   · · · · · · · · · · ·
00000050 9c 0d 0a 4e 2d 41 72 79 20 53 75 6d 6d 61 74 69 # · ␍ ␤ N - A r y   S u m m a t i
00000060 6f 6e 3a 20 e2 88 91 0d 0a 54 68 65 20 66 6f 6c # o n :   · · · ␍ ␤ T h e   f o l
00000070 6c 6f 77 69 6e 67 20 4c 69 6e 65 20 69 73 20 45 # l o w i n g   L i n e   i s   E
00000080 6d 70 74 79 3a 0d 0a 0d 0a 54 68 69 73 20 4c 69 # m p t y : ␍ ␤ ␍ ␤ T h i s   L i
00000090 6e 65 20 69 73 20 61 20 44 75 70 6c 69 63 61 74 # n e   i s   a   D u p l i c a t
000000A0 65 21 0d 0a 54 68 69 73 20 4c 69 6e 65 20 69 73 # e ! ␍ ␤ T h i s   L i n e   i s
000000B0 20 61 20 44 75 70 6c 69 63 61 74 65 21          #   a   D u p l i c a t e !"""

        self.assertEqual('\n'.join(get_raw_view_lines_gen(test_file_path, 'x')), expected_result)

    def test_mode_b(self):
        expected_result = """\
Address  00       01       02       03       04       05       06       07       08       09       0A       0B       0C       0D       0E       0F       # Decoded Text                   
00000000 01010011 01100001 01101101 01110000 01101100 01100101 00100000 01010100 01100101 01111000 01110100 00111010 00001101 00001010 01010100 01101000 # S a m p l e   T e x t : ␍ ␤ T h
00000010 01101001 01110011 00100000 01101001 01110011 00100000 01100001 00100000 01010100 01100001 01100010 00101101 01000011 01101000 01100001 01110010 # i s   i s   a   T a b - C h a r
00000020 01100001 01100011 01110100 01100101 01110010 00111010 00100000 00111110 00001001 00111100 00001101 00001010 01010100 01101000 01100101 01110011 # a c t e r :   > ␉ < ␍ ␤ T h e s
00000030 01100101 00100000 01100001 01110010 01100101 00100000 01010011 01110000 01100101 01100011 01101001 01100001 01101100 00100000 01000011 01101000 # e   a r e   S p e c i a l   C h
00000040 01100001 01110010 01110011 00111010 00100000 11000011 10100100 11000011 10110110 11000011 10111100 11000011 10000100 11000011 10010110 11000011 # a r s :   · · · · · · · · · · ·
00000050 10011100 00001101 00001010 01001110 00101101 01000001 01110010 01111001 00100000 01010011 01110101 01101101 01101101 01100001 01110100 01101001 # · ␍ ␤ N - A r y   S u m m a t i
00000060 01101111 01101110 00111010 00100000 11100010 10001000 10010001 00001101 00001010 01010100 01101000 01100101 00100000 01100110 01101111 01101100 # o n :   · · · ␍ ␤ T h e   f o l
00000070 01101100 01101111 01110111 01101001 01101110 01100111 00100000 01001100 01101001 01101110 01100101 00100000 01101001 01110011 00100000 01000101 # l o w i n g   L i n e   i s   E
00000080 01101101 01110000 01110100 01111001 00111010 00001101 00001010 00001101 00001010 01010100 01101000 01101001 01110011 00100000 01001100 01101001 # m p t y : ␍ ␤ ␍ ␤ T h i s   L i
00000090 01101110 01100101 00100000 01101001 01110011 00100000 01100001 00100000 01000100 01110101 01110000 01101100 01101001 01100011 01100001 01110100 # n e   i s   a   D u p l i c a t
000000A0 01100101 00100001 00001101 00001010 01010100 01101000 01101001 01110011 00100000 01001100 01101001 01101110 01100101 00100000 01101001 01110011 # e ! ␍ ␤ T h i s   L i n e   i s
000000B0 00100000 01100001 00100000 01000100 01110101 01110000 01101100 01101001 01100011 01100001 01110100 01100101 00100001                            #   a   D u p l i c a t e !"""

        self.assertEqual('\n'.join(get_raw_view_lines_gen(test_file_path, 'b')), expected_result)

    def test_mode_x_upper_colored(self):
        expected_result = """\
*Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text                   !
*00000000! 53 61 6D 70 6C 65 20 54 65 78 74 3A 0D 0A 54 68 *#! S a m p l e   T e x t : ␍ ␤ T h
*00000010! 69 73 20 69 73 20 61 20 54 61 62 2D 43 68 61 72 *#! i s   i s   a   T a b - C h a r
*00000020! 61 63 74 65 72 3A 20 3E 09 3C 0D 0A 54 68 65 73 *#! a c t e r :   > ␉ < ␍ ␤ T h e s
*00000030! 65 20 61 72 65 20 53 70 65 63 69 61 6C 20 43 68 *#! e   a r e   S p e c i a l   C h
*00000040! 61 72 73 3A 20 C3 A4 C3 B6 C3 BC C3 84 C3 96 C3 *#! a r s :   · · · · · · · · · · ·
*00000050! 9C 0D 0A 4E 2D 41 72 79 20 53 75 6D 6D 61 74 69 *#! · ␍ ␤ N - A r y   S u m m a t i
*00000060! 6F 6E 3A 20 E2 88 91 0D 0A 54 68 65 20 66 6F 6C *#! o n :   · · · ␍ ␤ T h e   f o l
*00000070! 6C 6F 77 69 6E 67 20 4C 69 6E 65 20 69 73 20 45 *#! l o w i n g   L i n e   i s   E
*00000080! 6D 70 74 79 3A 0D 0A 0D 0A 54 68 69 73 20 4C 69 *#! m p t y : ␍ ␤ ␍ ␤ T h i s   L i
*00000090! 6E 65 20 69 73 20 61 20 44 75 70 6C 69 63 61 74 *#! n e   i s   a   D u p l i c a t
*000000A0! 65 21 0D 0A 54 68 69 73 20 4C 69 6E 65 20 69 73 *#! e ! ␍ ␤ T h i s   L i n e   i s
*000000B0! 20 61 20 44 75 70 6C 69 63 61 74 65 21          *#!   a   D u p l i c a t e !"""

        self.assertEqual('\n'.join(get_raw_view_lines_gen(test_file_path, 'X', ['*', '!'])),
                         expected_result)

    def test_encoding_error(self):
        result = '\n'.join(get_raw_view_lines_gen(test_file_path, 'X', None, 'utf-16'))

        self.assertNotIn('␍', result)
        self.assertNotIn('␤', result)
        self.assertNotIn('·', result)
