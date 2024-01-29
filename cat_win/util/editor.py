"""
editor
"""

try:
    import curses
    def initscr():
        """
        fix windows-curses for Python 3.12:
        https://github.com/zephyrproject-rtos/windows-curses/issues/50
        """
        import _curses
        stdscr = _curses.initscr()
        for key, value in _curses.__dict__.items():
            if key[0:4] == 'ACS_' or key in ('LINES', 'COLS'):
                setattr(curses, key, value)

        return stdscr
    curses.initscr = initscr
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import sys

from cat_win.util.editorhelper import History, Position, UNIFY_HOTKEYS, \
    KEY_HOTKEYS, ACTION_HOTKEYS, SCROLL_HOTKEYS
from cat_win.util.rawviewer import SPECIAL_CHARS

def get_newline(file: str) -> str:
    """
    determines the line ending of a given file.
    
    Parameters:
    file (str):
        a file (-path) as string representation
        
    Returns:
    (str):
        the line ending that the given file is using
        (\r or \n or \r\n)
    """
    with open(file, 'rb') as _f:
        _l = _f.readline()
        _l += b'\n' * bool(not _l[-1:] or _l[-1:] not in b'\r\n')
        return '\r\n' if _l[-2:] == b'\r\n' else _l[-1:].decode()


class Editor:
    """
    Editor
    """
    loading_failed = False

    def __init__(self, file: str, file_encoding: str, debug_mode: bool = False) -> None:
        """
        defines an Editor object.
        
        Parameters:
        file (str):
            a string representation of a file (-path)
        file_encoding:
            the encoding to read and write the given file
        debug_mode (bool)
            if True debug-statements will be printed to stderr
        """
        self.curse_window = None
        self.history = History()

        self.file = file
        self.file_encoding = file_encoding
        self.line_sep = '\n'
        self.window_content = []

        self.debug_mode = debug_mode
        self.special_chars: dict = {}

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False
        self.scrolling = False

        # current cursor position
        self.cpos = Position(0, 0)
        # window position (top-left)
        self.wpos = Position(0, 0)

        self._setup_file()

    def _set_special_chars(self, special_chars: dict) -> None:
        self.special_chars = special_chars

    def _get_special_char(self, char: str) -> str:
        if char in self.special_chars.keys():
            return self.special_chars[char]
        return '?'

    def _setup_file(self) -> None:
        """
        setup the editor content screen by reading the given file.
        """
        try:
            self.line_sep = get_newline(self.file)
            with open(self.file, 'r', encoding=self.file_encoding) as _f:
                for line in _f.read().split('\n'):
                    self.window_content.append(line)
        except (OSError, UnicodeDecodeError) as exc:
            self.window_content.append('')
            self.status_bar_size = 2
            self.error_bar = str(exc)
            self.unsaved_progress = True

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
            return ''
        return None

    def _key_dl(self, _) -> str:
        if self.cpos.col == len(self.window_content[self.cpos.row])-1:
            deleted = self.window_content[self.cpos.row][-1]
            self.window_content[self.cpos.row] = self.window_content[self.cpos.row][:-1]
            self.unsaved_progress = True
            return deleted
        if self.cpos.col < len(self.window_content[self.cpos.row])-1:
            cur_col = self.cpos.col+1
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
            return ''
        return None

    def _key_backspace(self, _) -> str:
        if self.cpos.col: # delete char
            self.cpos.col -= 1
            deleted = self.window_content[self.cpos.row][self.cpos.col]
            self.window_content[self.cpos.row] = \
                self.window_content[self.cpos.row][:self.cpos.col] + \
                self.window_content[self.cpos.row][self.cpos.col+1:]
            self.unsaved_progress = True
            return deleted
        if self.cpos.row: # or delete line
            line = self.window_content[self.cpos.row]
            del self.window_content[self.cpos.row]
            self.cpos.row -= 1
            self.cpos.col = len(self.window_content[self.cpos.row])
            self.window_content[self.cpos.row] += line
            self.unsaved_progress = True
            return ''
        return None

    def _key_ctl_backspace(self, _) -> str:
        if self.cpos.col == 1: # delete char
            self.cpos.col = 0
            deleted = self.window_content[self.cpos.row][self.cpos.col]
            self.window_content[self.cpos.row] = self.window_content[self.cpos.row][1:]
            self.unsaved_progress = True
            return deleted
        if self.cpos.col > 1:
            old_col = self.cpos.col
            self.cpos.col -= 2
            t_p = self.window_content[self.cpos.row][self.cpos.col].isalnum()
            while self.cpos.col > 0 and \
                t_p == self.window_content[self.cpos.row][self.cpos.col].isalnum():
                self.cpos.col -= 1
            if self.cpos.col:
                self.cpos.col += 1
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
        self.wpos.row = max(min(self.wpos.row+max_y, len(self.window_content)-max_y), 0)
        self.cpos.row = min(self.cpos.row+max_y, len(self.window_content)-1)

    def _scroll_key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(self.wpos.row-max_y, 0)

    def _scroll_key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = max(min(self.wpos.row+max_y, len(self.window_content)-max_y), 0)

    def _move_key_end(self) -> None:
        self.cpos.col = len(self.window_content[self.cpos.row])

    def _move_key_ctl_end(self) -> None:
        self.cpos.row = len(self.window_content)-1
        self.cpos.col = len(self.window_content[-1])

    def _scroll_key_end(self) -> None:
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

    def _key_string(self, wchars) -> str:
        """
        tries to append (a) char(s) to the screen.
        
        Parameters:
        wchars (int|str):
            given by curses get_wch()
        """
        if not isinstance(wchars, str) or not wchars:
            return ''
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

    def _action_save(self, write_func) -> bool:
        """
        handle the save file action.
        
        Parameters:
        write_func (function):
            the function to use for saving the file
        
        Returns
        (bool):
            indicates if the editor should keep running
        """
        content = self.line_sep.join(self.window_content)
        try:
            write_func(content, self.file, self.file_encoding)
            self.changes_made = True
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1
        except (OSError, UnicodeError) as exc:
            self.unsaved_progress = True
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                print(self.error_bar, file=sys.stderr)
        return True

    def _action_quit(self, write_func) -> bool:
        """
        handles the quit editor action.
        
        Parameters:
        write_func (function):
            the function to use for possibly saving the file
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        if self.unsaved_progress:
            def _render_scr() -> None:
                max_y, max_x = self.getxymax()
                try:
                    if self.error_bar:
                        self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                                self.error_bar[:max_x].ljust(max_x),
                                                self._get_color(2))
                    save_message = 'Save changes? [y]es, [n]o; Abort? ESC'[:max_x].ljust(max_x)
                    self.curse_window.addstr(max_y + self.status_bar_size - 1, 0, save_message,
                                            self._get_color(5))
                except curses.error:
                    pass
                self.curse_window.refresh()
            curses.curs_set(0)

            wchar = ''
            while self.unsaved_progress and str(wchar).upper() != 'N':
                _render_scr()
                wchar, key = self._get_new_char()
                if key in ACTION_HOTKEYS:
                    if key == b'_action_quit':
                        break
                    getattr(self, key.decode(), lambda *_: False)(write_func)
                elif wchar.upper() in ['Y', 'J']:
                    self._action_save(write_func)
                elif wchar == '\x1b': # ESC
                    return True

        return False

    def _action_interrupt(self, _) -> bool:
        """
        handles the interrupt action.
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        if self.debug_mode:
            print('Interrupting...', file=sys.stderr)
        raise KeyboardInterrupt

    def _action_resize(self, _) -> bool:
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

    def _get_new_char(self) -> tuple:
        """
        get next char
        
        Returns
        (tuple):
            the char received and the possible action it means.
        """
        wchar = -1
        while wchar == -1:
            try: # try-except in case of no delay mode
                wchar = self.curse_window.get_wch()
            except curses.error:
                pass
        _key = curses.keyname(wchar if isinstance(wchar, int) else ord(wchar))
        key = UNIFY_HOTKEYS.get(_key, b'_key_string')
        if self.debug_mode:
            _debug_info = repr(chr(wchar)) if isinstance(wchar, int) else ord(wchar)
            print(f"__DEBUG__: Received wchar \t{repr(wchar)} " + \
                f"\t{_debug_info} \t{str(_key).ljust(15)} \t{key}", file=sys.stderr)
        return (wchar, key)

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
        try:
            self.curse_window.move(0, 0)
        except curses.error:
            pass

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
            for col in range(max_x):
                bcol = col + self.wpos.col
                if brow >= len(self.window_content) or bcol >= len(self.window_content[brow]):
                    break
                try:
                    cur_char = self.window_content[brow][bcol]
                    if cur_char == '\t':
                        self.curse_window.addch(row, col, '>', self._get_color(4))
                    elif not cur_char.isprintable():
                        self.curse_window.addch(row, col, self._get_special_char(cur_char),
                                                self._get_color(5))
                    elif all(map(lambda c: c.isspace(), self.window_content[brow][bcol:])):
                        self.curse_window.addch(row, col, cur_char,
                                                self._get_color(3))
                    else:
                        self.curse_window.addch(row, col, cur_char)
                except curses.error:
                    break
            self.curse_window.clrtoeol()
            try:
                self.curse_window.addch('\n')
            except curses.error:
                break
        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            status_bar = f"File: {self.file} | Exit: ^q | Save: ^s | Pos: {self.cpos.col}"
            status_bar += f", {self.cpos.row} | {'NOT ' * self.unsaved_progress}Saved!"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col} {self.wpos.row} | {max_y}x{max_x}"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.file) + 3))
                status_bar = f"File: ...{self.file[-necc_space:] * bool(necc_space)} "
                status_bar += f"| Exit: ^q | Save: ^s | Pos: {self.cpos.col}, {self.cpos.row} "
                status_bar += f"| {'NOT ' * self.unsaved_progress}Saved!"[:max_x]
                if self.debug_mode:
                    status_bar += f" - Win: {self.wpos.col} {self.wpos.row} | {max_y}x{max_x}"
            status_bar = status_bar.ljust(max_x)
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                     status_bar, self._get_color(1))
        except curses.error:
            pass

        try:
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

    def _run(self, write_func) -> None:
        """
        main loop for the editor.
        
        Parameters:
        write_func (function):
            a function to write a file
        """
        running = True

        while running:
            self._render_scr()

            wchar, key = self._get_new_char()

            # handle new wchar
            if key in KEY_HOTKEYS:
                f_len = len(self.window_content)
                pre_pos = self.cpos.get_pos()
                action_text = getattr(self, key.decode(), lambda *_: None)(wchar)
                self.history.add(key, action_text, f_len, pre_pos, self.cpos.get_pos())
            elif key in ACTION_HOTKEYS:
                running &= getattr(self, key.decode(), lambda *_: False)(write_func)
            elif key in SCROLL_HOTKEYS:
                self.scrolling = True
                getattr(self, key.decode(), lambda *_: None)()
            else:
                getattr(self, key.decode(), lambda *_: None)()

    def _open(self, curse_window, write_func) -> None:
        """
        define curses settings and
        run the editor on the initialized data.
        
        Parameters:
        curse_window (curses._Window):
            the curses window from initscr()
        write_func (function):
            a function to write a file
        """
        self.curse_window = curse_window
        if curses.can_change_color():
            # status_bar
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
            # error_bar
            curses.init_pair(2, curses.COLOR_RED  , curses.COLOR_WHITE)
            # trailing_whitespace
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED  )
            # tab-char
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            # special char (not printable) & quit-prompt
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED  )
        curses.raw()
        self.curse_window.nodelay(False)
        self._run(write_func)

    @classmethod
    def open(cls, file: str, file_encoding: str, write_func, on_windows_os: bool,
             debug_mode: bool = False) -> bool:
        """
        simple editor to change the contents of any provided file.
        the first file in the list will be loaded as a basis but all
        files will be written with the changed content.
        
        Parameters:
        file (str):
            a string representing a file(-path)
        file_encoding (str):
            an encoding the open the file with
        write_func (method):
            stdinhelper.write_file [simply writes a file]
        on_windows_os (bool):
            indicates if the user is on windows OS using platform.system() == 'Windows'
        debug_mode (bool):
            indicates if debug information should be displayed
        
        Returns:
        (bool):
            indicates whether or not the editor has written any content to the provided files
        """
        if Editor.loading_failed:
            return False

        if CURSES_MODULE_ERROR:
            print("The Editor could not be loaded. No Module 'curses' was found.", file=sys.stderr)
            if on_windows_os:
                print('If you are on Windows OS, try pip-installing ', end='', file=sys.stderr)
                print("'windows-curses'.", file=sys.stderr)
            print(file=sys.stderr)
            Editor.loading_failed = True
            return False
        # if not (sys.stdin.isatty() | sys.stdout.isatty()): # use os.isatty instead
        #     print("The Editor could not be loaded.", file=sys.stderr)
        #     return False


        editor = cls(file, file_encoding, debug_mode)
        special_chars = dict(map(lambda x: (chr(x[0]), x[2]), SPECIAL_CHARS))
        editor._set_special_chars(special_chars)

        curses.wrapper(editor._open, write_func)
        return editor.changes_made
