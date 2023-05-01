from unittest import TestCase
import os

from cat_win.const.ArgConstants import *
import cat_win.util.ArgParser as ArgParser
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')



class TestArgParser(TestCase):
    maxDiff = None
    
    def tearDown(self):
        ArgParser.FILE_ENCODING = 'utf-8'
        ArgParser.FILE_MATCH = []
        ArgParser.FILE_SEARCH = []
        ArgParser.FILE_TRUNCATE = [None, None, None]
        
    def test_getArguments_empty(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_duplicate(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', '-n', '-n', '-c'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_concatenated(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', '-abcef'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_concatenated_unknown(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', '-+abce?fϵg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-e', '-f', '-g'])
        self.assertCountEqual(unknown_args, ['-+', '-?', '-ϵ'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_concatenated_invalid(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', '--abcde?fg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcde?fg'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_encoding(self):
        ArgParser.getArguments(['CAT', 'enc:ascii'])
        self.assertEqual(ArgParser.FILE_ENCODING, 'ascii')
        ArgParser.getArguments(['CAT', 'enc=utf-8'])
        self.assertEqual(ArgParser.FILE_ENCODING, 'utf-8')
        
    def test_getArguments_match(self):
        ArgParser.getArguments(['CAT', 'match:\\Atest\\Z'])
        self.assertCountEqual(ArgParser.FILE_MATCH, ['\\Atest\\Z'])
        ArgParser.getArguments(['CAT', 'match=\\Atest\\Z'])
        self.assertCountEqual(ArgParser.FILE_MATCH, ['\\Atest\\Z'] * 2)
        
    def test_getArguments_find(self):
        ArgParser.getArguments(['CAT', 'find=Test123'])
        self.assertCountEqual(ArgParser.FILE_SEARCH, ['Test123'])
        ArgParser.getArguments(['CAT', 'find:Test123'])
        self.assertCountEqual(ArgParser.FILE_SEARCH, ['Test123'] * 2)
        
    def test_getArguments_trunc(self):
        ArgParser.getArguments(['CAT', 'trunc=0:'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [0, None, None])
        ArgParser.getArguments(['CAT', 'trunc:1:'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [0, None, None])
        ArgParser.getArguments(['CAT', 'trunc:2:'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [1, None, None])
        ArgParser.getArguments(['CAT', 'trunc:::-1'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [None, None, -1])
        ArgParser.getArguments(['CAT', 'trunc:4::-5'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [3, None, -5])
        ArgParser.getArguments(['CAT', 'trunc:4:6:-5'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [3, 6, -5])
        ArgParser.getArguments(['CAT', 'trunc=:2*4-3:'])
        self.assertListEqual(ArgParser.FILE_TRUNCATE, [None, 5, None])
        
    def test_getArguments_cut(self):
        args, _, _, _, _ = ArgParser.getArguments(['CAT', '[2*5:20]'])
        self.assertCountEqual(args, [(ARGS_CUT, '[2*5:20]')])
        
    def test_getArguments_replace(self):
        args, _, _, _, _ = ArgParser.getArguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test,404]')])
        
    def test_getArguments_dir(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', test_file_dir])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, [])
        
    def test_getArguments_files_equal_dir(self):
        _, _, known_files_dir, _, _ = ArgParser.getArguments(['CAT', test_file_dir])
        _, _, known_files_files, _, _ = ArgParser.getArguments(['CAT', test_file_dir + '/**.txt'])
        self.assertCountEqual(known_files_dir, known_files_files)
        
    def test_getArguments_unknown_file(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', 'testTesttest', 'test-file.txt'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(echo_args, [])
        self.assertEqual(len(unknown_files), 2)
        self.assertIn('testTesttest', ''.join(unknown_files))
        self.assertIn('test-file.txt', ''.join(unknown_files))
        
    def test_getArguments_unknown_args(self):
        _, unknown_args, _, _, _ = ArgParser.getArguments(['CAT', '--test-file.txt'])
        self.assertCountEqual(unknown_args, ['--test-file.txt'])
        
    def test_getArguments_echo_args(self):
        args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(['CAT', '-n', '-E', '-n', 'random', test_file_dir])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        self.assertCountEqual(echo_args, ['-n', 'random', test_file_dir])
        
    def test_getArguments_echo_args_recursive(self):
        args = []
        echo = ArgParser.__addArgument__(args, [], [], [], '-nEn')
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-E'])
        self.assertEqual(echo, True)
        
    def test_deleteQueried(self):
        ArgParser.__addArgument__([], [], [], [], 'find=hello')
        ArgParser.__addArgument__([], [], [], [], 'find=world')
        self.assertListEqual(ArgParser.FILE_SEARCH, ['hello', 'world'])
        ArgParser.__addArgument__([], [], [], [], 'find=hello', True)
        self.assertListEqual(ArgParser.FILE_SEARCH, ['world'])
        
        ArgParser.__addArgument__([], [], [], [], 'match=[a-z]')
        ArgParser.__addArgument__([], [], [], [], 'match=[0-9]')
        self.assertListEqual(ArgParser.FILE_MATCH, ['[a-z]', '[0-9]'])
        ArgParser.__addArgument__([], [], [], [], 'match=[0-9]', True)
        self.assertListEqual(ArgParser.FILE_MATCH, ['[a-z]'])