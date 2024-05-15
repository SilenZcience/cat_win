"""
hexeditor
"""

try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import signal
import sys

from cat_win.src.service.rawviewer import get_display_char_gen
from cat_win.src.service.helper.editorhelper import Position, UNIFY_HOTKEYS, \
    KEY_HOTKEYS, ACTION_HOTKEYS, MOVE_HOTKEYS, HEX_BYTE_KEYS
from cat_win.src.service.helper.iohelper import IoHelper, err_print


class HexEditor:
    """
    HexEditor
    """
    loading_failed = False

    debug_mode = False
    save_with_alt = False

    columns = 16

    def __init__(self, file: str, display_name: str) -> None:
        self.curse_window = None
        self.decode_char = get_display_char_gen()

        self.file = file
        self.display_name = display_name
        self._f_content = b''
        self.hex_array = []
        self.hex_array_edit = []

        self.edited_byte_pos = 0

        self.search = ''

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False

        self.top_line = '┌' + '─' * 10 + '┬' + '─' * (HexEditor.columns * 3 + 1) + '┬' + \
            '─' * (HexEditor.columns + 2) + '┐'
        self.bot_line = '└' + '─' * 10 + '┴' + '─' * (HexEditor.columns * 3 + 1) + '┴' + \
            '─' * (HexEditor.columns + 2) + '┘'
        self.top_offset = ('   Offset    ' + ' '.join(
            f"{byte_:02X}" for byte_ in range(HexEditor.columns)
            ) + '   Decoded text')

        # current cursor position
        self.cpos = Position(0, 0)
        # window position (top-left)
        self.wpos = Position(0, 0)

        self._setup_file()

    def _build_file_upto(self, to_row: int) -> None:
        _start = len(self.hex_array) * HexEditor.columns
        _end   = to_row              * HexEditor.columns
        for i, byte_ in enumerate(self._f_content[_start:_end], start=_start):
            if not i % HexEditor.columns:
                self.hex_array.append([])
            self.hex_array[-1].append(f"{byte_:02X}")
        for row in self.hex_array[len(self.hex_array_edit):]:
            self.hex_array_edit.append([None] * len(row))

    def _setup_file(self) -> None:
        """
        setup the editor content screen by reading the given file.
        """
        self.hex_array = []
        self.hex_array_edit = []
        try:
            self._f_content = IoHelper.read_file(self.file, True)
            self._build_file_upto(30)
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1
        except OSError as exc:
            self.unsaved_progress = True
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                err_print(self.error_bar)
        if not self.hex_array:
            self.hex_array.append([])

    def getxymax(self) -> tuple:
        """
        find the size of the window.
        
        Returns:
        (tuple):
            the size of the display that is free to use
            for text/content
        """
        max_y, max_x = self.curse_window.getmaxyx()
        return (max_y-self.status_bar_size-3, max_x)

    def _key_dc(self, _) -> None:
        if not self.hex_array_edit[self.cpos.row]:
            return
        self.hex_array_edit[self.cpos.row][self.cpos.col] = None
        self._move_key_right()

    def _key_dl(self, _) -> str:
        if not self.hex_array_edit[self.cpos.row]:
            return
        self.hex_array_edit[self.cpos.row][self.cpos.col] = '--'
        # self.hex_array[self.cpos.row][self.cpos.col] = '--'
        self._move_key_right()

    def _key_backspace(self, _) -> None:
        if not self.hex_array_edit[self.cpos.row]:
            return
        self.hex_array_edit[self.cpos.row][self.cpos.col] = None
        self._move_key_left()

    def _key_ctl_backspace(self, _) -> str:
        if not self.hex_array_edit[self.cpos.row]:
            return
        self.hex_array_edit[self.cpos.row][self.cpos.col] = '--'
        # self.hex_array[self.cpos.row][self.cpos.col] = '--'
        self._move_key_left()

    def _move_key_left(self) -> None:
        self.cpos.col -= 1

    def _move_key_right(self) -> None:
        self.cpos.col += 1

    def _move_key_up(self) -> None:
        self.cpos.row -= 1

    def _move_key_down(self) -> None:
        self.cpos.row += 1

    def _move_key_ctl_left(self) -> None:
        self.cpos.col -= HexEditor.columns//2

    def _move_key_ctl_right(self) -> None:
        self.cpos.col += HexEditor.columns//2

    def _move_key_ctl_up(self) -> None:
        self.cpos.row -= 10

    def _move_key_ctl_down(self) -> None:
        self.cpos.row += 10

    def _key_string(self, wchar) -> None:
        """
        tries to replace a byte on the screen.
        
        Parameters:
        wchars (int|str):
            given by curses get_wch()
        """
        if not isinstance(wchar, str) or not wchar:
            return ''
        wchar = wchar.upper()
        if wchar in HEX_BYTE_KEYS and self.hex_array_edit[self.cpos.row]:
            if self.hex_array_edit[self.cpos.row][self.cpos.col] is None:
                self.hex_array_edit[self.cpos.row][self.cpos.col] = \
                    self.hex_array[self.cpos.row][self.cpos.col]
            self.hex_array_edit[self.cpos.row][self.cpos.col] = \
                self.hex_array_edit[self.cpos.row][self.cpos.col][:self.edited_byte_pos] + \
                wchar + self.hex_array_edit[self.cpos.row][self.cpos.col][self.edited_byte_pos+1:]
            if self.edited_byte_pos:
                self._move_key_right()
            self.edited_byte_pos = (self.edited_byte_pos+1)%2

            self.unsaved_progress = True
        elif wchar in '<> ':
            self.hex_array[self.cpos.row].insert(self.cpos.col+(wchar!='<'), '--')
            self.hex_array_edit[self.cpos.row].insert(self.cpos.col+(wchar!='<'), '--')
            for i in range(self.cpos.row+1, len(self.hex_array)):
                extracted_byte = self.hex_array[i-1][-1]
                self.hex_array[i-1] = self.hex_array[i-1][:-1]
                self.hex_array[i].insert(0, extracted_byte)
                extracted_byte = self.hex_array_edit[i-1][-1]
                self.hex_array_edit[i-1] = self.hex_array_edit[i-1][:-1]
                self.hex_array_edit[i].insert(0, extracted_byte)
            if len(self.hex_array[-1]) > HexEditor.columns:
                extracted_byte = self.hex_array[-1][-1]
                self.hex_array[-1] = self.hex_array[-1][:-1]
                self.hex_array.append([extracted_byte])
                extracted_byte = self.hex_array_edit[-1][-1]
                self.hex_array_edit[-1] = self.hex_array_edit[-1][:-1]
                self.hex_array_edit.append([extracted_byte])
            if wchar != '<':
                self._move_key_right()

            self.unsaved_progress = True

    def _action_render_scr(self, msg) -> None:
        max_y, max_x = self.getxymax()
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size + 1, 0,
                                        self.error_bar[:max_x].ljust(max_x),
                                        self._get_color(2))
            self.curse_window.addstr(max_y + self.status_bar_size + 2, 0,
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
        bytes_loaded = len(self.hex_array)*HexEditor.columns
        bytes_loaded-= HexEditor.columns
        bytes_loaded+= len(self.hex_array[-1])
        content = b''
        for i, row in enumerate(self.hex_array):
            for j, byte in enumerate(row):
                hex_byte = self.hex_array_edit[i][j]
                if hex_byte is None:
                    hex_byte = byte
                try:
                    content += bytes.fromhex(hex_byte)
                except ValueError:
                    pass
        content += self._f_content[bytes_loaded:]
        try:
            IoHelper.write_file(self.file, content)
            self.changes_made = True
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1

            self._setup_file()
        except OSError as exc:
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
        wchar, l_jmp = '', ''
        while str(wchar).upper() not in ['\x1b', 'N']:
            self._action_render_scr(f"Confirm: [y]es, [n]o - Jump to byte: 0x{l_jmp}␣")
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            if key == b'_key_string' and wchar.upper() in HEX_BYTE_KEYS:
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    l_jmp_int = int(l_jmp, 16)
                    self.cpos.row = l_jmp_int // HexEditor.columns
                    self.cpos.col = l_jmp_int %  HexEditor.columns
                break
        return True

    def _action_find(self) -> bool:
        """
        handles the find in editor action.
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        def find_bytes(row: int, col: int = 0) -> int:
            search_in = ''.join(self.hex_array[row][col:])
            search_wrap = ''
            while len(self.search)-1 > len(search_wrap) and row < len(self.hex_array)-1:
                row += 1
                search_wrap += ''.join(self.hex_array[row])
            search_in += search_wrap[:len(self.search)-1]

            found_pos = search_in.find(self.search)
            while found_pos >= 0:
                if found_pos % 2:
                    search_in = search_in[found_pos+1:]
                    found_pos = search_in.find(self.search)
                    continue
                break
            return found_pos//2

        wchar, sub_s = '', ''
        while str(wchar) != '\x1b':
            pre_s = f" [0x{repr(self.search)[1:-1]}]" if self.search else ''
            self._action_render_scr(f"Confirm: 'ENTER' - Search for{pre_s}: 0x{sub_s}␣")
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            if key == b'_key_backspace':
                sub_s = sub_s[:-1]
            if key == b'_key_string' and wchar.upper() in HEX_BYTE_KEYS:
                sub_s += wchar.upper()
            elif key == b'_key_enter':
                self.search = sub_s if sub_s else self.search
                if not self.search:
                    break
                # check current line
                search_result = find_bytes(self.cpos.row, self.cpos.col+1)
                if search_result >= 0:
                    self.cpos.col += search_result+1
                    break
                # check rest of file until back at current line
                c_row = self.cpos.row
                while c_row < self.cpos.row+len(self.hex_array):
                    if c_row+1 >= len(self.hex_array):
                        self._build_file_upto(c_row+30)
                    c_row += 1
                    c_row_wrapped = c_row%len(self.hex_array)
                    search_result = find_bytes(c_row_wrapped)
                    if search_result >= 0:
                        self.cpos.row = c_row_wrapped
                        self.cpos.col = search_result
                        break
                break
        return True

    def _action_background(self) -> bool:
        # only callable on UNIX
        curses.endwin()
        os.kill(os.getpid(), signal.SIGSTOP)
        self._init_screen()
        return True

    def _action_reload(self) -> bool:
        """
        prompt to reload the file.
        
        Returns:
        (bool):
            indicates if the editor should keep running
        """
        wchar = ''
        while str(wchar).upper() not in ['\x1b', 'N']:
            self._action_render_scr('Reload File? [y]es, [n]o; Abort? ESC')
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            elif wchar.upper() in ['Y', 'J']:
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
            wchar = ''
            while self.unsaved_progress and str(wchar).upper() != 'N':
                self._action_render_scr('Save changes? [y]es, [n]o; Abort? ESC')
                wchar, key = self._get_next_char()
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
                elif wchar.upper() in ['Y', 'J']:
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

    def _get_next_char(self) -> tuple:
        """
        get next char
        
        Returns
        (wchar, key) (tuple):
            the char received and the possible action it means.
        """
        def debug_out(wchar_, key__, key_) -> None:
            if self.debug_mode:
                _debug_info = repr(chr(wchar_)) if isinstance(wchar_, int) else \
                    ord(wchar_) if len(wchar_) == 1 else '-'
                err_print(f"__DEBUG__: Received  {key_}\t{_debug_info}" + \
                    f"\t{str(key__):<15} \t{repr(wchar_)}")
        wchar = self.curse_window.get_wch()
        _key = curses.keyname(wchar if isinstance(wchar, int) else ord(wchar))
        key = UNIFY_HOTKEYS.get(_key, b'_key_string')
        debug_out(wchar, _key, key)
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

    def _fix_cursor_position(self, max_y: int) -> None:
        # fix cursor position (makes movement hotkeys easier)
        # since it would be unusual for a hexeditor to paste large amount of key-strokes into
        # at once, rendering is allowed to be slower here ...
        self.cpos.row = min(len(self.hex_array)-1, max(self.cpos.row, 0))
        while self.cpos.row and self.cpos.col < 0:
            self.cpos.col += HexEditor.columns
            self.cpos.row -= 1
        while self.cpos.row < len(self.hex_array)-1 and \
            self.cpos.col >= len(self.hex_array[self.cpos.row]):
            self.cpos.col -= len(self.hex_array[self.cpos.row])
            self.cpos.row += 1
        self.cpos.col = min(self.cpos.col, len(self.hex_array[self.cpos.row])-1)
        self.cpos.col = max(self.cpos.col, 0)

        if self.cpos.row < self.wpos.row:
            self.wpos.row = self.cpos.row
        elif self.cpos.row >= self.wpos.row + max_y:
            self.wpos.row = self.cpos.row - max_y + 1
        # if self.cpos.col < self.wpos.col:
        #     self.wpos.col = self.cpos.col
        # elif self.cpos.col >= self.wpos.col + max_x:
        #     self.wpos.col = self.cpos.col - max_x + 1

    def _render_title_offset(self, max_x: int) -> None:
        # Draw Title:
        self.curse_window.addstr(0, 0, self.top_offset[:max_x])
        self.curse_window.addstr(1, 0, self.top_line[:max_x])

    def _render_draw_rows(self, max_y: int, max_x: int) -> None:
        # Draw Rows
        hex_section = self.hex_array[self.wpos.row:self.wpos.row + max_y]
        hex_offset = [f"{byte_*HexEditor.columns:08X}" for byte_ in range(
            self.wpos.row, self.wpos.row + max_y)]
        encoded_section = [' '.join(line).ljust(HexEditor.columns*3-1) for line in hex_section]
        decoded_section = [''.join(self.decode_char(obj) for obj in line).ljust(
            HexEditor.columns) for line in hex_section]
        for row_id, row in enumerate(
            map(' │ '.join, zip(hex_offset, encoded_section, decoded_section)),
            start=2
        ):
            self.curse_window.addstr(row_id, 0, f"│ {row} │"[:max_x])

        self.curse_window.move(len(hex_section)+2, 0)
        if len(self.hex_array) <= self.wpos.row + max_y:
            self.curse_window.addstr(len(hex_section)+2, 0, self.bot_line[:max_x])
        self.curse_window.clrtobot()

    def _render_highlight_selection(self) -> None:
        # Highlight Selection
        cursor_y= self.cpos.row-self.wpos.row+2
        if self.hex_array[self.cpos.row]:
            # only highlight if the file has content
            try:
                self.curse_window.chgat(cursor_y, 13 + self.cpos.col*3,
                                        2, self._get_color(4))
                self.curse_window.chgat(cursor_y, 15 + HexEditor.columns*3 + self.cpos.col,
                                        1, self._get_color(4))
            except curses.error:
                pass

    def _render_highlight_edits(self, max_y: int) -> None:
        # Highlight Edits
        hex_section_edit = self.hex_array_edit[self.wpos.row:self.wpos.row + max_y]
        selected_byte = (self.cpos.row-self.wpos.row, self.cpos.col)
        for i, row in enumerate(hex_section_edit):
            for j, byte in enumerate(row):
                if byte is None:
                    continue
                color_id = 6 if selected_byte == (i, j) else 5
                try:
                    self.curse_window.addstr(i+2, j*3 + 13, byte, self._get_color(color_id))
                    self.curse_window.addstr(i+2, 15 + HexEditor.columns*3 + j,
                                            self.decode_char(byte),
                                            self._get_color(color_id))
                except curses.error:
                    pass

    def _render_status_bar(self, max_y: int, max_x: int) -> None:
        # Draw status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size + 1, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            save_hotkey = ('alt+' if self.save_with_alt else '^') + 's'
            status_bar = f"File: {self.display_name} | Exit: ^q | Save: {save_hotkey} | "
            status_bar += f"{self.cpos.row*HexEditor.columns+self.cpos.col:08X}"
            status_bar += f" | {'NOT ' * self.unsaved_progress}Saved!"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.display_name) + 3))
                status_bar = f"File: ...{self.display_name[-necc_space:] * bool(necc_space)} "
                status_bar += f"| Exit: ^q | Save: {save_hotkey} | "
                status_bar += f"{self.cpos.row*HexEditor.columns+self.cpos.col:08X}"
                status_bar += f" | {'NOT ' * self.unsaved_progress}Saved!"
                if self.debug_mode:
                    status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            # this throws an error (should be max_x-1), but looks better:
            status_bar = status_bar[:max_x].ljust(max_x)
            self.curse_window.addstr(max_y + self.status_bar_size + 2, 0,
                                     status_bar, self._get_color(1))
        except curses.error:
            pass

    def _render_scr(self) -> None:
        """
        render the curses window.
        """
        max_y, max_x = self.getxymax()
        self._build_file_upto(max_y+self.cpos.row+1)

        self._fix_cursor_position(max_y)

        self._render_title_offset(max_x)
        self._render_draw_rows(max_y, max_x)
        self._render_highlight_selection()
        self._render_highlight_edits(max_y)
        self._render_status_bar(max_y, max_x)

        self.curse_window.refresh()

    def _run(self) -> None:
        """
        main loop for the editor.
        """
        running = True

        while running:
            self._render_scr()
            wchar, key = self._get_next_char()
            if key != b'_key_string':
                self.edited_byte_pos = 0

            if key in KEY_HOTKEYS:
                getattr(self, key.decode(), lambda *_: None)(wchar)
            elif key in ACTION_HOTKEYS:
                running &= getattr(self, key.decode(), lambda *_: True)()
            elif key in MOVE_HOTKEYS:
                getattr(self, key.decode(), lambda *_: None)()

    def _init_screen(self) -> None:
        """
        init and define curses
        """
        self.curse_window = curses.initscr()
        curses.curs_set(0)

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
                # prompts
                curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED  )
                # selected byte
                curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
                # edited byte
                curses.init_pair(5, curses.COLOR_RED  , curses.COLOR_BLACK)
                # selected and edited byte
                curses.init_pair(6, curses.COLOR_RED  , curses.COLOR_WHITE)
        curses.raw()
        self.curse_window.nodelay(False)

    def _open(self) -> None:
        """
        init, run, deinit
        """
        try:
            self._init_screen()
            self._run()
        finally:
            # self.curse_window.erase()
            curses.endwin()

    @classmethod
    def open(cls, file: str, display_name: str, on_windows_os: bool) -> bool:
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
        if HexEditor.loading_failed:
            return False

        if CURSES_MODULE_ERROR:
            err_print("The Editor could not be loaded. No Module 'curses' was found.")
            if on_windows_os:
                err_print('If you are on Windows OS, try pip-installing ', end='')
                err_print("'windows-curses'.")
            err_print()
            HexEditor.loading_failed = True
            return False

        editor = cls(file, display_name)

        if on_windows_os:
            # disable background feature on windows
            editor._action_background = lambda *_: True
        else:
            # ignore background signals on UNIX, since a custom background implementation exists
            signal.signal(signal.SIGTSTP, signal.SIG_IGN)

        editor._open()
        return editor.changes_made

    @staticmethod
    def set_flags(save_with_alt: bool, debug_mode: bool, columns: int) -> None:
        """
        set the config flags for the Editor
        
        Parameters:
        save_with_alt (bool):
            indicates whetcher the stdin pipe has been used (and therefor tampered)
        debug_mode (bool)
            indicates if debug info should be displayed
        columns (int):
            defines how many columns the editor should have
        """
        HexEditor.save_with_alt = save_with_alt
        HexEditor.debug_mode = debug_mode
        HexEditor.columns = columns
