from unittest import TestCase
import os

from cat_win.const.argconstants import ARGS_B64E, ARGS_NOCOL, ARGS_LLENGTH
from cat_win.const.argconstants import ARGS_NUMBER, ARGS_ENDS, ARGS_REPLACE
from cat_win.util.holder import Holder, reduce_list, diff_list
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path        = os.path.join(test_file_dir, 'test.txt')
test_file_edge_case_1 = os.path.join(test_file_dir, 'test_holderEdgeCase_1.txt')
test_file_edge_case_2 = os.path.join(test_file_dir, 'test_holderEdgeCase_2.txt')
test_file_edge_case_3 = os.path.join(test_file_dir, 'test_holderEdgeCase_3.txt')
test_file_edge_case_4 = os.path.join(test_file_dir, 'test_holderEdgeCase_4.txt')
test_file_empty       = os.path.join(test_file_dir, 'test_empty.txt')


class TestHolder(TestCase):
    def test__calc_file_line_length_place_holder__(self):
        holder = Holder()
        holder.set_files([test_file_path])
        holder.__calc_file_line_length_place_holder__()
        self.assertEqual(holder.file_line_length_place_holder, 2)

    def test__calc_file_line_length_place_holder__edge(self):
        holder = Holder()
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
        holder = Holder()
        self.assertEqual(holder.__calc_max_line_length__(test_file_empty), 0)

    def test_all_files_lines_sum(self):
        holder = Holder()
        holder.set_files([test_file_path, test_file_edge_case_1])
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_files_lines_sum, 10)

        holder.set_files([test_file_path] * 13)
        holder.__calc_place_holder__()
        self.assertEqual(holder.all_files_lines_sum, 104)

    def test_all_line_number_place_holder(self):
        holder = Holder()
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
        holder = Holder()
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
        holder = Holder()
        holder.set_args([(ARGS_B64E, '--b64e')])
        self.assertEqual(holder.args_id[ARGS_B64E], True)
        self.assertEqual(holder.args_id[ARGS_NOCOL], True)
        self.assertEqual(holder.args_id[ARGS_LLENGTH], False)
        self.assertEqual(holder.args_id[ARGS_NUMBER], False)

    def test_get_file_display_name(self):
        holder = Holder()
        holder.set_temp_file_stdin('STDINFILE')
        holder.set_temp_file_echo('TEMPFILEECHO')
        holder.set_files([test_file_edge_case_3, 'STDINFILE',
                          test_file_edge_case_4, 'TEMPFILEECHO'])

        self.assertEqual(
            holder.get_file_display_name('STDINFILE'), '<STDIN>')
        self.assertEqual(
            holder.get_file_display_name('TEMPFILEECHO'), '<ECHO>')
        self.assertEqual(
            holder.get_file_display_name(test_file_edge_case_3), test_file_edge_case_3)
        self.assertEqual(
            holder.get_file_display_name(test_file_edge_case_4), test_file_edge_case_4)

    def test_add_args(self):
        holder = Holder()
        holder.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.add_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(holder.args_id.count(True), 2)

        holder.add_args([(ARGS_ENDS, 'c')])
        self.assertListEqual(holder.args,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'c')])
        self.assertEqual(holder.args_id.count(True), 3)

    def test_delete_args(self):
        holder = Holder()
        holder.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.delete_args([(ARGS_ENDS, 'a'), (ARGS_NUMBER, 'x')])
        self.assertListEqual(holder.args, [(ARGS_LLENGTH, 'b')])
        self.assertEqual(holder.args_id.count(True), 1)

        holder.delete_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [])
        self.assertEqual(holder.args_id.count(True), 0)

    def test_reduce_list(self):
        test_list = [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])

        test_list += [(ARGS_NUMBER, 'c'), (ARGS_ENDS, 'd')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'd')])

        test_list += [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_NUMBER, 'c'), (ARGS_ENDS, 'd')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'd')])

    def test_diff_list(self):
        test_list = [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')]
        reduced_list = diff_list(test_list, [(ARGS_ENDS, 'a'), (ARGS_LLENGTH, 'c')])
        self.assertListEqual(reduced_list, [(ARGS_NUMBER, 'a')])

    def test_diff_list_differentiable(self):
        test_list = [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')]
        reduced_list = diff_list(test_list, [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[l,l]')])
        self.assertListEqual(reduced_list, [(ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')])

        test_list = [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')]
        reduced_list = diff_list(test_list, [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[a,b]')])
        self.assertListEqual(reduced_list, [(ARGS_REPLACE, '[c,a]')])
