try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import sys

from cat_win.util.editorhelper import UNIFY_HOTKEYS, KEY_HOTKEYS, ACTION_HOTKEYS


class _Editor:
    def __init__(self, file: str, file_encoding: str, debug_mode: bool) -> None:
        self.curse_window = None

        self.file = file
        self.file_encoding = file_encoding
        self.line_sep = '\n'
        self.window_content = []

        self.debug_mode = debug_mode

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False

        self.cur_col = 0
        self.cur_row = 0
        self.x = 0
        self.y = 0

        self._setup_file()

    def _setup_file(self) -> None:
        try:
            self.line_sep = Editor.get_newline(self.file)
            with open(self.file, 'r', encoding=self.file_encoding) as f:
                for line in f.read().split('\n'):
                    self.window_content.append([*line])
        except (OSError, UnicodeDecodeError) as e:
            self.window_content.append([])
            self.status_bar_size = 2
            self.error_bar = str(e)
            self.unsaved_progress = True

    def getxymax(self) -> tuple:
        max_y, max_x = self.curse_window.getmaxyx()
        return (max_y-self.status_bar_size, max_x)

    def _key_enter(self) -> bool:
        new_line = self.window_content[self.cur_row][self.cur_col:]
        self.window_content[self.cur_row] = self.window_content[self.cur_row][:self.cur_col]
        self.cur_row += 1
        self.cur_col = 0
        self.window_content.insert(self.cur_row, [] + new_line)
        self.unsaved_progress = True

    def _key_dc(self) -> None:
        if self.cur_col < len(self.window_content[self.cur_row]):
            del self.window_content[self.cur_row][self.cur_col]
            self.unsaved_progress = True
        elif self.cur_row < len(self.window_content)-1:
            self.window_content[self.cur_row] += self.window_content[self.cur_row+1]
            del self.window_content[self.cur_row+1]
            self.unsaved_progress = True

    def _key_dl(self) -> None:
        if self.cur_col == len(self.window_content[self.cur_row])-1:
            self.window_content[self.cur_row] = self.window_content[self.cur_row][:self.cur_col]
            self.unsaved_progress = True
        elif self.cur_col < len(self.window_content[self.cur_row])-1:
            cur_col = self.cur_col+1
            tp = self.window_content[self.cur_row][cur_col].isalnum()
            while cur_col < len(self.window_content[self.cur_row]) and tp == self.window_content[self.cur_row][cur_col].isalnum():
                cur_col += 1
            self.window_content[self.cur_row] = self.window_content[self.cur_row][:self.cur_col] + self.window_content[self.cur_row][cur_col:]
            self.unsaved_progress = True
        elif self.cur_row < len(self.window_content)-1:
            self.window_content[self.cur_row] += self.window_content[self.cur_row+1]
            del self.window_content[self.cur_row+1]
            self.unsaved_progress = True

    def _key_backspace(self) -> None:
        if self.cur_col: # delete char
            self.cur_col -= 1
            del self.window_content[self.cur_row][self.cur_col]
            self.unsaved_progress = True
        elif self.cur_row: # or delete line
            line = self.window_content[self.cur_row]
            del self.window_content[self.cur_row]
            self.cur_row -= 1
            self.cur_col = len(self.window_content[self.cur_row])
            self.window_content[self.cur_row] += line
            self.unsaved_progress = True

    def _key_ctl_backspace(self) -> None:
        if self.cur_col == 1: # delete char
            self.cur_col = 0
            del self.window_content[self.cur_row][self.cur_col]
            self.unsaved_progress = True
        elif self.cur_col > 1:
            old_col = self.cur_col
            self.cur_col -= 2
            tp = self.window_content[self.cur_row][self.cur_col].isalnum()
            while self.cur_col > 0 and tp == self.window_content[self.cur_row][self.cur_col].isalnum():
                self.cur_col -= 1
            if self.cur_col:
                self.cur_col += 1
            del self.window_content[self.cur_row][self.cur_col:old_col]
            self.unsaved_progress = True
        elif self.cur_row: # or delete line
            line = self.window_content[self.cur_row]
            del self.window_content[self.cur_row]
            self.cur_row -= 1
            self.cur_col = len(self.window_content[self.cur_row])
            self.window_content[self.cur_row] += line
            self.unsaved_progress = True

    def _key_left(self) -> None:
        if self.cur_col:
            self.cur_col -= 1
        elif self.cur_row:
            self.cur_row -= 1
            self.cur_col = len(self.window_content[self.cur_row])

    def _key_right(self) -> None:
        if self.cur_col < len(self.window_content[self.cur_row]):
            self.cur_col += 1
        elif self.cur_row < len(self.window_content)-1:
            self.cur_row += 1
            self.cur_col = 0

    def _key_up(self) -> None:
        if self.cur_row:
            self.cur_row -= 1

    def _key_down(self) -> None:
        if self.cur_row < len(self.window_content)-1:
            self.cur_row += 1

    def _key_ctl_left(self) -> None:
        if self.cur_col == 1:
            self.cur_col = 0
        elif self.cur_col > 1:
            self.cur_col -= 2
            tp = self.window_content[self.cur_row][self.cur_col].isalnum()
            while self.cur_col > 0 and tp == self.window_content[self.cur_row][self.cur_col].isalnum():
                self.cur_col -= 1
            if self.cur_col:
                self.cur_col += 1
        elif self.cur_row:
            self.cur_row -= 1
            self.cur_col = len(self.window_content[self.cur_row])

    def _key_ctl_right(self) -> None:
        if self.cur_col == len(self.window_content[self.cur_row])-1:
            self.cur_col = len(self.window_content[self.cur_row])
        elif self.cur_col < len(self.window_content[self.cur_row])-1:
            self.cur_col += 1
            tp = self.window_content[self.cur_row][self.cur_col].isalnum()
            while self.cur_col < len(self.window_content[self.cur_row]) and tp == self.window_content[self.cur_row][self.cur_col].isalnum():
                self.cur_col += 1
        elif self.cur_row < len(self.window_content)-1:
            self.cur_row += 1
            self.cur_col = 0

    def _key_ctl_up(self) -> None:
        if self.cur_row >= 10:
            self.cur_row -= 10
        else:
            self.cur_row = 0

    def _key_ctl_down(self) -> None:
        if self.cur_row < len(self.window_content)-10:
            self.cur_row += 10
        else:
            self.cur_row = len(self.window_content)-1

    def _key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.y = max(self.y-max_y, 0)
        self.cur_row = max(self.cur_row-max_y, 0)

    def _key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.y = max(min(self.y+max_y, len(self.window_content)-1-max_y), 0)
        self.cur_row = min(self.cur_row+max_y, len(self.window_content)-1)

    def _key_end(self) -> None:
        self.cur_col = len(self.window_content[self.cur_row])

    def _key_ctl_end(self) -> None:
        max_y, _ = self.getxymax()
        self.y = max(len(self.window_content)-1-max_y, 0)
        self.cur_row = len(self.window_content)-1
        self.cur_col = len(self.window_content[-1])

    def _key_home(self) -> None:
        self.cur_col = 0

    def _key_ctl_home(self) -> None:
        self.cur_row = 0
        self.cur_col = 0

    def _key_char(self, wchar: str) -> None:
        self.unsaved_progress = True
        self.window_content[self.cur_row].insert(self.cur_col, wchar)
        self.cur_col += 1        

    def _action_save(self, write_func) -> bool:
        content = self.line_sep.join([''.join(line) for line in self.window_content])
        try:
            write_func(content, self.file, self.file_encoding)
            self.changes_made = True
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1
        except OSError as e:
            self.unsaved_progress = True
            self.error_bar = str(e)
            self.status_bar_size = 2
            if self.debug_mode:
                print(self.error_bar, file=sys.stderr)
        return True

    def _action_quit(self, write_func) -> bool:
        if self.unsaved_progress:
            max_y, max_x = self.getxymax()
            save_message = 'Save changes? [y]es, [n]o'[:max_x]
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0, save_message, self._get_color(5))
            if max_x > len(save_message):
                self.curse_window.addstr(max_y + self.status_bar_size - 1, len(save_message), ' ' * (max_x-len(save_message)-1), self._get_color(5))
            self.curse_window.refresh()

            wchar = ''
            while self.unsaved_progress and wchar.upper() != 'N':
                wchar, key = self._get_new_char()
                if key in ACTION_HOTKEYS:
                    if key == b'_action_quit':
                        break
                    getattr(self, key.decode(), lambda *_: False)(write_func)
                elif wchar.upper() in ['Y', 'J']:
                    self._action_save(write_func)
                    break

        return False

    def _action_interrupt(self, _) -> bool:
        if self.debug_mode:
            print('Interrupting...', file=sys.stderr)
        raise KeyboardInterrupt()

    def _action_resize(self, _) -> bool:
        try:
            curses.resize_term(*self.curse_window.getmaxyx())
        except curses.error:
            pass
        self.curse_window.clear()
        return True

    def _get_new_char(self) -> tuple:
        # get next char
        wchar = -1
        while wchar == -1:
            try: # try-except in case of no delay mode
                wchar = self.curse_window.get_wch()
            except curses.error:
                pass
        _key = curses.keyname(wchar if isinstance(wchar, int) else ord(wchar))
        key = UNIFY_HOTKEYS.get(_key, _key)
        if self.debug_mode:
            print(f"__DEBUG__: Received wchar \t{repr(wchar)} \t{repr(chr(wchar)) if isinstance(wchar, int) else ord(wchar)} \t{str(_key).ljust(15)} \t{key}", file=sys.stderr)
        return (wchar, key)

    def _get_color(self, id: int) -> int:
        if not curses.has_colors():
            return 0
        return curses.color_pair(id)

    def _render_scr(self) -> tuple:
        max_y, max_x = self.getxymax()

        # fix cursor position (makes movement hotkeys easier)
        row = self.window_content[self.cur_row] if self.cur_row < len(self.window_content) else None
        rowlen = len(row) if row is not None else 0
        if self.cur_col > rowlen:
            self.cur_col = rowlen

        # set/enforce the boundaries
        curses.curs_set(0)
        try:
            self.curse_window.move(0, 0)
        except curses.error:
            pass
        if self.cur_row < self.y:
            self.y = self.cur_row
        elif self.cur_row >= self.y + max_y:
            self.y = self.cur_row - max_y + 1
        if self.cur_col < self.x:
            self.x = self.cur_col
        elif self.cur_col >= self.x + max_x:
            self.x = self.cur_col - max_x + 1
        # display screen
        for row in range(max_y):
            brow = row + self.y
            for col in range(max_x):
                bcol = col + self.x
                try:
                    if self.window_content[brow][bcol] == '\t':
                        self.curse_window.addch(row, col, '>', self._get_color(4))
                    elif not self.window_content[brow][bcol].isprintable():
                        self.curse_window.addch(row, col, '?', self._get_color(5))
                    elif all(map(lambda c: c.isspace(), self.window_content[brow][bcol:])):
                        self.curse_window.addch(row, col, self.window_content[brow][bcol], self._get_color(3))
                    else:
                        self.curse_window.addch(row, col, self.window_content[brow][bcol])
                except (IndexError, curses.error):
                    break
            self.curse_window.clrtoeol()
            try:
                self.curse_window.addch('\n')
            except curses.error:
                break
        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0, self.error_bar[:max_x], self._get_color(2))
                if (max_x - len(self.error_bar) - 1) > 0:
                    self.curse_window.addstr(max_y + self.status_bar_size - 2, len(self.error_bar), " " * (max_x - len(self.error_bar) - 1), self._get_color(2))

            status_bar = f"File: {self.file} | Exit: ^q | Save: ^s | Pos: {self.cur_col}, {self.cur_row} | {'NOT ' * self.unsaved_progress}Saved!"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.file) + 3))
                status_bar = f"File: ...{self.file[-necc_space:] * bool(necc_space)} | Exit: ^q | Save: ^s | Pos: {self.cur_col}, {self.cur_row} | {'NOT ' * self.unsaved_progress}Saved!"[:max_x]
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0, status_bar, self._get_color(1))
            if (max_x - len(status_bar) - 1) > 0:
                self.curse_window.addstr(max_y + self.status_bar_size - 1, len(status_bar), " " * (max_x - len(status_bar) - 1), self._get_color(1))
        except curses.error:
            pass

        try:
            self.curse_window.move(max(self.cur_row-self.y, 0), max(self.cur_col-self.x, 0))
        except curses.error:
            pass
        curses.curs_set(1)
        self.curse_window.refresh()

    def _open(self, write_func) -> None:
        running = True

        while running:
            self._render_scr()

            wchar, key = self._get_new_char()

            # handle new wchar
            if key in KEY_HOTKEYS:
                getattr(self, key.decode(), lambda: None)()
            elif key in ACTION_HOTKEYS:
                running &= getattr(self, key.decode(), lambda *_: False)(write_func)

            # insert new key
            elif isinstance(wchar, str) and wchar.isprintable() or wchar == '\t':
                self._key_char(wchar)

    def _run(self, curse_window, write_func) -> None:
        self.curse_window = curse_window
        if curses.can_change_color():
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # status_bar
            curses.init_pair(2, curses.COLOR_RED  , curses.COLOR_WHITE) # error_bar
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED  ) # trailing_whitespace
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN) # tab-char
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED  ) # special char (not printable) & quit-prompt
        curses.raw()
        self.curse_window.nodelay(False)
        self._open(write_func)

    def run(self, write_func) -> bool:
        curses.wrapper(self._run, write_func)
        return self.changes_made


class Editor:
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
        with open(file, 'rb') as f:
            l = f.readline()
            l += b'\n' * bool(not l[-1:] or l[-1:] not in b'\r\n')
            return '\r\n' if l[-2:] == b'\r\n' else l[-1:].decode()

    def open(file: str, file_encoding: str, write_func, on_windows_os: bool, debug_mode: bool = False) -> bool:
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
        if CURSES_MODULE_ERROR:
            print("The Editor could not be loaded. No Module 'curses' was found.", file=sys.stderr)
            if on_windows_os:
                print("If you are on Windows OS, try pip-installing 'windows-curses'.", file=sys.stderr)
            return False
        # if not (sys.stdin.isatty() | sys.stdout.isatty()):
        #     print("The Editor could not be loaded.", file=sys.stderr)
        #     return False

        editor = _Editor(file, file_encoding, debug_mode)
        return editor.run(write_func)
