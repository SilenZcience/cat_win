from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdInMock, StdOutMock, OSAttyDefGen
from cat_win.util.service.more import More


bottom_line = '-' * 56 + 'cat_win' + '-' * 57

# @patch('os.get_terminal_size', lambda: (120, 30))
@patch('os.isatty', OSAttyDefGen.get_def({0: True, 1: True}))
@patch('sys.stdin', new=StdInMock())
class TestMore(TestCase):
    maxDiff = None

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
                self.assertEqual(fake_out.getvalue(), 'line1\n' * 29)
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

    @patch('cat_win.util.service.more.More.step_length', 2)
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
                self.assertIn('\x1b[2K\x1b[1F\x1b[2K' + str(l[n]), fake_out.getvalue())

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
                self.assertIn('\x1b[2K\x1b[1F\x1b[2K' + '\n'.join(list(map(str, range(29, max(29+n, 30))))) + '\n\n-', fake_out.getvalue())


@patch('os.isatty', OSAttyDefGen.get_def({0: True, 1: False}))
class TestMorePiped(TestCase):
    maxDiff = None

    def test_piped_output(self):
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            (More(['a'] * 100)).step_through()
            self.assertEqual('a\n' * 100, fake_out.getvalue())
