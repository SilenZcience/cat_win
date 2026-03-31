"""
editorsearch-related test mocks
"""

from unittest.mock import MagicMock


class PosMock:
    def __init__(self, row=0, col=0):
        self.row = row
        self.col = col


class EditorSearchMock:
    def __init__(self, lines, row=0, col=0, search='x', replace='R', selecting=False):
        self.cpos = PosMock(row, col)
        self.search = search
        self.replace = replace
        self.line_sep = '\n'
        self.window_content = list(lines)
        self.selecting = selecting
        self.selected_area = ((0, 0), (len(self.window_content) - 1, 9999))
        self.search_items = {(row, col): 1}
        self._build_file_calls = 0
        self._build_file_upto_calls = []
        self._build_file = MagicMock(side_effect=self._on_build_file)
        self._build_file_upto = MagicMock(side_effect=self._on_build_file_upto)
        self._next_extend_lines = []

    def _on_build_file(self):
        self._build_file_calls += 1

    def _on_build_file_upto(self, upto):
        self._build_file_upto_calls.append(upto)
        if self._next_extend_lines:
            self.window_content.extend(self._next_extend_lines)
            self._next_extend_lines = []


class HexEditorSearchMock:
    def __init__(self, rows_bytes, row=0, col=0, search='AB'):
        self.cpos = PosMock(row, col)
        self.search = search
        self.selecting = False
        self.selected_area = ((0, 0), (len(rows_bytes) - 1, len(rows_bytes[-1]) if rows_bytes else 0))
        self.hex_array = [object() for _ in rows_bytes]
        self._rows_bytes = list(rows_bytes)
        self._build_file = MagicMock()

    def _get_current_state_bytes_row(self, i):
        return self._rows_bytes[i]


class DiffItemSearchMock:
    def __init__(self, line1, line2):
        self.line1 = line1
        self.line2 = line2


class DiffViewerSearchMock:
    def __init__(self, items, row=0, col=0, search='x'):
        self.cpos = PosMock(row, col)
        self.search = search
        self.diff_items = [DiffItemSearchMock(a, b) for a, b in items]
