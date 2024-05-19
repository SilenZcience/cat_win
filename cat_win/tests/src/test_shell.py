from unittest.mock import patch
from unittest import TestCase

from cat_win.src import cat
from cat_win.tests.mocks.std import IoHelperMock, StdOutMock, StdInMock, OSAttyDefGen
from cat_win.src.persistence.cconfig import CConfig
from cat_win.src.persistence.config import Config
# import sys
# sys.path.append('../cat_win')
stdinhelpermock = IoHelperMock()


@patch('sys.argv', ['<CAT>'])
@patch('cat_win.src.service.helper.iohelper.IoHelper.get_stdin_content', stdinhelpermock.get_stdin_content)
@patch('cat_win.src.cat.cconfig.load_config', lambda: dict.fromkeys(CConfig.default_dic, ''))
@patch('cat_win.src.cat.config.load_config', lambda: Config.default_dic.copy())
@patch('sys.stdin', StdInMock())
@patch('os.isatty', OSAttyDefGen.get_def({0: True}))
class TestShell(TestCase):
    maxDiff = None

    def tearDown(self):
        cat._calculate_line_prefix_spacing.cache_clear()
        cat._calculate_line_length_prefix_spacing.cache_clear()

    def test_cat_shell_output_unchanged(self):
        stdinhelpermock.set_content('abc\nxyz')
        expected_output = ['abc', 'xyz']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_line_count(self):
        stdinhelpermock.set_content('test1\n!add -n\n!help\ntest2')
        expected_output = ['2) test2']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[-2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_unknown_param(self):
        wrong_cmd = '!xyz'
        stdinhelpermock.set_content(wrong_cmd)
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            self.assertIn(wrong_cmd, fake_out.getvalue())

    def test_cat_shell_help_param(self):
        stdinhelpermock.set_content('!help')
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            self.assertIn('!add', fake_out.getvalue())
            self.assertIn('!del', fake_out.getvalue())
            self.assertIn('!see', fake_out.getvalue())

    def test_cat_shell_add_param(self):
        stdinhelpermock.set_content('abc\n!add -ln\nabc')
        expected_output = ['abc', "successfully added ['-l', '-n'].", '2) [3] abc']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_delete_param(self):
        stdinhelpermock.set_content('abc\n!add -ln\n!del -l\nabc')
        expected_output = ['abc', "successfully added ['-l', '-n'].",
                        "successfully removed ['-l'].", '2) abc']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_see_param(self):
        stdinhelpermock.set_content('!add -ln FIND=test match=[0-9]\n!see')
        expected_output = ["successfully added ['-l', '-n'].", "Active Args: ['-l', '-n']",
                           "Literals:    [('test', 'CI')]", "Matches:     {re.compile('[0-9]', re.DOTALL)}"]
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_clear_param(self):
        stdinhelpermock.set_content('!add -ln find=test match=[0-9]\n!see\n!clear\n!see')
        expected_output = ["successfully added ['-l', '-n'].", "Active Args: ['-l', '-n']",
                           "Literals:    [('test', 'CS')]", "Matches:     {re.compile('[0-9]', re.DOTALL)}",
                           "successfully removed ['-l', '-n'].", 'Active Args: []']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_exit(self):
        stdinhelpermock.set_content('abc\n!exit\nabc')
        expected_output = ['abc']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

    def test_cat_shell_cmd_escape(self):
        stdinhelpermock.set_content('\\!exit\ntest')
        expected_output = ['!exit', 'test']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)

        stdinhelpermock.set_content('\\' * 5 + 'test')
        expected_output = ['\\' * 4 + 'test']
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            cat.shell_main()
            fake_output = [line.lstrip('>>> ') for line in fake_out.getvalue().splitlines()[2:-1]]
            self.assertListEqual(fake_output, expected_output)
