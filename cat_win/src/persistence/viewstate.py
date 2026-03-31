"""
Persist and restore curses view objects.
"""

from pathlib import Path
import pickle

from cat_win.src.curses.diffviewer import DiffViewer
from cat_win.src.curses.editor import Editor
from cat_win.src.curses.hexeditor import HexEditor


_SUPPORTED_VIEWS = (DiffViewer, Editor, HexEditor)
_VIEW_NAME_TO_TYPE = {
    'DiffViewer': DiffViewer,
    'Editor'    : Editor,
    'HexEditor' : HexEditor,
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
        else:
            # Keep non-serializable runtime handles as empty placeholders.
            # TODO: make this a debug statement
            # print(f"Warning: Skipping non-serializable attribute '{key}' in view state.")
            state[key] = None

    return state


class ViewStateWriter:
    """
    Save state of DiffViewer, Editor or HexEditor objects.
    """

    @staticmethod
    def save(file_path: str, view_obj) -> None:
        if not isinstance(view_obj, _SUPPORTED_VIEWS):
            raise TypeError(
                'view_obj must be an instance of DiffViewer, Editor or HexEditor'
            )

        payload = {
            'view_type': type(view_obj).__name__,
            'state': _collect_state(view_obj),
        }

        file_path = str(file_path)
        out_path = Path(file_path)
        if out_path.parent: # TODO: weird
            out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open('wb') as f_handle:
            pickle.dump(payload, f_handle, protocol=pickle.HIGHEST_PROTOCOL)


class ViewStateLoader:
    """
    Load state and recreate DiffViewer, Editor or HexEditor objects.
    """

    @staticmethod
    def load(file_path: str):
        with Path(file_path).open('rb') as f_handle:
            payload = pickle.load(f_handle)

        view_type_name = payload.get('view_type')
        state = payload.get('state')

        if view_type_name not in _VIEW_NAME_TO_TYPE:
            raise ValueError(f'Unsupported view type in state file: {view_type_name}')
        if not isinstance(state, dict):
            raise ValueError('Invalid state file: missing object state')

        view_type = _VIEW_NAME_TO_TYPE[view_type_name]
        view_obj = view_type.__new__(view_type)
        view_obj.__dict__.update(state)
        # _rehydrate_runtime_members(view_obj)
        return view_obj


def save_view_state(file_path: str, view_obj) -> None:
    """
    Convenience wrapper for ViewStateWriter.save().
    """
    ViewStateWriter.save(file_path, view_obj)


def load_view_state(file_path: str):
    """
    Convenience wrapper for ViewStateLoader.load().
    """
    return ViewStateLoader.load(file_path)
