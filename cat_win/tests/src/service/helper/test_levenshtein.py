from unittest import TestCase

from cat_win.src.const.argconstants import ALL_ARGS
from cat_win.src.service.helper.levenshtein import levenshtein, calculate_suggestions
# import sys
# sys.path.append('../cat_win')
# if shell:
#     arg_options = [(arg.short_form, arg.long_form)
#                     for arg in ALL_ARGS if arg.show_arg_on_shell]
# else:
#     arg_options = [(arg.short_form, arg.long_form)
#                     for arg in ALL_ARGS]

class TestLevenshtein(TestCase):
    maxDiff = None

    def test_levenshtein(self):
        self.assertEqual(levenshtein('-a', '-b'), 0.0)
        self.assertEqual(levenshtein('', ''), 100.0)
        self.assertEqual(levenshtein('', 'test'), 0.0)
        self.assertEqual(levenshtein('abc', ''), 0.0)
        self.assertAlmostEqual(levenshtein('The dog sat on the cat', 'The cat sat on the mat'),
                               81.8181, 3)
        self.assertAlmostEqual(levenshtein('lower!', 'LOWER?'), 83.3333, 3)
        self.assertAlmostEqual(levenshtein('--hecksview', '--hexview'), 66.6666, 3)

    def test_calculate_suggestions(self):
        result = [('--sord', [('--sort', 75.0)]),
                  ('--b64', [('--b64d', 75.0), ('--b64e',  75.0)]),
                  ('--blq4k', [('--blank', 60.0)]),
                  ('--UNIQUE', [('--unique', 100.0)])]
        self.assertListEqual(calculate_suggestions(['--sord', '--b64', '--blq4k', '--UNIQUE'],
                                                   [(arg.short_form, arg.long_form)
                                                    for arg in ALL_ARGS]),
                             result)
        result = [('--sord', []),
                  ('--b64', [('--b64d', 75.0), ('--b64e',  75.0)]),
                  ('--blq4k', [('--blank', 60.0)]),
                  ('--UNIQUE', [])]
        self.assertListEqual(calculate_suggestions(['--sord', '--b64', '--blq4k', '--UNIQUE'],
                                                   [(arg.short_form, arg.long_form)
                                                    for arg in ALL_ARGS if arg.show_arg_on_shell]),
                             result)
