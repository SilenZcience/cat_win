import os
import sys
sys.path.append("../cat_win")

from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from cat_win.cat import editFiles
from cat_win.util.Holder import Holder

script_dir = os.path.dirname(__file__)
test_file_dir = script_dir + "/test.txt"
test_file_content = []
with open(test_file_dir, 'r') as f:
    test_file_content = f.read().splitlines()
expected_output = ""

holder = Holder()

class TestCat(TestCase):
      
    def test_cat_output_default_file(self):
        holder.setFiles([test_file_dir])
        expected_output = "\n".join(test_file_content) + "\n"
        
        with patch('sys.stdout', new = StringIO()) as fake_out:
            editFiles(holder)
            self.assertEqual(fake_out.getvalue(), expected_output)
            
    def test_cat_output_multiple_files(self):
        holder.setFiles([test_file_dir, test_file_dir, test_file_dir])
        
        expected_output = ("\n".join(test_file_content) + "\n") * 3
        
        with patch('sys.stdout', new = StringIO()) as fake_out:
            editFiles(holder)
            self.assertEqual(fake_out.getvalue(), expected_output)



#python -m unittest discover -s tests -p test*.py