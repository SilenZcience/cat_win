"""
editor
"""

try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import signal
import sys

from cat_win.src.service.helper.editorhelper import History, Position, wcwidth, UNIFY_HOTKEYS, \
    KEY_HOTKEYS, ACTION_HOTKEYS, SCROLL_HOTKEYS, MOVE_HOTKEYS
from cat_win.src.service.helper.iohelper import IoHelper, err_print
from cat_win.src.service.rawviewer import SPECIAL_CHARS


class Editor:
    """
    Editor
    """
    wc_width = wcwidth
    loading_failed = False
    special_indentation = '\t'
    auto_indent = False

    debug_mode = False
    save_with_alt = False

    unicode_escaped_search = True
    file_encoding = 'utf-8'

    def __init__(self, file: str, display_name: str) -> None:
        """
        defines an Editor object.
        
        Parameters:
        file (str):
            a string representation of a file (-path)
        display_name (str):
            the display name for the current file
        """
        self.curse_window = None
        self.history = History()
        self.get_char = self._get_new_char()

        self.file = file
        self.display_name = display_name
        self._f_content_gen = None
        self.line_sep = '\n'
        self.window_content = []

        self.special_chars: dict = {}
        self.search = ''

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False
        self.scrolling = False
        self.deleted_line = False

        # current cursor position
        self.cpos = Position(0, 0)
        # window position (top-left)
        self.wpos = Position(0, 0)

        self._setup_file()

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
        try:
            self.unsaved_progress = False
            self.line_sep = IoHelper.get_newline(self.file)
            self._f_content_gen = IoHelper.yield_file(self.file, False, self.file_encoding)
            self._build_file_upto(30)
            self.error_bar = ''
            self.status_bar_size = 1
        except (OSError, UnicodeError) as exc:
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                err_print(self.error_bar)
        if not self.window_content:
            self.window_content.append('')

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

    def _key_enter(self, _) -> str:
        new_line = self.window_content[self.cpos.row][self.cpos.col:]
        self.window_content[self.cpos.row] = self.window_content[self.cpos.row][:self.cpos.col]
        self.cpos.row += 1
        self.cpos.col = 0
        self.window_content.insert(self.cpos.row, new_line)
        self.unsaved_progress = True
        return ''

    def _key_dc(self, _) -> str:
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
        if self.cpos.col < len(self.window_content[self.cpos.row]):
            cur_col = self.cpos.col
            t_p = self.window_content[self.cpos.row][cur_col].isalnum()
            while cur_col < len(self.window_content[self.cpos.row]) and \
                t_p == self.window_content[self.cpos.row][cur_col].isalnum():
                cur_col += 1
            deleted = self.window_content[self.cpos.row][self.cpos.col:cur_col]
            self.window_content[self.cpos.row] = (
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][cur_col:])
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
            return wchars
        return None

    def _key_ctl_backspace(self, _) -> str:
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

    def _move_key_left(self) -> None:
        if self.cpos.col:
            self.cpos.col -= 1
        elif self.cpos.row:
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])

    def _move_key_right(self) -> None:
        if self.cpos.col < len(self.window_content[self.cpos.row]):
            self.cpos.col += 1
        elif self.cpos.row < len(self.window_content)-1:
            self.cpos.row += 1
            self.cpos.col = 0

    def _move_key_up(self) -> None:
        if self.cpos.row:
            self.cpos.row -= 1

    def _move_key_down(self) -> None:
        if self.cpos.row < len(self.window_content)-1:
            self.cpos.row += 1

    def _move_key_ctl_left(self) -> None:
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
        if self.cpos.row >= 10:
            self.cpos.row -= 10
        else:
            self.cpos.row = 0
            self.cpos.col = 0

    def _move_key_ctl_down(self) -> None:
        if self.cpos.row < len(self.window_content)-10:
            self.cpos.row += 10
        else:
            self.cpos.row = len(self.window_content)-1
            self.cpos.col = len(self.window_content[self.cpos.row])

    def _scroll_key_shift_left(self) -> None:
        self.wpos.col = max(self.wpos.col-1, 0)

    def _scroll_key_shift_right(self) -> None:
        max_y, max_x = self.getxymax()
        max_line = max(map(len,self.window_content[self.wpos.row:self.wpos.row+max_y]))
        self.wpos.col = max(min(self.wpos.col+1, max_line+1-max_x), 0)

    def _scroll_key_shift_up(self) -> None:
        self.wpos.row = max(self.wpos.row-1, 0)

    def _scroll_key_shift_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(min(self.wpos.row+1, len(self.window_content)-max_y), 0)

    def _move_key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(self.wpos.row-max_y, 0)
        self.cpos.row = max(self.cpos.row-max_y, 0)

    def _move_key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row += max_y
        self.cpos.row += max_y
        self._build_file_upto()
        self.wpos.row = max(min(self.wpos.row, len(self.window_content)-max_y), 0)
        self.cpos.row = min(self.cpos.row, len(self.window_content)-1)

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

    def _scroll_key_end(self) -> None:
        self._build_file()
        max_y, max_x = self.getxymax()
        self.wpos.row = max(len(self.window_content)-max_y, 0)
        max_line = max(map(len,self.window_content[-max_y:]))
        self.wpos.col = max(max_line+1-max_x, 0)

    def _move_key_home(self) -> None:
        self.cpos.col = 0

    def _move_key_ctl_home(self) -> None:
        self.cpos.row = 0
        self.cpos.col = 0

    def _scroll_key_home(self) -> None:
        self.wpos.row = 0
        self.wpos.col = 0

    def _key_btab(self, _) -> str:
        c_row = self.window_content[self.cpos.row]
        indent_l = len(self.special_indentation)
        if c_row.startswith(self.special_indentation):
            self.window_content[self.cpos.row] = c_row[indent_l:]
            self.cpos.col = max(self.cpos.col-indent_l, 0)
            return self.special_indentation
        return None

    def _key_btab_reverse(self, tab) -> str:
        c_row = self.window_content[self.cpos.row]
        self.window_content[self.cpos.row] = tab + c_row
        self.cpos.col += len(tab)
        return tab

    def _key_string(self, wchars_) -> str:
        """
        tries to append (a) char(s) to the screen.
        
        Parameters:
        wchars (int|str):
            given by curses get_wch()
        """
        if not isinstance(wchars_, str) or not wchars_:
            return ''

        # windows-curses sometimes returns characters like '\ud83e\udd23' (e.g. emojis)
        # we can fix these with the utf-16 surrogatepass error-handler
        wchars = wchars_.encode('utf-16', 'surrogatepass').decode('utf-16')
        if self.debug_mode and wchars != wchars_:
            err_print(f"__DEBUG__: Changed {wchars_} to {wchars}", end=' ')
            err_print(f"Length: {len(wchars)} Ord: {ord(wchars[0])}")
        # in case the line has no text yet and tab is pressed, we indent with
        # the custom indentation
        if self.special_indentation != '\t' == wchars and \
            (self.window_content[self.cpos.row][:self.cpos.col].replace(
                self.special_indentation, '') + ' ').isspace():
            return self._key_string(self.special_indentation)
        self.unsaved_progress = True
        self.window_content[self.cpos.row] = \
            self.window_content[self.cpos.row][:self.cpos.col] + wchars + \
            self.window_content[self.cpos.row][self.cpos.col:]
        self.cpos.col += len(wchars)
        return wchars

    def _key_undo(self, _) -> str:
        self.history.undo(self)
        return None

    def _key_redo(self, _) -> str:
        self.history.redo(self)
        return None

    def _action_render_scr(self, msg) -> None:
        max_y, max_x = self.getxymax()
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                        self.error_bar[:max_x].ljust(max_x),
                                        self._get_color(2))
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                        msg[:max_x].ljust(max_x),
                                        self._get_color(3))
        except curses.error:
            pass
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
            if self.debug_mode:
                err_print(self.error_bar)
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
        while str(wchar).upper() not in ['\x1b', 'N']:
            self._action_render_scr(f"Confirm: [y]es, [n]o - Jump to line: {l_jmp}␣")
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
                    curses.curs_set(0)
            if not isinstance(wchar, str):
                continue
            if key == b'_key_string' and wchar.isdigit():
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    self.cpos.row = max(int(l_jmp)-1, 0)
                    self._build_file_upto()
                    self.cpos.row = min(self.cpos.row, len(self.window_content)-1)
                break
        return True

    def _action_find(self) -> bool:
        """
        handles the find in editor action.
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        curses.curs_set(0)

        wchar, sub_s = '', ''
        while str(wchar) != '\x1b':
            pre_s = f" [{repr(self.search)[1:-1]}]" if self.search else ''
            self._action_render_scr(f"Confirm: 'ENTER' - Search for{pre_s}: {sub_s}␣")
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
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
                if Editor.unicode_escaped_search and sub_s:
                    try:
                        sub_s = sub_s.encode().decode('unicode_escape').encode('latin-1').decode()
                    except UnicodeError:
                        pass
                self.search = sub_s if sub_s else self.search
                # check current line
                if self.search in self.window_content[self.cpos.row][self.cpos.col+1:]:
                    self.cpos.col += \
                        self.window_content[self.cpos.row][self.cpos.col+1:].find(self.search)+1
                    break
                # check rest of file until back at current line
                c_row = self.cpos.row
                while c_row < self.cpos.row+len(self.window_content):
                    if c_row+1 >= len(self.window_content):
                        self._build_file_upto(c_row+30)
                    c_row += 1
                    c_row_wrapped = c_row%len(self.window_content)
                    if self.search in self.window_content[c_row_wrapped]:
                        self.cpos.row = c_row_wrapped
                        self.cpos.col = self.window_content[c_row_wrapped].find(self.search)
                        break
                break
        return True

    def _action_background(self) -> bool:
        # only callable on UNIX
        curses.endwin()
        os.kill(os.getpid(), signal.SIGSTOP)
        self._init_screen()
        self.get_char = self._get_new_char()
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
        while str(wchar).upper() != ['\x1b', 'N']:
            self._action_render_scr('Reload File? [y]es, [n]o; Abort? ESC')
            wchar, key = next(self.get_char)
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
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
                self.cpos = Position(0, 0)
                self.wpos = Position(0, 0)
                break

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
                elif wchar == '\x1b': # ESC
                    return True

        return False

    def _action_interrupt(self) -> bool:
        """
        handles the interrupt action.
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        if self.debug_mode:
            err_print('Interrupting...')
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

    def _get_new_char(self):
        """
        get next char
        
        Yields
        (wchar, key) (tuple):
            the char received and the possible action it means.
        """
        def debug_out(wchar_, key__, key_) -> None:
            if self.debug_mode:
                _debug_info = repr(chr(wchar_)) if isinstance(wchar_, int) else \
                    ord(wchar_) if len(wchar_) == 1 else '-'
                err_print(f"__DEBUG__: Received  {key_}\t{_debug_info}" + \
                    f"\t{str(key__):<15} \t{repr(wchar_)}")
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
                            buffer = (nchar,
                                    curses.keyname(
                                        nchar if isinstance(nchar, int) else ord(nchar)
                                        )
                                    )
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

    def _render_scr(self) -> None:
        """
        render the curses window.
        """
        max_y, max_x = self.getxymax()

        # fix cursor position (makes movement hotkeys easier)
        row = self.window_content[self.cpos.row] if (
            self.cpos.row < len(self.window_content)) else None
        rowlen = len(row) if row is not None else 0
        self.cpos.col = min(self.cpos.col, rowlen)

        # set/enforce the boundaries
        self.curse_window.move(0, 0)

        if not self.scrolling:
            if self.cpos.row < self.wpos.row:
                self.wpos.row = self.cpos.row
            elif self.cpos.row >= self.wpos.row + max_y:
                self.wpos.row = self.cpos.row - max_y + 1
            if self.cpos.col < self.wpos.col:
                self.wpos.col = self.cpos.col
            elif self.cpos.col >= self.wpos.col + max_x:
                self.wpos.col = self.cpos.col - max_x + 1

        # display screen
        for row in range(max_y):
            brow = row + self.wpos.row
            if brow >= len(self.window_content):
                self.curse_window.clrtobot()
                break
            for col in range(max_x):
                bcol = col + self.wpos.col
                if bcol >= len(self.window_content[brow]):
                    break
                cur_char = self.window_content[brow][bcol]
                if cur_char == '\t':
                    self.curse_window.addch(row, col, '>',
                                            self._get_color(4))
                elif not cur_char.isprintable():
                    self.curse_window.addch(row, col, self._get_special_char(cur_char),
                                            self._get_color(3))
                elif self.window_content[brow][bcol:].isspace():
                    self.curse_window.addch(row, col, cur_char,
                                            self._get_color(3))
                else:
                    try:
                        if Editor.wc_width(cur_char) != 1:
                            raise TypeError
                        # CJK unicode (problems in windows-terminal) fix:
                        # if 12799 < ord(cur_char) < 65103:
                        #     raise TypeError
                        self.curse_window.addch(row, col, cur_char)
                    except TypeError:
                        self.curse_window.addch(row, col, '�', self._get_color(3))
            self.curse_window.clrtoeol()
            self.curse_window.move(row+1, 0)

        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            save_hotkey = ('alt+' if self.save_with_alt else '^') + 's'
            status_bar = f"File: {self.display_name} | Exit: ^q | Save: {save_hotkey} | "
            status_bar += f"Ln {self.cpos.row+1}, Col {self.cpos.col+1} "
            status_bar += f"| {'NOT ' * self.unsaved_progress}Saved!"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.display_name) + 3))
                status_bar = f"File: ...{self.display_name[-necc_space:] * bool(necc_space)} "
                status_bar += f"| Exit: ^q | Save: {save_hotkey} | "
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
        curses.curs_set(not self.scrolling or not (
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
                    if key in KEY_HOTKEYS:
                        pre_pos = self.cpos.get_pos()
                        action_text = getattr(self, key.decode(), lambda *_: None)(wchar)
                        self.history.add(key, action_text, self.deleted_line,
                                         pre_pos, self.cpos.get_pos())
                        if Editor.auto_indent and key == b'_key_enter':
                            indent_offset = 0
                            while self.window_content[self.cpos.row-1][indent_offset:].startswith(
                                self.special_indentation):
                                pre_pos = self.cpos.get_pos()
                                action_text = self._key_string(self.special_indentation)
                                self.history.add(b'_key_string', action_text, self.deleted_line,
                                                 pre_pos, self.cpos.get_pos())
                                indent_offset += len(self.special_indentation)
                    # actions like search, jump, quit, save, resize:
                    elif key in ACTION_HOTKEYS:
                        running &= getattr(self, key.decode(), lambda *_: True)()
                    # scrolling via alt + ...
                    elif key in SCROLL_HOTKEYS:
                        self.scrolling = True
                        getattr(self, key.decode(), lambda *_: None)()
                    # moving the cursor:
                    elif key in MOVE_HOTKEYS:
                        getattr(self, key.decode(), lambda *_: None)()
                    self.curse_window.nodelay(True)
                    force_render += 1
                    if force_render > 50:
                        break
                except curses.error:
                    self.curse_window.nodelay(False)
                    self.get_char = self._get_new_char()
                    break

    def _init_screen(self) -> None:
        """
        init and define curses
        """
        self.curse_window = curses.initscr()

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()

        # --------https://github.com/asottile/babi/blob/main/babi/main.py-------- #
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
                # status_bar
                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
                # error_bar
                curses.init_pair(2, curses.COLOR_RED  , curses.COLOR_WHITE)
                # special char (not printable or ws) & prompts
                curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED  )
                # tab-char
                curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.raw()
        self.curse_window.nodelay(False)

    def _open(self) -> None:
        """
        init, run, deinit
        """
        try:
            self._init_screen()
            self._build_file_upto()
            self._run()
        finally:
            try: # cleanup - close file
                self._f_content_gen.throw(StopIteration)
            except StopIteration:
                pass
            curses.endwin()

    @classmethod
    def open(cls, file: str, display_name: str, on_windows_os: bool,
             skip_binary: bool = False) -> bool:
        """
        simple editor to change the contents of any provided file.
        
        Parameters:
        file (str):
            a string representing a file(-path)
        display_name (str):
            the display name for the current file
        on_windows_os (bool):
            indicates if the user is on windows OS using platform.system() == 'Windows'
        skip_binary (bool):
            indicates if the Editor should skip non-plaintext files
        
        Returns:
        (bool):
            indicates whether or not the editor has written any content to the provided files
        """
        if Editor.loading_failed:
            return False

        if CURSES_MODULE_ERROR:
            err_print("The Editor could not be loaded. No Module 'curses' was found.")
            if on_windows_os:
                err_print('If you are on Windows OS, try pip-installing ', end='')
                err_print("'windows-curses'.")
            err_print()
            Editor.loading_failed = True
            return False

        editor = cls(file, display_name)
        if skip_binary and editor.error_bar:
            return False
        special_chars = dict(map(lambda x: (chr(x[0]), x[2]), SPECIAL_CHARS))
        editor._set_special_chars(special_chars)

        if on_windows_os:
            Editor.wc_width = lambda _: 1
            # disable background feature on windows
            editor._action_background = lambda *_: True
        else:
            # ignore background signals on UNIX, since a custom background implementation exists
            signal.signal(signal.SIGTSTP, signal.SIG_IGN)

        editor._open()
        return editor.changes_made

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
    def set_flags(save_with_alt: bool, debug_mode: bool, unicode_escaped_search: bool,
                  file_encoding: str) -> None:
        """
        set the config flags for the Editor
        
        Parameters:
        save_with_alt (bool):
            indicates whetcher the stdin pipe has been used (and therefor tampered)
        debug_mode (bool)
            indicates if debug info should be displayed
        file_encoding (str):
            the file encoding to use when opening a file
        """
        Editor.save_with_alt = save_with_alt
        Editor.debug_mode = debug_mode
        Editor.unicode_escaped_search = unicode_escaped_search
        Editor.file_encoding = file_encoding
