from unittest.mock import patch
from unittest import TestCase

from cat_win import cat
from cat_win.tests.mocks.std import StdInHelperMock, StdOutMock
from cat_win.util.holder import Holder
# import sys
# sys.path.append('../cat_win')
stdinhelpermock = StdInHelperMock()


@patch('cat_win.cat.sys.argv', ['<CAT>'])
@patch('cat_win.cat.stdinhelper.get_stdin_content', stdinhelpermock.get_stdin_content)
class TestShell(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()
        cat.holder = Holder()

    def test_cat_shell_output_unchanged(self):
        stdinhelpermock.set_content('abc\nxyz')
        expected_output = ['abc', 'xyz']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_line_count(self):
        stdinhelpermock.set_content('test1\n!add -n\n!help\ntest2')
        expected_output = ['2) test2']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[-2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_unknown_param(self):
        wrong_cmd = '!xyz'
        stdinhelpermock.set_content(wrong_cmd)
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            self.assertIn(wrong_cmd, fake_out.getvalue())

    def test_cat_shell_help_param(self):
        stdinhelpermock.set_content('!help')
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            self.assertIn('!add', fake_out.getvalue())
            self.assertIn('!del', fake_out.getvalue())
            self.assertIn('!see', fake_out.getvalue())

    def test_cat_shell_add_param(self):
        stdinhelpermock.set_content('abc\n!add -ln\nabc')
        expected_output = ['abc', "successfully added ['-l', '-n'].", '2) [3] abc']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_delete_param(self):
        stdinhelpermock.set_content('abc\n!add -ln\n!del -l\nabc')
        expected_output = ['abc', "successfully added ['-l', '-n'].", "successfully removed ['-l'].", '2) abc']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_see_param(self):
        stdinhelpermock.set_content('!add -ln find=test match=[0-9]\n!see')
        expected_output = ["successfully added ['-l', '-n'].", "Active Args: ['-l', '-n']",
                           "Literals:    {'test'}", "Matches:     {'[0-9]'}"]
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_clear_param(self):
        stdinhelpermock.set_content('!add -ln find=test match=[0-9]\n!see\n!clear\n!see')
        expected_output = ["successfully added ['-l', '-n'].", "Active Args: ['-l', '-n']",
                           "Literals:    {'test'}", "Matches:     {'[0-9]'}",
                           "successfully removed ['-l', '-n'].", 'Active Args: []']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_exit(self):
        stdinhelpermock.set_content('abc\n!exit\nabc')
        expected_output = ['abc']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_cmd_escape(self):
        stdinhelpermock.set_content('\\!exit\ntest')
        expected_output = ['!exit', 'test']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

        stdinhelpermock.set_content('\\' * 5 + 'test')
        expected_output = ['\\' * 4 + 'test']
        with patch('cat_win.cat.sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)
