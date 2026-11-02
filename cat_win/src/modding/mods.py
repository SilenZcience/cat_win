"""
mods
"""

import importlib.util
import sys

import cat_win.src.const.argconstants as argconstants
from cat_win.src.persistence.xdgconfig import xdg_config


MODS_DIR = xdg_config('~mods', ensure_dir=True)


def load_mods() -> tuple:
    """
    import every .py file in the mods directory.

    Returns:
    (loaded, failed) (tuple):
        loaded: list of successfully loaded module names
        failed: list of (mod_name, exception) tuples for failed mods
    """
    if not MODS_DIR.is_dir():
        return [], []

    loaded = []
    failed = []
    for mod_path in sorted(MODS_DIR.glob('*.py')):
        if mod_path.name.startswith('_'):
            continue
        module_name = f'cat_win.mods.{mod_path.stem}'
        try:
            spec = importlib.util.spec_from_file_location(module_name, mod_path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            loaded.append(module_name)
        except Exception as exc:
            failed.append((module_name, f"{type(exc).__name__}: {exc}"))

    argconstants.ALL_ARGS.sort(key=lambda x:x.section) # sort again ...

    return loaded, failed
