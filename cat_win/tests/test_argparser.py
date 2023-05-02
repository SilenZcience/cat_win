from unittest import TestCase
import os

from cat_win.const.argconstants import ARGS_CUT, ARGS_REPLACE
from cat_win.util import argparser
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')


class TestArgParser(TestCase):
    maxDiff = None

    def tearDown(self):
        argparser.FILE_ENCODING = 'utf-8'
        argparser.FILE_MATCH  = set()
        argparser.FILE_SEARCH = set()
        argparser.FILE_TRUNCATE = [None, None, None]

    def test_get_arguments_empty(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_duplicate(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', '-n', '-n', '-c'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', '-abcef'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_unknown(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', '-+abce?fϵg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f', '-g'])
        self.assertCountEqual(unknown_args, ['-+', '-?', '-ϵ'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_invalid(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', '--abcde?fg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcde?fg'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_encoding(self):
        argparser.get_arguments(['CAT', 'enc:ascii'])
        self.assertEqual(argparser.FILE_ENCODING, 'ascii')
        argparser.get_arguments(['CAT', 'enc=utf-8'])
        self.assertEqual(argparser.FILE_ENCODING, 'utf-8')

    def test_get_arguments_match(self):
        argparser.get_arguments(['CAT', 'match:\\Atest\\Z'])
        self.assertCountEqual(argparser.FILE_MATCH, set(['\\Atest\\Z']))
        argparser.get_arguments(['CAT', 'match=\\Atest\\Z'])
        self.assertCountEqual(argparser.FILE_MATCH, set(['\\Atest\\Z']))

    def test_get_arguments_find(self):
        argparser.get_arguments(['CAT', 'find=Test123'])
        self.assertCountEqual(argparser.FILE_SEARCH, set(['Test123']))
        argparser.get_arguments(['CAT', 'find:Test123'])
        self.assertCountEqual(argparser.FILE_SEARCH, set(['Test123']))

    def test_get_arguments_trunc(self):
        argparser.get_arguments(['CAT', 'trunc=0:'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [0, None, None])
        argparser.get_arguments(['CAT', 'trunc:1:'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [0, None, None])
        argparser.get_arguments(['CAT', 'trunc:2:'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [1, None, None])
        argparser.get_arguments(['CAT', 'trunc:::-1'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [None, None, -1])
        argparser.get_arguments(['CAT', 'trunc:4::-5'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [3, None, -5])
        argparser.get_arguments(['CAT', 'trunc:4:6:-5'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [3, 6, -5])
        argparser.get_arguments(['CAT', 'trunc=:2*4-3:'])
        self.assertListEqual(argparser.FILE_TRUNCATE, [None, 5, None])

    def test_get_arguments_cut(self):
        args, _, _, _, _ = argparser.get_arguments(['CAT', '[2*5:20]'])
        self.assertCountEqual(args, [(ARGS_CUT, '[2*5:20]')])

    def test_get_arguments_replace(self):
        args, _, _, _, _ = argparser.get_arguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test,404]')])

    def test_get_arguments_dir(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', test_file_dir])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_files_equal_dir(self):
        _, _, known_files_dir, _, _ = argparser.get_arguments(['CAT', test_file_dir])
        _, _, known_files_files, _, _ = argparser.get_arguments(['CAT', test_file_dir + '/**.txt'])
        self.assertCountEqual(known_files_dir, known_files_files)

    def test_get_arguments_unknown_file(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', 'testTesttest', 'test-file.txt'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])
        self.assertEqual(len(unknown_files), 2)
        self.assertIn('testTesttest', ''.join(unknown_files))
        self.assertIn('test-file.txt', ''.join(unknown_files))

    def test_get_arguments_unknown_args(self):
        _, unknown_args, _, _, _ = argparser.get_arguments(['CAT', '--test-file.txt'])
        self.assertCountEqual(unknown_args, ['--test-file.txt'])

    def test_get_arguments_echo_args(self):
        args, unknown_args, known_files, unknown_files, echo_args = argparser.get_arguments(['CAT', '-n', '-E', '-n', 'random', test_file_dir])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, ['-n', 'random', test_file_dir])

    def test_get_arguments_echo_args_recursive(self):
        args = []
        echo = argparser._add_argument(args, [], [], [], '-nEn')
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertEqual(echo, True)

    def test_delete_queried(self):
        argparser._add_argument([], [], [], [], 'find=hello')
        argparser._add_argument([], [], [], [], 'find=world')
        self.assertSetEqual(argparser.FILE_SEARCH, set(['hello', 'world']))
        argparser._add_argument([], [], [], [], 'find=hello', True)
        self.assertSetEqual(argparser.FILE_SEARCH, set(['world']))

        argparser._add_argument([], [], [], [], 'match=[a-z]')
        argparser._add_argument([], [], [], [], 'match=[0-9]')
        self.assertSetEqual(argparser.FILE_MATCH, set(['[a-z]', '[0-9]']))
        argparser._add_argument([], [], [], [], 'match=[0-9]', True)
        self.assertSetEqual(argparser.FILE_MATCH, set(['[a-z]']))
