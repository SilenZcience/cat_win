from unittest.mock import patch
from unittest import TestCase

from cat_win.src.service.helper.winstreams import WinStreams
# import sys
# sys.path.append('../cat_win')


class TestWinStreams(TestCase):
    maxDiff = None

    @patch('cat_win.src.service.helper.winstreams.WINSTREAMS_MODULE_ERROR', True)
    def test_winstreams_module_error(self):
        ws = WinStreams(__file__)
        self.assertCountEqual(list(ws), [])

    def test_winstreams_empty(self):
        ws = WinStreams(__file__)
        self.assertCountEqual(list(ws), [])
