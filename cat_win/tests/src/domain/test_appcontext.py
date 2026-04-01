from unittest import TestCase

from cat_win.src.argparser import ArgParser
from cat_win.src.domain.appcontext import AppContext
from cat_win.src.domain.arguments import Arguments
from cat_win.src.domain.files import Files
from cat_win.src.persistence.cconfig import CConfig
from cat_win.src.persistence.config import Config


class TestAppContext(TestCase):
    def test_appcontext_init(self):
        app_context = AppContext()

        self.assertIsNotNone(app_context.cconfig)
        self.assertIsInstance(app_context.cconfig, CConfig)
        self.assertIsNotNone(app_context.config)
        self.assertIsInstance(app_context.config, Config)
        self.assertEqual(app_context.default_color_dic, {})
        self.assertEqual(app_context.color_dic, {})
        self.assertEqual(app_context.const_dic, {})
        self.assertIsNone(app_context.arg_parser)
        self.assertIsNotNone(app_context.u_args)
        self.assertIsInstance(app_context.u_args, Arguments)
        self.assertIsNotNone(app_context.u_files)
        self.assertIsInstance(app_context.u_files, Files)
        self.assertEqual(app_context.args, [])
        self.assertEqual(app_context.unknown_args, [])
        self.assertEqual(app_context.known_files, [])
        self.assertEqual(app_context.unknown_files, [])
        self.assertEqual(app_context.valid_urls, [])
        self.assertEqual(app_context.known_dirs, [])
        self.assertEqual(app_context.echo_args, '')

    def test_appcontext_init_method(self):
        app_context = AppContext()
        app_context.init()

        self.assertIsNotNone(app_context.default_color_dic)
        self.assertIsNotNone(app_context.color_dic)
        self.assertIsNotNone(app_context.const_dic)
        self.assertIsNotNone(app_context.arg_parser)
        self.assertIsInstance(app_context.arg_parser, ArgParser)
