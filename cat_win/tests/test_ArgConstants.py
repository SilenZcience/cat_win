from unittest import TestCase

from cat_win.const.ArgConstants import *
# import sys
# sys.path.append('../cat_win')


class TestArgConstants(TestCase):
    def test_unique_parameters(self):
        parameters_shortForm = [x.shortForm for x in ALL_ARGS]
        parameters_longForm = [x.longForm for x in ALL_ARGS]
        parameters_help = [x.help for x in ALL_ARGS]
        parameters_id= [x.id for x in ALL_ARGS]
        self.assertEqual(len(set(parameters_shortForm)), len(parameters_shortForm))
        self.assertEqual(len(set(parameters_longForm)), len(parameters_longForm))
        self.assertEqual(len(set(parameters_help)), len(parameters_help))
        self.assertEqual(len(set(parameters_id)), len(parameters_id))
        
    def test_no_concats(self):
        parameters_shortForm = [x.shortForm for x in ALL_ARGS]
        parameters_longForm = [x.longForm for x in ALL_ARGS]
        parameters = parameters_shortForm + parameters_longForm
        for param in parameters:
            self.assertEqual(param[:1], '-')
            if not param.startswith('--'):
                self.assertEqual(len(param), 2)