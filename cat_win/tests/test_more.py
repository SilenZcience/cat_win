from unittest import TestCase
from unittest.mock import patch

from cat_win.tests.mocks.std import StdInMock, StdOutMock
from cat_win.util.more import More


@patch('os.get_terminal_size', lambda: (120, 30))
@patch('sys.stdin', new=StdInMock())
class TestMore(TestCase):
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
            self.assertEqual(fake_out.getvalue(), 'line1\n' * 29 + 'test\n\x1b[1F\x1b[2Kline1\n')

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
            self.assertEqual(fake_out.getvalue(), 'line1\n' * 29 + '\x1b[1F\x1b[2K')

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
            self.assertEqual('a\n' * 29 + '\x1b[1F\x1b[2K' + 'a\n' * 29 + '\x1b[1F\x1b[2Ka\n' , fake_out.getvalue())

    def test_multiple_inputs_with_custom_step_size(self):
        More.setup(step_length=2)
        def input_mock_helper():
            yield ''
            yield ''

        helper = input_mock_helper()
        def input_mock(_):
            return next(helper)

        more = More(['a'] * 32)
        with patch('builtins.input', input_mock), patch('sys.stdout', new=StdOutMock()) as fake_out:
            more.step_through()
            self.assertEqual('a\n' * 29 + '\x1b[1F\x1b[2K' + 'a\na\n\x1b[1F\x1b[2Ka\n' , fake_out.getvalue())
