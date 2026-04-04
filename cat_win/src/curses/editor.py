"""
editor
"""

from pathlib import Path
try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import re
import signal
import sys

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.const.regex import compile_re
from cat_win.src.curses.helper.editorsearchhelper import _SearchIterBase, search_iter_factory
from cat_win.src.curses.helper.editorhelper import History, Position, frepr, \
    UNIFY_HOTKEYS, KEY_HOTKEYS, ACTION_HOTKEYS, SCROLL_HOTKEYS, MOVE_HOTKEYS, \
        SELECT_HOTKEYS, HISTORY_HOTKEYS, INDENT_HOTKEYS, FUNCTION_HOTKEYS, HEX_BYTE_KEYS
from cat_win.src.curses.helper.diffviewerhelper import is_special_character
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.curses.helper.githelper import GitHelper
from cat_win.src.service.helper.iohelper import IoHelper, logger
from cat_win.src.curses.helper.syntaxhighlight import SyntaxHighlighter
from cat_win.src.persistence.viewstate import save_view_state, get_view_state_time
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.fileattributes import get_file_mtime
from cat_win.src.service.rawviewer import SPECIAL_CHARS


class Editor:
    """
    Editor
    """
    loading_failed = False
    special_indentation = '\t'
    auto_indent = False

    save_with_alt = False
    debug_mode = False

    unicode_escaped_search  = True
    unicode_escaped_replace = True
    file_encoding = 'utf-8'

    _SYNTAX_COLOR_IDS = {
        'keyword': 200,
        'string':  201,
        'number':  202,
        'comment': 203,
        'builtin': 204,
    }

    def __init__(self, files: list, file_idx: int = 0, file_commit_hash = None) -> None:
        """
        defines an Editor object.

        Parameters:
        files (list):
            list of tuples (file, display_name)
        file_idx (int):
            index of the file to open in the editor
        file_commit_hash (str|dict|None):
             commit hashes for the files to open in the editor
        """
        self.curse_window = None
        self.history = History()
        self.get_char = self._get_new_char()

        self.files = files
        self.file_commit_hash = file_commit_hash
        self.file = self.files[file_idx][0]
        self.display_name = self.files[file_idx][1]
        self.open_next_idx = None
        self.open_next_hash = None
        self._f_content_gen = None
        self.line_sep = '\n'
        self.window_content = []
        self._syntax_cache: dict = {}
        self._syntax_highlighter = SyntaxHighlighter.get_plugin(Path(self.file).suffix.casefold())

        self.special_chars: dict = {}
        self.search  = '' # str | re.Pattern
        self.replace = ''
        self.search_items: dict = {}
        self.search_items_focused_span: list = []

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False
        self.scrolling = False
        self.selecting = False
        self.deleted_line = False

        # current cursor position
        self.cpos = Position(0, 0)
        self.snap_pos = Position(0, 0)
        # window position (top-left)
        self.wpos = Position(0, 0)
        # second cursor for selection area
        self.spos = Position(0, 0)

        self._setup_file()

    @property
    def selected_area(self):
        if self.spos.get_pos() <= self.cpos.get_pos():
            return (self.spos.get_pos(), self.cpos.get_pos())
        return (self.cpos.get_pos(), self.spos.get_pos())

    @property
    def selected_text(self):
        (sel_from_y, sel_from_x), (sel_to_y, sel_to_x) = self.selected_area
        if not self.selecting:
            sel_from_y, sel_from_x = self.cpos.get_pos()
            sel_to_y, sel_to_x = sel_from_y, sel_from_x+1
        content_window = self.window_content[sel_from_y:sel_to_y+1]
        content_window[-1] = content_window[-1][:sel_to_x]
        content_window[0] = content_window[0][sel_from_x:]
        return content_window

    def _set_special_chars(self, special_chars: dict) -> None:
        self.special_chars = special_chars

    def _get_special_char(self, char: str) -> str:
        return self.special_chars.get(char, '?')

    def _build_file(self) -> None:
        for line in self._f_content_gen:
            self.window_content.append(line)

    def _build_file_upto(self, to_row: int = None) -> None:
        if to_row is None:
            to_row = self.getxymax()[0]+max(self.cpos.row, self.wpos.row)+1
        if len(self.window_content) >= to_row:
            return
        for line in self._f_content_gen:
            self.window_content.append(line)
            if len(self.window_content) >= to_row:
                break

    def _setup_file(self) -> None:
        """
        setup the editor content screen by reading the given file.
        """
        self.window_content = []
        self._syntax_cache.clear()
        try:
            self.line_sep = IoHelper.get_newline(self.file)
            if self.file_commit_hash is None:
                self._f_content_gen = IoHelper.yield_file(self.file, False, self.file_encoding)
                self._build_file_upto(30)
                self.unsaved_progress = False
            else:
                self.window_content = GitHelper.get_git_file_content_at_commit(
                    self.file, self.file_commit_hash
                )
                self.display_name = f"GIT: {self.display_name}"
                self._f_content_gen = (line for line in [])
                self.unsaved_progress = True
            self.error_bar = ''
            self.status_bar_size = 1
        except (OSError, UnicodeError) as exc:
            self.unsaved_progress = True
            self.error_bar = str(exc)
            self.status_bar_size = 2
            logger(self.error_bar, priority=logger.DEBUG)
        if not self.window_content:
            self.window_content.append('')

    def _get_syntax_tokens(self, top_row: int, bottom_row: int) -> None:
        if self._syntax_highlighter is None:
            return

        start_row = 0
        start_state = None
        for prev_row in range(top_row - 1, -1, -1):
            cached = self._syntax_cache.get(prev_row)
            if cached is None:
                continue
            if cached[0] != self.window_content[prev_row]:
                continue
            start_row = prev_row + 1
            start_state = cached[2]
            break

        current_state = start_state
        for current_row in range(start_row, bottom_row):
            line = self.window_content[current_row]
            cached = self._syntax_cache.get(current_row)

            if cached is not None and cached[0] == line and cached[1] == current_state:
                current_state = cached[2]
                continue

            tokens, end_state = self._syntax_highlighter.tokenize_line(line, current_state)
            self._syntax_cache[current_row] = (line, current_state, end_state, tokens)
            current_state = end_state

    def getxymax(self) -> tuple:
        """
        find the size of the window.

        Returns:
        (tuple):
            the size of the display that is free to use
            for text/content
        """
        max_y, max_x = self.curse_window.getmaxyx()
        return (max_y-self.status_bar_size, max_x)

    def _get_clipboard(self) -> bool:
        clipboard = Clipboard.get()
        if clipboard is None:
            self.error_bar = 'An error occured pasting the clipboard!'
        return clipboard

    def _key_enter(self, _) -> str:
        new_line = self.window_content[self.cpos.row][self.cpos.col:]
        self.window_content[self.cpos.row] = self.window_content[self.cpos.row][:self.cpos.col]
        self.cpos.row += 1
        self.cpos.col = 0
        self.window_content.insert(self.cpos.row, new_line)
        self.unsaved_progress = True
        return ''

    def _key_dc(self, _) -> str:
        if self.selecting:
            return None
        if self.cpos.col < len(self.window_content[self.cpos.row]):
            deleted = self.window_content[self.cpos.row][self.cpos.col]
            self.window_content[self.cpos.row] = \
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][self.cpos.col+1:]
            self.unsaved_progress = True
            return deleted
        if self.cpos.row < len(self.window_content)-1:
            self.window_content[self.cpos.row] += self.window_content[self.cpos.row+1]
            del self.window_content[self.cpos.row+1]
            self.unsaved_progress = True
            self.deleted_line = True
            return ''
        return None

    def _key_dl(self, _) -> str:
        if self.selecting:
            return None
        if self.cpos.col < len(self.window_content[self.cpos.row]):
            cur_col = self.cpos.col
            t_p = self.window_content[self.cpos.row][cur_col].isalnum()
            while cur_col < len(self.window_content[self.cpos.row]) and \
                t_p == self.window_content[self.cpos.row][cur_col].isalnum():
                cur_col += 1
            deleted = self.window_content[self.cpos.row][self.cpos.col:cur_col]
            self.window_content[self.cpos.row] = (
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][cur_col:]
            )
            self.unsaved_progress = True
            return deleted
        if self.cpos.row < len(self.window_content)-1:
            self.window_content[self.cpos.row] += self.window_content[self.cpos.row+1]
            del self.window_content[self.cpos.row+1]
            self.unsaved_progress = True
            self.deleted_line = True
            return ''
        return None

    def _key_backspace(self, wchars) -> str:
        if self.selecting:
            return None
        # usually wchars has len() == 1
        # generic backspace handling in case of auto indent
        wchar_l = len(wchars) if isinstance(wchars, str) else 1
        if self.cpos.col: # delete char
            self.cpos.col -= wchar_l
            deleted = self.window_content[self.cpos.row][self.cpos.col:self.cpos.col+wchar_l]
            self.window_content[self.cpos.row] = \
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][self.cpos.col+wchar_l:]
            self.unsaved_progress = True
            return deleted
        if self.cpos.row: # or delete line
            line = self.window_content[self.cpos.row]
            del self.window_content[self.cpos.row]
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])
            self.window_content[self.cpos.row] += line
            self.unsaved_progress = True
            self.deleted_line = True
            return '\n'
        return None

    def _key_ctl_backspace(self, _) -> str:
        if self.selecting:
            return None
        if self.cpos.col:
            old_col = self.cpos.col
            self.cpos.col -= 1
            t_p = self.window_content[self.cpos.row][self.cpos.col].isalnum()
            while self.cpos.col > 0 and \
                t_p == self.window_content[self.cpos.row][self.cpos.col-1].isalnum():
                self.cpos.col -= 1
            deleted = self.window_content[self.cpos.row][self.cpos.col:old_col]
            self.window_content[self.cpos.row] = \
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][old_col:]
            self.unsaved_progress = True
            return deleted
        if self.cpos.row: # or delete line
            line = self.window_content[self.cpos.row]
            del self.window_content[self.cpos.row]
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])
            self.window_content[self.cpos.row] += line
            self.unsaved_progress = True
            self.deleted_line = True
            return ''
        return None

    def _move_key_mouse(self) -> None:
        """
        handles mouse events.
        """
        self.selecting = False
        _, x, y, _, bstate = curses.getmouse()
        if bstate & curses.BUTTON1_CLICKED:
            self.cpos.row = min(self.wpos.row+y, len(self.window_content)-1)
            self.cpos.col = min(self.wpos.col+x, len(self.window_content[self.cpos.row]))
            # logger(f" {x} {y} {bstate} CLICKED")
        elif bstate & curses.BUTTON1_PRESSED:
            self.spos.row = min(self.wpos.row+y, len(self.window_content)-1)
            self.spos.col = min(self.wpos.col+x, len(self.window_content[self.spos.row]))
            # logger(f" {x} {y} {bstate} PRESSED")
        elif bstate & curses.BUTTON1_RELEASED:
            self.selecting = True
            self.cpos.row = min(self.wpos.row+y, len(self.window_content)-1)
            self.cpos.col = min(self.wpos.col+x, len(self.window_content[self.cpos.row]))
            # logger(f" {x} {y} {bstate} RELEASED")
            # logger(f"Selected area: {self.spos.get_pos()} {self.cpos.get_pos()}")

        elif bstate & curses.BUTTON4_PRESSED:
            for _ in range(3):
                self._move_key_up()
        elif bstate & curses.BUTTON5_PRESSED:
            for _ in range(3):
                self._move_key_down()

    def _move_key_left(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        if self.cpos.col:
            self.cpos.col -= 1
        elif self.cpos.row:
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])

    def _move_key_right(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        if self.cpos.col < len(self.window_content[self.cpos.row]):
            self.cpos.col += 1
        elif self.cpos.row < len(self.window_content)-1:
            self.cpos.row += 1
            self.cpos.col = 0

    def _move_key_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        if self.cpos.row:
            self.cpos.row -= 1

    def _move_key_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        if self.cpos.row < len(self.window_content)-1:
            self.cpos.row += 1

    def _move_key_ctl_left(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        if self.cpos.col == 1:
            self.cpos.col = 0
        elif self.cpos.col > 1:
            self.cpos.col -= 2
            t_p = self.window_content[self.cpos.row][self.cpos.col].isalnum()
            while self.cpos.col > 0 and \
                t_p == self.window_content[self.cpos.row][self.cpos.col].isalnum():
                self.cpos.col -= 1
            if self.cpos.col:
                self.cpos.col += 1
        elif self.cpos.row:
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])

    def _move_key_ctl_right(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        if self.cpos.col == len(self.window_content[self.cpos.row])-1:
            self.cpos.col = len(self.window_content[self.cpos.row])
        elif self.cpos.col < len(self.window_content[self.cpos.row])-1:
            self.cpos.col += 1
            t_p = self.window_content[self.cpos.row][self.cpos.col].isalnum()
            while self.cpos.col < len(self.window_content[self.cpos.row]) and \
                t_p == self.window_content[self.cpos.row][self.cpos.col].isalnum():
                self.cpos.col += 1
        elif self.cpos.row < len(self.window_content)-1:
            self.cpos.row += 1
            self.cpos.col = 0

    def _move_key_ctl_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        if self.cpos.row >= 10:
            self.cpos.row -= 10
        else:
            self.cpos.row = 0
            self.cpos.col = 0

    def _move_key_ctl_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        if self.cpos.row < len(self.window_content)-10:
            self.cpos.row += 10
        else:
            self.cpos.row = len(self.window_content)-1
            self.cpos.col = len(self.window_content[self.cpos.row])

    def _select_key_left(self) -> None:
        self.selecting = False
        self._move_key_left()

    def _select_key_right(self) -> None:
        self.selecting = False
        self._move_key_right()

    def _select_key_up(self) -> None:
        self.selecting = False
        self._move_key_up()

    def _select_key_down(self) -> None:
        self.selecting = False
        self._move_key_down()

    def _scroll_key_left(self) -> None:
        self.wpos.col = max(self.wpos.col-1, 0)

    def _scroll_key_right(self) -> None:
        max_y, max_x = self.getxymax()
        max_line = max(map(len,self.window_content[self.wpos.row:self.wpos.row+max_y]))
        self.wpos.col = max(min(self.wpos.col+1, max_line+1-max_x), 0)

    def _scroll_key_up(self) -> None:
        self.wpos.row = max(self.wpos.row-1, 0)

    def _scroll_key_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(min(self.wpos.row+1, len(self.window_content)-max_y), 0)

    def _move_key_page_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        max_y, _ = self.getxymax()
        self.wpos.row = max(self.wpos.row-max_y, 0)
        self.cpos.row = max(self.cpos.row-max_y, 0)

    def _move_key_page_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        max_y, _ = self.getxymax()
        self.wpos.row += max_y
        self.cpos.row += max_y
        self._build_file_upto()
        self.wpos.row = max(min(self.wpos.row, len(self.window_content)-max_y), 0)
        self.cpos.row = min(self.cpos.row, len(self.window_content)-1)

    def _select_key_page_up(self) -> None:
        self.selecting = False
        self._move_key_page_up()

    def _select_key_page_down(self) -> None:
        self.selecting = False
        self._move_key_page_down()

    def _scroll_key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(self.wpos.row-max_y, 0)

    def _scroll_key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row += max_y
        self._build_file_upto()
        self.wpos.row = max(min(self.wpos.row, len(self.window_content)-max_y), 0)

    def _move_key_end(self) -> None:
        self.cpos.col = len(self.window_content[self.cpos.row])

    def _move_key_ctl_end(self) -> None:
        self._build_file()
        self.cpos.row = len(self.window_content)-1
        self.cpos.col = len(self.window_content[-1])

    def _select_key_end(self) -> None:
        self._move_key_end()

    def _scroll_key_end(self) -> None:
        self._build_file()
        max_y, max_x = self.getxymax()
        self.wpos.row = max(len(self.window_content)-max_y, 0)
        max_line = max(map(len,self.window_content[-max_y:]))
        self.wpos.col = max(max_line+1-max_x, 0)

    def _move_key_home(self) -> None:
        n_col = len(self.window_content[self.cpos.row])
        n_col-= len(self.window_content[self.cpos.row].lstrip())
        self.cpos.col = n_col if n_col < self.cpos.col else 0

    def _move_key_ctl_home(self) -> None:
        self.cpos.row = 0
        self.cpos.col = 0

    def _select_key_home(self) -> None:
        self._move_key_home()

    def _scroll_key_home(self) -> None:
        self.wpos.row = 0
        self.wpos.col = 0

    def _indent_tab(self, indentation_: str) -> str:
        if not self.selecting and '\0' not in indentation_:
            return self._key_string(indentation_)
        (sel_from_y, _), (sel_to_y, _) = self.selected_area
        if indentation_.count('\0') == 1:
            sel_from_y = sel_to_y = self.cpos.row
        if '\0' not in indentation_:
            indentation_ = self.special_indentation
        changed_indent = indentation_.split('\0')
        changed_indent += [self.special_indentation] * (sel_to_y-sel_from_y+1-len(changed_indent))
        for row, indent in zip(range(sel_from_y, sel_to_y+1), changed_indent):
            c_row = self.window_content[row]
            self.window_content[row] = indent + c_row
            if row == self.cpos.row:
                self.cpos.col += len(self.special_indentation)
            if row == self.spos.row:
                self.spos.col += len(self.special_indentation)
        self.unsaved_progress = True
        self.deleted_line = True
        return '\0'.join([self.special_indentation] * (sel_to_y-sel_from_y+1)) + '\0'

    def _indent_btab(self, indentation_) -> str:
        sel_from_y = sel_to_y = self.cpos.row
        if isinstance(indentation_, str) and indentation_.count('\0') > 1 \
            or self.selecting:
            (sel_from_y, _), (sel_to_y, _) = self.selected_area
        indent_l = len(self.special_indentation)
        changed_indent = []
        for row in range(sel_from_y, sel_to_y+1):
            c_row = self.window_content[row]
            if c_row.startswith(self.special_indentation):
                self.window_content[row] = c_row[indent_l:]
                if row == self.cpos.row:
                    self.cpos.col = max(self.cpos.col-indent_l, 0)
                if row == self.spos.row:
                    self.spos.col = max(self.spos.col-indent_l, 0)
                self.unsaved_progress = True
                changed_indent.append(self.special_indentation)
            else:
                changed_indent.append('')
        if self.special_indentation in changed_indent:
            return '\0'.join(changed_indent) + '\0'
        return None

    def _key_replace_search(self, r_this: str, r_with: str) -> str:
        self.window_content[self.cpos.row] = self.window_content[self.cpos.row][:self.cpos.col] + \
            r_with + self.window_content[self.cpos.row][self.cpos.col+len(r_this):]
        self.cpos.col += len(r_with)
        self.unsaved_progress = True

    def _key_replace_search_(self, r_this: str, r_with: str) -> str:
        self.cpos.col -= len(r_with)
        return self._key_replace_search(r_this=r_with, r_with=r_this)

    def _replace_search(self, r_this, r_with: str, search_: _SearchIterBase) -> None:
        pre_cpos = self.cpos.get_pos()
        pre_spos = self.spos.get_pos()
        if not isinstance(r_this, str):
            r_this = self.window_content[self.cpos.row][self.cpos.col:self.cpos.col+search_.s_len]
            r_with = search_.replace
        if not r_this and not r_with:
            return
        self._key_replace_search(r_this, r_with)
        self.history.add(b'_key_replace_search', False,
                            pre_cpos, self.cpos.get_pos(),
                            pre_spos, self.spos.get_pos(),
                            False, False,
                            r_this, r_with)

    def _key_remove_chunk(self, _) -> str:
        (sel_from_y, sel_from_x), (sel_to_y, sel_to_x) = self.selected_area
        self.cpos.set_pos((sel_from_y, sel_from_x))
        if sel_from_y == sel_to_y:
            deleted = self.window_content[sel_from_y][sel_from_x:sel_to_x]
            self.window_content[sel_from_y] = \
                self.window_content[sel_from_y][:sel_from_x] + \
                self.window_content[sel_from_y][sel_to_x:]
            self.unsaved_progress = True
            return deleted
        deleted = self.window_content[sel_from_y][sel_from_x:]
        self.window_content[sel_from_y] = self.window_content[sel_from_y][:sel_from_x]
        deleted_middle = ''
        for row in range(sel_to_y-1, sel_from_y, -1):
            deleted_middle = self.window_content[row] + '\n' + deleted_middle
            del self.window_content[row]
        deleted += '\n' + deleted_middle + self.window_content[sel_from_y+1][:sel_to_x]
        self.window_content[sel_from_y] += self.window_content[sel_from_y+1][sel_to_x:]
        del self.window_content[sel_from_y+1]
        self.unsaved_progress = True
        return deleted

    def _key_add_chunk(self, wchars_: str) -> str:
        segments = wchars_.split('\n')
        segments.reverse()
        end_segment = self.window_content[self.cpos.row][self.cpos.col:]
        self.window_content[self.cpos.row] = \
            self.window_content[self.cpos.row][:self.cpos.col] + segments[-1]
        if len(segments) == 1:
            self.window_content[self.cpos.row] += end_segment
            self.unsaved_progress = True
            return wchars_
        self.window_content.insert(self.cpos.row+1, segments[0] + end_segment)
        for row in segments[1:-1]:
            self.window_content.insert(self.cpos.row+1, row)
        self.unsaved_progress = True
        return wchars_

    def _remove_chunk(self) -> None:
        """
        after calling this method:
            cpos will be the previous selected start pos,
            spos is unreliable and should not be used
        """
        pre_cpos = self.cpos.get_pos()
        pre_spos = self.spos.get_pos()
        pre_selecting = self.selecting
        action_text = self._key_remove_chunk(None)
        self.history.add(b'_key_remove_chunk', '\n' in action_text,
                            pre_cpos, self.cpos.get_pos(),
                            pre_spos, self.spos.get_pos(),
                            pre_selecting, self.selecting,
                            action_text)

    def _add_chunk(self, wchars_) -> None:
        """
        after calling this method:
            cpos will be the end of the chunk,
            spos will be the start of the chunk
        """
        if isinstance(wchars_, str):
            line_break = '\n'
            for lb in ('\r\n', '\r', '\n'):
                if lb in wchars_:
                    line_break = lb
                    break
            wchars_ = wchars_.split(line_break)

        pre_cpos = self.cpos.get_pos()
        pre_spos = self.spos.get_pos()
        pre_selecting = self.selecting
        action_text = self._key_add_chunk('\n'.join(wchars_))
        # _remove_chunk needs both pos-markers, so set them after add chunk,
        # such that undo works correctly, and cursor is at the end of the chunk
        self.spos.set_pos(pre_cpos)
        self.cpos.set_pos((
            pre_cpos[0]+len(wchars_)-1,
            pre_cpos[1]+len(wchars_[-1]) if len(wchars_) == 1 else len(wchars_[-1])
        ))
        self.history.add(b'_key_add_chunk', '\n' in action_text,
                            pre_cpos, self.cpos.get_pos(),
                            pre_spos, self.spos.get_pos(),
                            pre_selecting, self.selecting,
                            action_text)

    def _key_string(self, wchars_) -> str:
        """
        tries to append (a) char(s) to the screen.

        Parameters:
        wchars (int|str):
            given by curses get_wch()

        Returns:
        (str):
            wchars_
        """
        if not isinstance(wchars_, str) or not wchars_:
            return ''

        # windows-curses sometimes returns characters like '\ud83e\udd23' (e.g. emojis)
        # we can fix these with the utf-16 surrogatepass error-handler
        wchars = wchars_.encode('utf-16', 'surrogatepass').decode('utf-16')
        if wchars != wchars_:
            logger(f"__DEBUG__: Changed {wchars_} to {wchars}", end=' ', priority=logger.DEBUG)
            logger(f"Length: {len(wchars)} Ord: {ord(wchars[0])}", priority=logger.DEBUG)
        # in case the line has no text yet and tab is pressed, we indent with
        # the custom indentation
        if self.special_indentation != '\t' == wchars and \
            (self.window_content[self.cpos.row][:self.cpos.col].replace(
                self.special_indentation, ''
            ) + ' ').isspace():
            return self._key_string(self.special_indentation)
        self.unsaved_progress = True
        self.window_content[self.cpos.row] = \
            self.window_content[self.cpos.row][:self.cpos.col] + wchars + \
            self.window_content[self.cpos.row][self.cpos.col:]
        self.cpos.col += len(wchars)
        return wchars

    def _history_undo(self) -> None:
        self.history.undo(self)

    def _history_redo(self) -> None:
        self.history.redo(self)

    def _select_key_all(self) -> None:
        self._build_file()
        self.spos.set_pos((0, 0))
        self.cpos.set_pos((len(self.window_content)-1, len(self.window_content[-1])))
        return None

    def _action_copy(self) -> bool:
        if not self.selecting:
            return True
        self.error_bar = self.error_bar if (
            Clipboard.put(self.line_sep.join(self.selected_text))
        ) else 'An error occured copying the selected text to the clipboard!'
        return True

    def _action_paste(self) -> bool:
        clipboard = self._get_clipboard()
        if clipboard is None:
            return True

        if self.selecting:
            self._remove_chunk()
        self._add_chunk(clipboard)
        return True

    def _action_cut(self) -> bool:
        if self.selecting:
            self._action_copy()
            self._remove_chunk()
        return True

    def _action_render_scr(self, msg: str, tmp_error: str = '', error_color: int = 2) -> None:
        max_y, max_x = self.getxymax()
        msg = msg.replace('\0', '')
        error_bar_backup = self.error_bar
        if tmp_error:
            logger(tmp_error, priority=logger.WARNING)
        self.error_bar = tmp_error if tmp_error else self.error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                        self.error_bar[:max_x].ljust(max_x),
                                        self._get_color(error_color))
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                        msg[:max_x].ljust(max_x),
                                        self._get_color(3))
        except curses.error:
            pass
        self.error_bar = error_bar_backup
        self.curse_window.refresh()

    def _action_save(self) -> bool:
        """
        handle the save file action.

        Returns
        (bool):
            indicates if the editor should keep running
        """
        self._build_file()
        content = self.line_sep.join(self.window_content)
        try:
            # encode here to potentially trigger the unicodeerror event before erasing the file
            IoHelper.write_file(self.file, content.encode(self.file_encoding))
            self.changes_made = True
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1
        except (OSError, UnicodeError) as exc:
            self.unsaved_progress = True
            self.error_bar = str(exc)
            self.status_bar_size = 2
            logger(self.error_bar, priority=logger.ERROR)
        return True

    def _action_transform(self) -> bool:
        """
        handles the transform query action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        bool_expressions = {
            'isalnum': str.isalnum,
            'isalpha': str.isalpha,
            'isdecimal': str.isdecimal,
            'isdigit': str.isdigit,
            'isidentifier': str.isidentifier,
            'islower': str.islower,
            'isnumeric': str.isnumeric,
            'isprintable': str.isprintable,
            'isspace': str.isspace,
            'istitle': str.istitle,
            'isupper': str.isupper,
        }
        try:
            bool_expressions.update({
                'isascii': str.isascii,
            })
        except AttributeError: # Python 3.6 does not have str.isascii
            bool_expressions.update({
                'isascii': lambda x: all(ord(c) < 128 for c in x),
            })

        string_expressions = {
            'capitalize': str.capitalize,
            'casefold': str.casefold,
            'lower': str.lower,
            'lstrip': str.lstrip,
            'rstrip': str.rstrip,
            'strip': str.strip,
            'swapcase': str.swapcase,
            'title': str.title,
            'upper': str.upper,
        }
        curses.curs_set(0)

        wchar, w_query, query_result = '', '', ''
        result_color = 2
        while str(wchar).upper() != ESC_CODE:
            self._action_render_scr(f"Query: {frepr(w_query)}␣", query_result, result_color)
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        w_query += clipboard
                if key == b'_action_transform':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if key == b'_key_string':
                w_query += wchar
            elif key == b'_key_backspace':
                w_query = w_query[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = w_query[-1:].isalnum()
                while w_query and w_query[-1:].isalnum() == t_p:
                    w_query = w_query[:-1]
            elif key == b'_key_enter':
                w_query = w_query.casefold()
                if w_query == 'exit':
                    break
                result_color = 2
                content_window = self.selected_text
                if w_query in bool_expressions:
                    joined_content = self.line_sep.join(content_window)
                    query_truthy = bool_expressions[w_query](joined_content)
                    query_result = f"{w_query}? {query_truthy}"
                    query_result+= f" ({repr(joined_content)})"
                    result_color = 4 if query_truthy else 2
                    continue
                if w_query in string_expressions:
                    if (
                        not self.selecting and self.cpos.col == len(self.window_content[self.cpos.row])
                    ) or self.cpos.get_pos() == self.spos.get_pos():
                        query_result = 'no valid area has been selected!'
                        continue
                    if not self.selecting:
                        self.spos.row = self.cpos.row
                        self.spos.col = self.cpos.col + 1
                    new_content = [string_expressions[w_query](line) for line in content_window]
                    self._remove_chunk()
                    self._add_chunk(new_content)
                    break
                if w_query.startswith('lambda'):
                    try:
                        lambda_func = eval(w_query)
                        if not callable(lambda_func):
                            raise ValueError('not a function')
                        lambda_result = [lambda_func(line) for line in content_window]
                        if all(isinstance(r, bool) for r in lambda_result):
                            query_truthy = lambda_func(self.line_sep.join(content_window))
                            query_result = f"{w_query}? {query_truthy}"
                            query_result+= f" ({repr(self.line_sep.join(content_window))})"
                            result_color = 4 if query_truthy else 2
                        elif all(isinstance(r, str) for r in lambda_result):
                            if (
                                not self.selecting and self.cpos.col == len(self.window_content[self.cpos.row])
                            ) or self.cpos.get_pos() == self.spos.get_pos():
                                query_result = 'no valid area has been selected!'
                                continue
                            if not self.selecting:
                                self.spos.row = self.cpos.row
                                self.spos.col = self.cpos.col + 1
                            self._remove_chunk()
                            self._add_chunk(lambda_result)
                            break
                    except Exception as exc:
                        query_result = f"Error evaluating lambda: {exc}"
                else:
                    query_result = f"'{frepr(w_query)}' not found!"
        return True

    def _action_jump(self) -> bool:
        """
        handles the jump to line action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        curses.curs_set(0)

        wchar, l_jmp = '', ''
        while str(wchar).upper() not in [ESC_CODE, 'N']:
            self._action_render_scr(f"Confirm: [y]es, [n]o - Jump to line: {l_jmp}␣")
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        l_jmp += ''.join(filter(str.isdigit, clipboard))
                if key == b'_action_jump':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                l_jmp = l_jmp[:-1]
            elif key == b'_key_ctl_backspace':
                l_jmp = ''
            elif key == b'_key_string' and wchar.isdigit():
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    self.cpos.row = max(int(l_jmp)-1, 0)
                    self._build_file_upto()
                    self.cpos.row = min(self.cpos.row, len(self.window_content)-1)
                break
        return True

    def _action_find(self, find_next: int = 0) -> bool:
        """
        handles the find in editor action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        curses.curs_set(0)

        search_regex = not isinstance(self.search, str)
        wchar, sub_s, tmp_error = '', '', ''
        key, running = b'_key_enter', False
        while str(wchar) != ESC_CODE:
            if not find_next:
                pre_s = ''
                if self.search and isinstance(self.search, str):
                    pre_s = f" [{repr(self.search)[1:-1]}]"
                elif self.search:
                    pre_s = f" re:[{repr(self.search.pattern)[1:-1]}]"
                rep_r = 'Match' if search_regex else 'Search for'
                self._action_render_scr(
                    f"Confirm: 'ENTER' - {rep_r}{pre_s}: {frepr(sub_s)}␣",
                    tmp_error
                )
                wchar, key = next(self.get_char)
            elif running:
                break
            running = True
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        sub_s += clipboard
                if key == b'_action_find':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_insert':
                    search_regex = not search_regex
                    self.search = ''
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                sub_s = sub_s[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = sub_s[-1:].isalnum()
                while sub_s and sub_s[-1:].isalnum() == t_p:
                    sub_s = sub_s[:-1]
            elif key == b'_key_string':
                sub_s += wchar
            elif key == b'_key_enter':
                self.search = sub_s if sub_s else self.search
                if not self.search:
                    break
                if Editor.unicode_escaped_search and sub_s:
                    try:
                        self.search = sub_s.encode().decode('unicode_escape').encode('latin-1').decode()
                    except UnicodeError:
                        pass
                if search_regex and isinstance(self.search, str):
                    try:
                        self.search = compile_re(self.search, True)
                    except re.error as exc:
                        tmp_error = 'invalid regular expression: ' + str(exc)
                        continue
                cpos_tmp, spos_tmp = self.cpos.get_pos(), self.spos.get_pos()
                try:
                    sel_pos_a, sel_pos_b = self.selected_area
                    if self.selecting and self.cpos.get_pos() == sel_pos_b and find_next >= 0:
                        self.cpos.set_pos(sel_pos_a)
                        self.spos.set_pos(sel_pos_b)
                    elif self.selecting and self.cpos.get_pos() == sel_pos_a and find_next < 0:
                        self.cpos.set_pos(sel_pos_b)
                        self.spos.set_pos(sel_pos_a)
                    try:
                        search = search_iter_factory(
                            self,
                            1-(self.selecting and find_next >= 0),
                            downwards=(find_next >= 0)
                        )
                    except ValueError as exc:
                        tmp_error = str(exc)
                        continue
                    max_y, _ = self.getxymax()
                    cpos = next(search)
                    self.search_items[cpos] = search.s_len
                    self.search_items_focused_span = list(search.s_rows)
                    for pos, l in search.s_rows:
                        self.search_items[pos] = l
                    if not self.selecting:
                        if find_next >= 0:
                            self.cpos.set_pos((max(cpos[0]-max_y, 0), 0))
                        else:
                            self.cpos.set_pos((min(cpos[0]+max_y, len(self.window_content)-1),
                                               len(self.window_content[cpos[0]])))
                    search = search_iter_factory(
                        self,
                        1,
                        downwards=(find_next >= 0)
                    )
                    for search_pos in search:
                        if search_pos[0] < cpos[0]-max_y or search_pos[0] > cpos[0]+max_y:
                            break
                        self.cpos.set_pos(search_pos)
                        if search.s_len:
                            self.search_items[search_pos] = search.s_len
                            for pos, l in search.s_rows:
                                self.search_items[pos] = l
                    self.cpos.set_pos(cpos)
                    break
                except StopIteration:
                    if self.selecting:
                        self.cpos.set_pos(cpos_tmp)
                        self.spos.set_pos(spos_tmp)
                    tmp_error = 'no matches were found'
                    tmp_error+= ' within the selection!' if self.selecting else '!'
        return True

    def _action_replace(self, replace_next: int = 0) -> bool:
        """
        handles the replace in editor action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        curses.curs_set(0)

        replace_all = False
        wchar, sub_s, tmp_error = '', '', ''
        key, running = b'_key_enter', False
        while str(wchar) != ESC_CODE:
            if not replace_next:
                pre_s = '[]'
                if self.search and isinstance(self.search, str):
                    pre_s = f"[{repr(self.search)[1:-1]}]"
                elif self.search:
                    pre_s = f"re:[{repr(self.search.pattern)[1:-1]}]"
                pre_r = f" [{repr(self.replace)[1:-1]}]" if self.replace else ''
                rep_a = 'ALL ' if replace_all else ''
                self._action_render_scr(
                    f"Confirm: 'ENTER' - Replace {rep_a}{pre_s} with{pre_r}: {frepr(sub_s)}␣",
                    tmp_error
                )
                wchar, key = next(self.get_char)
            elif running:
                break
            running = True
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        sub_s += clipboard
                if key == b'_action_find':
                    cpos_tmp, spos_tmp = self.cpos.get_pos(), self.spos.get_pos()
                    search_items_tmp = self.search_items.copy()
                    getattr(self, key.decode(), lambda *_: False)()
                    self.search_items = search_items_tmp
                    self.cpos.set_pos(cpos_tmp)
                    self.spos.set_pos(spos_tmp)
                    tmp_error = ''
                if key == b'_action_replace':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_insert':
                    replace_all = not replace_all
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                sub_s = sub_s[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = sub_s[-1:].isalnum()
                while sub_s and sub_s[-1:].isalnum() == t_p:
                    sub_s = sub_s[:-1]
            elif key == b'_key_string':
                sub_s += wchar
            elif key == b'_key_enter':
                if not self.search:
                    tmp_error = 'unspecified search!'
                    continue
                self.replace = sub_s if sub_s else self.replace
                if Editor.unicode_escaped_replace and sub_s:
                    try:
                        self.replace = sub_s.encode().decode('unicode_escape').encode('latin-1').decode()
                    except UnicodeError:
                        pass
                cpos_tmp, spos_tmp = self.cpos.get_pos(), self.spos.get_pos()
                sel_pos_a, sel_pos_b = self.selected_area
                if self.selecting and self.cpos.get_pos() == sel_pos_b and replace_next >= 0:
                    self.cpos.set_pos(sel_pos_a)
                    self.spos.set_pos(sel_pos_b)
                elif self.selecting and self.cpos.get_pos() == sel_pos_a and replace_next < 0:
                    self.cpos.set_pos(sel_pos_b)
                    self.spos.set_pos(sel_pos_a)
                try:
                    search = search_iter_factory(
                        self,
                        0,
                        True,
                        downwards=(replace_next >= 0)
                    )
                except ValueError as exc:
                    tmp_error = str(exc)
                    continue
                for search_pos in search:
                    self.cpos.set_pos(search_pos)
                    if search.r_len:
                        self.search_items[search_pos] = search.r_len
                    self._replace_search(self.search, self.replace, search)
                    if replace_next < 0:
                        self.cpos.set_pos(search_pos)
                    if not replace_all:
                        break
                else:
                    if search.yielded_result:
                        self.cpos.col -= search.r_len
                if self.selecting:
                    self.cpos.set_pos(cpos_tmp)
                    self.spos.set_pos(spos_tmp)
                if search.yielded_result:
                    break
                tmp_error = 'no matches were found'
                tmp_error+= ' within the selection!' if self.selecting else '!'
        return True

    def _action_reload(self) -> bool:
        """
        prompt to reload the file.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        curses.curs_set(0)

        wchar = ''
        while str(wchar).upper() not in [ESC_CODE, 'N']:
            self._action_render_scr('Reload File? [y]es, [n]o; Abort? ESC')
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_reload':
                    wchar = 'Y'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if wchar.upper() in ['Y', 'J']:
                self._setup_file()
                self._build_file_upto()
                self.cpos.row = min(self.cpos.row, len(self.window_content)-1)
                self.history.clear()
                break

        return True

    def _action_insert(self) -> bool:
        """
        handles the insert bytes action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        tmp_error_bar = ''
        wchar, i_bytes = '', ''
        while str(wchar) != ESC_CODE:
            self._action_render_scr(f"Confirm: 'ENTER' - Insert byte(s): 0x{i_bytes}␣",
                                    tmp_error_bar)
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        i_bytes += ''.join(filter(HEX_BYTE_KEYS.__contains__, clipboard))
                if key == b'_action_insert':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                i_bytes = i_bytes[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = i_bytes[-1:].isalpha()
                while i_bytes and i_bytes[-1:].isalpha() == t_p:
                    i_bytes = i_bytes[:-1]
            elif key == b'_key_string' and all(wch in HEX_BYTE_KEYS for wch in wchar.upper()):
                i_bytes += wchar.upper()
            elif key == b'_key_enter':
                try:
                    i_string = bytes.fromhex(i_bytes).decode(self.file_encoding)
                except (ValueError, UnicodeError) as exc:
                    tmp_error_bar = str(exc)
                    continue
                pre_cpos = self.cpos.get_pos()
                pre_spos = self.spos.get_pos()
                pre_selecting = self.selecting
                action_text = self._key_string(i_string)
                self.history.add(b'_key_string', False,
                                    pre_cpos, self.cpos.get_pos(),
                                    pre_spos, self.spos.get_pos(),
                                    pre_selecting, self.selecting,
                                    action_text)
                break
        return True

    def _action_background(self) -> bool:
        if on_windows_os:
            self._build_file()
            success = save_view_state(self)
            if not success:
                self.error_bar = 'Error saving view state for backgrounding!'
            return not success
        # only callable on UNIX
        curses.endwin()
        os.kill(os.getpid(), signal.SIGSTOP)
        self._init_screen()
        self.get_char = self._get_new_char()
        return True

    def _action_quit(self) -> bool:
        """
        handles the quit editor action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        if self.unsaved_progress:
            curses.curs_set(0)

            wchar = ''
            while self.unsaved_progress and str(wchar).upper() != 'N':
                self._action_render_scr('Save changes? [y]es, [n]o; Abort? ESC')
                wchar, key = next(self.get_char)
                if key in ACTION_HOTKEYS:
                    if key == b'_action_quit':
                        break
                    if key == b'_action_interrupt':
                        return True
                    if key == b'_action_background':
                        getattr(self, key.decode(), lambda *_: False)()
                    if key == b'_action_save':
                        getattr(self, key.decode(), lambda *_: False)()
                    if key == b'_action_resize':
                        getattr(self, key.decode(), lambda *_: False)()
                        self._render_scr()
                        curses.curs_set(0)
                if not isinstance(wchar, str):
                    continue
                if wchar.upper() in ['Y', 'J']:
                    self._action_save()
                elif wchar == ESC_CODE: # ESC
                    self.open_next_idx = None
                    self.open_next_hash = None
                    return True

        return False

    def _action_interrupt(self) -> bool:
        """
        handles the interrupt action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        logger('Interrupting...', priority=logger.DEBUG)
        raise KeyboardInterrupt

    def _action_resize(self) -> bool:
        """
        handles the resizing of the (terminal) window.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        try:
            curses.resize_term(*self.curse_window.getmaxyx())
        except curses.error:
            pass
        self.curse_window.clear()
        return True

    def _action_file_selection(self) -> bool:
        """
        handles the file selection action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """

        curses.curs_set(0)
        self.curse_window.clear()

        def _find_current_idx(target_file: Path, target_display: str) -> int:
            try:
                return self.files.index((target_file, target_display))
            except ValueError:
                for idx, (file_path, _) in enumerate(self.files):
                    if file_path == target_file:
                        return idx
            return 0

        selected_idx = _find_current_idx(self.file, self.display_name)

        max_y, max_x = self.getxymax()
        max_y += self.status_bar_size - 2
        nav_x = 0
        nav_y = max(0, min(selected_idx - max_y // 2, len(self.files) - max_y))

        mode = 'files'
        file_commits = None
        file_selected_idx = selected_idx

        wchar, key = '', b''
        while str(wchar) != ESC_CODE:
            if mode == 'files':
                data_list = self.files
                maxlen_displayname = max(
                    (len(display_name) for _, display_name in self.files[nav_y:nav_y+max_y]),
                    default=0
                )
            else:
                data_list = file_commits or []
                maxlen_displayname = max((
                    len(f"{commit['hash'][:7]} | {commit['date'][:10]} | {commit['author']} | {commit['message']}")
                    for commit in data_list[nav_y:nav_y+max_y]
                ), default=0)

            self.curse_window.move(max_y, 0)
            self.curse_window.clrtoeol()
            for row in range(max_y):
                entry_idx = row + nav_y
                if entry_idx >= len(data_list):
                    break

                if mode == 'files':
                    file_path, display_name = data_list[entry_idx]
                    is_selected = selected_idx == entry_idx
                    is_current = file_path == self.file
                else:
                    commit = data_list[entry_idx]
                    display_name = f"{commit['hash'][:7]} | {commit['date'][:10]} | {commit['author']} | {commit['message']}"
                    is_selected = selected_idx == entry_idx

                    current_hash = self.file_commit_hash
                    if isinstance(current_hash, dict):
                        current_hash = current_hash.get('hash')
                    is_current = (
                        self.files[file_selected_idx][0] == self.file and (
                            (commit['hash'] == '_LOCAL_' and current_hash is None) or
                            (commit['hash'] == current_hash)
                        )
                    )

                color = 0
                if is_selected and is_current:
                    color = self._get_color(8)
                elif is_selected:
                    color = self._get_color(1)
                elif is_current:
                    color = self._get_color(9)

                try:
                    self.curse_window.addstr(
                        row, 0, f"{display_name}"[nav_x:nav_x+max_x].ljust(max_x),
                        color
                    )
                    self.curse_window.clrtoeol()
                except curses.error:
                    break

                if row == max_y - 1:
                    if len(data_list) > max_y + nav_y:
                        self.curse_window.addstr(row+1, 0, '...')
                        self.curse_window.clrtoeol()
                    break
            self.curse_window.clrtobot()

            if mode == 'files':
                status_msg = 'Select file to open. Confirm with <Enter> or <Space>.'
            else:
                status_msg = 'Select commit (or go back with <Escape>). Confirm with <Enter> or <Space>.'

            try:
                self.curse_window.addstr(
                    max_y+1, 0,
                    status_msg[:max_x].ljust(max_x),
                    self._get_color(1)
                )
            except curses.error:
                pass

            self.curse_window.refresh()

            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_file_selection':
                    wchar, key = ' ', b'_key_string'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    max_y, max_x = self.getxymax()
                    max_y += self.status_bar_size - 2
            if key in MOVE_HOTKEYS:
                list_len = len(data_list)
                if list_len == 0:
                    continue

                if key == b'_move_key_up':
                    selected_idx = max(0, selected_idx - 1)
                    nav_y = min(nav_y, selected_idx)
                elif key == b'_move_key_ctl_up':
                    selected_idx = max(0, selected_idx - 10)
                    nav_y = min(nav_y, selected_idx)
                elif key == b'_move_key_down':
                    selected_idx = min(list_len - 1, selected_idx + 1)
                    if selected_idx >= nav_y + max_y - 1:
                        nav_y = selected_idx - max_y + 1
                elif key == b'_move_key_ctl_down':
                    selected_idx = min(list_len - 1, selected_idx + 10)
                    if selected_idx >= nav_y + max_y - 1:
                        nav_y = selected_idx - max_y + 1
                elif key == b'_move_key_left':
                    nav_x = max(0, nav_x - 1)
                elif key == b'_move_key_ctl_left':
                    nav_x = max(0, nav_x - 10)
                elif key == b'_move_key_right':
                    nav_x = max(0, min(maxlen_displayname - max_x, nav_x + 1))
                elif key == b'_move_key_ctl_right':
                    nav_x = max(0, min(maxlen_displayname - max_x, nav_x + 10))

            if key == b'_key_enter' or (key == b'_key_string' and wchar == ' '):
                if mode == 'files':
                    file_selected_idx = selected_idx

                    try:
                        file_commits = GitHelper.get_git_file_history(
                            self.files[file_selected_idx][0]
                        )
                    except OSError:
                        file_commits = None

                    if file_commits:
                        file_commits = [
                            {
                                'hash': '_LOCAL_', 'date': ' _Latest_ ',
                                'author': '_Local_', 'message': 'Use local file (not git)'
                            }
                        ] + file_commits
                        mode = 'commits'
                        selected_idx = 0
                        if self.file_commit_hash is not None:
                            try:
                                selected_idx = file_commits.index(self.file_commit_hash) if (
                                    isinstance(self.file_commit_hash, dict)
                                ) else [
                                    item['hash'] for item in file_commits
                                ].index(self.file_commit_hash)
                            except ValueError:
                                pass
                        nav_x = 0
                        nav_y = 0
                        self.curse_window.clear()
                    else:
                        current_idx = _find_current_idx(self.file, self.display_name)
                        if file_selected_idx != current_idx:
                            self.open_next_idx = file_selected_idx
                        break
                else:
                    current_idx = _find_current_idx(self.file, self.display_name)

                    current_hash = None if (
                        file_commits and file_commits[selected_idx]['hash'] == '_LOCAL_'
                    ) else (
                        file_commits[selected_idx] if file_commits else None
                    )

                    if file_selected_idx != current_idx or self.file_commit_hash != current_hash:
                        self.open_next_idx = file_selected_idx
                        self.open_next_hash = current_hash
                    break

            if mode == 'commits' and str(wchar) == ESC_CODE:
                mode = 'files'
                wchar = ''
                selected_idx = file_selected_idx
                nav_x = 0
                nav_y = max(0, min(selected_idx - max_y // 2, len(self.files) - max_y))

        self.curse_window.clear()
        return True if self.open_next_idx is None else self._action_quit()

    def _function_help(self) -> None:
        curses.curs_set(0)
        self.curse_window.clear()
        coff = 20

        help_text = [
            f"{'F1':<{coff}}help",
            '',
            f"{'^A':<{coff}}select all",
            f"{'^C':<{coff}}copy selection",
            f"{'^V':<{coff}}paste from clipboard",
            f"{'^X':<{coff}}cut selection",
            '',
            f"{'^Z':<{coff}}undo",
            f"{'^Y':<{coff}}redo",
            '',
            f"{'^E':<{coff}}jump to line",
            f"{'^T':<{coff}}transform",
            f"{'^N':<{coff}}insert byte sequence",
            f"{'^F':<{coff}}find strings or patterns",
            f"{'(Shift-)F3':<{coff}}find next/(previous)",
            f"{'^P':<{coff}}replace string or pattern",
            f"{'(Shift-)F2':<{coff}}replace next/(previous)",
            '',
            f"{'(Shift-)Tab':<{coff}}(de-)indent",
            '',
            f"{'alt+S' if self.save_with_alt else '^S':<{coff}}save file",
            f"{'^R':<{coff}}reload file",
            f"{'Ctrl+F1':<{coff}}open file manager",
            f"{'F4':<{coff}}open syntax highlighter selection",
            '',
            f"{'^B':<{coff}}put editor in background",
            f"{'^D':<{coff}}interrupt/force close",
            f"{'^Q':<{coff}}quit",
        ]
        max_y, max_x = self.getxymax()
        coff = ' ' * ((max_x - max(len(line) for line in help_text)) // 2)
        for row, line in enumerate(
            help_text,
            start = max(
                (max_y+self.status_bar_size-len(help_text)) // 2,
                0
            )
        ):
            try:
                self.curse_window.addstr(row, 0, coff + f"{line}")
            except curses.error:
                self.curse_window.addstr(row-1, 0, coff + '...')
                self.curse_window.clrtoeol()
                break
        self.curse_window.refresh()
        next(self.get_char)

    def _function_search(self) -> None:
        if not self.search:
            return
        self._action_find(1)

    def _function_search_r(self) -> None:
        if not self.search:
            return
        self._action_find(-1)

    def _function_replace(self) -> None:
        if not self.search:
            return
        self._action_replace(1)

    def _function_replace_r(self) -> None:
        if not self.search:
            return
        self._action_replace(-1)

    def _function_sel_highlight(self) -> None:
        curses.curs_set(0)
        self.curse_window.clear()

        available_plugins, extensions_by_name = SyntaxHighlighter.get_available_plugins()
        current_plugin_name = next(
            (k for k, v in available_plugins.items() if v == self._syntax_highlighter),
            None
        )
        selected_idx = 0
        if self._syntax_highlighter is not None:
            selected_idx = list(available_plugins.values()).index(self._syntax_highlighter)
        available_plugins = list(available_plugins.keys())

        max_y, max_x = self.getxymax()
        max_y += self.status_bar_size - 2
        nav_x = 0
        nav_y = max(0, min(selected_idx - max_y // 2, len(available_plugins) - max_y))

        wchar, key = '', b''
        while str(wchar) != ESC_CODE:
            maxlen_displayname = max(
                (len(plugin) for plugin in available_plugins),
                default=0
            )

            self.curse_window.move(max_y, 0)
            self.curse_window.clrtoeol()
            for row in range(max_y):
                entry_idx = row + nav_y
                if entry_idx >= len(available_plugins):
                    break

                is_selected = selected_idx == entry_idx
                is_current = available_plugins[entry_idx] == current_plugin_name

                color = 0
                if is_selected and is_current:
                    color = self._get_color(8)
                elif is_selected:
                    color = self._get_color(1)
                elif is_current:
                    color = self._get_color(9)

                try:
                    self.curse_window.addstr(
                        row, 0,
                        f"Language mode: {available_plugins[entry_idx]} {extensions_by_name.get(available_plugins[entry_idx], '')}"[nav_x:nav_x+max_x].ljust(max_x),
                        color
                    )
                    self.curse_window.clrtoeol()
                except curses.error:
                    break

                if row == max_y - 1:
                    if len(available_plugins) > max_y + nav_y:
                        self.curse_window.addstr(row+1, 0, '...')
                        self.curse_window.clrtoeol()
                    break
            self.curse_window.clrtobot()

            status_msg = 'Select syntax highlighter. Confirm with <Enter> or <Space>.'
            try:
                self.curse_window.addstr(
                    max_y+1, 0,
                    status_msg[:max_x].ljust(max_x),
                    self._get_color(1)
                )
            except curses.error:
                pass

            self.curse_window.refresh()

            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    max_y, max_x = self.getxymax()
                    max_y += self.status_bar_size - 2
            elif key in FUNCTION_HOTKEYS:
                if key == b'_function_sel_highlight':
                    wchar, key = ' ', b'_key_string'
            elif key in MOVE_HOTKEYS:
                list_len = len(available_plugins)
                if list_len == 0:
                    continue

                if key == b'_move_key_up':
                    selected_idx = max(0, selected_idx - 1)
                    nav_y = min(nav_y, selected_idx)
                elif key == b'_move_key_ctl_up':
                    selected_idx = max(0, selected_idx - 10)
                    nav_y = min(nav_y, selected_idx)
                elif key == b'_move_key_down':
                    selected_idx = min(list_len - 1, selected_idx + 1)
                    if selected_idx >= nav_y + max_y - 1:
                        nav_y = selected_idx - max_y + 1
                elif key == b'_move_key_ctl_down':
                    selected_idx = min(list_len - 1, selected_idx + 10)
                    if selected_idx >= nav_y + max_y - 1:
                        nav_y = selected_idx - max_y + 1
                elif key == b'_move_key_left':
                    nav_x = max(0, nav_x - 1)
                elif key == b'_move_key_ctl_left':
                    nav_x = max(0, nav_x - 10)
                elif key == b'_move_key_right':
                    nav_x = max(0, min(maxlen_displayname - max_x, nav_x + 1))
                elif key == b'_move_key_ctl_right':
                    nav_x = max(0, min(maxlen_displayname - max_x, nav_x + 10))

            if key == b'_key_enter' or (key == b'_key_string' and wchar == ' '):
                _syntax_highlighter = SyntaxHighlighter.get_plugin(available_plugins[selected_idx])
                if _syntax_highlighter != self._syntax_highlighter:
                    self._syntax_highlighter = _syntax_highlighter
                    self._syntax_cache.clear()
                    self._init_highlighter_colors()
                break

    def _get_new_char(self):
        """
        get next char

        Yields
        (wchar, key) (tuple):
            the char received and the possible action it means.
        """
        def debug_out(wchar_, key__, key_) -> None:
            _debug_info = repr(chr(wchar_)) if isinstance(wchar_, int) else \
                ord(wchar_) if len(wchar_) == 1 else '-'
            logger(f"__DEBUG__: Received  {str(key_):<22}{_debug_info}" + \
                f"\t{str(key__):<15} \t{repr(wchar_)}", priority=logger.DEBUG)
        buffer: tuple = None
        while True:
            if buffer is not None:
                key = UNIFY_HOTKEYS.get(buffer[1], b'_key_string')
                debug_out(*buffer, key)
                yield (buffer[0], key)
                buffer = None
            wchar = self.curse_window.get_wch()
            _key = curses.keyname(wchar if isinstance(wchar, int) else ord(wchar))
            key = UNIFY_HOTKEYS.get(_key, b'_key_string')

            if key == b'_key_string':
                self.curse_window.nodelay(True)
                while True:
                    try:
                        nchar = self.curse_window.get_wch()
                        if UNIFY_HOTKEYS.get(curses.keyname(
                            nchar if isinstance(nchar, int) else ord(nchar)
                        ), b'_key_string') == b'_key_string':
                            wchar += nchar
                        else:
                            buffer = (nchar, curses.keyname(
                                nchar if isinstance(nchar, int) else ord(nchar)
                            ))
                            break
                    except curses.error:
                        break

            self.curse_window.nodelay(False)
            debug_out(wchar, _key, key)
            yield (wchar, key)

    def _get_color(self, c_id: int) -> int:
        """
        get curses color by id.

        Parameter:
        c_id (int):
            the id of the color to grab

        Returns
        (int):
            the curses.color
        """
        if not curses.has_colors():
            return 0
        return curses.color_pair(c_id)

    def _enforce_boundaries(self, key: bytes) -> None:
        """
        Enforce boundary constraints for cursor and window positions.
        Adjusts cursor snap position, window position and column boundaries
        based on cursor movement and window size.

        Parameters:
        key (bytes):
            The key that was pressed last
        """
        max_y, max_x = self.getxymax()

        # fix cursor position (makes movement hotkeys easier)
        rowlen = len(self.window_content[self.cpos.row]) if(
            self.cpos.row < len(self.window_content)
        ) else 0
        if key in MOVE_HOTKEYS | SELECT_HOTKEYS and (
            b'_up' in key or b'_down' in key
        ):
            self.snap_pos.row = self.cpos.row
            self.cpos.col = min(self.snap_pos.col, rowlen)
        else:
            self.snap_pos.set_pos(self.cpos.get_pos())
        self.cpos.col = min(self.cpos.col, rowlen)

        if not self.scrolling:
            if self.cpos.row < self.wpos.row:
                self.wpos.row = self.cpos.row
            elif self.cpos.row >= self.wpos.row + max_y:
                self.wpos.row = self.cpos.row - max_y + 1
            if self.cpos.col < self.wpos.col:
                self.wpos.col = self.cpos.col
            elif self.cpos.col >= self.wpos.col + max_x:
                self.wpos.col = self.cpos.col - max_x + 1

    def _render_scr(self) -> None:
        """
        render the curses window.
        """
        max_y, max_x = self.getxymax()
        # self._enforce_boundaries()
        self._get_syntax_tokens(self.wpos.row, min(self.wpos.row+max_y, len(self.window_content)))

        # display screen
        self.curse_window.move(0, 0)
        for row in range(max_y):
            brow = row + self.wpos.row
            if brow >= len(self.window_content):
                for i_row in range(row, max_y):
                    color = self._get_color(10)
                    self.curse_window.addch(i_row, 0, '~', color)
                    self.curse_window.clrtoeol()
                break

            syntax_token_idx = 0
            for col in range(max_x):
                bcol = col + self.wpos.col
                if bcol >= len(self.window_content[brow]):
                    break
                cur_char = self.window_content[brow][bcol]
                color = 0

                if cur_char == '\t':
                    cur_char = '>'
                    color = self._get_color(4)
                elif not cur_char.isprintable():
                    cur_char = self._get_special_char(cur_char)
                    color = self._get_color(3)
                elif self.window_content[brow][bcol:].isspace():
                    color = self._get_color(3)
                elif self._syntax_highlighter is not None:
                    syntax_tokens = self._syntax_cache.get(brow, [None, None, None, []])[3]
                    while syntax_token_idx < len(syntax_tokens) and bcol >= syntax_tokens[syntax_token_idx][1]:
                        syntax_token_idx += 1
                    if syntax_token_idx < len(syntax_tokens):
                        token_start, token_end, token_type = syntax_tokens[syntax_token_idx]
                        if token_start <= bcol < token_end:
                            syntax_color = self._SYNTAX_COLOR_IDS.get(token_type)
                            if syntax_color is not None:
                                color = self._get_color(syntax_color)

                sel_from, sel_to = self.selected_area
                if self.selecting and sel_from <= (brow, bcol) < sel_to:
                    color = self._get_color(5)

                if is_special_character(cur_char):
                    cur_char = '�'
                    color = self._get_color(3)

                try:
                    self.curse_window.addstr(row, col, cur_char, color)
                except curses.error:
                    self.curse_window.addch(row, col, ord(cur_char), self._get_color(3))

            self.curse_window.clrtoeol()
            self.curse_window.move(row+1, 0)

        for (row, col), length in self.search_items.items():
            if row < self.wpos.row or row >= self.wpos.row+max_y:
                continue
            if col+length < self.wpos.col or col >= self.wpos.col+max_x:
                continue
            if col < self.wpos.col:
                length -= self.wpos.col - col
                col = self.wpos.col
            self.curse_window.chgat(
                row-self.wpos.row,
                col-self.wpos.col,
                length,
                self._get_color(6)
            )
        if self.cpos.get_pos() in self.search_items:
            self.curse_window.chgat(
                self.cpos.row-self.wpos.row,
                self.cpos.col-self.wpos.col,
                self.search_items[self.cpos.get_pos()],
                self._get_color(4)
            )
            for (row, col), length in self.search_items_focused_span:
                if row < self.wpos.row or row >= self.wpos.row+max_y:
                    continue
                if col+length < self.wpos.col or col >= self.wpos.col+max_x:
                    continue
                if col < self.wpos.col:
                    length -= self.wpos.col - col
                    col = self.wpos.col
                self.curse_window.chgat(
                    row-self.wpos.row,
                    col-self.wpos.col,
                    length,
                    self._get_color(4)
                )
        self.search_items.clear()
        self.search_items_focused_span.clear()

        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            status_bar = f"File: {self.display_name} | Help: F1 | "
            status_bar += f"Ln {self.cpos.row+1}, Col {self.cpos.col+1} "
            status_bar += f"| {'NOT ' * self.unsaved_progress}Saved!"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.display_name) + 3))
                status_bar = f"File: ...{self.display_name[-necc_space:] * bool(necc_space)} "
                status_bar += '| Help: F1 | '
                status_bar += f"Ln {self.cpos.row+1}, Col {self.cpos.col+1} "
                status_bar += f"| {'NOT ' * self.unsaved_progress}Saved!"
                if self.debug_mode:
                    status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            # this throws an error (should be max_x-1), but looks better:
            status_bar = status_bar[:max_x].ljust(max_x)
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                     status_bar, self._get_color(1))
        except curses.error:
            pass

        try:
            # can throw an error when using the scrolling functionality:
            # ==> max(self.cpos.row-self.wpos.row, 0) > max_y ==> Error
            # ==> max(self.cpos.col-self.wpos.col, 0) > max_x ==> Error
            self.curse_window.move(max(self.cpos.row-self.wpos.row, 0),
                                   max(self.cpos.col-self.wpos.col, 0))
        except curses.error:
            pass
        curses.curs_set(
            not self.scrolling or not (
                self.cpos.row < self.wpos.row or \
                self.cpos.col < self.wpos.col or \
                self.cpos.row >= self.wpos.row+max_y or \
                self.cpos.col >= self.wpos.col+max_x
            )
        )

        self.scrolling = False
        self.curse_window.refresh()

    def _run(self) -> None:
        """
        main loop for the editor.
        """
        running = True

        while running:
            self._render_scr()
            force_render = 0
            while True:
                self._build_file_upto()
                try:
                    wchar, key = next(self.get_char)

                    # handle new wchar
                    self.deleted_line = False
                    pre_cpos = self.cpos.get_pos()
                    pre_spos = self.spos.get_pos()
                    pre_selecting = self.selecting
                    action_text = None
                    if key in KEY_HOTKEYS:
                        if self.selecting:
                            self._remove_chunk()
                            pre_cpos = self.cpos.get_pos()
                            pre_spos = self.spos.get_pos()
                        action_text = getattr(self, key.decode(), lambda *_: None)(wchar)
                    elif key in INDENT_HOTKEYS:
                        action_text = getattr(self, key.decode(), lambda *_: None)(wchar)
                    # actions like search, jump, quit, save, resize:
                    elif key in ACTION_HOTKEYS:
                        running &= getattr(self, key.decode(), lambda *_: True)()
                    # scrolling via alt + ...
                    elif key in SCROLL_HOTKEYS:
                        self.scrolling = True
                        getattr(self, key.decode(), lambda *_: None)()
                    # moving the cursor:
                    elif key in MOVE_HOTKEYS | HISTORY_HOTKEYS | FUNCTION_HOTKEYS:
                        getattr(self, key.decode(), lambda *_: None)()
                    # select text:
                    if key in SELECT_HOTKEYS:
                        if not self.selecting:
                            self.spos.set_pos(self.cpos.get_pos())
                        getattr(self, key.decode(), lambda *_: None)()
                        self.selecting = True
                    elif key not in (INDENT_HOTKEYS | HISTORY_HOTKEYS) and key != b'_move_key_mouse':
                        self.selecting = False

                    self._enforce_boundaries(key)

                    self.history.add(key, self.deleted_line,
                                        pre_cpos, self.cpos.get_pos(),
                                        pre_spos, self.spos.get_pos(),
                                        pre_selecting, self.selecting,
                                        action_text)

                    if Editor.auto_indent and key == b'_key_enter':
                        pre_cpos = self.cpos.get_pos()
                        pre_spos = self.spos.get_pos()
                        pre_selecting = self.selecting
                        indent_offset = 0
                        while self.window_content[self.cpos.row-1][indent_offset:].startswith(
                            self.special_indentation
                        ):
                            indent_offset += len(self.special_indentation)
                        action_text = self._key_string(
                            (indent_offset//len(self.special_indentation)) * \
                                self.special_indentation
                        )
                        if indent_offset > 0:
                            self.history.add(b'_key_string', False,
                                                pre_cpos, self.cpos.get_pos(),
                                                pre_spos, self.spos.get_pos(),
                                                pre_selecting, self.selecting,
                                                action_text)

                    self.curse_window.nodelay(True)
                    force_render += 1
                    if force_render > 50:
                        break
                except curses.error:
                    self.curse_window.nodelay(False)
                    self.get_char = self._get_new_char()
                    break

    def _init_highlighter_colors(self) -> None:
        if curses.can_change_color():
            bg_color = -1
            try:
                # syntax-highlight keyword
                curses.init_pair(200, curses.COLOR_CYAN, bg_color)
            except curses.error:
                bg_color = curses.COLOR_BLACK
                curses.init_pair(200, curses.COLOR_CYAN, bg_color)
            # syntax-highlight string
            curses.init_pair(201, curses.COLOR_GREEN   , bg_color)
            # syntax-highlight number
            curses.init_pair(202, curses.COLOR_RED+8   , bg_color)
            # syntax-highlight comment
            curses.init_pair(203, curses.COLOR_BLACK+8 , bg_color)
            # syntax-highlight builtin
            curses.init_pair(204, curses.COLOR_BLUE    , bg_color)
            if self._syntax_highlighter and self._syntax_highlighter.token_color_map:
                new_color_id = max(self._SYNTAX_COLOR_IDS.values(), default=204) + 1
                for token_type, color in self._syntax_highlighter.token_color_map.items():
                    if token_type not in self._SYNTAX_COLOR_IDS:
                        self._SYNTAX_COLOR_IDS[token_type] = new_color_id
                        new_color_id += 1
                    color = color.casefold()
                    color_offset = 0
                    if color.startswith('light'):
                        color = color[5:]
                        color_offset = 8
                    curses_color = getattr(curses, f'COLOR_{color.upper()}', None)
                    if curses_color is not None:
                        curses.init_pair(
                            self._SYNTAX_COLOR_IDS[token_type], curses_color + color_offset, -1
                        )

    def _init_screen(self) -> None:
        """
        init and define curses
        """
        self.curse_window = curses.initscr()

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()

        curses.mousemask(-1)
        curses.mouseinterval(100)

        # inspired by:
        # -------- https://github.com/asottile/babi -------- #
        # set the escape delay so curses does not pause waiting for sequences
        if (
                sys.version_info >= (3, 9) and
                hasattr(curses, 'set_escdelay')
        ):  # pragma: >=3.9 cover
            curses.set_escdelay(25)
        else:  # pragma: <3.9 cover
            os.environ.setdefault('ESCDELAY', '25')
        # ----------------------------------------------------------------------- #

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        self.curse_window.keypad(1)
        try:
            curses.start_color()
        finally:
            if curses.can_change_color():
                if not on_windows_os:
                    curses.use_default_colors()
                bg_color = -1
                # status_bar
                curses.init_pair(1 , curses.COLOR_BLACK  , curses.COLOR_WHITE )
                # error_bar
                curses.init_pair(2 , curses.COLOR_RED    , curses.COLOR_WHITE )
                # special char (not printable or ws) & prompts
                curses.init_pair(3 , curses.COLOR_WHITE  , curses.COLOR_RED   )
                # tab-char & current match
                curses.init_pair(4 , curses.COLOR_BLACK  , curses.COLOR_GREEN )
                # selection
                curses.init_pair(5 , curses.COLOR_BLACK  , curses.COLOR_YELLOW)
                # find & replace
                curses.init_pair(6 , curses.COLOR_WHITE  , curses.COLOR_BLUE  )
                # correct transform query
                curses.init_pair(7 , curses.COLOR_GREEN  , curses.COLOR_WHITE )
                # file-selector, active file
                curses.init_pair(8 , curses.COLOR_MAGENTA, curses.COLOR_WHITE )
                try:
                    # file-selector, active file selected
                    curses.init_pair(9 , curses.COLOR_MAGENTA, bg_color       )
                except curses.error:
                    logger(
                        'Your terminal does not support default background color. '
                        'Syntax highlighting might look weird. '
                        'Consider switching to a different terminal or adjusting its settings.',
                        priority=logger.DEBUG
                    )
                    bg_color = curses.COLOR_BLACK
                    # file-selector, active file selected
                    curses.init_pair(9 , curses.COLOR_MAGENTA, bg_color       )
                # ~ characters to indicate lines after the end of the file
                curses.init_pair(10, curses.COLOR_BLUE       , bg_color       )
        curses.raw()
        self.curse_window.nodelay(False)

    def _open(self, fg: bool = False) -> None:
        """
        init, run, deinit
        """
        try:
            self._init_screen()
            self._init_highlighter_colors()
            if fg:
                self.get_char = self._get_new_char()
                self._f_content_gen = (line for line in [])
                if self.file_commit_hash is None and get_view_state_time() < get_file_mtime(self.file):
                    self.error_bar = 'Out-Of-Sync Error: The file has been modified since backgrounding.'
            else:
                self._build_file_upto()
            self._run()
        except (Exception, KeyboardInterrupt) as e:
            curses.endwin()
            if not self.unsaved_progress:
                raise e
            if not isinstance(e, KeyboardInterrupt):
                logger('Oops..! Something went wrong.', priority=logger.ERROR)
            user_input = ''
            while user_input not in ['Y', 'J', 'N']:
                user_input = input('Do you want to save the changes? [Y/N]').upper()
            if user_input == 'N':
                raise e
            self._action_save()
            if self.unsaved_progress:
                logger(
                    'Oops..! Something went wrong. The file could not be saved.',
                    priority=logger.ERROR
                )
            else:
                logger('The file has been successfully saved.', priority=logger.INFO)
            raise e
        finally:
            try: # cleanup - close file
                self._f_content_gen.close()
            except StopIteration:
                pass
            except Exception as exc:
                logger(f"Error while closing file: {exc}", priority=logger.ERROR)
            curses.endwin()

    @classmethod
    def open(cls, files: list, skip_binary: bool = False, fg_state = None) -> bool:
        """
        simple editor to change the contents of any provided file.

        Parameters:
        files (list):
            list of tuples (file, display_name)
        skip_binary (bool):
            indicates if the Editor should skip non-plaintext files
        fg_state:
            the state of the previously opened editor that got put into background

        Returns:
        (bool):
            indicates whether or not the editor has written any content to the provided files
        """
        if Editor.loading_failed:
            return False

        if CURSES_MODULE_ERROR:
            logger(
                "The Editor could not be loaded. No Module 'curses' was found.",
                priority=logger.INFO
            )
            if on_windows_os:
                logger(
                    'If you are on Windows OS, try pip-installing ', end='',
                    priority=logger.INFO
                )
                logger("'windows-curses'.", priority=logger.INFO)
            logger(priority=logger.INFO)
            Editor.loading_failed = True
            return False

        changes_made = False

        if fg_state is None:
            editor = cls(files)
            if skip_binary and editor.error_bar:
                return False
            special_chars = dict(map(lambda x: (chr(x[0]), x[2]), SPECIAL_CHARS))
            editor._set_special_chars(special_chars)
        else:
            editor = fg_state

        if not on_windows_os:
            # ignore background signals on UNIX, since a custom background implementation exists
            signal.signal(signal.SIGTSTP, signal.SIG_IGN)

        editor._open(fg=fg_state is not None)
        changes_made |= editor.changes_made
        while editor.open_next_idx is not None:
            editor = cls(
                files,
                file_idx = editor.open_next_idx, file_commit_hash = editor.open_next_hash
            )
            editor._set_special_chars(special_chars)
            editor._open()
            changes_made |= editor.changes_made

        return changes_made

    @staticmethod
    def set_indentation(indentation: str = '\t', auto_indent: bool = True) -> None:
        """
        set the indentation when using tab on an empty line

        Parameters:
        indentation (str):
            the indentation to use (may be choosen by the user via config)
        auto_indent (bool):
            indicates whetcher the editor should automatically match the
            previous indentation when pressing enter
        """
        Editor.special_indentation = indentation
        Editor.auto_indent = auto_indent

    @staticmethod
    def set_flags(save_with_alt: bool, debug_mode: bool,
                  unicode_escaped_search: bool, unicode_escaped_replace: bool,
                  file_encoding: str) -> None:
        """
        set the config flags for the Editor

        Parameters:
        save_with_alt (bool):
            indicates whetcher the stdin pipe has been used (and therefor tampered)
        debug_mode (bool):
            indicates if debug info should be displayed
        unicode_escaped_search (bool):
            indicates if the search should be unicode escaped
        file_encoding (str):
            the file encoding to use when opening a file
        """
        Editor.save_with_alt = save_with_alt
        Editor.debug_mode = debug_mode
        Editor.unicode_escaped_search = unicode_escaped_search
        Editor.unicode_escaped_replace = unicode_escaped_replace
        Editor.file_encoding = file_encoding
