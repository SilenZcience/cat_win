from unittest import TestCase
import os

from cat_win.const.argconstants import ARGS_CUT, ARGS_REPLACE
from cat_win.util.argparser import ArgParser
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')


class TestArgParser(TestCase):
    maxDiff = None

    def test_get_arguments_empty(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_duplicate(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '-n', '-n', '-c'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '-abcef'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_unknown(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '-+abce?fϵg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f', '-g'])
        self.assertCountEqual(unknown_args, ['-+', '-?', '-ϵ'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_invalid(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '--abcde?fg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcde?fg'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_encoding(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'enc:ascii'])
        self.assertEqual(arg_parser.file_encoding, 'ascii')
        arg_parser.get_arguments(['CAT', 'enc=utf-8'])
        self.assertEqual(arg_parser.file_encoding, 'utf-8')

    def test_get_arguments_match(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'match:\\Atest\\Z'])
        self.assertCountEqual(arg_parser.file_match, set(['\\Atest\\Z']))
        arg_parser.get_arguments(['CAT', 'match=\\Atest\\Z'])
        self.assertCountEqual(arg_parser.file_match, set(['\\Atest\\Z']))

    def test_get_arguments_find(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'find=Test123'])
        self.assertCountEqual(arg_parser.file_search, set(['Test123']))
        arg_parser.get_arguments(['CAT', 'find:Test123'])
        self.assertCountEqual(arg_parser.file_search, set(['Test123']))

    def test_get_arguments_trunc(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'trunc=0:'])
        self.assertListEqual(arg_parser.file_truncate, [0, None, None])
        arg_parser.get_arguments(['CAT', 'trunc:1:'])
        self.assertListEqual(arg_parser.file_truncate, [1, None, None])
        arg_parser.get_arguments(['CAT', 'trunc:2:'])
        self.assertListEqual(arg_parser.file_truncate, [2, None, None])
        arg_parser.get_arguments(['CAT', 'trunc:::-1'])
        self.assertListEqual(arg_parser.file_truncate, [None, None, -1])
        arg_parser.get_arguments(['CAT', 'trunc:4::-5'])
        self.assertListEqual(arg_parser.file_truncate, [4, None, -5])
        arg_parser.get_arguments(['CAT', 'trunc:4:6:-5'])
        self.assertListEqual(arg_parser.file_truncate, [4, 6, -5])
        arg_parser.get_arguments(['CAT', 'trunc=:2*4-3:'])
        self.assertListEqual(arg_parser.file_truncate, [None, 5, None])

    def test_get_arguments_cut(self):
        arg_parser = ArgParser()
        arg_parser.gen_arguments(['CAT', '[2*5:20]'])
        self.assertCountEqual(arg_parser._args, [(ARGS_CUT, '[2*5:20]')])

    def test_get_arguments_replace(self):
        arg_parser = ArgParser()
        args, _, _, _, _ = arg_parser.get_arguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test,404]')])

    def test_get_arguments_dir(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', test_file_dir])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_files_equal_dir(self):
        arg_parser = ArgParser()
        _, _, known_files_dir, _, _ = arg_parser.get_arguments(['CAT', test_file_dir])
        _, _, known_files_files, _, _ = arg_parser.get_arguments(['CAT', test_file_dir + '/**.txt'])
        self.assertCountEqual(known_files_dir, known_files_files)

    def test_get_arguments_unknown_file(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', 'testTesttest', 'test-file.txt'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])
        self.assertEqual(len(unknown_files), 2)
        self.assertIn('testTesttest', ''.join(unknown_files))
        self.assertIn('test-file.txt', ''.join(unknown_files))

    def test_get_arguments_unknown_args(self):
        arg_parser = ArgParser()
        arg_parser.gen_arguments(['CAT', '--test-file.txt'])
        self.assertCountEqual(arg_parser._unknown_args, ['--test-file.txt'])

    def test_get_arguments_echo_args(self):
        arg_parser = ArgParser()
        args, unknown_args, known_files, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '-n', '-E', '-n', 'random', test_file_dir])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, ['-n', 'random', test_file_dir])

    def test_get_arguments_echo_args_recursive(self):
        arg_parser = ArgParser()
        echo = arg_parser._add_argument('-nEn')
        args = list(map(lambda x: x[1], arg_parser._args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertEqual(echo, True)

    def test_delete_queried(self):
        arg_parser = ArgParser()
        arg_parser._add_argument('find=hello')
        arg_parser._add_argument('find=world')
        self.assertSetEqual(arg_parser.file_search, set(['hello', 'world']))
        arg_parser._add_argument('find=hello', True)
        self.assertSetEqual(arg_parser.file_search, set(['world']))

        arg_parser._add_argument('match=[a-z]')
        arg_parser._add_argument('match=[0-9]')
        self.assertSetEqual(arg_parser.file_match, set(['[a-z]', '[0-9]']))
        arg_parser._add_argument('match=[0-9]', True)
        self.assertSetEqual(arg_parser.file_match, set(['[a-z]']))
