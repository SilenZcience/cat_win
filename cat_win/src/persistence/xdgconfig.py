"""
xdgconfig
"""

import os
import sys
from pathlib import Path

ENV_OVERRIDE = "CAT_WIN_CONFIG_DIR"


def _config_root() -> Path:
    """
    Return the OS-appropriate base directory for configuration files.

    Returns:
    (Path):
        the base directory for configuration files, determined by the OS and environment variables.
    """
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(os.path.expanduser(override))

    plat = sys.platform

    if plat.startswith("win"):
        for env_var in ("APPDATA", "LOCALAPPDATA"):
            env_path = os.environ.get(env_var)
            if env_path:
                return Path(env_path)
        return Path.home() / "AppData" / "Roaming"

    if plat == "darwin":
        return Path.home() / "Library" / "Application Support"

    xdg_path = os.environ.get("XDG_CONFIG_HOME")
    if xdg_path:
        return Path(xdg_path)

    return Path.home() / ".config"


def xdg_config(*parts: str, ensure_dir: bool = False) -> Path:
    """
    Return a configuration path under cat_win/config for the current OS.

    If ensure_dir is True, create the containing directory (or the path itself
    when the target is a directory) before returning.

    Parameters:
    *parts (str):
        path components to append to the base config directory, e.g. ("cat_win", "settings.ini").
    ensure_dir (bool):
        whether to create the containing directory (or the path itself if it's a directory) if it

    Returns:
    (Path):
        the full path to the configuration file or directory, with directories created if ensure_dir is True.
    """
    root = _config_root()
    path = Path(root, 'cat_win', *parts)

    if ensure_dir:
        # If parts are empty or look like a directory, create the path; otherwise
        # create its parent so file writes succeed.
        target_dir = path if not parts or path.suffix == "" else path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

    return path
