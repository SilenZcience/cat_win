try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import sys


def _editor(curse_window, file: str, file_encoding: str, write_func) -> bool:
    """
    See editor() method
    """
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.raw()
    curse_window.nodelay(True)

    window_content = []
    error_bar = ''
    unsaved_progress = False
    status_bar_size = 1
    x, cur_col = 0, 0
    y, cur_row = 0, 0

    has_written = False

    try:
        with open(file, 'r', encoding=file_encoding) as f:
            for line in f.read().split('\n'):
                window_content.append([ord(char) for char in line])
    except OSError as e:
        status_bar_size = 2
        error_bar = str(e)
        window_content.append([])

    while True:
        max_y, max_x = curse_window.getmaxyx()

        curses.curs_set(0)
        curse_window.move(0, 0)
        # set the boundaries
        if cur_row < y:
            y = cur_row
        if cur_row >= y + max_y-status_bar_size:
            y = cur_row - max_y+1+status_bar_size
        if cur_col < x:
            x = cur_col
        if cur_col >= x + max_x:
            x = cur_col - max_x+1
        for row in range(max_y-1):
            brow = row + y
            for col in range(max_x):
                bcol = col + x
                try:
                    curse_window.addch(row, col, window_content[brow][bcol])
                except (IndexError, curses.error):
                    break
            curse_window.clrtoeol()
            try:
                curse_window.addch('\n')
            except curses.error:
                break
        try:
            curse_window.attron(curses.color_pair(2))

            if error_bar:
                curse_window.addstr(max_y - 2, 0, error_bar)
                curse_window.addstr(max_y - 2, len(error_bar), " " * (max_x - len(error_bar) - 1))

            curse_window.attron(curses.color_pair(1))

            status_bar = f"File: {file} | Exit: ^c | Save: ^s | Pos: {cur_col}, {cur_row} | {'NOT ' * unsaved_progress}Saved!"
            if len(status_bar) > max_x:
                necc_space = max(0, max_x - (len(status_bar) - len(file) + 3))
                status_bar = f"File: ...{file[-necc_space:] * bool(necc_space)} | Exit: ^c | Save: ^s | Pos: {cur_col}, {cur_row} | {'NOT ' * unsaved_progress}Saved!"
            curse_window.addstr(max_y - 1, 0, status_bar)
            curse_window.addstr(max_y - 1, len(status_bar), " " * (max_x - len(status_bar) - 1))

            curse_window.attroff(curses.color_pair(1))
        except curses.error:
            curse_window.attroff(curses.color_pair(1))
            curse_window.attroff(curses.color_pair(2))
        curse_window.move(cur_row-y, cur_col-x)
        curses.curs_set(1)
        curse_window.refresh()

        # get next char
        char = -1
        while char == -1:
            char = curse_window.getch()

        # default ascii char or TAB
        if char != ((char) & 0x1F) and char < 128 or char == 9:
            unsaved_progress = True
            window_content[cur_row].insert(cur_col, char)
            cur_col += 1
        # essentially 'enter'
        elif chr(char) in '\n\r':
            unsaved_progress = True
            new_line = window_content[cur_row][cur_col:]
            window_content[cur_row] = window_content[cur_row][:cur_col]
            cur_row += 1
            cur_col = 0
            window_content.insert(cur_row, [] + new_line)
        elif char in [8, 263]: # backspace
            unsaved_progress = True
            if cur_col: # delete char
                cur_col -= 1
                del window_content[cur_row][cur_col]
            elif cur_row: # or delete line
                line = window_content[cur_row]
                del window_content[cur_row]
                cur_row -= 1
                cur_col = len(window_content[cur_row])
                window_content[cur_row] += line
        elif char == curses.KEY_LEFT:
            if cur_col:
                cur_col -= 1
            elif cur_row:
                cur_row -= 1
                cur_col = len(window_content[cur_row])
        elif char == curses.KEY_RIGHT:
            if cur_col < len(window_content[cur_row]):
                cur_col += 1
            elif cur_row < len(window_content)-1:
                cur_row += 1
                cur_col = 0
        elif char == curses.KEY_UP and cur_row:
            cur_row -= 1
        elif char == curses.KEY_DOWN and cur_row < len(window_content)-1:
            cur_row += 1

        row = window_content[cur_row] if cur_row < len(window_content) else None
        rowlen = len(row) if row is not None else 0
        if cur_col > rowlen:
            cur_col = rowlen

        if char == (ord('s') & 0x1F):
            content = '\n'.join([''.join([chr(char) for char in line]) for line in window_content])
            try:
                write_func(content, file, file_encoding)
                has_written = True
                unsaved_progress = False
                error_bar = ''
                status_bar_size = 1
            except OSError as e:
                unsaved_progress = True
                error_bar = str(e)
                status_bar_size = 2
                print(error_bar, file=sys.stderr)
        elif char == (ord('q') & 0x1F):
            break
        elif char == (ord('c') & 0x1F):
            raise KeyboardInterrupt()

    return has_written

def editor(file: str, file_encoding: str, write_func, on_windows_os: bool) -> bool:
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
    
    Returns:
    (bool):
        indicates whether or not the editor has written any content to the provided files   
    """
    if CURSES_MODULE_ERROR:
        print("The Editor could not be loaded. No Module 'curses' was found.", file=sys.stderr)
        if on_windows_os:
            print("If you are on Windows OS, try pip-installing 'windows-curses'.", file=sys.stderr)
        return False

    return curses.wrapper(_editor, file, file_encoding, write_func)
