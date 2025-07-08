"""
DiffViewer
"""

try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import signal
import sys

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.service.helper.editorhelper import Position, \
    UNIFY_HOTKEYS, ACTION_HOTKEYS, MOVE_HOTKEYS, FUNCTION_HOTKEYS
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.diffviewerhelper import DifflibParser, DifflibID
from cat_win.src.service.helper.iohelper import IoHelper, err_print


class DiffViewer:
    """
    DiffViewer
    """
    loading_failed = False

    debug_mode = False

    file_encoding = 'utf-8'

    def __init__(self, files: list, display_names: list) -> None:
        self.curse_window = None

        self.files = files
        self.display_names = display_names
        self.difflibparser = None
        self.diff_items = None

        self.half_width = 0
        self.l_offset = 0
        self.status_bar_size = 1
        self.error_bar = ''

        # window position (top-left)
        self.wpos = Position(0, 0)

        self._setup_file()


    def _setup_file(self) -> None:
        """
        setup the diffviewer content screen by reading the given file.
        """
        try:
            self.difflibparser = DifflibParser(
                IoHelper.read_file(self.files[0], False, DiffViewer.file_encoding).splitlines(),
                IoHelper.read_file(self.files[1], False, DiffViewer.file_encoding).splitlines(),
                0.5, 0.6
            )
            self.diff_items = self.difflibparser.get_diff()
            if self.diff_items:
                self.l_offset = len(self.diff_items[0].lineno)+1
            else:
                self.l_offset = 0
            self.error_bar = ''
            self.status_bar_size = 1
        except OSError as exc:
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                err_print(self.error_bar)

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


    def lllen(self) -> int:
        """
        find the length of the longest line in the diffviewer content.

        Returns:
        (int):
            the length of the longest line
        """
        if not self.diff_items:
            return 0
        return max(
            max(
                len(item.line1),
                len(item.line2)
            ) for item in self.diff_items[
                self.wpos.row:self.wpos.row+self.getxymax()[0]
            ]
        )

    def _move_key_left(self) -> None:
        self.wpos.col -= 1

    def _move_key_right(self) -> None:
        self.wpos.col += 1

    def _move_key_up(self) -> None:
        self.wpos.row -= 1

    def _move_key_down(self) -> None:
        self.wpos.row += 1

    def _move_key_ctl_left(self) -> None:
        self.wpos.col -= 10

    def _move_key_ctl_right(self) -> None:
        self.wpos.col += 10

    def _move_key_ctl_up(self) -> None:
        self.wpos.row -= 10

    def _move_key_ctl_down(self) -> None:
        self.wpos.row += 10

    def _move_key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row -= max_y

    def _move_key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row += max_y

    def _move_key_end(self) -> None:
        self.wpos.col = self.lllen() - self.half_width

    def _move_key_ctl_end(self) -> None:
        max_y, _ = self.getxymax()
        self.wpos.row = len(self.diff_items) - max_y
        self.wpos.col = self.lllen() - self.half_width

    def _move_key_home(self) -> None:
        self.wpos.col = 0

    def _move_key_ctl_home(self) -> None:
        self.wpos.row = 0
        self.wpos.col = 0

    def _action_render_scr(self, msg: str, tmp_error: str = '') -> None:
        max_y, max_x = self.getxymax()
        error_bar_backup = self.error_bar
        self.error_bar = tmp_error if tmp_error else self.error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                        self.error_bar[:max_x].ljust(max_x),
                                        self._get_color(2))
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                        msg[:max_x].ljust(max_x),
                                        self._get_color(10))
        except curses.error:
            pass
        self.error_bar = error_bar_backup
        self.curse_window.refresh()

    def _action_jump(self) -> bool:
        """
        handles the jump to line action.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        wchar, l_jmp = '', ''
        while str(wchar).upper() not in [ESC_CODE, 'N']:
            self._action_render_scr(f"Confirm: [y]es, [n]o - Jump to line: {l_jmp}␣")
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
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
            elif key == b'_key_string' and wchar.isdigit():
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    l_jmp = max(min(int(l_jmp), self.difflibparser.last_lineno), 1)
                    for i in range(l_jmp-1, len(self.diff_items)):
                        if not self.diff_items[i].lineno.isspace() and int(self.diff_items[i].lineno) == l_jmp:
                            self.wpos.row = i
                            self.wpos.col = 0
                            break
                break
        return True

    def _action_reload(self) -> bool:
        """
        prompt to reload the file.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        self._setup_file()
        return True

    def _action_background(self) -> bool:
        # only callable on UNIX
        curses.endwin()
        os.kill(os.getpid(), signal.SIGSTOP)
        self._init_screen()
        return True

    def _action_quit(self) -> bool:
        """
        handles the quit diffviewer action.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        return False

    def _action_interrupt(self) -> bool:
        """
        handles the interrupt action.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        if self.debug_mode:
            err_print('Interrupting...')
        raise KeyboardInterrupt

    def _action_resize(self) -> bool:
        """
        handles the resizing of the (terminal) window.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        try:
            curses.resize_term(*self.curse_window.getmaxyx())
        except curses.error:
            pass
        self.half_width = (self.getxymax()[1]-4-self.l_offset) // 2
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
                err_print(f"__DEBUG__: Received  {str(key_):<22}{_debug_info}" + \
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

    def _enforce_boundaries(self, max_y: int) -> None:
        """
        enforce the boundaries of the diffviewer content.

        Parameters:
        max_y (int):
            the maximum y value of the curses window
        """
        self.wpos.row = min(self.wpos.row, len(self.diff_items) - max_y)
        self.wpos.row = max(self.wpos.row, 0)

        self.wpos.col = min(self.wpos.col, self.lllen() - self.half_width)
        self.wpos.col = max(self.wpos.col, 0)

    def _render_scr(self) -> None:
        """
        render the curses window.
        """
        max_y, max_x = self.getxymax()
        self._enforce_boundaries(max_y)

        self.curse_window.move(0, 0)
        for row in range(max_y):
            brow = row + self.wpos.row
            if brow >= len(self.diff_items):
                self.curse_window.clrtobot()
                break
            self.curse_window.clrtoeol()

            self.curse_window.addstr(
                row, 0,
                f"{self.diff_items[brow].lineno} ",
                self._get_color(8)
            )
            if self.diff_items[brow].code == DifflibID.EQUAL:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    self._get_color(7)
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    self._get_color(8)
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    self._get_color(7)
                )
            elif self.diff_items[brow].code == DifflibID.DELETE:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    ' ' * self.half_width,
                    self._get_color(9)
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    self._get_color(8)
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    ' ' * self.half_width,
                    self._get_color(6)
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width],
                    self._get_color(5) | curses.A_BLINK
                )
            elif self.diff_items[brow].code == DifflibID.INSERT:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    ' ' * self.half_width,
                    self._get_color(4)
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width],
                    self._get_color(3) | curses.A_UNDERLINE
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    self._get_color(8)
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    ' ' * self.half_width,
                    self._get_color(9)
                )
            elif self.diff_items[brow].code == DifflibID.CHANGED:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    self._get_color(4)
                )
                for idx_ in self.diff_items[brow].changes2:
                    idx = idx_ - self.wpos.col
                    if idx < 0 or idx >= self.half_width:
                        continue
                    self.curse_window.chgat(
                        row, self.l_offset + self.half_width + 3 + idx,
                        1, self._get_color(3) | curses.A_UNDERLINE
                    )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    self._get_color(8)
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    self._get_color(6)
                )
                for idx_ in self.diff_items[brow].changes1:
                    idx = idx_ - self.wpos.col
                    if idx < 0 or idx >= self.half_width:
                        continue
                    self.curse_window.chgat(
                        row, self.l_offset + idx,
                        1, self._get_color(5) | curses.A_UNDERLINE
                    )

            self.curse_window.move(row+1, 0)

        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            status_bar = f"Equal: {self.difflibparser.count_equal} | "
            status_bar+= f"Insertions: {self.difflibparser.count_insert} | "
            status_bar+= f"Deletions: {self.difflibparser.count_delete} | "
            status_bar+= f"Modifications: {self.difflibparser.count_changed}"
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            # this throws an error (should be max_x-1), but looks better:
            status_bar = status_bar[:max_x].ljust(max_x)
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                     status_bar, self._get_color(1))
        except curses.error:
            pass

        self.curse_window.refresh()

    def _run(self) -> None:
        """
        main loop for the diffviewer.
        """
        self.half_width = (self.getxymax()[1]-4-self.l_offset) // 2
        running = True

        while running:
            self._render_scr()
            _, key = self._get_next_char()

            if key in ACTION_HOTKEYS:
                running &= getattr(self, key.decode(), lambda *_: True)()
            elif key in MOVE_HOTKEYS | FUNCTION_HOTKEYS:
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
                curses.use_default_colors()
                # status_bar
                curses.init_pair(1, curses.COLOR_BLACK  , curses.COLOR_WHITE)
                # error_bar
                curses.init_pair(2, curses.COLOR_RED    , curses.COLOR_WHITE)
                # green background
                curses.init_pair(3, curses.COLOR_BLACK  , curses.COLOR_GREEN)
                # light green background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN+8)
                    except curses.error:
                        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
                else:
                    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
                # red background
                curses.init_pair(5, curses.COLOR_BLACK  , curses.COLOR_RED  )
                # light red background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED+8)
                    except curses.error:
                        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)
                else:
                    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)
                # default color
                curses.init_pair(7, curses.COLOR_WHITE  , curses.COLOR_BLACK)
                # lineno color
                curses.init_pair(8, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                # gray background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK+8)
                    except curses.error:
                        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)
                else:
                    curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)
                # prompts
                curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_RED)

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
            if not isinstance(e, KeyboardInterrupt):
                err_print('Oops..! Something went wrong.')
            raise e
        finally:
            curses.endwin()

    @classmethod
    def open(cls, files: list, display_names: list) -> None:
        """
        simple diffviewer to view the contents/differences of two provided files.

        Parameters:
        file (Path):
            a list containing exactly two files(-path)
        display_name (str):
            the display names for the two files
        """
        if DiffViewer.loading_failed:
            return

        if CURSES_MODULE_ERROR:
            err_print("The Diffviewer could not be loaded. No Module 'curses' was found.")
            if on_windows_os:
                err_print('If you are on Windows OS, try pip-installing ', end='')
                err_print("'windows-curses'.")
            err_print()
            DiffViewer.loading_failed = True
            return

        diffviewer = cls(files, display_names)

        if on_windows_os:
            # disable background feature on windows
            diffviewer._action_background = lambda *_: True
        else:
            # ignore background signals on UNIX, since a custom background implementation exists
            signal.signal(signal.SIGTSTP, signal.SIG_IGN)

        diffviewer._open()

    @staticmethod
    def set_flags(debug_mode: bool, file_encoding: str) -> None:
        """
        set the config flags for the Diffviewer

        Parameters:
        debug_mode (bool)
            indicates if debug info should be displayed
        file_encoding (str):
            the file encoding to use when opening a file
        """
        DiffViewer.debug_mode = debug_mode
        DiffViewer.file_encoding = file_encoding
