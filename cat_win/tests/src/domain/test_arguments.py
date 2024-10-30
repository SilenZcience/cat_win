from unittest import TestCase

from cat_win.src.const.argconstants import ARGS_B64E, ARGS_LLENGTH
from cat_win.src.const.argconstants import ARGS_NUMBER, ARGS_ENDS, ARGS_REPLACE
from cat_win.src.domain.arguments import Arguments, reduce_list, diff_list
# import sys
# sys.path.append('../cat_win')


class TestArguments(TestCase):
    def test_setargbase64(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_B64E, '--b64e')])
        self.assertEqual(u_args[ARGS_B64E], True)
        self.assertEqual(u_args[ARGS_LLENGTH], False)
        self.assertEqual(u_args[ARGS_NUMBER], False)

    def test_add_args(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        u_args.add_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(u_args.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(len(u_args.args_id), 2)

        u_args.add_args([(ARGS_ENDS, 'c')])
        self.assertListEqual(u_args.args,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'c')])
        self.assertEqual(len(u_args.args_id), 3)

    def test_delete_args(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        u_args.delete_args([(ARGS_ENDS, 'a'), (ARGS_NUMBER, 'x')])
        self.assertListEqual(u_args.args, [(ARGS_LLENGTH, 'b')])
        self.assertEqual(len(u_args.args_id), 1)

        u_args.delete_args([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(u_args.args, [])
        self.assertEqual(len(u_args.args_id), 0)

    def test_reduce_list(self):
        test_list = [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])

        test_list += [(ARGS_NUMBER, 'c'), (ARGS_ENDS, 'd')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'd')])

        test_list += [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_NUMBER, 'c'), (ARGS_ENDS, 'd')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list,
                             [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_ENDS, 'd')])

    def test_diff_list(self):
        test_list = [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')]
        reduced_list = diff_list(test_list, [(ARGS_ENDS, 'a'), (ARGS_LLENGTH, 'c')])
        self.assertListEqual(reduced_list, [(ARGS_NUMBER, 'a')])

    def test_diff_list_differentiable(self):
        test_list = [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')]
        reduced_list = diff_list(test_list, [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[l,l]')])
        self.assertListEqual(reduced_list, [(ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')])

        test_list = [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')]
        reduced_list = diff_list(test_list, [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[a,b]')])
        self.assertListEqual(reduced_list, [(ARGS_REPLACE, '[c,a]')])
