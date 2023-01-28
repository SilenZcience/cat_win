from cat_win.util.Holder import Holder
import cat_win.cat as cat
from unittest.mock import patch
from unittest import TestCase
from io import StringIO
import os
# import sys
# sys.path.append("../cat_win")


test_file_dir = os.path.dirname(__file__) + '/texts/'
test_file_path = test_file_dir + "test.txt"
test_file_content = []
with open(test_file_path, 'r', encoding='utf-8') as f:
    test_file_content = f.read().split('\n')


holder = Holder()

@patch('cat_win.cat.holder', holder)
@patch('cat_win.cat.color_dic', dict.fromkeys(cat.color_dic, ""))
class TestCat(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._CalculateLinePrefixSpacing.cache_clear()
        cat._CalculateLineLengthPrefixSpacing.cache_clear()
    
    def test_cat_output_default_file(self):
        holder.setFiles([test_file_path])
        holder.setArgs([])
        
        check_against = "\n".join(test_file_content) + "\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            cat.editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_multiple_files(self):
        holder.setFiles([test_file_path, test_file_path, test_file_path])
        holder.setArgs([])

        check_against = ("\n".join(test_file_content) +
                         "\n") * 3

        with patch('sys.stdout', new=StringIO()) as fake_out:
            cat.editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_reverse(self):
        holder.setFiles([test_file_path])
        holder.setArgs([[5, '']]) #reverse

        check_against = test_file_content
        check_against.reverse()
        check_against = ("\n".join(check_against) +
                         "\n")

        with patch('sys.stdout', new=StringIO()) as fake_out:
            cat.editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_ends_and_tabs(self):
        holder.setFiles([test_file_path])
        holder.setArgs([[2, ''], [3, '']]) #ends & tabs

        check_against = ("\n".join([c.replace("\t", "^I") + "$" for c in test_file_content]) +
                         "\n")

        with patch('sys.stdout', new=StringIO()) as fake_out:
            cat.editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)
            
    def test_cat__getLinePrefix_file_excess(self):
        holder.fileLineNumberPlaceHolder = 5
        self.assertEqual(cat._getLinePrefix(9, 1), '    9) ')
        
    def test_cat__getLinePrefix_file_occupied(self):
        holder.fileLineNumberPlaceHolder = 2
        self.assertEqual(cat._getLinePrefix(10, 1), '10) ')
    
    def test_cat__getLinePrefix_file_excess_long(self):
        holder.fileLineNumberPlaceHolder = 12
        self.assertEqual(cat._getLinePrefix(34719, 1), '       34719) ')
    
    def test_cat__getLinePrefix_file_occupied_long(self):
        holder.fileLineNumberPlaceHolder = 5
        self.assertEqual(cat._getLinePrefix(34718, 1), '34718) ')
        
    def test_cat__getLinePrefix_files_excess(self):
        holder.fileLineNumberPlaceHolder = 5
        holder.fileNumberPlaceHolder = 4
        holder.files = [1,2]
        self.assertEqual(cat._getLinePrefix(9, 1), '   1.    9) ')
        
    def test_cat__getLinePrefix_files_occupied(self):
        holder.fileLineNumberPlaceHolder = 3
        holder.fileNumberPlaceHolder = 2
        holder.files = [1,2]
        self.assertEqual(cat._getLinePrefix(987, 10), '10.987) ')
        
    def test_cat__getLinePrefix_files_excess_long(self):
        holder.fileLineNumberPlaceHolder = 12
        holder.fileNumberPlaceHolder = 10
        holder.files = [1,2]
        self.assertEqual(cat._getLinePrefix(101, 404), '       404.         101) ')
        
    def test_cat__getLinePrefix_files_occupied_long(self):
        holder.fileLineNumberPlaceHolder = 11
        holder.fileNumberPlaceHolder = 9
        holder.files = [1,2]
        self.assertEqual(cat._getLinePrefix(12345123451, 123456789), '123456789.12345123451) ')
    
    def test_cat__getLineLengthPrefix_string_excess(self):
        holder.fileLineLengthPlaceHolder = 5
        holder.setArgs([])
        self.assertEqual(cat._getLineLengthPrefix('testtest', 'abcdefghi'), 'testtest[    9] ')
    
    def test_cat__getLineLengthPrefix_string_occupied(self):
        holder.fileLineLengthPlaceHolder = 2
        holder.setArgs([])
        self.assertEqual(cat._getLineLengthPrefix('prefix', 'abcdefghij'), 'prefix[10] ')
        
    def test_cat__getLineLengthPrefix_bytes_excess(self):
        holder.fileLineLengthPlaceHolder = 5
        holder.setArgs([])
        self.assertEqual(cat._getLineLengthPrefix('testtest', b'abcdefghi'), 'testtest[    9] ')
    
    def test_cat__getLineLengthPrefix_bytes_occupied(self):
        holder.fileLineLengthPlaceHolder = 2
        holder.setArgs([])
        self.assertEqual(cat._getLineLengthPrefix('prefix', b'abcdefghij'), 'prefix[10] ')

# python -m unittest discover -s tests -p test*.py
