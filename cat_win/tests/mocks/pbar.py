"""
std
"""

import contextlib


class PBarMock:
    """
    mock the progress bar
    """
    def __init__(self, *_, **__) -> None:
        pass

    @contextlib.contextmanager
    def init(self):
        yield lambda _: None
