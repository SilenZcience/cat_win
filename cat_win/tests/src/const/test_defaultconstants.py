from unittest import TestCase

from cat_win.src.const.defaultconstants import DKW


class TestDefaultConstants(TestCase):
    def test_default_constants(self):
        self.assertEqual(DKW.DEFAULT_COMMAND_LINE, 'default_command_line')
