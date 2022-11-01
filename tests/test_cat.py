from cat_win.util.Holder import Holder
from cat_win.cat import editFiles
from unittest.mock import patch
from unittest import TestCase
from io import StringIO
import os
import sys
sys.path.append("../cat_win")


script_dir = os.path.dirname(__file__)
test_file_dir = script_dir + "/test.txt"
test_file_content = []
with open(test_file_dir, 'r') as f:
    test_file_content = f.read().splitlines()
expected_output = ""

holder = Holder()


@patch('cat_win.cat.holder', holder)
class TestCat(TestCase):
    maxDiff = None

    def test_cat_output_default_file(self):
        holder.setFiles([test_file_dir])
        holder.setArgs([])

        check_against = "\n".join(test_file_content) + "\n" + "\x1b[0m\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_multiple_files(self):
        holder.setFiles([test_file_dir, test_file_dir, test_file_dir])
        holder.setArgs([])

        check_against = ("\n".join(test_file_content) +
                         "\n") * 3 + "\x1b[0m\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_reverse(self):
        holder.setFiles([test_file_dir])
        holder.setArgs([[5, '']])

        check_against = test_file_content
        check_against.reverse()
        check_against = ("\n".join(check_against) +
                         "\n") + "\x1b[0m\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

    def test_cat_output_ends_and_tabs(self):
        holder.setFiles([test_file_dir])
        holder.setArgs([[2, ''], [3, '']])

        check_against = ("\n".join([c.replace("\t", "^I" + "\x1b[0m") + "$" + "\x1b[0m" for c in test_file_content]) +
                         "\n") + "\x1b[0m\n"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            editFiles()
            self.assertEqual(fake_out.getvalue(), check_against)

# python -m unittest discover -s tests -p test*.py
