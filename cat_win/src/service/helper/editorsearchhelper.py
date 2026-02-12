"""
editorsearchhelper
"""
import re


class _SearchIterBase:
    def __init__(self, editor, offset: int, replacing: bool = False) -> None:
        self.editor = editor
        self.offset = offset
        self.empty_match_offset = 0
        self.replacing = replacing
        self.wrapped = False
        self._start_y = editor.cpos.row
        self._start_x = editor.cpos.col
        self.yielded_result = False
        self.search = self.editor.search
        self.s_len = len(self.search) if isinstance(self.search, str) else 0
        self.replace = self.editor.replace
        self.r_len = len(self.replace)

    def __iter__(self):
        return self

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        raise NotImplementedError

    def __next__(self) -> tuple:
        raise NotImplementedError

class _SearchIterUp(_SearchIterBase):
    def _get_next_pos(self, line: str, col: int = None):
        if col is not None and col < 0:
            return -1
        if isinstance(self.search, str):
            if col is not None:
                col += self.s_len
            found_pos = line.rfind(self.search, 0, col)
            return found_pos
        if col is None:
            col = len(line)
        match_ = None
        match_start = None
        for i in range(col, -1, -1):
            m_ = self.search.search(line[i:])
            if m_ is not None and m_.start() == 0:
                match_ = m_
                match_start = i
                break
        if match_ is None:
            return -1
        self.s_len = match_.end()#  - match_.start()
        self.empty_match_offset = int(self.s_len == 0 == self.offset)
        try:
            self.replace = self.search.sub(self.editor.replace,
                                           line[match_start:match_start+self.s_len])
            self.r_len = len(self.replace)
        except re.error:
            self.replace = self.editor.replace
            self.r_len = len(self.replace)
        return match_start

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row < self._start_y or
            row == self._start_y and f_col < self._start_x
        ):
            raise StopIteration()
        if self.editor.selecting and (
            (row, f_col) < self.editor.selected_area[0]
        ):
            raise StopIteration()
        if self.replacing and row == self._start_y:
            # offset highlights and start positions
            self.editor.search_items = {
                ((r, c+self.r_len-self.s_len) if r == row and c >= f_col else (r, c)): l
                for (r, c), l in self.editor.search_items.items()
            }
            if not self.wrapped:
                self._start_x += self.r_len-self.s_len
        self.yielded_result = True
        return (row, f_col)

    def __next__(self) -> tuple:
        row = self.editor.cpos.row
        col = self.editor.cpos.col - self.offset - self.empty_match_offset

        found_pos = self._get_next_pos(self.editor.window_content[row], col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos)
        if self.wrapped:
            for line_y in range(row-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(self.editor.window_content[line_y])
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            for line_y in range(row-1, -1, -1):
                found_pos = self._get_next_pos(self.editor.window_content[line_y])
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
            self.editor._build_file()
            if self.editor.selecting:
                raise StopIteration()
            self.wrapped = True
            for line_y in range(len(self.editor.window_content)-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(self.editor.window_content[line_y])
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()

class _SearchIterDown(_SearchIterBase):
    def _get_next_pos(self, line: str, col: int = None):
        if col is not None and col > len(line):
            return -1
        line = line[col:]
        if isinstance(self.search, str):
            return line.find(self.search)
        match_ = self.search.search(line)
        if match_ is None:
            return -1
        self.s_len = match_.end() - match_.start()
        self.empty_match_offset = int(self.s_len == 0 == self.offset)
        try:
            self.replace = self.search.sub(self.editor.replace, line[match_.start():match_.end()])
            self.r_len = len(self.replace)
        except re.error:
            self.replace = self.editor.replace
            self.r_len = len(self.replace)
        return match_.start()

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row > self._start_y or
            row == self._start_y and f_col > self._start_x - (not self.offset)
        ):
            raise StopIteration()
        if self.editor.selecting and (
            (row, f_col) >= self.editor.selected_area[1]
        ):
            raise StopIteration()
        if self.replacing and row == self._start_y:
            # offset highlights and start positions
            self.editor.search_items = {
                ((r, c+self.r_len-self.s_len) if r == row and c >= f_col else (r, c)): l
                for (r, c), l in self.editor.search_items.items()
            }
            if self.wrapped:
                self._start_x += self.r_len-self.s_len
        self.yielded_result = True
        return (row, f_col)

    def __next__(self) -> tuple:
        row = self.editor.cpos.row
        col = self.editor.cpos.col + self.offset + self.empty_match_offset

        found_pos = self._get_next_pos(self.editor.window_content[row], col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos+col)
        if self.wrapped:
            for line_y in range(row+1, self._start_y+1):
                found_pos = self._get_next_pos(self.editor.window_content[line_y])
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            content_len = -1
            while content_len != len(self.editor.window_content):
                content_len = len(self.editor.window_content)
                for line_y in range(row+1, len(self.editor.window_content)):
                    found_pos = self._get_next_pos(self.editor.window_content[line_y])
                    if found_pos >= 0:
                        return self._stop_if_past_original(line_y, found_pos)
                self.editor._build_file_upto(content_len+30)
            if self.editor.selecting:
                raise StopIteration()
            self.wrapped = True
            for line_y in range(0, self._start_y+1):
                found_pos = self._get_next_pos(self.editor.window_content[line_y])
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()


def search_iter_factory(*args, downwards: bool = True) -> _SearchIterBase:
    if downwards:
        return _SearchIterDown(*args)
    return _SearchIterUp(*args)


class _SearchIterHexBase:
    def __init__(self, editor, offset: int) -> None:
        self.editor = editor
        self.offset = offset
        self.wrapped = False
        self._start_y = editor.cpos.row
        self._start_x = editor.cpos.col + offset
        self.search = self.editor.search
        self.s_len = len(self.search)

    def __iter__(self):
        return self

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        raise NotImplementedError

    def __next__(self) -> tuple:
        raise NotImplementedError

class _SearchIterHexUp(_SearchIterHexBase):
    def _get_next_pos(self, row: int, col: int = None):
        search_in = ''.join(self.editor._get_current_state_row(row))
        if col is None:
            col = len(search_in)//2
        search_wrap = ''
        while self.s_len-1 > len(search_wrap) and row < len(self.editor.hex_array)-1:
            row += 1
            search_wrap += ''.join(self.editor._get_current_state_row(row))
        search_in += search_wrap[:self.s_len-1]
        for i in range(col*2, -1, -2):
            if search_in[i:].startswith(self.search):
                return i//2
        return -1

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row < self._start_y or
            row == self._start_y and f_col < self._start_x
        ):
            raise StopIteration()
        if self.editor.selecting and (
            (row, f_col) < self.editor.selected_area[0]
        ):
            raise StopIteration()
        return (row, f_col)

    def __next__(self) -> tuple:
        row = self.editor.cpos.row
        col = self.editor.cpos.col - self.offset

        found_pos = self._get_next_pos(row, col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos)
        if self.wrapped:
            for line_y in range(row-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            for line_y in range(row-1, -1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
            self.editor._build_file()
            if self.editor.selecting:
                raise StopIteration()
            self.wrapped = True
            for line_y in range(len(self.editor.hex_array)-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()

class _SearchIterHexDown(_SearchIterHexBase):
    def _get_next_pos(self, row: int, col: int = 0):
        search_in = ''.join(self.editor._get_current_state_row(row)[col:])
        search_wrap = ''
        while self.s_len-1 > len(search_wrap) and row < len(self.editor.hex_array)-1:
            row += 1
            search_wrap += ''.join(self.editor._get_current_state_row(row))
        search_in += search_wrap[:self.s_len-1]

        for i in range(0, len(search_in)-len(self.search)+1, 2):
            if search_in[i:].startswith(self.search):
                return i//2
        return -1

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row > self._start_y or
            row == self._start_y and f_col >= self._start_x
        ):
            raise StopIteration()
        if self.editor.selecting and (
            (row, f_col) > self.editor.selected_area[1]
        ):
            raise StopIteration()
        return (row, f_col)

    def __next__(self) -> tuple:
        row = self.editor.cpos.row
        col = self.editor.cpos.col + self.offset

        found_pos = self._get_next_pos(row, col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos+col)
        if self.wrapped:
            for line_y in range(row+1, self._start_y+1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            content_len = -1
            while content_len != len(self.editor.hex_array):
                content_len = len(self.editor.hex_array)
                for line_y in range(row+1, len(self.editor.hex_array)):
                    found_pos = self._get_next_pos(line_y)
                    if found_pos >= 0:
                        return self._stop_if_past_original(line_y, found_pos)
                self.editor._build_file_upto(content_len+30)
            if self.editor.selecting:
                raise StopIteration()
            self.wrapped = True
            for line_y in range(0, self._start_y+1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()


def search_iter_hex_factory(*args, downwards: bool = True) -> _SearchIterHexBase:
    if downwards:
        return _SearchIterHexDown(*args)
    return _SearchIterHexUp(*args)


class _SearchIterDiffBase:
    def __init__(self, diffviewer, offset: int) -> None:
        self.diffviewer = diffviewer
        self.offset = offset
        self.wrapped = False
        self._start_y = diffviewer.cpos.row
        self._start_x = diffviewer.cpos.col
        self.search = self.diffviewer.search
        self.s_len = len(self.search)
        self.line2_matched = False
        self.match_buffer = None

    def __iter__(self):
        return self

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        raise NotImplementedError

    def __next__(self) -> tuple:
        raise NotImplementedError

class _SearchIterDiffUp(_SearchIterDiffBase):
    def _get_next_pos(self, row: int, col: int = None):
        if col is not None and col < 0:
            return -1
        if col is not None:
            col += self.s_len
        line1_find = self.diffviewer.diff_items[row].line1.rfind(self.search, 0, col)
        line2_find = self.diffviewer.diff_items[row].line2.rfind(self.search, 0, col)
        if line1_find < 0 and line2_find < 0:
            return -1
        if line1_find < 0 or line2_find > line1_find >= 0:
            self.line2_matched = True
            return line2_find
        if line2_find < 0 or line1_find > line2_find >= 0:
            self.line2_matched = False
            return line1_find
        if line1_find == line2_find:
            self.match_buffer = (row, line1_find)
            self.line2_matched = False
            return line1_find

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row < self._start_y or
            row == self._start_y and f_col < self._start_x
        ):
            raise StopIteration()
        return (row, f_col)

    def __next__(self) -> tuple:
        if self.match_buffer is not None:
            buf = self.match_buffer
            self.match_buffer = None
            self.line2_matched = True
            return self._stop_if_past_original(*buf)
        row = self.diffviewer.cpos.row
        col = self.diffviewer.cpos.col - self.offset

        found_pos = self._get_next_pos(row, col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos)
        if self.wrapped:
            for line_y in range(row-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            for line_y in range(row-1, -1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
            self.wrapped = True
            for line_y in range(len(self.diffviewer.diff_items)-1, self._start_y-1, -1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()

class _SearchIterDiffDown(_SearchIterDiffBase):
    def _get_next_pos(self, row: int, col: int = None):
        if col is not None and col > max(
            len(self.diffviewer.diff_items[row].line1),
            len(self.diffviewer.diff_items[row].line2)
        ):
            return -1
        line1_find = self.diffviewer.diff_items[row].line1[col:].find(self.search)
        line2_find = self.diffviewer.diff_items[row].line2[col:].find(self.search)
        if line1_find < 0 and line2_find < 0:
            return -1
        if line1_find < 0 or 0 <= line2_find < line1_find:
            self.line2_matched = True
            return line2_find
        if line2_find < 0 or 0 <= line1_find < line2_find:
            self.line2_matched = False
            return line1_find
        if line1_find == line2_find:
            self.match_buffer = (row, line1_find+(col or 0))
            self.line2_matched = False
            return line1_find

    def _stop_if_past_original(self, row: int, f_col: int) -> tuple:
        if self.wrapped and (
            row > self._start_y or
            row == self._start_y and f_col > self._start_x - (not self.offset)
        ):
            raise StopIteration()
        return (row, f_col)

    def __next__(self) -> tuple:
        if self.match_buffer is not None:
            buf = self.match_buffer
            self.match_buffer = None
            self.line2_matched = True
            return self._stop_if_past_original(*buf)
        row = self.diffviewer.cpos.row
        col = self.diffviewer.cpos.col + self.offset

        found_pos = self._get_next_pos(row, col)
        if found_pos >= 0:
            return self._stop_if_past_original(row, found_pos+col)
        if self.wrapped:
            for line_y in range(row+1, self._start_y+1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        else:
            for line_y in range(row+1, len(self.diffviewer.diff_items)):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
            self.wrapped = True
            for line_y in range(0, self._start_y+1):
                found_pos = self._get_next_pos(line_y)
                if found_pos >= 0:
                    return self._stop_if_past_original(line_y, found_pos)
        raise StopIteration()


def search_iter_diff_factory(*args, downwards: bool = True) -> _SearchIterDiffBase:
    if downwards:
        return _SearchIterDiffDown(*args)
    return _SearchIterDiffUp(*args)
