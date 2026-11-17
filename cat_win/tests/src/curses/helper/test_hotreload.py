from unittest.mock import patch, MagicMock
from unittest import TestCase
import importlib.machinery
import importlib.util
import os
import sys
import tempfile

from cat_win.tests.mocks.curses import CursesMock
from cat_win.tests.mocks.logger import LoggerStub

from cat_win.src.curses import editor
from cat_win.src.curses import diffviewer
from cat_win.src.curses import hexeditor
if editor.CURSES_MODULE_ERROR:
    setattr(editor, 'curses', None)
if diffviewer.CURSES_MODULE_ERROR:
    setattr(diffviewer, 'curses', None)
if hexeditor.CURSES_MODULE_ERROR:
    setattr(hexeditor, 'curses', None)
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor
from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.helper.curseshelper import ACTION_HOTKEYS, UNIFY_HOTKEYS
from cat_win.src.curses.helper import hotreload


mm = CursesMock(error=Exception)
logger = LoggerStub()

_HELPER_V1 = 'class Helper:\n    value = 1\n'
_VIEW_V1 = (
    "from hot_pkg.helper import Helper\n"
    "\n"
    "class View:\n"
    "    flag = False\n"
    "    def __init__(self):\n"
    "        self.helper = Helper()\n"
    "        self.get_char = self.char_gen()\n"
    "    def char_gen(self):\n"
    "        return iter(['v1'])\n"
    "    def act(self):\n"
    "        return Helper.value\n"
)


@patch.object(editor, 'logger', logger)
@patch('cat_win.src.curses.editor.curses', mm)
@patch('cat_win.src.curses.hexeditor.curses', mm)
@patch('cat_win.src.curses.diffviewer.curses', mm)
class TestHotReload(TestCase):
    maxDiff = None

    def setUp(self):
        mm.reset()

    def _register_tmp_module(self, module_name: str, source: str):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        path = os.path.join(tmp_dir.name, module_name + '.py')
        with open(path, 'w', encoding='utf-8') as f_mod:
            f_mod.write(source)
        module = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(module_name, None, origin=path)
        )
        self.addCleanup(sys.modules.pop, module_name, None)
        sys.modules[module_name] = module
        return module

    def _mk_tmp_pkg(self, helper_source: str, view_source: str):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        pkg_dir = os.path.join(tmp_dir.name, 'hot_pkg')
        os.makedirs(pkg_dir)
        paths = {
            '__init__': os.path.join(pkg_dir, '__init__.py'),
            'helper'  : os.path.join(pkg_dir, 'helper.py'),
            'view'    : os.path.join(pkg_dir, 'view.py'),
        }
        for key, source in (
                ('__init__', ''), ('helper', helper_source), ('view', view_source)):
            with open(paths[key], 'w', encoding='utf-8') as f_mod:
                f_mod.write(source)
        self.addCleanup(sys.modules.pop, 'hot_pkg', None)
        self.addCleanup(sys.modules.pop, 'hot_pkg.helper', None)
        self.addCleanup(sys.modules.pop, 'hot_pkg.view', None)
        self.addCleanup(sys.path.remove, tmp_dir.name)
        sys.path.insert(0, tmp_dir.name)
        import hot_pkg.view
        return tmp_dir, paths, hot_pkg.view

    def _write(self, path: str, source: str) -> None:
        with open(path, 'w', encoding='utf-8') as f_mod:
            f_mod.write(source)

    def _mk_glue_view(self, view_type):
        view = view_type.__new__(view_type)
        view._action_render_scr = MagicMock()
        view._syntax_highlighter_key = ''
        view._syntax_highlighter = None
        view._syntax_cache = {}
        return view

    def test_hotkey_registered(self):
        self.assertEqual(UNIFY_HOTKEYS[b'KEY_F(6)'], b'_action_hot_reload')
        self.assertIn(b'_action_hot_reload', ACTION_HOTKEYS)

    def test_precheck_all_helper_modules(self):
        self.assertEqual(hotreload.precheck_modules(hotreload.HELPER_MODULES), '')

    def test_precheck_detects_syntax_error(self):
        self._register_tmp_module(
            'tmp_hotreload_badsyntax', 'def broken((:\n  pass\n')
        res = hotreload.precheck_modules(('tmp_hotreload_badsyntax',))
        self.assertTrue(res)
        self.assertIn('SyntaxError', res)

    def test_precheck_ignores_modules_without_source(self):
        module = self._register_tmp_module(
            'tmp_hotreload_synthetic', 'def broken((:\n  pass\n')
        del module.__spec__
        self.assertEqual(hotreload.precheck_modules(('tmp_hotreload_synthetic',)), '')

    def test_reload_modules_reloads_in_dependency_order(self):
        _, paths, view_module = self._mk_tmp_pkg(_HELPER_V1, _VIEW_V1)
        viewer = view_module.View()
        self.assertEqual(viewer.act(), 1)

        self._write(paths['helper'], _HELPER_V1.replace('value = 1', 'value = 2'))
        self._write(paths['view'],
                    _VIEW_V1.replace('return Helper.value',
                                     'return Helper.value * 10'))
        res = hotreload.reload_modules(('hot_pkg.helper', 'hot_pkg.view'))
        self.assertEqual(res, '')
        # the view module now references the freshly reloaded Helper;
        # (the instance still runs its old methods until hot_swap_view swaps the class)
        self.assertEqual(viewer.act(), 2)

    def test_reload_modules_skips_unknown(self):
        self.assertEqual(hotreload.reload_modules(('tmp_does_not_exist',)), '')

    def test_reload_modules_reports_failure(self):
        _, paths, _ = self._mk_tmp_pkg(_HELPER_V1, _VIEW_V1)
        self._write(paths['helper'],
                    "raise RuntimeError('reload failed on purpose')\n")
        res = hotreload.reload_modules(('hot_pkg.helper',))
        self.assertTrue(res)
        self.assertIn('RuntimeError', res)

    def test_reload_preserves_runtime_plugin_registrations(self):
        highlighter_src = (
            "class SyntaxHighlighter:\n"
            "    _plugins_by_name = {}\n"
            "    _extensions_by_name = {}\n"
            "    _plugins_by_extension = {}\n"
            "\n"
            "SyntaxHighlighter._plugins_by_name['py'] = 'tok_v1'\n"
            "SyntaxHighlighter._extensions_by_name['py'] = ('.py',)\n"
        )
        _, paths, _ = self._mk_tmp_pkg(
            _HELPER_V1 + '\n\n' + highlighter_src, _VIEW_V1)
        helper_module = sys.modules['hot_pkg.helper']
        highlighter = helper_module.SyntaxHighlighter
        # a mod registers an additional plugin at runtime
        highlighter._plugins_by_name['custom'] = 'tok_mod'
        self._write(paths['helper'],
                    (_HELPER_V1 + '\n\n' + highlighter_src)
                    .replace("'tok_v1'", "'tok_v2'"))

        self.assertEqual(hotreload.reload_modules(('hot_pkg.helper',)), '')
        fresh = sys.modules['hot_pkg.helper'].SyntaxHighlighter
        # re-executed (builtin) registration wins ...
        self.assertEqual(fresh._plugins_by_name['py'], 'tok_v2')
        # ... while runtime registered plugins survive the reload
        self.assertEqual(fresh._plugins_by_name['custom'], 'tok_mod')

    def test_hot_swap_view_applies_code_changes(self):
        _, paths, view_module = self._mk_tmp_pkg(_HELPER_V1, _VIEW_V1)
        old_cls = view_module.View
        status = []
        old_cls.flag = True
        viewer = old_cls()

        self._write(paths['helper'], _HELPER_V1.replace('value = 1', 'value = 4'))
        self._write(paths['view'],
                    _VIEW_V1.replace("return iter(['v1'])",
                                     "return iter(['v2'])"))
        res = hotreload.hot_swap_view(
            viewer, 'hot_pkg.view', 'View',
            module_names=('hot_pkg.helper', 'hot_pkg.view'),
            class_flags=('flag',),
            char_gen_method='char_gen',
            on_status=status.append
        )
        self.assertEqual(res, '')
        self.assertEqual(status, ['Hot reload: applying changes ...'])
        new_cls = sys.modules['hot_pkg.view'].View
        self.assertIsNot(new_cls, old_cls)
        self.assertIs(type(viewer), new_cls)
        # the source edit became effective on the running instance
        self.assertEqual(next(viewer.get_char), 'v2')
        self.assertEqual(viewer.act(), 4)
        # the class flags were carried over
        self.assertIs(new_cls.flag, True)

    def test_hot_swap_view_survives_broken_edits(self):
        _, paths, view_module = self._mk_tmp_pkg(_HELPER_V1, _VIEW_V1)
        viewer = view_module.View()
        current_cls = type(viewer)

        self._write(paths['helper'], 'def broken((:\n')
        res = hotreload.hot_swap_view(
            viewer, 'hot_pkg.view', 'View',
            module_names=('hot_pkg.helper', 'hot_pkg.view'),
            on_status=lambda *_: None
        )
        self.assertTrue(res)
        self.assertIn('SyntaxError', res)
        self.assertIs(type(viewer), current_cls)
        self.assertEqual(viewer.act(), 1)

    def test_hot_swap_view_reports_missing_view_module(self):
        _, _, view_module = self._mk_tmp_pkg(_HELPER_V1, _VIEW_V1)
        viewer = view_module.View()
        current_cls = type(viewer)

        res = hotreload.hot_swap_view(
            viewer, 'hot_pkg.view.unknown_submodule', 'View',
            module_names=('hot_pkg.helper',)
        )
        self.assertTrue(res)
        self.assertIn('AttributeError', res)
        self.assertIs(type(viewer), current_cls)

    def test_view_action_hot_reload_glue(self):
        cases = (
            ('cat_win.src.curses.editor', Editor, 'Editor'),
            ('cat_win.src.curses.hexeditor', HexEditor, 'HexEditor'),
            ('cat_win.src.curses.diffviewer', DiffViewer, 'DiffViewer'),
        )
        for view_module, view_type, class_name in cases:
            with self.subTest(class_name=class_name):
                view = self._mk_glue_view(view_type)
                with patch(view_module + '.hot_swap_view',
                           return_value='') as pseudo_swap, \
                     patch.object(view_type, '_run') as pseudo_run, \
                     patch.object(view_type, 'debug_mode', True):
                    # success returns False: the outdated loop frame unwinds
                    self.assertFalse(view._action_hot_reload())
                pseudo_swap.assert_called_once()
                self.assertEqual(pseudo_swap.call_args.args[1], view_module)
                self.assertEqual(pseudo_swap.call_args.args[2], class_name)
                view._action_render_scr.assert_any_call(
                    'Hot reload: applied your code changes!')
                # the outdated main loop frame is replaced by the reloaded one
                self.assertEqual(pseudo_run.call_count, 1)

    def test_view_action_hot_reload_glue_failure(self):
        cases = (
            ('cat_win.src.curses.editor', Editor),
            ('cat_win.src.curses.hexeditor', HexEditor),
            ('cat_win.src.curses.diffviewer', DiffViewer),
        )
        for view_module, view_type in cases:
            with self.subTest(view_module=view_module):
                view = self._mk_glue_view(view_type)
                renders = []
                view._action_render_scr = lambda *a, **k: renders.append(a)
                with patch(view_module + '.hot_swap_view',
                           return_value='SyntaxError: oops') as pseudo_swap, \
                     patch.object(view_type, '_run') as pseudo_run, \
                     patch.object(view_type, 'debug_mode', True):
                    self.assertTrue(view._action_hot_reload())
                pseudo_swap.assert_called_once()
                failures = [args for args in renders
                            if args and 'failed' in str(args[0])]
                self.assertEqual(len(failures), 1)
                self.assertIn('SyntaxError', failures[0][1])
                # on failure the running frame keeps looping; no re-entry
                self.assertFalse(pseudo_run.called)
