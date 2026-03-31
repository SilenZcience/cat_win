"""
edit
"""

from cat_win.src.curses.helper.editorhelper import Position

def getxymax(*_, **__) -> tuple:
    return (30, 120)


class EditorHistoryMock:
    def __init__(self):
        self.cpos = Position(0, 0)
        self.spos = Position(0, 0)
        self.selecting = False
        self.calls = []

    def _record(self, name, *args):
        self.calls.append((name, args, self.cpos.get_pos(), self.spos.get_pos(), self.selecting))

    def _key_string(self, *args):
        self._record('_key_string', *args)

    def _key_backspace(self, *args):
        self._record('_key_backspace', *args)

    def _key_enter(self, *args):
        self._record('_key_enter', *args)
