"""
hotreload
"""

import importlib
import os
import sys


# the shared helper modules the editor based views rely on
# (order matters, dependencies get reloaded first)
HELPER_MODULES = (
    'cat_win.src.curses.helper.syntaxhighlight',
    'cat_win.src.curses.helper.diffviewerhelper',
    'cat_win.src.curses.helper.editorsearchhelper',
    'cat_win.src.curses.helper.githelper',
    'cat_win.src.curses.helper.curseshelper',
    'cat_win.src.curses.helper.fileselectionhelper',
)

# every view gets reloaded so that
# all in-process references stay in sync after a reload
VIEW_MODULES = (
    'cat_win.src.curses.editor',
    'cat_win.src.curses.hexeditor',
    'cat_win.src.curses.diffviewer',
)


def precheck_modules(module_names: tuple) -> str:
    """
    syntax-check the source files of the given modules without reloading
    them, so that outdated code does not break the running editor.

    Parameters:
    module_names (tuple):
        names of the modules to check

    Returns:
    (str):
        empty on success, otherwise a description of the first error
    """
    for module_name in module_names:
        module = sys.modules.get(module_name)
        origin = getattr(getattr(module, '__spec__', None), 'origin', None)
        if not module or not origin or not os.path.isfile(origin):
            continue  # module not imported or without a source file
        try:
            with open(origin, 'rb') as f_module_src:
                compile(f_module_src.read(), origin, 'exec')
        except (SyntaxError, ValueError) as exc:
            return f'{type(exc).__name__}: {exc}'
    return ''


def _drop_bytecode_cache(module) -> None:
    cached = getattr(module, '__cached__', None)
    # only remove the bytecode cache if the target is a source file
    if not cached or not cached.endswith('.pyc'):
        return
    try:
        os.remove(cached)
    except OSError:
        pass


# registries of SyntaxHighlighter plugins.
# used to merge potentially modded entries back
_PLUGIN_REGISTRIES = (
    '_plugins_by_name',
    '_extensions_by_name',
    '_plugins_by_extension',
)


def _stash_plugin_registries(module):
    highlighter = getattr(module, 'SyntaxHighlighter', None)
    stashed = {
        name: dict(getattr(highlighter, name, {}))
        for name in _PLUGIN_REGISTRIES
        if isinstance(getattr(highlighter, name, None), dict)
    }
    return stashed or None


def _restore_plugin_registries(module, stashed: dict) -> None:
    highlighter = getattr(module, 'SyntaxHighlighter', None)
    if highlighter is None:
        return
    for name, entries in stashed.items():
        registry = getattr(highlighter, name, None)
        if isinstance(registry, dict):
            for key, value in entries.items():
                registry.setdefault(key, value)


def reload_modules(module_names: tuple) -> str:
    """
    dynamically reload the given modules in place, keeping the
    already initialized instances/objects alive.

    Parameters:
    module_names (tuple):
        names of the modules to reload, in dependency order

    Returns:
    (str):
        empty on success, otherwise a description of the first error
    """
    for module_name in module_names:
        module = sys.modules.get(module_name)
        if module is None:
            continue
        stashed_registries = _stash_plugin_registries(module)
        _drop_bytecode_cache(module)
        try:
            importlib.reload(module)
        except Exception as exc:
            return f'{type(exc).__name__}: {exc}'
        if stashed_registries is not None:
            _restore_plugin_registries(module, stashed_registries)
    return ''


def hot_swap_view(
        view_obj,
        view_module_name: str,
        class_name: str,
        module_names: tuple = None,
        class_flags: tuple = (),
        char_gen_method: str = '',
        on_status=None
) -> str:
    """
    dynamically reload the curses applications and apply the changes
    to the given running view object.

    Parameters:
    view_obj (Diffviewer | Editor | HexEditor):
        the currently running view object to apply the changes to
    view_module_name (str):
        the module name the view object class is defined in
    class_name (str):
        the name of the class defined within the view module
    module_names (tuple):
        names of the modules to reload in dependency order;
        defaults to all editor based views and their shared helpers
    class_flags (tuple):
        names of class attributes (set via set_flags/set_indentation)
        to carry over to the reloaded class
    char_gen_method (str):
        optional name of the key reading generator method, recreated
        on the view object after the swap ('get_char')
    on_status (callable):
        optional callback receiving the 'applying changes' status message

    Returns:
    (str):
        empty on success, otherwise a description of the first error.
        on error the view object is left untouched
    """
    if module_names is None:
        module_names = (*HELPER_MODULES, *VIEW_MODULES)
    tmp_error = precheck_modules(module_names)
    if tmp_error:
        return tmp_error
    if not tmp_error:
        if on_status is not None:
            on_status('Hot reload: applying changes ...')
        tmp_error = reload_modules(module_names)

    view_module = sys.modules.get(view_module_name)
    new_class = getattr(view_module, class_name, None) if view_module else None
    if new_class is None:
        return f'AttributeError: {view_module_name}.{class_name} is missing'

    for name in class_flags:
        if hasattr(type(view_obj), name):
            setattr(new_class, name, getattr(type(view_obj), name))
    view_obj.__class__ = new_class
    if char_gen_method:
        char_gen = getattr(new_class, char_gen_method, None)
        if char_gen is not None:
            view_obj.get_char = char_gen(view_obj)
    return ''
