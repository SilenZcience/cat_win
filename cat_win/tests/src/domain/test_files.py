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
    def test__calc_max_line_length_(self):
        u_files = Files()
        self.assertEqual(u_files._calc_max_line_length_(test_file_path), 2)
        self.assertEqual(u_files._calc_max_line_length_(test_file_empty), 0)
        self.assertEqual(u_files._calc_max_line_length_('randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

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

    def test__get_file_lines_sum_(self):
        u_files = Files()
        self.assertEqual(u_files._get_file_lines_sum_(test_file_path), 8)
        self.assertEqual(u_files._get_file_lines_sum_(test_file_empty), 1)
        self.assertEqual(u_files._get_file_lines_sum_('randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety*!?\\/:<>|'), 0)

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

    def test_is_temp_file(self):
        u_files = Files()
        u_files.set_temp_file_stdin('STDINFILE')
        u_files.set_temp_file_echo('TEMPFILEECHO')
        u_files.set_temp_files_url({'TEMPFILEURL1': 'www.example.com',
                                    'TEMPFILEURL2': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'})
        u_files.set_files([test_file_edge_case_3, 'STDINFILE',
                          test_file_edge_case_4, 'TEMPFILEECHO',
                          'TEMPFILEURL1', 'TEMPFILEURL2'])
        self.assertEqual(u_files.is_temp_file(0), False)
        self.assertEqual(u_files.is_temp_file(1), True)
        self.assertEqual(u_files.is_temp_file(2), False)
        self.assertEqual(u_files.is_temp_file(3), True)
        self.assertEqual(u_files.is_temp_file(4), True)
        self.assertEqual(u_files.is_temp_file(5), True)

    def test_files_len(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        self.assertEqual(len(u_files.files), 2)
        self.assertEqual(len(u_files), 2)

    def test_files_getitem(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        self.assertEqual(u_files[0].path, test_file_edge_case_3)
        self.assertEqual(u_files[1].path, test_file_edge_case_4)

    def test_files_iter(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        for file, expected_path in zip(u_files, [test_file_edge_case_3, test_file_edge_case_4]):
            self.assertEqual(file.path, expected_path)

    def test_files_generate_values(self):
        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        self.assertEqual(u_files.file_number_place_holder, 0)
        self.assertEqual(u_files.all_line_number_place_holder, 0)
        self.assertEqual(u_files.file_line_length_place_holder, 0)

        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        u_files.generate_values(False, False)
        self.assertEqual(u_files.file_number_place_holder, 1)
        self.assertEqual(u_files.all_line_number_place_holder, 0)
        self.assertEqual(u_files.file_line_length_place_holder, 0)

        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        u_files.generate_values(True, False)
        self.assertEqual(u_files.file_number_place_holder, 1)
        self.assertEqual(u_files.all_line_number_place_holder, 2)
        self.assertEqual(u_files.file_line_length_place_holder, 0)

        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        u_files.generate_values(False, True)
        self.assertEqual(u_files.file_number_place_holder, 1)
        self.assertEqual(u_files.all_line_number_place_holder, 0)
        self.assertEqual(u_files.file_line_length_place_holder, 1)

        u_files = Files()
        u_files.set_files([test_file_edge_case_3, test_file_edge_case_4])
        u_files.generate_values(True, True)
        self.assertEqual(u_files.file_number_place_holder, 1)
        self.assertEqual(u_files.all_line_number_place_holder, 2)
        self.assertEqual(u_files.file_line_length_place_holder, 1)
