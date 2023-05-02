from unittest import TestCase
import os

from cat_win.const.argconstants import HIGHEST_ARG_ID, ARGS_B64E, ARGS_NOCOL, ARGS_LLENGTH, ARGS_NUMBER, ARGS_TABS, ARGS_ENDS
from cat_win.util.holder import Holder
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path        = os.path.join(test_file_dir, 'test.txt')
test_file_edge_case_1 = os.path.join(test_file_dir, 'test_holderEdgeCase_1.txt')
test_file_edge_case_2 = os.path.join(test_file_dir, 'test_holderEdgeCase_2.txt')
test_file_edge_case_3 = os.path.join(test_file_dir, 'test_holderEdgeCase_3.txt')
test_file_edge_case_4 = os.path.join(test_file_dir, 'test_holderEdgeCase_4.txt')
test_file_empty       = os.path.join(test_file_dir, 'test_empty.txt')
holder = Holder()


class TestHolder(TestCase):
    def tearDown(self):
        holder.args = []
        holder.args_id = [False] * (HIGHEST_ARG_ID + 1)

    def test__calc_file_line_length_place_holder__(self):
        holder.set_files([test_file_path])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 2)

    def test__calc_file_line_length_place_holder__edge(self):
        holder.set_files([test_file_edge_case_1])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 1)

        holder.set_files([test_file_edge_case_2])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 2)

        holder.set_files([test_file_edge_case_3, test_file_edge_case_4])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 1)

        holder.set_files([test_file_edge_case_2, test_file_edge_case_4])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 2)

    def test___calc_max_line_length___empty(self):
        self.assertEqual(holder.__calc_max_line_length__(test_file_empty), 0)

    def test_all_files_lines_sum(self):
        holder.set_files([test_file_path, test_file_edge_case_1])
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_files_lines_sum, 10)

        holder.set_files([test_file_path] * 13)
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_files_lines_sum, 104)

    def test_all_line_number_place_holder(self):
        holder.set_files([test_file_path])
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_line_number_place_holder, 1)

        holder.set_files([test_file_path, test_file_path])
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_line_number_place_holder, 1)

        holder.set_files([test_file_edge_case_3])
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_line_number_place_holder, 2)

    def test_file_number_place_holder(self):
        holder.set_files([test_file_edge_case_1] * 9)
        holder.__calc_file_number_place_holder__()
        self.assertEqual(holder.file_number_place_holder, 1)

        holder.set_files([test_file_edge_case_1] * 10)
        holder.__calc_file_number_place_holder__()
        self.assertEqual(holder.file_number_place_holder, 2)

        holder.set_files([test_file_edge_case_1] * 99)
        holder.__calc_file_number_place_holder__()
        self.assertEqual(holder.file_number_place_holder, 2)

        holder.set_files([test_file_edge_case_1] * 100)
        holder.__calc_file_number_place_holder__()
        self.assertEqual(holder.file_number_place_holder, 3)

    def test_setargbase64(self):
        holder.set_args([(ARGS_B64E, '--b64e')])
        self.assertEqual(holder.args_id[ARGS_B64E], True)
        self.assertEqual(holder.args_id[ARGS_NOCOL], True)
        self.assertEqual(holder.args_id[ARGS_LLENGTH], False)
        self.assertEqual(holder.args_id[ARGS_NUMBER], False)

    def test__get_file_display_name(self):
        holder.set_temp_file_stdin('STDINFILE')
        holder.set_temp_file_echo('TEMPFILEECHO')
        holder.set_files([test_file_edge_case_3, 'STDINFILE', test_file_edge_case_4, 'TEMPFILEECHO'])

        self.assertEqual(holder._get_file_display_name('STDINFILE'), '<STDIN>')
        self.assertEqual(holder._get_file_display_name('TEMPFILEECHO'), '<ECHO>')
        self.assertEqual(holder._get_file_display_name(test_file_edge_case_3), test_file_edge_case_3)
        self.assertEqual(holder._get_file_display_name(test_file_edge_case_4), test_file_edge_case_4)

    def test_set_decoding_temp_files(self):
        holder.set_files([test_file_path] * 3)
        self.assertListEqual(holder._inner_files, [test_file_path] * 3)

        holder.set_decoding_temp_files([test_file_empty] * 4)
        self.assertListEqual(holder._inner_files, [test_file_empty] * 4)

    def test_add_args(self):
        holder.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.add_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_NUMBER, 'x')])
        self.assertEqual(holder.args_id.count(True), 2)

        holder.add_args([(ARGS_TABS, 'c')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_NUMBER, 'x'), (ARGS_TABS, 'c')])
        self.assertEqual(holder.args_id.count(True), 3)

    def test_delete_args(self):
        holder.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.delete_args([(ARGS_ENDS, 'a'), (ARGS_NUMBER, 'x')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(holder.args_id.count(True), 2)

        holder.delete_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a')])
        self.assertEqual(holder.args_id.count(True), 1)
        