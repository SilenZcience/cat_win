"""
curses
"""

from unittest.mock import MagicMock


class CursesMock:
    def __init__(self, **defaults) -> None:
        """
        Parameters:
        **defaults:
            attributes each fresh MagicMock is created with
        """
        object.__setattr__(self, '_defaults', defaults)
        object.__setattr__(self, '_mock', None)

    def reset(self) -> None:
        """
        discard the current mock.
        the next attribute access creates a new one.
        """
        object.__setattr__(self, '_mock', None)

    def _get_mock(self) -> MagicMock:
        mock = object.__getattribute__(self, '_mock')
        if mock is None:
            mock = MagicMock(**object.__getattribute__(self, '_defaults'))
            object.__setattr__(self, '_mock', mock)
        return mock

    def __getattr__(self, name: str):
        return getattr(self._get_mock(), name)

    def __setattr__(self, name: str, value) -> None:
        setattr(self._get_mock(), name, value)

    def __delattr__(self, name: str) -> None:
        delattr(self._get_mock(), name)
