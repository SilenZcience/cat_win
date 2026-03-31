from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.src.const.argconstants import ARGS_CUT, ARGS_REPLACE, ARGS_ECHO
from cat_win.src.argparser import ArgParser, IS_FILE, IS_DIR, IS_PATTERN
# import sys
# sys.path.append('../cat_win')

test_file_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
project_dir = os.path.realpath(os.path.join(test_file_dir, '..'))
test_text_file_dir = os.path.realpath(os.path.join(test_file_dir, 'texts'))


class TestArgParser(TestCase):
    maxDiff = None

    def test_get_arguments_empty(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(['CAT'])
        known_files = arg_parser.get_files()
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_duplicate(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '-n', '-c'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(['CAT', '-abcef'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_concatenated_unknown(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '-+abcefϵg'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f', '-g'])
        self.assertCountEqual(unknown_args, ['-+', '-ϵ'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])

    def test_get_arguments_invalid(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '--abcdefg'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcdefg'])
        self.assertCountEqual(known_files, [])
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
        arg_parser.get_arguments(['CAT', 'm=\\Atest\\Z'])
        self.assertCountEqual([p.pattern for p, _ in arg_parser.file_queries], ['\\Atest\\Z'] * 3)

    def test_get_arguments_find(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'find=Test123'])
        self.assertCountEqual(arg_parser.file_queries, [('Test123', False)])
        arg_parser.get_arguments(['CAT', 'FIND:Test123'])
        self.assertCountEqual(arg_parser.file_queries, [('Test123', False), ('Test123', True)])
        arg_parser.get_arguments(['CAT', 'f:Test123'])
        self.assertCountEqual(arg_parser.file_queries, [('Test123', False), ('Test123', True), ('Test123', False)])

    def test_get_arguments_replace_query(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'replace=Test123'])
        self.assertListEqual(arg_parser.file_queries_replacement, [])
        arg_parser.get_arguments(['CAT', 'f:1', 'REPLACE:Test123'])
        self.assertListEqual(arg_parser.file_queries_replacement, ['Test123'])
        arg_parser.get_arguments(['CAT', 'r:Test123'])
        self.assertListEqual(arg_parser.file_queries_replacement, ['Test123'])
        arg_parser.get_arguments(['CAT', 'f:2', 'f:3', 'r:Test123'])
        self.assertListEqual(arg_parser.file_queries_replacement, ['Test123'] * 3)

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
        arg_parser.get_arguments(['CAT', 't=:2*4-3:'])
        self.assertListEqual(arg_parser.file_truncate, [None, 5, None])

    def test_get_arguments_cut(self):
        arg_parser = ArgParser()
        arg_parser.gen_arguments(['CAT', '[2*5:20]'])
        self.assertCountEqual(arg_parser.get_args(), [(ARGS_CUT, (10, 20, None))])

    def test_get_arguments_replace(self):
        arg_parser = ArgParser()

        args, _, _ = arg_parser.get_arguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, ('test', '404'))])

        args, _, _ = arg_parser.get_arguments(['CAT', '[test\\,,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, ('test,', '404'))])

        args, _, _ = arg_parser.get_arguments(['CAT', '[\\n\\t,\\,\f]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, ('\n\t', ',\x0c'))])

    def test_get_arguments_dir(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', test_text_file_dir])
        known_files = arg_parser.get_files()
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
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
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', 'testTesttest', 'test-file.txt'])
        unknown_files, _ = arg_parser.filter_urls(False)
        known_files = arg_parser.get_files()
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])
        self.assertEqual(len(unknown_files), 2)
        self.assertIn('testTesttest', ''.join(map(str,unknown_files)))
        self.assertIn('test-file.txt', ''.join(map(str,unknown_files)))

    def test_get_arguments_unknown_file_expanduser(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '~/randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety!:<>|'])
        known_files = arg_parser.get_files()
        unknown_files, _ = arg_parser.filter_urls(False)
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])
        self.assertEqual(len(unknown_files), 1)
        self.assertIn('randomFileThatHopefullyDoesNotExistWithWeirdCharsForSafety!:<>|', str(unknown_files[0]))

    def test_get_arguments_unknown_args(self):
        arg_parser = ArgParser()
        arg_parser.gen_arguments(['CAT', '--test-file.txt'])
        self.assertCountEqual(arg_parser._unknown_args, ['--test-file.txt'])

    def test_get_arguments_echo_args(self):
        arg_parser = ArgParser(unicode_echo=False)
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '--echo', '-n', 'random', test_text_file_dir])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '--echo'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertEqual(echo_args, '-n random ' + test_text_file_dir)

    def test_get_arguments_echo_args_escaped(self):
        arg_parser = ArgParser()
        args, unknown_args, echo_args = arg_parser.get_arguments(
            ['CAT', '-n', '-E', '-n', '\\n', 'random'])
        known_files = arg_parser.get_files()
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
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
        dirs = '\n'.join(map(os.path.basename, arg_parser.get_dirs()))
        for _dir in inside_test_dirs:
            self.assertIn(_dir, dirs)

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

    def test_get_arguments_echo_unicode_error_is_ignored(self):
        arg_parser = ArgParser()
        _, _, echo_args = arg_parser.get_arguments(['CAT', 'enc:ascii', '-E', '\\ud800'])
        self.assertEqual(echo_args, '\\ud800')

    def test_filter_urls_enabled(self):
        arg_parser = ArgParser()
        arg_parser.get_arguments(['CAT', 'placeholder'])
        arg_parser._unknown_files = ['u-file', 'u-url']
        with patch('cat_win.src.argparser.sep_valid_urls', return_value=(['u-file'], ['u-url'])):
            unknown_files, valid_urls = arg_parser.filter_urls(True)
        self.assertEqual(list(map(str, unknown_files)), ['u-file'])
        self.assertEqual(valid_urls, ['u-url'])

    def test_get_files_includes_direct_file_struct_and_dot_files_flag(self):
        arg_parser = ArgParser()
        direct_file = os.path.realpath(os.path.join(test_text_file_dir, 'ansi-base.txt'))
        arg_parser._known_file_structures = [(IS_FILE, direct_file)]
        known = arg_parser.get_files(dot_files=True)
        self.assertIn(direct_file, list(map(str, known)))

    def test_get_files_filename_empty_and_oserror_fallbacks(self):
        arg_parser = ArgParser()
        arg_parser.win_prefix_lit = 'LIT:'
        arg_parser._known_file_structures = [(IS_PATTERN, '*.txt')]

        with patch('glob.iglob', return_value=['']):
            with patch('os.path.realpath', return_value='root/fallback_dir'):
                with patch('pathlib.Path.is_file', side_effect=[OSError('n'), OSError('l')]):
                    with patch('pathlib.Path.is_dir', side_effect=[False, True]):
                        arg_parser.get_files()

        self.assertEqual(len(arg_parser.get_dirs()), 1)
        self.assertTrue(str(arg_parser.get_dirs()[0]).startswith('LIT:'))

    def test_get_files_prefers_lit_path_when_norm_missing(self):
        arg_parser = ArgParser()
        arg_parser.win_prefix_lit = 'LIT:'
        arg_parser._known_file_structures = [(IS_PATTERN, '*.txt')]

        with patch('glob.iglob', return_value=['x.txt']):
            with patch('os.path.realpath', return_value='root/x.txt'):
                with patch('pathlib.Path.is_file', side_effect=[False, True]):
                    with patch('pathlib.Path.is_dir', return_value=False):
                        files = arg_parser.get_files()

        self.assertEqual(len(files), 1)
        self.assertTrue(str(files[0]).startswith('LIT:'))

    def test_get_files_ignores_oserror_for_dir_checks(self):
        arg_parser = ArgParser()
        arg_parser.win_prefix_lit = 'LIT:'
        arg_parser._known_file_structures = [(IS_PATTERN, '*.txt')]

        with patch('glob.iglob', return_value=['x.txt']):
            with patch('os.path.realpath', return_value='root/x.txt'):
                with patch('pathlib.Path.is_file', side_effect=[False, False]):
                    with patch('pathlib.Path.is_dir', side_effect=[OSError('norm-dir'), OSError('lit-dir')]):
                        files = arg_parser.get_files()

        self.assertEqual(files, [])
        self.assertEqual(arg_parser.get_dirs(), [])

    def test_add_path_struct_filename_empty_and_exists_branches(self):
        arg_parser = ArgParser()
        arg_parser.win_prefix_lit = 'LIT:'

        with patch('os.path.realpath', return_value='root/name'):
            with patch('pathlib.Path.is_file', side_effect=[True, False]):
                with patch('pathlib.Path.is_dir', side_effect=[False, True]):
                    is_struct = arg_parser._add_path_struct('/')

        self.assertTrue(is_struct)
        self.assertEqual(arg_parser._known_file_structures[0][0], IS_FILE)
        self.assertEqual(arg_parser._known_file_structures[1][0], IS_DIR)
        self.assertTrue(str(arg_parser._known_file_structures[1][1]).startswith('LIT:'))

    def test_add_path_struct_lit_file_only_and_pattern(self):
        arg_parser = ArgParser()
        arg_parser.win_prefix_lit = 'LIT:'

        with patch('os.path.realpath', return_value='root/match.txt'):
            with patch('pathlib.Path.is_file', side_effect=[False, True]):
                with patch('pathlib.Path.is_dir', return_value=False):
                    is_struct = arg_parser._add_path_struct('*.txt')

        self.assertTrue(is_struct)
        self.assertIn((IS_PATTERN, '*.txt'), arg_parser._known_file_structures)
        self.assertEqual(arg_parser._known_file_structures[0][0], IS_FILE)
        self.assertTrue(str(arg_parser._known_file_structures[0][1]).startswith('LIT:'))

    def test_delete_match_and_find_also_pop_replacement(self):
        arg_parser = ArgParser()
        arg_parser._add_argument('match=foo')
        arg_parser._add_argument('find=bar')
        arg_parser.file_queries_replacement = ['mrep', 'frep']

        arg_parser._add_argument('match=foo', True)
        self.assertEqual(arg_parser.file_queries_replacement, ['frep'])

        arg_parser._add_argument('find=bar', True)
        self.assertEqual(arg_parser.file_queries_replacement, [])

    def test_find_unicode_error_is_ignored(self):
        arg_parser = ArgParser()
        arg_parser._add_argument(r'find=\ud800')
        self.assertEqual(arg_parser.file_queries[-1][0], r'\ud800')

    def test_replace_unicode_error_is_ignored(self):
        arg_parser = ArgParser()
        arg_parser._add_argument(r'replace=\ud800')
        self.assertEqual(arg_parser.file_queries_replacement, [])

        arg_parser._add_argument('find=a')
        arg_parser._add_argument(r'replace=\ud800')
        self.assertEqual(arg_parser.file_queries_replacement, [r'\ud800'])

    def test_replace_delete_branch_idx_e_zero(self):
        arg_parser = ArgParser()
        arg_parser.file_queries_replacement = ['a', 'b', 'x']
        arg_parser._add_argument('replace=x', True)
        self.assertEqual(arg_parser.file_queries_replacement, ['a', 'b'])

    def test_replace_delete_branch_idx_e_non_zero(self):
        arg_parser = ArgParser()
        arg_parser.file_queries_replacement = ['x', 'x', 'a']
        arg_parser._add_argument('replace=x', True)
        self.assertEqual(arg_parser.file_queries_replacement, ['a', 'a', 'a'])

    def test_cut_eval_error_path(self):
        arg_parser = ArgParser()
        with patch('builtins.eval', side_effect=[1, ArithmeticError('bad'), 3]):
            arg_parser.gen_arguments(['CAT', '[1:2:3]'])
        self.assertEqual(arg_parser.get_args(), [(ARGS_CUT, (1, None, 3))])

    def test_replace_escape_comma_and_unicode_error(self):
        arg_parser = ArgParser()
        args, _, _ = arg_parser.get_arguments(['CAT', r'[left\,,right\,]'])
        self.assertEqual(args, [(ARGS_REPLACE, ('left,', 'right,'))])

        args, _, _ = arg_parser.get_arguments(['CAT', r'[\ud800,a]'])
        self.assertEqual(args, [(ARGS_REPLACE, (r'\ud800', 'a'))])

    def test_custom_command_complicated_expands_and_stops_at_echo(self):
        custom_commands = {'-1': ['-b', '-lnEwtf', 'test']}
        arg_parser = ArgParser(custom_commands=custom_commands)

        args, unknown_args, echo_args = arg_parser.get_arguments(['CAT', '-1'])
        arg_ids = [arg_id for arg_id, _ in args]
        arg_flags = [flag for _, flag in args]

        self.assertIn('-b', arg_flags)
        self.assertIn('-l', arg_flags)
        self.assertIn('-n', arg_flags)
        self.assertIn(ARGS_ECHO, arg_ids)
        self.assertNotIn('-w', arg_flags)
        self.assertNotIn('-t', arg_flags)
        self.assertNotIn('-f', arg_flags)
        self.assertEqual(unknown_args, [])
        self.assertEqual(echo_args, 'wtf test')

    def test_custom_command_complicated_keeps_echo_for_following_input(self):
        custom_commands = {'-1': ['-b', '-lnEwtf', 'test']}
        arg_parser = ArgParser(custom_commands=custom_commands)

        _, _, echo_args = arg_parser.get_arguments(['CAT', '-1', 'tail'])

        self.assertEqual(echo_args, 'wtf test tail')

    def test_custom_command_complicated(self):
        custom_commands = {'-1': ['-ln'], '-2': ['-ub']}
        arg_parser = ArgParser(custom_commands=custom_commands)

        args, unknown_args, echo_args = arg_parser.get_arguments(['CAT', '-#1!2?'])

        self.assertEqual(echo_args, '')
        self.assertListEqual(unknown_args, [])
        self.assertListEqual([v for _,v in args], ['-#', '-l', '-n', '-!', '-u', '-b', '-?'])
