from unittest import TestCase
import os

from cat_win.src.domain.files import Files
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'texts')
test_file_path        = os.path.join(test_file_dir, 'test.txt')
test_file_edge_case_1 = os.path.join(test_file_dir, 'test_holderEdgeCase_1.txt')
test_file_edge_case_2 = os.path.join(test_file_dir, 'test_holderEdgeCase_2.txt')
test_file_edge_case_3 = os.path.join(test_file_dir, 'test_holderEdgeCase_3.txt')
test_file_edge_case_4 = os.path.join(test_file_dir, 'test_holderEdgeCase_4.txt')
test_file_empty       = os.path.join(test_file_dir, 'test_empty.txt')


class TestFiles(TestCase):
    def test_calc_file_line_length_place_holder_(self):
        u_files = Files()
        u_files.set_files([test_file_path])
        u_files._calc_file_line_length_place_holder_()
        self.assertEqual(u_files.file_line_length_place_holder, 2)

    def test_calc_file_line_length_place_holder_edge(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_1])
        u_files._calc_file_line_length_place_holder_()
        self.assertEqual(u_files.file_line_length_place_holder, 1)

        u_files.set_files([test_file_edge_case_2])
        u_files._calc_file_line_length_place_holder_()
        self.assertEqual(u_files.file_line_length_place_holder, 2)

        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        u_files._calc_file_line_length_place_holder_()
        self.assertEqual(u_files.file_line_length_place_holder, 1)

        u_files.set_files([test_file_edge_case_2, test_file_edge_case_4])
        u_files._calc_file_line_length_place_holder_()
        self.assertEqual(u_files.file_line_length_place_holder, 2)

    def test__calc_max_line_length__empty(self):
        u_files = Files()
        self.assertEqual(u_files._calc_max_line_length_(test_file_empty), 0)

    def test_all_files_lines_sum(self):
        u_files = Files()
        u_files.set_files([test_file_path, test_file_edge_case_1])
        u_files._calc_place_holder_()
        self.assertEqual(u_files.all_files_lines_sum, 10)

        u_files.set_files([test_file_path] * 13)
        u_files._calc_place_holder_()
        self.assertEqual(u_files.all_files_lines_sum, 104)

    def test_all_line_number_place_holder(self):
        u_files = Files()
        u_files.set_files([test_file_path])
        u_files._calc_place_holder_()
        self.assertEqual(u_files.all_line_number_place_holder, 1)

        u_files.set_files([test_file_path, test_file_path])
        u_files._calc_place_holder_()
        self.assertEqual(u_files.all_line_number_place_holder, 1)

        u_files.set_files([test_file_edge_case_3])
        u_files._calc_place_holder_()
        self.assertEqual(u_files.all_line_number_place_holder, 2)

    def test_file_number_place_holder(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_1] * 9)
        u_files._calc_file_number_place_holder_()
        self.assertEqual(u_files.file_number_place_holder, 1)

        u_files.set_files([test_file_edge_case_1] * 10)
        u_files._calc_file_number_place_holder_()
        self.assertEqual(u_files.file_number_place_holder, 2)

        u_files.set_files([test_file_edge_case_1] * 99)
        u_files._calc_file_number_place_holder_()
        self.assertEqual(u_files.file_number_place_holder, 2)

        u_files.set_files([test_file_edge_case_1] * 100)
        u_files._calc_file_number_place_holder_()
        self.assertEqual(u_files.file_number_place_holder, 3)

    def test_get_file_display_name(self):
        u_files = Files()
        u_files.set_temp_file_stdin('STDINFILE')
        u_files.set_temp_file_echo('TEMPFILEECHO')
        u_files.set_temp_files_url({'TEMPFILEURL1': 'www.example.com',
                                    'TEMPFILEURL2': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'})
        u_files.set_files([test_file_edge_case_3, 'STDINFILE',
                          test_file_edge_case_4, 'TEMPFILEECHO',
                          'TEMPFILEURL1', 'TEMPFILEURL2'])

        self.assertEqual(
            u_files.get_file_display_name('STDINFILE'), '<STDIN>')
        self.assertEqual(
            u_files.get_file_display_name('TEMPFILEECHO'), '<ECHO>')
        self.assertEqual(
            u_files.get_file_display_name(test_file_edge_case_3), test_file_edge_case_3)
        self.assertEqual(
            u_files.get_file_display_name(test_file_edge_case_4), test_file_edge_case_4)
        self.assertEqual(
            u_files.get_file_display_name('TEMPFILEURL1'), '<URL www.example.com>')
        self.assertEqual(
            u_files.get_file_display_name('TEMPFILEURL2'), '<URL abcdefghijklmnopqrst...0123456789>')
