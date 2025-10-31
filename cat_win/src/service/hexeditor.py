"""
hexeditor
"""

from pathlib import Path
try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import signal
import sys

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.service.helper.editorsearchhelper import search_iter_hex_factory
from cat_win.src.service.helper.editorhelper import Position, frepr, \
    UNIFY_HOTKEYS, KEY_HOTKEYS, ACTION_HOTKEYS, MOVE_HOTKEYS, SELECT_HOTKEYS, \
        FUNCTION_HOTKEYS, HEX_BYTE_KEYS
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.iohelper import IoHelper, err_print
from cat_win.src.service.clipboard import Clipboard
from cat_win.src.service.rawviewer import get_display_char_gen


class HexEditor:
    """
    HexEditor
    """
    loading_failed = False

    save_with_alt = False
    debug_mode = False

    unicode_escaped_search = True
    unicode_escaped_insert = True
    columns = 16

    def __init__(self, file: Path, display_name: str) -> None:
        self.curse_window = None
        self.decode_char = get_display_char_gen()

        self.file = file
        self.display_name = display_name
        self._f_content_gen = None
        self.hex_array = [[]]
        self.hex_array_edit = [[]]

        self.edited_byte_pos = 0

        self.search = ''
        self.search_items: dict = {}

        self.status_bar_size = 1
        self.error_bar = ''
        self.unsaved_progress = False
        self.changes_made = False
        self.selecting = False

        self.top_line = '┌' + '─' * 10 + '┬' + '─' * (HexEditor.columns * 3 + 1) + '┬' + \
            '─' * (HexEditor.columns + 2) + '┐'
        self.bot_line = '└' + '─' * 10 + '┴' + '─' * (HexEditor.columns * 3 + 1) + '┴' + \
            '─' * (HexEditor.columns + 2) + '┘'
        self.top_offset = ('  Address    ' + ' '.join(
            f"{byte_:02X}" for byte_ in range(HexEditor.columns)
        ) + '   Decoded text')

        # current cursor position
        self.cpos = Position(0, 0)
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

    @staticmethod
    def pos_between(from_pos: tuple, to_pos: tuple):
        """
        every position between two positions

        Parameters:
        from_pos (tuple):
            the start pos
        to_pos (tuple):
            the end pos

        Yields:
        (tuple):
            a position between start and end
        """
        from_y, from_x = from_pos
        while (from_y, from_x) <= to_pos:
            yield (from_y, from_x)
            from_x += 1
            from_y += (from_x // HexEditor.columns)
            from_x = from_x % HexEditor.columns

    def _build_file(self):
        for _byte in self._f_content_gen:
            if len(self.hex_array[-1]) >= HexEditor.columns:
                self.hex_array.append([])
                self.hex_array_edit.append([])
            self.hex_array[-1].append(f"{_byte:02X}")
            self.hex_array_edit[-1].append(None)

    def _yield_next_bytes(self, n: int):
        for _ in range(n):
            try:
                yield f"{next(self._f_content_gen):02X}"
            except StopIteration:
                break

    def _build_file_upto(self, to_row: int) -> None:
        if len(self.hex_array) >= to_row:
            return
        next_bytes = self._yield_next_bytes((to_row-len(self.hex_array))*HexEditor.columns)
        for _byte in next_bytes:
            if len(self.hex_array[-1]) >= HexEditor.columns:
                self.hex_array.append([])
                self.hex_array_edit.append([])
            self.hex_array[-1].append(_byte)
            self.hex_array_edit[-1].append(None)

    def _setup_file(self) -> None:
        """
        setup the editor content screen by reading the given file.
        """
        self.hex_array = [[]]
        self.hex_array_edit = [[]]
        try:
            self._f_content_gen = IoHelper.yield_file(self.file, True)
            self._build_file_upto(31)
            self.unsaved_progress = False
            self.error_bar = ''
            self.status_bar_size = 1
        except OSError as exc:
            self.unsaved_progress = True
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                err_print(self.error_bar, priority=err_print.WARNING)

    def _get_current_state_row(self, row: int) -> list:
        """
        get the current state of the hex row

        Parameters:
        row (int):
            the row to get

        Returns:
        hex_row (list):
            the row in the current edited state
        """
        hex_row = []
        for j, byte in enumerate(self.hex_array[row]):
            hex_byte = self.hex_array_edit[row][j]
            if hex_byte is None:
                hex_byte = byte
            hex_row.append(hex_byte)
        return hex_row

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

    def _get_clipboard(self) -> bool:
        clipboard = Clipboard.get()
        if clipboard is None:
            self.error_bar = 'An error occured pasting the clipboard!'
        return clipboard

    def _key_dc(self, _) -> None:
        if not self.hex_array_edit[self.cpos.row]:
            return
        if self.selecting:
            sel_from, sel_to = self.selected_area
            for (pos_y, pos_x) in HexEditor.pos_between(sel_from, sel_to):
                self.hex_array_edit[pos_y][pos_x] = None
            self.cpos.set_pos(sel_to)
        else:
            self.hex_array_edit[self.cpos.row][self.cpos.col] = None
        self.cpos.col += 1

    def _key_dl(self, _) -> str:
        if not self.hex_array_edit[self.cpos.row]:
            return
        if self.selecting:
            sel_from, sel_to = self.selected_area
            for (pos_y, pos_x) in HexEditor.pos_between(sel_from, sel_to):
                self.hex_array_edit[pos_y][pos_x] = '--'
            self.cpos.set_pos(sel_to)
        else:
            self.hex_array_edit[self.cpos.row][self.cpos.col] = '--'
            # self.hex_array[self.cpos.row][self.cpos.col] = '--'
        self.unsaved_progress = True
        self.cpos.col += 1

    def _key_backspace(self, _) -> None:
        if not self.hex_array_edit[self.cpos.row]:
            return
        if self.selecting:
            sel_from, sel_to = self.selected_area
            for (pos_y, pos_x) in HexEditor.pos_between(sel_from, sel_to):
                self.hex_array_edit[pos_y][pos_x] = None
            self.cpos.set_pos(sel_from)
        else:
            self.hex_array_edit[self.cpos.row][self.cpos.col] = None
        self.cpos.col -= 1

    def _key_ctl_backspace(self, _) -> str:
        if not self.hex_array_edit[self.cpos.row]:
            return
        if self.selecting:
            sel_from, sel_to = self.selected_area
            for (pos_y, pos_x) in HexEditor.pos_between(sel_from, sel_to):
                self.hex_array_edit[pos_y][pos_x] = '--'
            self.cpos.set_pos(sel_from)
        else:
            self.hex_array_edit[self.cpos.row][self.cpos.col] = '--'
            # self.hex_array[self.cpos.row][self.cpos.col] = '--'
        self.unsaved_progress = True
        self.cpos.col -= 1

    def _move_key_mouse_get_cell_by_mouse_pos(self, x: int, y: int) -> tuple:
        y += self.wpos.row - 2
        if y > len(self.hex_array):
            return None
        x -= 13
        if x < 0:
            return None
        if x < HexEditor.columns * 3:
            return (y, x//3)
        x -= HexEditor.columns * 3
        x -= 2
        if x < 0:
            return None
        if x < HexEditor.columns:
            return (y, x)

    def _move_key_mouse(self) -> None:
        """
        handles mouse events.
        """
        self.selecting = False
        _, x, y, _, bstate = curses.getmouse()
        if bstate & curses.BUTTON1_CLICKED:
            cell = self._move_key_mouse_get_cell_by_mouse_pos(x, y)
            if cell is not None:
                self.cpos.set_pos(cell)
        elif bstate & curses.BUTTON1_PRESSED:
            cpos_tmp = self.cpos.get_pos()
            cell = self._move_key_mouse_get_cell_by_mouse_pos(x, y)
            if cell is not None:
                self.cpos.set_pos(cell)
                self._fix_cursor_position(self.getxymax()[0])
                self.spos.set_pos(self.cpos.get_pos())
                self.cpos.set_pos(cpos_tmp)
        elif bstate & curses.BUTTON1_RELEASED:
            self.selecting = True
            cell = self._move_key_mouse_get_cell_by_mouse_pos(x, y)
            if cell is not None:
                self.cpos.set_pos(cell)

        elif bstate & curses.BUTTON4_PRESSED:
            for _ in range(3):
                self._move_key_up()
        elif bstate & curses.BUTTON5_PRESSED:
            for _ in range(3):
                self._move_key_down()

    def _move_key_left(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        self.cpos.col -= 1

    def _move_key_right(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        self.cpos.col += 1

    def _move_key_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        self.cpos.row -= 1

    def _move_key_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        self.cpos.row += 1

    def _move_key_ctl_left(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        self.cpos.col -= HexEditor.columns//2

    def _move_key_ctl_right(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        self.cpos.col += HexEditor.columns//2

    def _move_key_ctl_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        self.cpos.row -= 10

    def _move_key_ctl_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        self.cpos.row += 10

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

    def _move_key_page_up(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[0])
        max_y, _ = self.getxymax()
        self.cpos.row -= max_y
        self.wpos.row = max(self.wpos.row-max_y, 0)

    def _move_key_page_down(self) -> None:
        if self.selecting:
            self.cpos.set_pos(self.selected_area[1])
        max_y, _ = self.getxymax()
        self.cpos.row += max_y
        self._build_file_upto(max_y+self.cpos.row+2)

    def _select_key_page_up(self) -> None:
        self.selecting = False
        self._move_key_page_up()

    def _select_key_page_down(self) -> None:
        self.selecting = False
        self._move_key_page_down()

    def _move_key_end(self) -> None:
        self.cpos.col = len(self.hex_array[self.cpos.row])-1

    def _move_key_ctl_end(self) -> None:
        self._build_file()
        self.cpos.set_pos((len(self.hex_array)-1, len(self.hex_array[-1])-1))

    def _select_key_end(self) -> None:
        self._move_key_end()

    def _move_key_home(self) -> None:
        self.cpos.col = 0

    def _move_key_ctl_home(self) -> None:
        self.cpos.row = 0
        self.cpos.col = 0

    def _select_key_home(self) -> None:
        self._move_key_home()

    def _insert_byte(self, wchar: str) -> None:
        if wchar == ' ':
            r_len = len(self.hex_array[self.cpos.row])
            if r_len < HexEditor.columns:
                self.hex_array[self.cpos.row][r_len:r_len] = ['--'] * (HexEditor.columns-r_len)
                self.hex_array_edit[self.cpos.row][r_len:r_len] = ['--'] * (HexEditor.columns-r_len)
                self.cpos.col = r_len
            else:
                self.hex_array.insert(self.cpos.row+1, ['--'] * HexEditor.columns)
                self.hex_array_edit.insert(self.cpos.row+1, ['--'] * HexEditor.columns)
                self.cpos.set_pos((self.cpos.row+1, 0))
            return
        pos_offset = int(wchar=='>')
        self.hex_array[self.cpos.row].insert(self.cpos.col+pos_offset, '--')
        self.hex_array_edit[self.cpos.row].insert(self.cpos.col+pos_offset, '--')
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
        if wchar == '>':
            self.cpos.col += 1

    def _key_string(self, wchar) -> None:
        """
        tries to replace a byte on the screen.

        Parameters:
        wchars (int|str):
            given by curses get_wch()
        """
        if not isinstance(wchar, str) or not wchar:
            return
        wchar = wchar.upper()
        if wchar in HEX_BYTE_KEYS and self.hex_array_edit[self.cpos.row]:
            if self.hex_array_edit[self.cpos.row][self.cpos.col] is None:
                self.hex_array_edit[self.cpos.row][self.cpos.col] = \
                    self.hex_array[self.cpos.row][self.cpos.col]
            self.hex_array_edit[self.cpos.row][self.cpos.col] = \
                self.hex_array_edit[self.cpos.row][self.cpos.col][:self.edited_byte_pos] + \
                wchar + self.hex_array_edit[self.cpos.row][self.cpos.col][self.edited_byte_pos+1:]
            if self.edited_byte_pos:
                self.cpos.col += 1
            self.edited_byte_pos = (self.edited_byte_pos+1)%2

            self.unsaved_progress = True
        elif wchar in '<> ':
            self._insert_byte(wchar)

    def _select_key_all(self) -> None:
        self._build_file()
        self.spos.set_pos((0, 0))
        self.cpos.set_pos((len(self.hex_array)-1, len(self.hex_array[-1])-1))
        return None

    def _action_copy(self) -> bool:
        sel_from, sel_to = self.selected_area
        if not self.selecting:
            sel_from = sel_to = self.cpos.get_pos()
        sel_bytes = ''
        for row, col in HexEditor.pos_between(sel_from, sel_to):
            hex_byte = self.hex_array_edit[row][col]
            if hex_byte is None:
                hex_byte = self.hex_array[row][col]
            sel_bytes += hex_byte
        self.error_bar = self.error_bar if (
            Clipboard.put(sel_bytes)
        ) else 'An error occured copying the selected bytes to the clipboard!'
        return True

    def _action_paste(self) -> bool:
        clipboard = self._get_clipboard()
        if clipboard is None:
            return True
        max_y, _ = self.getxymax()
        i_chars = clipboard.encode('utf-16', 'surrogatepass').decode('utf-16')
        insert_paste = self.hex_array_edit[self.cpos.row][self.cpos.col] in ['--', None] and \
            self.hex_array[self.cpos.row][self.cpos.col] == '--'
        for i_char in filter(HEX_BYTE_KEYS.__contains__, i_chars.upper()):
            self._key_string(i_char)
            if insert_paste and not self.edited_byte_pos%2:
                self._insert_byte('<')
            self._fix_cursor_position(max_y)
        self.unsaved_progress = True
        return True

    def _action_cut(self) -> bool:
        cpos = self.cpos.get_pos()
        self._action_copy()
        self._key_ctl_backspace(None)
        self.cpos.set_pos(cpos)
        return True

    def _action_render_scr(self, msg: str, tmp_error: str = '') -> None:
        max_y, max_x = self.getxymax()
        error_bar_backup = self.error_bar
        self.error_bar = tmp_error if tmp_error else self.error_bar
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
        self.error_bar = error_bar_backup
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
        for i in range(len(self.hex_array)):
            for hex_byte in self._get_current_state_row(i):
                try:
                    content += bytes.fromhex(hex_byte)
                except ValueError:
                    pass
        content += bytes(self._f_content_gen)
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
                err_print(self.error_bar, priority=err_print.WARNING)
        return True

    def _action_jump(self) -> bool:
        """
        handles the jump to line action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        wchar, l_jmp = '', ''
        while str(wchar).upper() not in [ESC_CODE, 'N']:
            self._action_render_scr(f"Confirm: [y]es, [n]o - Jump to byte: 0x{l_jmp}␣")
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        l_jmp += ''.join(filter(HEX_BYTE_KEYS.__contains__, clipboard.upper()))
                if key == b'_action_jump':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                l_jmp = l_jmp[:-1]
            elif key == b'_key_ctl_backspace':
                l_jmp = ''
            elif key == b'_key_string' and wchar.upper() in HEX_BYTE_KEYS:
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    l_jmp_int = int(l_jmp, 16)
                    self.cpos.row = l_jmp_int // HexEditor.columns
                    self.cpos.col = l_jmp_int %  HexEditor.columns
                break
        return True

    def _action_find(self, find_next: int = 0) -> bool:
        """
        handles the find in editor action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        search_byte_mode, bm_ind = True, '0x'
        sub_s_encoded = self.search
        wchar, sub_s, tmp_error= '', '', ''
        key, running = b'_key_enter', False
        while str(wchar) != ESC_CODE:
            if not find_next:
                pre_s = ''
                if self.search:
                    pre_s = f" [{bm_ind}{repr(self.search)[1:-1]}]"
                    if not search_byte_mode:
                        try:
                            pre_s = f" [{bm_ind}{repr(bytes.fromhex(self.search))[2:-1]}]"
                        except ValueError:
                            pass
                self._action_render_scr(
                    f"Confirm: 'ENTER' - Search for{pre_s}: {bm_ind}{frepr(sub_s)}␣",
                    tmp_error
                )
                wchar, key = self._get_next_char()
            elif running:
                break
            running = True
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        if search_byte_mode:
                            sub_s += ''.join(filter(HEX_BYTE_KEYS.__contains__, clipboard.upper()))
                        else:
                            sub_s += clipboard
                if key == b'_action_find':
                    wchar, key = '', b'_key_enter'
                if key == b'_action_insert':
                    search_byte_mode = not search_byte_mode
                    bm_ind = '0x' * search_byte_mode
                    self.search = self.search[:-1] if len(self.search) % 2 else self.search
                    sub_s_encoded = self.search
                    sub_s = ''
                if key == b'_action_background':
                    getattr(self, key.decode(), lambda *_: False)()
                if key == b'_action_resize':
                    getattr(self, key.decode(), lambda *_: False)()
                    self._render_scr()
            if not isinstance(wchar, str):
                continue
            if key == b'_key_backspace':
                sub_s = sub_s[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = sub_s[-1:].isalpha()
                while sub_s and sub_s[-1:].isalpha() == t_p:
                    sub_s = sub_s[:-1]
            elif key == b'_key_string' and not search_byte_mode:
                sub_s += wchar
            elif key == b'_key_string' and wchar.upper() in HEX_BYTE_KEYS:
                sub_s += wchar.upper()
            elif key == b'_key_enter':
                self.search = sub_s if sub_s else self.search
                if not self.search:
                    break
                if not search_byte_mode and self.search != sub_s_encoded:
                    i_chars = self.search.encode('utf-16', 'surrogatepass').decode('utf-16')
                    if HexEditor.unicode_escaped_search and sub_s:
                        try:
                            i_chars = i_chars.encode().decode('unicode_escape').encode('latin-1').decode()
                        except UnicodeError:
                            pass
                    self.search = ''
                    for i_char in i_chars:
                        for byte_ in i_char.encode():
                            self.search += f"{byte_:02X}"
                sub_s_encoded = self.search

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
                        search = search_iter_hex_factory(
                            self,
                            1-self.selecting,
                            downwards=(find_next >= 0)
                        )
                    except ValueError as exc:
                        tmp_error = str(exc)
                        continue
                    max_y, _ = self.getxymax()
                    cpos = next(search)
                    self.search_items[cpos] = search.s_len
                    if not self.selecting:
                        if find_next >= 0:
                            self.cpos.set_pos((max(cpos[0]-max_y, 0), 0))
                        else:
                            self.cpos.set_pos((min(cpos[0]+max_y, len(self.hex_array)-1),
                                               len(self.hex_array[cpos[0]])-1))
                    search = search_iter_hex_factory(
                        self,
                        1,
                        downwards=(find_next >= 0)
                    )
                    for search_pos in search:
                        if search_pos[0] < cpos[0]-max_y or search_pos[0] > cpos[0]+max_y:
                            break
                        self.cpos.set_pos(search_pos)
                        self.search_items[search_pos] = search.s_len
                    self.cpos.set_pos(cpos)
                    break
                except StopIteration:
                    if self.selecting:
                        self.cpos.set_pos(cpos_tmp)
                        self.spos.set_pos(spos_tmp)
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
        wchar = ''
        while str(wchar).upper() not in [ESC_CODE, 'N']:
            self._action_render_scr('Reload File? [y]es, [n]o; Abort? ESC')
            wchar, key = self._get_next_char()
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
            if not isinstance(wchar, str):
                continue
            if wchar.upper() in ['Y', 'J']:
                self._setup_file()
                break

        return True

    def _action_insert(self) -> bool:
        """
        handles the insert char action.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        wchar, i_chars = '', ''
        while str(wchar) != ESC_CODE:
            self._action_render_scr(f"Confirm: 'ENTER' - Insert char(s): {frepr(i_chars)}␣")
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                if key == b'_action_paste':
                    clipboard = self._get_clipboard()
                    if clipboard is not None:
                        i_chars += clipboard
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
                i_chars = i_chars[:-1]
            elif key == b'_key_ctl_backspace':
                t_p = i_chars[-1:].isalnum()
                while i_chars and i_chars[-1:].isalnum() == t_p:
                    i_chars = i_chars[:-1]
            elif key == b'_key_string':
                i_chars += wchar
            elif key == b'_key_enter':
                i_chars = i_chars.encode('utf-16', 'surrogatepass').decode('utf-16')
                if HexEditor.unicode_escaped_insert:
                    try:
                        i_chars = i_chars.encode().decode('unicode_escape').encode('latin-1').decode()
                    except UnicodeError:
                        pass
                max_y, _ = self.getxymax()
                for i_char in i_chars:
                    for byte_ in i_char.encode():
                        self._insert_byte('>')
                        self._fix_cursor_position(max_y)
                        self.hex_array_edit[self.cpos.row][self.cpos.col] = f"{byte_:02X}"
                self.unsaved_progress = True
                break
        return True

    def _action_background(self) -> bool:
        # only callable on UNIX
        curses.endwin()
        os.kill(os.getpid(), signal.SIGSTOP)
        self._init_screen()
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
                if not isinstance(wchar, str):
                    continue
                if wchar.upper() in ['Y', 'J']:
                    self._action_save()
                elif wchar == ESC_CODE: # ESC
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
            err_print('Interrupting...', priority=err_print.INFORMATION)
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


    def _function_help(self) -> None:
        curses.curs_set(0)
        self.curse_window.clear()
        coff = 20

        help_text = [
            f"{'F1':<{coff}}help",
            '',
            f"{'^A':<{coff}}select all",
            f"{'^C':<{coff}}copy selection",
            f"{'^X':<{coff}}cut selection",
            f"{'^V':<{coff}}paste from clipboard",
            '',
            f"{'^E':<{coff}}jump to offset",
            f"{'^N':<{coff}}insert text sequence",
            f"{'^F':<{coff}}find bytes or strings",
            f"{'(Shift+)F3':<{coff}}find next/(previous)",
            '',
            f"{'Space,>,<':<{coff}}insert new byte(s)",
            '',
            f"{'alt+S' if self.save_with_alt else '^S':<{coff}}save file",
            f"{'^R':<{coff}}reload file",
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
                (max_y+self.status_bar_size+3-len(help_text)) // 2,
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
        self._get_next_char()

    def _function_search(self) -> None:
        if not self.search:
            return
        self._action_find(1)

    def _function_search_r(self) -> None:
        if not self.search:
            return
        self._action_find(-1)

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
                err_print(f"__DEBUG__: Received  {str(key_):<22}{_debug_info}" + \
                    f"\t{str(key__):<15} \t{repr(wchar_)}", priority=err_print.INFORMATION)
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
            self.wpos.row, self.wpos.row + max_y
        )]
        encoded_section = [' '.join(line).ljust(HexEditor.columns*3-1) for line in hex_section]
        decoded_section = [
            ''.join(self.decode_char(obj) for obj in line).ljust(
                HexEditor.columns
            ) for line in hex_section
        ]
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
        # only highlight if the file has content
        if not self.hex_array[self.cpos.row]:
            return
        # Highlight Selection
        cursor_y = self.cpos.row-self.wpos.row+2
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

    def _render_highlight_selected_area(self, max_y: int) -> None:
        if not self.selecting:
            return
        # Highlight Selected Area
        sel_from, sel_to = self.selected_area
        for row, col in HexEditor.pos_between(sel_from, sel_to):
            if row < self.wpos.row:
                continue
            if row >= self.wpos.row+max_y:
                break
            color_id = 7 if self.hex_array_edit[row][col] is None else 8
            if (row, col) == self.cpos.get_pos():
                color_id = 4 if self.hex_array_edit[row][col] is None else 6
            try:
                self.curse_window.chgat(row-self.wpos.row+2, 13 + col*3,
                                        2, self._get_color(color_id))
                self.curse_window.chgat(row-self.wpos.row+2, 15 + HexEditor.columns*3 + col,
                                        1, self._get_color(color_id))
            except curses.error:
                pass

    def _render_search_items(self, max_y: int) -> None:
        # Highlight Search Items
        for (row, col), length in self.search_items.items():
            e_row = row + (col+length//2 - 1) // HexEditor.columns
            e_col = (col+length//2 - 1) % HexEditor.columns

            for p_row, p_col in HexEditor.pos_between((row, col), (e_row, e_col)):
                if p_row < self.wpos.row:
                    continue
                if p_row >= self.wpos.row+max_y:
                    break
                self.curse_window.chgat(p_row-self.wpos.row+2, 13 + p_col*3,
                                        2, self._get_color(9))
                self.curse_window.chgat(p_row-self.wpos.row+2, 15 + HexEditor.columns*3 + p_col,
                                        1, self._get_color(9))
            else:
                if length%2:
                    e_row = row + (col+length//2) // HexEditor.columns
                    e_col = (col+length//2) % HexEditor.columns
                    if e_row < self.wpos.row or e_row >= self.wpos.row+max_y:
                        continue
                    self.curse_window.chgat(e_row-self.wpos.row+2, 13 + e_col*3,
                                            1, self._get_color(9))
                    self.curse_window.chgat(e_row-self.wpos.row+2, 15 + HexEditor.columns*3 + e_col,
                                            1, self._get_color(9))

        if self.cpos.get_pos() in self.search_items:
            row, col = self.cpos.get_pos()
            length = self.search_items[self.cpos.get_pos()]
            e_row = row + (col+length//2 - 1) // HexEditor.columns
            e_col = (col+length//2 - 1) % HexEditor.columns

            for p_row, p_col in HexEditor.pos_between((row, col), (e_row, e_col)):
                if p_row >= self.wpos.row+max_y:
                    break
                self.curse_window.chgat(p_row-self.wpos.row+2, 13 + p_col*3,
                                        2, self._get_color(10))
                self.curse_window.chgat(p_row-self.wpos.row+2,
                                        15 + HexEditor.columns*3 + p_col,
                                        1, self._get_color(10))
            else:
                if length%2:
                    e_row = row + (col+length//2) // HexEditor.columns
                    e_col = (col+length//2) % HexEditor.columns
                    if self.wpos.row <= e_row < self.wpos.row+max_y:
                        self.curse_window.chgat(e_row-self.wpos.row+2, 13 + e_col*3,
                                                1, self._get_color(10))
                        self.curse_window.chgat(e_row-self.wpos.row+2,
                                                15 + HexEditor.columns*3 + e_col,
                                                1, self._get_color(10))

        self.search_items.clear()

    def _render_status_bar(self, max_y: int, max_x: int) -> None:
        # Draw status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size + 1, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            status_bar = f"File: {self.display_name} | Help: F1 | "
            status_bar += f"{self.cpos.row*HexEditor.columns+self.cpos.col:08X}"
            status_bar += f" | {'NOT ' * self.unsaved_progress}Saved!"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(self.display_name) + 3))
                status_bar = f"File: ...{self.display_name[-necc_space:] * bool(necc_space)} "
                status_bar += '| Help: F1 | '
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
        self._build_file_upto(max_y+self.cpos.row+2)

        self._fix_cursor_position(max_y)

        self._render_title_offset(max_x)
        self._render_draw_rows(max_y, max_x)
        self._render_highlight_selection()
        self._render_highlight_edits(max_y)
        self._render_highlight_selected_area(max_y)
        self._render_search_items(max_y)
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
            elif key in MOVE_HOTKEYS | FUNCTION_HOTKEYS:
                getattr(self, key.decode(), lambda *_: None)()
            # select bytes:
            if key in SELECT_HOTKEYS:
                if not self.selecting:
                    self.spos.set_pos(self.cpos.get_pos())
                getattr(self, key.decode(), lambda *_: None)()
                self.selecting = True
            elif key != b'_move_key_mouse':
                self.selecting = False

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

        curses.mousemask(-1)
        curses.mouseinterval(100)

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
                curses.use_default_colors()
                # status_bar
                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE )
                # error_bar
                curses.init_pair(2, curses.COLOR_RED  , curses.COLOR_WHITE )
                # prompts
                curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED   )
                # selected byte
                curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE )
                # edited byte
                curses.init_pair(5, curses.COLOR_RED  , curses.COLOR_BLACK )
                # selected and edited byte
                curses.init_pair(6, curses.COLOR_RED  , curses.COLOR_WHITE )
                # selected area
                curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)
                # selected area and edited byte
                curses.init_pair(8, curses.COLOR_RED  , curses.COLOR_YELLOW)
                # find (& replace)
                curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLUE  )
                # find (& replace) current match
                curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_GREEN )
        curses.raw()
        self.curse_window.nodelay(False)

    def _open(self) -> None:
        """
        init, run, deinit
        """
        try:
            self._init_screen()
            self._run()
        except (Exception, KeyboardInterrupt) as e:
            curses.endwin()
            if not self.unsaved_progress:
                raise e
            if not isinstance(e, KeyboardInterrupt):
                err_print('Oops..! Something went wrong.', priority=err_print.IMPORTANT)
            user_input = ''
            while user_input not in ['Y', 'J', 'N']:
                user_input = input('Do you want to save the changes? [Y/N]').upper()
            if user_input == 'N':
                raise e
            self._action_save()
            if self.unsaved_progress:
                err_print('Oops..! Something went wrong. The file could not be saved.', priority=err_print.IMPORTANT)
            else:
                err_print('The file has been successfully saved.', priority=err_print.INFORMATION)
            raise e
        finally:
            try: # cleanup - close file
                self._f_content_gen.throw(StopIteration)
            except StopIteration:
                pass
            curses.endwin()

    @classmethod
    def open(cls, file: Path, display_name: str) -> bool:
        """
        simple editor to change the contents of any provided file.

        Parameters:
        file (Path):
            a string representing a file(-path)
        display_name (str):
            the display name for the current file

        Returns:
        (bool):
            indicates whether or not the editor has written any content to the provided files
        """
        if HexEditor.loading_failed:
            return False

        if CURSES_MODULE_ERROR:
            err_print("The Editor could not be loaded. No Module 'curses' was found.", priority=err_print.INFORMATION)
            if on_windows_os:
                err_print('If you are on Windows OS, try pip-installing ', end='', priority=err_print.INFORMATION)
                err_print("'windows-curses'.", priority=err_print.INFORMATION)
            err_print(priority=err_print.INFORMATION)
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
    def set_flags(save_with_alt: bool, debug_mode: bool,
                  unicode_escaped_search: bool, unicode_escaped_insert: bool,
                  columns: int) -> None:
        """
        set the config flags for the Editor

        Parameters:
        save_with_alt (bool):
            indicates whetcher the stdin pipe has been used (and therefor tampered)
        debug_mode (bool)
            indicates if debug info should be displayed
        unicode_escaped_search (bool):
            indicates if the search should be unicode escaped
        columns (int):
            defines how many columns the editor should have
        """
        HexEditor.save_with_alt = save_with_alt
        HexEditor.debug_mode = debug_mode
        HexEditor.unicode_escaped_search = unicode_escaped_search
        HexEditor.unicode_escaped_insert = unicode_escaped_insert
        HexEditor.columns = columns
