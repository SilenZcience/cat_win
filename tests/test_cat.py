from cat_win.util.Holder import Holder
from cat_win.cat import editFiles, color_dic
from unittest.mock import patch
from unittest import TestCase
from io import StringIO
import os
import sys
sys.path.append("../cat_win")


script_dir = os.path.dirname(__file__)
test_file_path = script_dir + "/test.txt"
test_file_content = []
with open(test_file_path, 'r') as f:
    test_file_content = f.read().splitlines()
expected_output = ""

holder = Holder()
color_dic = dict.fromkeys(color_dic, "")

@patch('cat_win.cat.holder', holder)
@patch('cat_win.cat.color_dic', color_dic)
class TestCat(TestCase):
    maxDiff = None

    def test_cat_output_default_file(self):
        holder.setFiles([test_file_path])
        holder.setArgs([])
        
        check_against = "\n".join(test_file_content) + "\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_multiple_files(self):
        holder.setFiles([test_file_path, test_file_path, test_file_path])
        holder.setArgs([])

        check_against = ("\n".join(test_file_content) +
                         "\n") * 3

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_reverse(self):
        holder.setFiles([test_file_path])
        holder.setArgs([[5, '']]) #reverse

        check_against = test_file_content
        check_against.reverse()
        check_against = ("\n".join(check_against) +
                         "\n")

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_ends_and_tabs(self):
        holder.setFiles([test_file_path])
        holder.setArgs([[2, ''], [3, '']]) #ends & tabs

        check_against = ("\n".join([c.replace("\t", "^I") + "$" for c in test_file_content]) +
                         "\n")

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

# python -m unittest discover -s tests -p test*.py
