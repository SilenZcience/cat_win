from unittest.mock import patch, MagicMock
from unittest import TestCase

from cat_win.src.service.helper.tmpfilehelper import TmpFileHelper
# import sys
# sys.path.append('../cat_win')


@patch('tempfile.NamedTemporaryFile', MagicMock())
class TestTmpFileHelper(TestCase):
    maxDiff = None

    def test_tmpfilehelper(self):
        tfh = TmpFileHelper()
        self.assertCountEqual(tfh.get_generated_temp_files(), [])
        tfh.generate_temp_file_name()
        tfh.generate_temp_file_name()
        self.assertEqual(tfh.tmp_count, 2)
        self.assertEqual(len(tfh.tmp_files), 2)
        tfh.generate_temp_file_name()
        self.assertEqual(tfh.tmp_count, 3)
        self.assertEqual(len(tfh.tmp_files), 3)
