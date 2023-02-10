from cat_win.const.ArgConstants import *
from unittest import TestCase
# import sys
# sys.path.append("../cat_win")


class TestConverter(TestCase):
    def test_unique_parameters(self):
        parameters_shortForm = [x.shortForm for x in ALL_ARGS]
        parameters_longForm = [x.longForm for x in ALL_ARGS]
        parameters_help = [x.help for x in ALL_ARGS]
        parameters_id= [x.id for x in ALL_ARGS]
        self.assertEqual(len(set(parameters_shortForm)), len(parameters_shortForm))
        self.assertEqual(len(set(parameters_longForm)), len(parameters_longForm))
        self.assertEqual(len(set(parameters_help)), len(parameters_help))
        self.assertEqual(len(set(parameters_id)), len(parameters_id))