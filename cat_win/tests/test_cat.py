from unittest import TestCase
from unittest.mock import patch
import os

from cat_win import cat
from cat_win.tests.mocks.std import StdOutMock
from cat_win.util.file import File
from cat_win.util.holder import Holder

# import sys
# sys.path.append('../cat_win')


test_file_path = os.path.join(os.path.dirname(__file__), 'texts', 'test.txt')
test_file_content = []
with open(test_file_path, 'r', encoding='utf-8') as f:
    test_file_content = f.read().split('\n')


@patch('cat_win.cat.color_dic', dict.fromkeys(cat.color_dic, ''))
class TestCat(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()
        cat.holder = Holder()

    def test_cat_output_default_file(self):
        cat.holder.set_files([test_file_path])
        cat.holder.set_args([])

        check_against = '\n'.join(test_file_content) + '\n'

        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.edit_files()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_multiple_files(self):
        cat.holder.set_files([test_file_path, test_file_path, test_file_path])
        cat.holder.set_args([])

        check_against = '\n'.join(test_file_content * 3) + '\n'

        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.edit_files()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_reverse(self):
        cat.holder.set_files([test_file_path])
        cat.holder.set_args([(5, '')]) #reverse

        check_against = test_file_content
        check_against.reverse()
        check_against = '\n'.join(check_against) + '\n'

        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.edit_files()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_ends_and_tabs(self):
        cat.holder.set_files([test_file_path])
        cat.holder.set_args([(2, ''), (3, '')]) #ends & tabs

        check_against = ('\n'.join([c.replace('\t', '^I') + '$' for c in test_file_content]) +
                         '\n')

        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.edit_files()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat__get_line_prefix_file_excess(self):
        cat.holder.all_line_number_place_holder = 5
        self.assertEqual(cat._get_line_prefix(9, 1), '    9) ')

    def test_cat__get_line_prefix_file_occupied(self):
        cat.holder.all_line_number_place_holder = 2
        self.assertEqual(cat._get_line_prefix(10, 1), '10) ')

    def test_cat__get_line_prefix_file_excess_long(self):
        cat.holder.all_line_number_place_holder = 12
        self.assertEqual(cat._get_line_prefix(34719, 1), '       34719) ')

    def test_cat__get_line_prefix_file_occupied_long(self):
        cat.holder.all_line_number_place_holder = 5
        self.assertEqual(cat._get_line_prefix(34718, 1), '34718) ')

    def test_cat__get_line_prefix_files_excess(self):
        cat.holder.all_line_number_place_holder = 5
        cat.holder.file_number_place_holder = 4
        cat.holder.files = [1,2]
        self.assertEqual(cat._get_line_prefix(9, 1), '   1.    9) ')

    def test_cat__get_line_prefix_files_occupied(self):
        cat.holder.all_line_number_place_holder = 3
        cat.holder.file_number_place_holder = 2
        cat.holder.files = [1,2]
        self.assertEqual(cat._get_line_prefix(987, 10), '10.987) ')

    def test_cat__get_line_prefix_files_excess_long(self):
        cat.holder.all_line_number_place_holder = 12
        cat.holder.file_number_place_holder = 10
        cat.holder.files = [1,2]
        self.assertEqual(cat._get_line_prefix(101, 404), '       404.         101) ')

    def test_cat__get_line_prefix_files_occupied_long(self):
        cat.holder.all_line_number_place_holder = 11
        cat.holder.file_number_place_holder = 9
        cat.holder.files = [1,2]
        self.assertEqual(cat._get_line_prefix(12345123451, 123456789), '123456789.12345123451) ')

    def test_cat__get_line_length_prefix_string_excess(self):
        cat.holder.file_line_length_place_holder = 5
        cat.holder.set_args([])
        self.assertEqual(cat._get_line_length_prefix('testtest', 'abcdefghi'), 'testtest[    9] ')

    def test_cat__get_line_length_prefix_string_occupied(self):
        cat.holder.file_line_length_place_holder = 2
        cat.holder.set_args([])
        self.assertEqual(cat._get_line_length_prefix('prefix', 'abcdefghij'), 'prefix[10] ')

    def test_cat__get_line_length_prefix_bytes_excess(self):
        cat.holder.file_line_length_place_holder = 5
        cat.holder.set_args([])
        self.assertEqual(cat._get_line_length_prefix('testtest', b'abcdefghi'), 'testtest[    9] ')

    def test_cat__get_line_length_prefix_bytes_occupied(self):
        cat.holder.file_line_length_place_holder = 2
        cat.holder.set_args([])
        self.assertEqual(cat._get_line_length_prefix('prefix', b'abcdefghij'), 'prefix[10] ')

    def test_remove_ansi_codes_from_line(self):
        red = '\x1b[31m'
        reset = '\x1b[0m'
        random_string = f"abc{red}defghij{reset}klmnopq{red}r{reset}"
        expected_output = 'abcdefghijklmnopqr'
        self.assertEqual(cat.remove_ansi_codes_from_line(random_string), expected_output)

    @patch('cat_win.cat.print_update_information', new=lambda *_: '')
    def test__show_help(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat._show_help()
            for arg in cat.ALL_ARGS:
                if arg.show_arg:
                    self.assertIn(arg.short_form, fake_out.getvalue())
                    self.assertIn(arg.long_form, fake_out.getvalue())
                    self.assertIn(arg.arg_help, fake_out.getvalue())

    @patch('cat_win.cat.print_update_information', new=lambda *_: '')
    def test__show_help_shell(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat._show_help(True)
            for arg in cat.ALL_ARGS:
                if arg.show_arg and arg.show_arg_on_shell:
                    self.assertIn(arg.short_form, fake_out.getvalue())
                    self.assertIn(arg.long_form, fake_out.getvalue())
                    self.assertIn(arg.arg_help, fake_out.getvalue())

    @patch('cat_win.cat.print_update_information', new=lambda *_: '')
    def test__show_version(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat._show_version()
            self.assertIn('Catw', fake_out.getvalue())
            self.assertIn('Author', fake_out.getvalue())

    @patch('cat_win.cat.arg_parser.file_search', new=set(['hello', 'world']))
    def test__show_debug(self):
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat._show_debug([], ['test'], [], [], [])
            self.assertIn('test', fake_out.getvalue())
            self.assertIn('DEBUG', fake_out.getvalue())
            self.assertIn('hello', fake_out.getvalue())
            self.assertIn('world', fake_out.getvalue())

    def test__get_file_prefix(self):
        cat.holder.files = [File('a', 'b/c.x')]
        prefix = cat._get_file_prefix('pre ', 0, True)
        self.assertEqual(prefix, 'pre file://b/c.x ')

# python -m unittest discover -s cat_win.tests -p test*.py
