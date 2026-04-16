"""
viewstate
"""

import importlib
import pickle

from cat_win.src.persistence.xdgconfig import xdg_config
from cat_win.src.service.helper.iohelper import logger


_SUPPORTED_VIEWS = {
    'DiffViewer': 'cat_win.src.curses.diffviewer',
    'Editor'    : 'cat_win.src.curses.editor',
    'HexEditor' : 'cat_win.src.curses.hexeditor',
}


def _is_pickleable(value) -> bool:
    try:
        pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    except (pickle.PickleError, AttributeError, TypeError, ValueError):
        return False
    return True


def _collect_state(view_obj) -> dict:
    state = {}
    for key, value in vars(view_obj).items():
        if key in ['curse_window']:
            state[key] = None
            continue

        if _is_pickleable(value):
            state[key] = value
            logger(
                f"Info: Collected attribute '{key}' for view state.",
                priority=logger.DEBUG
            )
        else:
            # Keep non-serializable runtime handles as empty placeholders.
            logger(
                f"Warning: Skipping non-serializable attribute '{key}' in view state.",
                priority=logger.DEBUG
            )
            state[key] = None

    return state


def _collect_class_state(view_obj) -> dict:
    class_state = {}
    view_type = type(view_obj)
    for key, value in vars(view_type).items():
        if key.startswith('__'):
            continue
        if isinstance(value, (staticmethod, classmethod, property)) or callable(value):
            continue

        if _is_pickleable(value):
            class_state[key] = value
            logger(
                f"Info: Collected class attribute '{key}' for view state.",
                priority=logger.DEBUG
            )
        else:
            logger(
                f"Warning: Skipping non-serializable class attribute '{key}' in view state.",
                priority=logger.DEBUG
            )
    return class_state


def _apply_class_state(view_type, class_state: dict) -> None:
    for key, value in class_state.items():
        if not isinstance(key, str) or key.startswith('__'):
            continue
        if not hasattr(view_type, key):
            continue
        current = getattr(view_type, key)
        if isinstance(current, (staticmethod, classmethod, property)) or callable(current):
            continue
        setattr(view_type, key, value)


class ViewStateWriter:
    """
    Save state of DiffViewer, Editor or HexEditor objects.
    """

    @staticmethod
    def save(view_obj) -> None:
        """
        saves the state of the given view object to a file in the XDG config directory.

        Parameters:
        view_obj (Diffviewer | Editor | HexEditor):
            the object whose state should be saved. Must be an instance of DiffViewer, Editor or HexEditor.
        """
        view_type_name = type(view_obj).__name__
        view_module_name = type(view_obj).__module__
        if _SUPPORTED_VIEWS.get(view_type_name) != view_module_name:
            raise TypeError(
                'view_obj must be an instance of DiffViewer, Editor or HexEditor'
            )

        payload = {
            'view_type': view_type_name,
            'view_module': view_module_name,
            'state': _collect_state(view_obj),
            'class_state': _collect_class_state(view_obj),
        }

        with xdg_config('viewstate_obj.bin', ensure_dir=True).open('wb') as f_handle:
            pickle.dump(payload, f_handle, protocol=pickle.HIGHEST_PROTOCOL)


class ViewStateLoader:
    """
    Load state and recreate DiffViewer, Editor or HexEditor objects.
    """

    @staticmethod
    def load():
        """
        loads the state of a view object from a file in the XDG config directory and recreates the view object.

        Returns:
        (Diffviewer | Editor | HexEditor):
            the recreated view object, or None if loading failed.
        """
        with xdg_config('viewstate_obj.bin', ensure_dir=True).open('rb') as f_handle:
            payload = pickle.load(f_handle)

        view_type_name = payload.get('view_type')
        view_module_name = payload.get('view_module')
        state = payload.get('state')
        class_state = payload.get('class_state', {})

        if _SUPPORTED_VIEWS.get(view_type_name) != view_module_name:
            raise ValueError(f'Unsupported view type in state file: {view_type_name}')
        if not isinstance(state, dict):
            raise ValueError('Invalid state file: missing object state')
        if not isinstance(class_state, dict):
            raise ValueError('Invalid state file: malformed class state')

        view_module = importlib.import_module(view_module_name)
        view_type = getattr(view_module, view_type_name)
        _apply_class_state(view_type, class_state)
        view_obj = view_type.__new__(view_type)
        view_obj.__dict__.update(state)

        return view_obj


def get_view_state_time() -> float:
    """
    Get the creation time of the view state file.
    """
    try:
        return xdg_config('viewstate_obj.bin').stat().st_mtime
    except OSError:
        return 0.0


def save_view_state(view_obj) -> bool:
    """
    Convenience wrapper for ViewStateWriter.save().

    Parameters:
    view_obj (Diffviewer | Editor | HexEditor):
            the object whose state should be saved. Must be an instance of DiffViewer, Editor or HexEditor.

    Returns:
    (bool):
        True if the view state was saved successfully, False otherwise.
    """
    try:
        ViewStateWriter.save(view_obj)
    except (pickle.PickleError, AttributeError, TypeError, ValueError, OSError) as e:
        logger(f"Error saving view state: {e}", priority=logger.ERROR)
        return False
    return True


def load_view_state():
    """
    Convenience wrapper for ViewStateLoader.load().

    Returns:
    (Diffviewer | Editor | HexEditor):
        the recreated view object, or None if loading failed.
    """
    try:
        return ViewStateLoader.load()
    except (OSError, ValueError, TypeError) as e:
        logger(f"Error loading view state: {e}", priority=logger.ERROR)
    except (EOFError, pickle.PickleError) as e:
        logger(f"Error loading view state: {e} (file may be corrupted)", priority=logger.ERROR)
