"""
diffviewer-related test mocks
"""


class DummyDiffItem:
    def __init__(self, lineno='1', line1='', line2='', code=0, changes1=None, changes2=None):
        self.lineno = lineno
        self.line1 = line1
        self.line2 = line2
        self.code = code
        self.changes1 = list(changes1 or [])
        self.changes2 = list(changes2 or [])


class DummyDifflibParser:
    def __init__(self, diff_items=None, equal=0, insert=0, delete=0, changed=0, last_lineno=1):
        self._diff_items = list(diff_items or [])
        self.count_equal = equal
        self.count_insert = insert
        self.count_delete = delete
        self.count_changed = changed
        self.last_lineno = last_lineno

    def get_diff(self):
        return list(self._diff_items)


class DummyWindow:
    def __init__(self, max_y=30, max_x=120):
        self.max_y = max_y
        self.max_x = max_x
        self.calls = []
        self._next_wch = []

    def getmaxyx(self):
        return (self.max_y, self.max_x)

    def addstr(self, *args):
        self.calls.append(('addstr', args))

    def chgat(self, *args):
        self.calls.append(('chgat', args))

    def move(self, *args):
        self.calls.append(('move', args))

    def clrtoeol(self):
        self.calls.append(('clrtoeol', ()))

    def clrtobot(self):
        self.calls.append(('clrtobot', ()))

    def clear(self):
        self.calls.append(('clear', ()))

    def refresh(self):
        self.calls.append(('refresh', ()))

    def timeout(self, value):
        self.calls.append(('timeout', (value,)))

    def nodelay(self, value):
        self.calls.append(('nodelay', (value,)))

    def keypad(self, value):
        self.calls.append(('keypad', (value,)))

    def get_wch(self):
        if not self._next_wch:
            return -1
        return self._next_wch.pop(0)

    def set_input(self, items):
        self._next_wch = list(items)
