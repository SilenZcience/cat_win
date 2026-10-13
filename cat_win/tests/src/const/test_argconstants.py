from unittest import TestCase

from cat_win.src.const.argconstants import ALL_ARGS, VALUE_DESCRIPTIONS
# import sys
# sys.path.append('../cat_win')


class TestArgConstants(TestCase):
    def test_unique_parameters(self):
        parameters_short_form = [x.short_form for x in ALL_ARGS]
        parameters_long_form = [x.long_form for x in ALL_ARGS if x.long_form]
        parameters_help = [x.arg_help for x in ALL_ARGS]
        parameters_id= [x.arg_id for x in ALL_ARGS if x.arg_id != -1]
        self.assertEqual(len(set(parameters_short_form)), len(parameters_short_form))
        self.assertEqual(len(set(parameters_long_form)), len(parameters_long_form))
        self.assertEqual(len(set(parameters_help)), len(parameters_help))
        self.assertEqual(len(set(parameters_id)), len(parameters_id))

    def test_no_concats(self):
        parameters_short_form = [x.short_form for x in ALL_ARGS if x.arg_id != -1]
        parameters_long_form = [x.long_form for x in ALL_ARGS if x.arg_id != -1]
        parameters = parameters_short_form + parameters_long_form
        for param in parameters:
            if not param:
                continue
            self.assertEqual(param[:1], '-')
            if not param.startswith('--') and param != '-':
                self.assertEqual(len(param), 2)

    def test_existing_value_descriptions(self):
        for arg in ALL_ARGS:
            if arg.metavar:
                self.assertIn(arg.metavar, VALUE_DESCRIPTIONS)
            if arg.takes_value:
                self.assertIn(arg.takes_value, VALUE_DESCRIPTIONS)
