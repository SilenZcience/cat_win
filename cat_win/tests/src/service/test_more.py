from unittest import TestCase
from unittest.mock import patch

from cat_win.src.const.colorconstants import CKW
from cat_win.tests.mocks.std import StdInMock, StdOutMock, OSAttyDefGen
from cat_win.src.service.more import More


bottom_line = '-' * 56 + 'cat_win' + '-' * 57

@patch('shutil.get_terminal_size', lambda: (120, 30))
@patch('os.isatty', OSAttyDefGen.get_def({0: True, 1: True}))
@patch('sys.stdin', new=StdInMock())
class TestMore(TestCase):
    maxDiff = None

    def setUp(self):
        self._more_state = {
            'COLOR': More.COLOR,
            'COLOR_RESET': More.COLOR_RESET,
            'step_length': More.step_length,
            't_width': More.t_width,
            't_height': More.t_height,
        }

    def tearDown(self):
        More.COLOR = self._more_state['COLOR']
        More.COLOR_RESET = self._more_state['COLOR_RESET']
        More.step_length = self._more_state['step_length']
        More.t_width = self._more_state['t_width']
        More.t_height = self._more_state['t_height']

    def test_set_flags_oserror(self):
        prev_width, prev_height = More.t_width, More.t_height
        with patch('shutil.get_terminal_size', side_effect=OSError('ioctl')):
            More.set_flags(5)
        self.assertEqual(More.step_length, 5)
        self.assertEqual(More.t_width, prev_width)
        self.assertEqual(More.t_height, prev_height)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.yield_file', lambda *_args, **_kwargs: iter(['a', 'b', 'c']))
    @patch('cat_win.src.service.more.More.t_height', 2)
    def test_lazy_load_file(self):
        more = More()
        more.lazy_load_file('dummy.txt')
        self.assertTrue(more.lazy_load)
        self.assertEqual(more.lines, ['a', 'b'])

    def test_build_file_upto_negative_to_row(self):
        more = More(['line0'])
        more.lazy_load = True
        more._f_content_gen = iter(['line1', 'line2'])

        size = more._build_file_upto(-1)

        self.assertEqual(size, 3)
        self.assertEqual(more.lines, ['line0', 'line1', 'line2'])

    def test_build_file_upto_already_loaded(self):
        more = More(['line0', 'line1'])
        more.lazy_load = True
        more._f_content_gen = iter(['line2'])

        size = more._build_file_upto(1)

        self.assertEqual(size, 2)
        # Ensure generator content was not consumed on the early-return branch.
        self.assertEqual(next(more._f_content_gen), 'line2')

    @patch('cat_win.src.service.more.More.t_width', 5)
    @patch('builtins.input', side_effect=EOFError())
    def test_pause_output_eoferror_small_width(self, _):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            self.assertEqual(More._pause_output(50, 'x', 1), '')
            self.assertIn('-----', fake_out.getvalue())

    @patch('cat_win.src.service.more.More.t_width', 10)
    @patch('os.isatty', OSAttyDefGen.get_def({0: False, 1: True}))
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_pause_output_keyboardinterrupt(self, _):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            self.assertEqual(More._pause_output(25, '', 0), 'INTERRUPT')
            # extra newline is printed for piped input or interrupt
            self.assertIn('\n', fake_out.getvalue())

    def test_yield_parts_empty_line(self):
        self.assertEqual(list(More._yield_parts('')), [''])

    @patch('cat_win.src.service.more.More.t_width', 2)
    def test_yield_parts_wrap(self):
        self.assertEqual(list(More._yield_parts('ABCD')), ['AB', 'CD'])

    @patch('cat_win.src.service.more.More.t_width', 3)
    def test_yield_parts_escape_sequence(self):
        line = f"A{chr(27)}[31mBC"
        self.assertEqual(list(More._yield_parts(line)), [line])

    @patch('cat_win.src.service.more.More.t_height', 1)
    def test_step_through_interrupt(self):
        more = More(['line1'])
        with patch('sys.stdout', new=StdOutMock()):
            with patch.object(More, '_pause_output', return_value='INTERRUPT'):
                with self.assertRaises(KeyboardInterrupt):
                    more._step_through()

    def test_output_short(self):
        more = More(['line1'])
        more.add_lines(['line2', 'line3'])
        more.add_line('line4')
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertEqual(fake_out.getvalue(), 'line1\nline2\nline3\nline4\n')

    def test_output_triggers_input(self):
        def input_mock(_):
            print('test')
            return ''

        more = More(['line1'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('line1\n' * 28 + '\n', fake_out.getvalue())
            self.assertIn(bottom_line, fake_out.getvalue())
            self.assertIn('\x1b[2K\x1b[1F\x1b[2K', fake_out.getvalue())

    def test_input_triggers_behaviour_q(self):
        def input_mock(_):
            return 'q'

        more = More(['line1'] * 30)
        with self.assertRaises(SystemExit) as se:
            with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
                more.step_through()
        self.assertIn('line1\n' * 28 + '\n', fake_out.getvalue())
        self.assertEqual(se.exception.code, 0)

    def test_input_triggers_behaviour_n(self):
        def input_mock(_):
            return 'n'

        more = More(['line1'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('line1\n' * 28 + '\n', fake_out.getvalue())
            self.assertIn(bottom_line, fake_out.getvalue())
            self.assertIn('\x1b[1F\x1b[2K' * 2, fake_out.getvalue())

    def test_input_triggers_behaviour_h(self):
        def input_mock_helper():
            yield '?'
            yield 'n'

        helper = input_mock_helper()
        def input_mock(_):
            return next(helper)

        more = More(['line1'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('skip to next file', fake_out.getvalue())


    def test_multiple_inputs(self):
        def input_mock_helper():
            yield ''
            yield ''

        helper = input_mock_helper()
        def input_mock(_):
            return next(helper)

        more = More(['a'] * 59)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertGreater(fake_out.getvalue().rfind(bottom_line), fake_out.getvalue().find(bottom_line))
            self.assertIn(bottom_line, fake_out.getvalue())

    @patch('cat_win.src.service.more.More.step_length', 2)
    def test_multiple_inputs_with_custom_step_size(self):
        def input_mock_helper():
            yield ''
            yield ''

        helper = input_mock_helper()
        def input_mock(_):
            return next(helper)

        more = More(['a'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertGreater(fake_out.getvalue().rfind(bottom_line), fake_out.getvalue().find(bottom_line))
            self.assertIn(bottom_line, fake_out.getvalue())

    def test_line(self):
        def input_mock_helper():
            yield (1, 'LINE')
            yield (2, '')
            yield (3, 'LINE')
            yield (4, 'n')

        helper = input_mock_helper()
        def input_mock(inp: str):
            c, y = next(helper)
            if c == 1:
                self.assertEqual(inp, '-- More (46%) -- ')
            elif c == 2:
                self.assertEqual(inp, "-- More (46%)[Line: 28] -- ")
            elif c == 3:
                self.assertEqual(inp, '-- More (93%) -- ')
            elif c == 4:
                self.assertEqual(inp, "-- More (93%)[Line: 56] -- ")
            return y

        more = More(['a'] * 60)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('a\n' * 28 + '\n', fake_out.getvalue())

    def test_skip_one(self):
        def input_mock(_):
            return 's1'

        more = More(['a'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('a\n' * 28 + '\n', fake_out.getvalue())
            self.assertEqual(fake_out.getvalue().replace('cat_win', '').count('a'), 29)

    def test_skip_n(self):
        for n in list(range(100)):
            def input_mock(_):
                return f"s{n}"

            more = More(['a'] * (29+n))
            with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
                more.step_through()
                self.assertIn('a\n' * 28 + '\n', fake_out.getvalue())
                self.assertEqual(fake_out.getvalue().replace('cat_win', '').count('a'), 29)

    def test_jump_n(self):
        for n in list(range(-10, 100)):
            def input_mock_helper():
                yield f"j{n}"
                yield 'n'

            helper = input_mock_helper()
            def input_mock(_):
                return next(helper)

            l = list(map(str, range(1, max(30+n, 30))))

            more = More(l)
            with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
                more.step_through()
                index = n if n < 0 else n-1 if n > 0 else n
                self.assertIn('\x1b[2K\x1b[1F\x1b[2K' + str(l[index]), fake_out.getvalue())

    def test_down_n(self):
        for n in list(range(-10, 100)):
            def input_mock_helper():
                yield f"d{n}"
                yield 'n'

            helper = input_mock_helper()
            def input_mock(_):
                return next(helper)

            more = More(list(map(str, range(1, max(31+n, 31)))))
            with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
                more.step_through()
                if n < 0:
                    self.assertIn('\x1b[2K\x1b[1F\x1b[2K' + '\n'.join(list(map(str, range(1, 29)))) + '\n\n-', fake_out.getvalue())
                    continue
                self.assertIn('\x1b[2K\x1b[1F\x1b[2K' + '\n'.join(list(map(str, range(29, max(29+n, 30))))) + '\n\n-', fake_out.getvalue())

    def test_unknown_command(self):
        def input_mock_helper():
            yield (1, 'X')
            yield (2, 'DY')
            yield (3, 'SKIP?')
            yield (4, 'J!')
            yield (5, 'n')

        helper = input_mock_helper()
        def input_mock(inp: str):
            c, y = next(helper)
            if c == 1:
                self.assertEqual(inp, '-- More (93%) -- ')
            elif c == 2:
                self.assertEqual(inp, "-- More (93%)[invalid command: X - Type 'help'] -- ")
            elif c == 3:
                self.assertEqual(inp, "-- More (93%)[invalid input: Y] -- ")
            elif c == 4:
                self.assertEqual(inp, "-- More (93%)[invalid input: ?] -- ")
            elif c == 5:
                self.assertEqual(inp, "-- More (93%)[invalid input: !] -- ")
            return y

        more = More(['a'] * 30)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertIn('a\n' * 28 + '\n', fake_out.getvalue())

    def test_set_colors(self):
        backup_color = More.COLOR
        backup_color_reset = More.COLOR_RESET
        color_dic = {
            CKW.MORE_LESS_PROMPT: 'red',
            CKW.RESET_ALL: 'reset'
        }
        More.set_colors(color_dic)
        self.assertEqual(More.COLOR, 'red')
        self.assertEqual(More.COLOR_RESET, 'reset')
        color_dic = {
            CKW.MORE_LESS_PROMPT: backup_color,
            CKW.RESET_ALL: backup_color_reset
        }
        More.set_colors(color_dic)

@patch('shutil.get_terminal_size', lambda: (120, 30))
@patch('os.isatty', OSAttyDefGen.get_def({0: True, 1: False}))
class TestMorePiped(TestCase):
    maxDiff = None

    def setUp(self):
        self._more_state = {
            'COLOR': More.COLOR,
            'COLOR_RESET': More.COLOR_RESET,
            'step_length': More.step_length,
            't_width': More.t_width,
            't_height': More.t_height,
        }

    def tearDown(self):
        More.COLOR = self._more_state['COLOR']
        More.COLOR_RESET = self._more_state['COLOR_RESET']
        More.step_length = self._more_state['step_length']
        More.t_width = self._more_state['t_width']
        More.t_height = self._more_state['t_height']

    def test_piped_output(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            (More(['a'] * 100)).step_through()
            self.assertEqual('a\n' * 100, fake_out.getvalue())
