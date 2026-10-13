from unittest import TestCase

from cat_win.src.const.argconstants import ARGS_B64E, ARGS_LLENGTH
from cat_win.src.const.argconstants import ARGS_NUMBER, ARGS_ENDS, ARGS_REPLACE
from cat_win.src.const.argconstants import ARGS_CUT
from cat_win.src.const.argconstants import ARGS_COMPLETION
from cat_win.src.domain.arguments import Arguments, Param, reduce_list, diff_list
# import sys
# sys.path.append('../cat_win')


class TestParam(TestCase):
    def test_is_a_string_in_every_regard(self):
        param = Param('--completion', 'bash')
        self.assertIsInstance(param, str)
        self.assertEqual(param, '--completion')
        self.assertEqual(str(param), '--completion')
        self.assertEqual(repr(param), repr('--completion'))
        self.assertEqual('{0}'.format(param), '--completion')
        self.assertEqual('--completion {0}'.format(param), '--completion --completion')
        self.assertEqual(param.startswith('--comp'), True)
        self.assertEqual(param.split('='), ['--completion'])
        self.assertEqual({'--completion': 1}[param], 1)
        self.assertEqual([p for p in param], list('--completion'))

    def test_carries_its_argument(self):
        self.assertEqual(Param('--completion', 'bash').argument, 'bash')
        self.assertEqual(Param('--number', '3').argument, '3')
        self.assertIsNone(Param('--completion').argument)

    def test_argument_does_not_make_it_an_arbitrary_string(self):
        with self.assertRaises(AttributeError):
            Param('--completion').nonsense = 1

    def test_equal_params_compare_by_param_alone(self):
        self.assertEqual(Param('--completion', 'bash'), Param('--completion', 'fish'))


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

    def test_find_first(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertTupleEqual(u_args.find_first(ARGS_NUMBER, ARGS_LLENGTH, False), (ARGS_NUMBER, 'a'))
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertTupleEqual(u_args.find_first(ARGS_LLENGTH, ARGS_NUMBER, False), (ARGS_NUMBER, 'a'))
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_ENDS, 'c')])
        self.assertTupleEqual(u_args.find_first(ARGS_NUMBER, ARGS_LLENGTH, False), (ARGS_NUMBER, 'a'))
        u_args = Arguments()
        u_args.set_args([(ARGS_ENDS, 'c'), (ARGS_LLENGTH, 'b')])
        self.assertTupleEqual(u_args.find_first(ARGS_LLENGTH, ARGS_NUMBER, False), (ARGS_LLENGTH, 'b'))
        u_args = Arguments()
        u_args.set_args([(ARGS_ENDS, 'c')])
        self.assertEqual(u_args.find_first(ARGS_LLENGTH, ARGS_NUMBER, False), None)
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertTupleEqual(u_args.find_first(ARGS_NUMBER, ARGS_LLENGTH, True), (ARGS_NUMBER, 'a'))
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(u_args.find_first(ARGS_LLENGTH, ARGS_NUMBER, True), None)
        u_args = Arguments()
        u_args.set_args([(ARGS_ENDS, 'c')])
        self.assertEqual(u_args.find_first(ARGS_LLENGTH, ARGS_NUMBER, True), None)

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

    def test_reduce_list_differentiable(self):
        test_list = [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')]
        reduced_list = reduce_list(test_list)
        self.assertListEqual(reduced_list, [(ARGS_REPLACE, '[a,b]'), (ARGS_REPLACE, '[c,a]'), (ARGS_REPLACE, '[a,b]')])

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

    def test_len(self):
        u_args = Arguments()
        self.assertEqual(len(u_args), 0)
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(len(u_args), 2)

    def test_iter(self):
        u_args = Arguments()
        self.assertListEqual(list(u_args), [])
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(list(u_args), [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])

    def test_getitem(self):
        u_args = Arguments()
        self.assertEqual(u_args[ARGS_NUMBER], False)
        u_args.set_args([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(u_args[ARGS_NUMBER], True)
        self.assertEqual(u_args[ARGS_LLENGTH], True)
        self.assertEqual(u_args[ARGS_ENDS], False)

    def test_find_arg_value(self):
        u_args = Arguments()
        self.assertIsNone(u_args.find_arg_value(ARGS_NUMBER))
        u_args.set_args([(ARGS_NUMBER, '-n'), (ARGS_LLENGTH, '-l')])
        self.assertEqual(u_args.find_arg_value(ARGS_NUMBER), '-n')
        self.assertEqual(u_args.find_arg_value(ARGS_LLENGTH), '-l')
        self.assertIsNone(u_args.find_arg_value(ARGS_ENDS))

    def test_find_arg_value_returns_the_argument(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_COMPLETION, Param('--completion', 'bash'))])
        self.assertEqual(u_args[ARGS_COMPLETION], True)
        self.assertEqual(u_args.find_arg_value(ARGS_COMPLETION), 'bash')

    def test_find_arg_value_is_none_for_a_param_without_an_argument(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_COMPLETION, Param('--completion'))])
        self.assertEqual(u_args[ARGS_COMPLETION], True)
        self.assertIsNone(u_args.find_arg_value(ARGS_COMPLETION))

    def test_find_arg_value_is_the_index1_value_when_it_is_not_a_param(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_CUT, ('1', '3', None))])
        self.assertEqual(u_args.find_arg_value(ARGS_CUT), ('1', '3', None))

    def test_find_arg_value_tracks_add_and_delete(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, '-n')])
        self.assertEqual(u_args.find_arg_value(ARGS_NUMBER), '-n')

        u_args.add_args([(ARGS_LLENGTH, '-l')])
        self.assertEqual(u_args.find_arg_value(ARGS_LLENGTH), '-l')
        self.assertEqual(u_args.find_arg_value(ARGS_NUMBER), '-n')

        u_args.delete_args([(ARGS_LLENGTH, '-l')])
        self.assertIsNone(u_args.find_arg_value(ARGS_LLENGTH))
        self.assertEqual(u_args.find_arg_value(ARGS_NUMBER), '-n')

    def test_find_arg_value_returns_first_for_duplicates(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_CUT, 'a'), (ARGS_CUT, 'b')])
        self.assertEqual(u_args.find_arg_value(ARGS_CUT), 'a')

    def test_set_args_replaces_rather_than_accumulates(self):
        u_args = Arguments()
        u_args.set_args([(ARGS_NUMBER, '-n'), (ARGS_ENDS, '-e')])
        u_args.set_args([(ARGS_LLENGTH, '-l')])
        self.assertIsNone(u_args.find_arg_value(ARGS_NUMBER))
        self.assertIsNone(u_args.find_arg_value(ARGS_ENDS))
        self.assertEqual(u_args.find_arg_value(ARGS_LLENGTH), '-l')
