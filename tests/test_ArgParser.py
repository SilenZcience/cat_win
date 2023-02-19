import cat_win.util.ArgParser as ArgParser
from cat_win.const.ArgConstants import *
from unittest import TestCase
# import sys
# sys.path.append("../cat_win")


class TestArgParser(TestCase):
    maxDiff = None
    
    def tearDown(self):
        ArgParser.FILE_ENCODING = 'utf-8'
        ArgParser.FILE_MATCH = []
        ArgParser.FILE_SEARCH = []
        ArgParser.FILE_TRUNCATE = [None, None, None]
        
    def test_getArguments_empty(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_duplicate(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', '-n', '-n', '-c'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-n', '-c', '-n'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_concatenated(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', '-abcdef'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-d', '-e', '-f'])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_concatenated_unknown(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', '-+abcde?fg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, ['-a', '-b', '-c', '-d', '-e', '-f'])
        self.assertCountEqual(unknown_args, ['-+', '-?', '-g'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_concatenated_invalid(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', '--abcde?fg'])
        args = list(map(lambda x: x[1], args))
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, ['--abcde?fg'])
        self.assertCountEqual(known_files, [])
        self.assertCountEqual(unknown_files, [])
        
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
        args, _, _, _ = ArgParser.getArguments(['CAT', '[2*5:20]'])
        self.assertCountEqual(args, [(ARGS_CUT, '[2*5:20]')])
        
    def test_getArguments_replace(self):
        args, _, _, _ = ArgParser.getArguments(['CAT', '[test,404]'])
        self.assertCountEqual(args, [(ARGS_REPLACE, '[test,404]')])
        
    def test_getArguments_dir(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', './tests/texts/'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_files(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', '**/tests/texts/**.txt'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertGreaterEqual(len(known_files), 7)
        self.assertCountEqual(unknown_files, [])
        
    def test_getArguments_files_equal_dir(self):
        _, _, known_files_dir, _ = ArgParser.getArguments(['CAT', './tests/texts/'])
        _, _, known_files_files, _ = ArgParser.getArguments(['CAT', '**/tests/texts/**.txt'])
        self.assertCountEqual(known_files_dir, known_files_files)
        
    def test_getArguments_unknown_file(self):
        args, unknown_args, known_files, unknown_files = ArgParser.getArguments(['CAT', 'testTesttest', 'test-file.txt'])
        self.assertCountEqual(args, [])
        self.assertCountEqual(unknown_args, [])
        self.assertCountEqual(known_files, [])
        self.assertEqual(len(unknown_files), 2)
        self.assertIn('testTesttest', ''.join(unknown_files))
        self.assertIn('test-file.txt', ''.join(unknown_files))
        
    def test_getArguments_unknown_args(self):
        _, unknown_args, _, _ = ArgParser.getArguments(['CAT', '--test-file.txt'])
        self.assertCountEqual(unknown_args, ['--test-file.txt'])