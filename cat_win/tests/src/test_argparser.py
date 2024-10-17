from unittest import TestCase
import os

from cat_win.src.const.argconstants import ARGS_CUT, ARGS_REPLACE
from cat_win.src.argparser import ArgParser
# import sys
# sys.path.append('../cat_win')

test_file_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
project_dir = os.path.realpath(os.path.join(test_file_dir, '..'))
test_text_file_dir = os.path.realpath(os.path.join(test_file_dir, 'texts'))


class TestArgParser(TestCase):
    maxDiff = None

    def test_get_arguments_empty(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(['CAT'])
        known_files = arg_parser.get_files()
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_duplicate(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '-n', '-c'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(['CAT', '-abcef'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_unknown(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', '-+abcefϵg'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f', '-g'])
        self.assertCountEqual(unknown_args, ['-+', '-ϵ'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_invalid(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', '--abcdefg'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcdefg'])
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
        self.assertCountEqual([p.pattern for p, _ in arg_parser.file_queries], ['\\Atest\\Z'])
        arg_parser.get_arguments(['CAT', 'match=\\Atest\\Z'])
        self.assertCountEqual([p.pattern for p, _ in arg_parser.file_queries], ['\\Atest\\Z'] * 2)

    def test_get_arguments_find(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'find=Test123'])
        self.assertCountEqual(arg_parser.file_queries, [('Test123', False)])
        arg_parser.get_arguments(['CAT', 'FIND:Test123'])
        self.assertCountEqual(arg_parser.file_queries, [('Test123', False), ('Test123', True)])

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
        self.assertCountEqual(arg_parser.get_args(), [(ARGS_CUT, '[2*5:20]')])

    def test_get_arguments_replace(self):
        arg_parser = ArgParser()

        args, _, _, _ = arg_parser.get_arguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test,404]')])

        args, _, _, _ = arg_parser.get_arguments(['CAT', '[test\\,,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test\\,,404]')])

        self.assertEqual(arg_parser.file_replace_mapping['[test\\,,404]'], ('test,', '404'))
        args, _, _, _ = arg_parser.get_arguments(['CAT', '[\\n\\t,\\,\f]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[\\n\\t,\\,\x0c]')])
        self.assertEqual(arg_parser.file_replace_mapping['[\\n\\t,\\,\x0c]'], ('\n\t', ',\x0c'))

    def test_get_arguments_dir(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', test_text_file_dir])
        known_files = arg_parser.get_files()
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_files_equal_dir(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', test_text_file_dir])
        known_files_dir = arg_parser.get_files()
        arg_parser.get_arguments(['CAT', test_text_file_dir + '/**.txt'])
        known_files_files = arg_parser.get_files()
        self.assertCountEqual(known_files_dir, known_files_files)

    def test_get_arguments_unknown_file(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', 'testTesttest', 'test-file.txt'])
        known_files = arg_parser.get_files()
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
        arg_parser = ArgParser(unicode_echo=False)
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '--echo', '-n', 'random', test_text_file_dir])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '--echo'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertEqual(echo_args, '-n random ' + test_text_file_dir)

    def test_get_arguments_echo_args_escaped(self):
        arg_parser = ArgParser()
        args, unknown_args, unknown_files, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '-E', '-n', '\\n', 'random'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertEqual(echo_args, '-n \n random')

    def test_get_arguments_echo_args_recursive(self):
        arg_parser = ArgParser()
        echo = arg_parser._add_argument('-nEn')
        args = list(map(lambda x: x[1], arg_parser.get_args()))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertEqual(echo, True)

    def test_delete_queried(self):
        arg_parser = ArgParser()
        arg_parser._add_argument('find=hello')
        arg_parser._add_argument('find=world')
        self.assertCountEqual(arg_parser.file_queries, [('hello', False), ('world', False)])
        arg_parser._add_argument('find=hello', True)
        self.assertCountEqual(arg_parser.file_queries, [('world', False)])

        arg_parser._add_argument('match=[a-z]')
        arg_parser._add_argument('match=[0-9]')
        self.assertEqual(len(arg_parser.file_queries), 3)
        self.assertCountEqual([p.pattern for p, _ in arg_parser.file_queries if not isinstance(p, str)], ['[a-z]', '[0-9]'])
        arg_parser._add_argument('match=[0-9]', True)
        self.assertEqual(len(arg_parser.file_queries), 2)
        self.assertCountEqual([p.pattern for p, _ in arg_parser.file_queries if not isinstance(p, str)], ['[a-z]'])

    def test_known_directories(self):
        inside_project_dirs = [
            'src',
            'tests',
            'res',
        ]
        inside_test_dirs = [
            'mocks',
            'resources',
            'src',
            'texts',
        ]

        arg_parser = ArgParser()
        arg_parser._add_argument(test_file_dir + '/*')
        arg_parser.get_files()
        dirs = '\n'.join(map(os.path.basename, arg_parser.get_dirs()))
        for _dir in inside_test_dirs:
            self.assertIn(_dir, dirs)

        arg_parser = ArgParser()
        arg_parser._add_argument(test_file_dir)
        arg_parser.get_files()
        self.assertListEqual([test_file_dir], arg_parser.get_dirs())

        arg_parser = ArgParser()
        arg_parser._add_argument(project_dir + '/*')
        arg_parser.get_files()
        dirs = '\n'.join(map(os.path.basename, arg_parser.get_dirs()))
        for _dir in inside_project_dirs:
            self.assertIn(_dir, dirs)

        arg_parser = ArgParser()
        arg_parser._add_argument(project_dir + '/**/')
        arg_parser.get_files()
        dirs = '\n'.join(map(os.path.basename, arg_parser.get_dirs()))
        for _dir in inside_project_dirs + inside_test_dirs:
            self.assertIn(_dir, dirs)
