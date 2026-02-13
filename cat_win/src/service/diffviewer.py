"""
DiffViewer
"""
from datetime import datetime
from pathlib import Path
try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True
import os
import signal
import subprocess
import sys

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.service.fileattributes import get_file_size, _convert_size, \
    get_file_mtime, get_file_ctime
from cat_win.src.service.helper.editorsearchhelper import search_iter_diff_factory
from cat_win.src.service.helper.editorhelper import Position, frepr, \
    UNIFY_HOTKEYS, ACTION_HOTKEYS, MOVE_HOTKEYS, FUNCTION_HOTKEYS
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.diffviewerhelper import DifflibParser, DifflibID
from cat_win.src.service.helper.iohelper import IoHelper, err_print


def get_git_file_history(file_path: Path) -> list:
    """
    Get a list of all commits that changed a specific file.

    Parameters:
    file_path (Path):
        the path to the file.

    Returns:
    (list):
        A list of dictionaries, each containing:
        - 'hash': commit hash (str)
        - 'date': commit date (str)
        - 'author': commit author (str)
        - 'message': commit message (str)
        - 'file_path': path of the file at this commit (str, accounts for renames)

    Raises:
    OSError: if not in a git repository
    subprocess.CalledProcessError: if git command fails
    """
    repo_root = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=os.path.dirname(file_path) or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False
    ).stdout.decode().strip()
    if not repo_root:
        raise OSError('not a git repository (or any of the parent directories)')

    rel_path = os.path.relpath(file_path, repo_root)

    log_output = subprocess.run(
        ['git', 'log', '--follow', '--name-status',
         '--pretty=format:%H|%ai|%an|%s', '--', rel_path],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    ).stdout.decode().splitlines()

    commits = []
    i = 0
    while i < len(log_output):
        line = log_output[i].strip()

        if not line or '|' not in line:
            i += 1
            continue # Skip empty lines or lines without commit info

        parts = line.split('|', 3)
        if len(parts) != 4 or len(parts[0]) != 40:
            i += 1
            continue  # Not a valid commit line, skip

        commit_hash, commit_date, commit_author, commit_message = parts
        file_path_at_commit = rel_path
        if i + 1 < len(log_output):
            status_line = log_output[i + 1].strip()
            if status_line:
                status_parts = status_line.split('\t')
                if len(status_parts) >= 2:
                    # For renamed files (R), parts[1] is old name (needed for --follow)
                    # For other statuses (M, A, D), parts[1] is the file name
                    file_path_at_commit = status_parts[1]

        commits.append({
            'hash': commit_hash,
            'date': commit_date,
            'author': commit_author,
            'message': commit_message,
            'file_path': file_path_at_commit
        })

        i += 1

    return commits


def get_git_file_content_at_commit(file_path: Path, commit_hash: str) -> list:
    """
    Get the content of a file at a specific commit.

    Parameters:
    file_path (Path):
        the path to the file.
    commit_hash (str or dict):
        either a commit hash string, or a commit dictionary from get_git_file_history()

    Returns:
    (list):
        the content of the file at the specified commit as a list of lines.
        Returns empty list if the file doesn't exist at that commit.

    Raises:
    OSError: if not in a git repository
    subprocess.CalledProcessError: if git command fails
    """
    repo_root = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=os.path.dirname(file_path) or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False
    ).stdout.decode().strip()
    if not repo_root:
        raise OSError('not a git repository (or any of the parent directories)')

    if isinstance(commit_hash, dict):
        actual_hash = commit_hash['hash']
        file_path_at_commit = commit_hash.get('file_path')
        if not file_path_at_commit:
            file_path_at_commit = os.path.relpath(file_path, repo_root)
    else:
        actual_hash = commit_hash
        file_path_at_commit = os.path.relpath(file_path, repo_root)

    try:
        result = subprocess.run(
            ['git', 'show', f'{actual_hash}:{file_path_at_commit}'],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode(errors='replace').splitlines()
    except subprocess.CalledProcessError:
        return []


class DiffViewer:
    """
    DiffViewer
    """
    loading_failed = False

    debug_mode = False

    file_encoding = 'utf-8'

    def __init__(self, files: list, file_idxs: tuple = None, file_commit_hashes: tuple = (None, None)) -> None:
        """
        defines a DiffViewer object.

        Parameters:
        files (list):
            list of tuples (file, display_name)
        file_idxs (tuple):
            indexes of the files to open in the diffviewer
        """
        if file_idxs is None:
            file_idxs = (0, 1) if len(files) >= 2 else (0, 0)

        self.curse_window = None

        self.files = files
        self.file_commit_hashes = file_commit_hashes
        self.diff_files = [files[file_idxs[0]][0], files[file_idxs[1]][0]]
        self.display_names = [files[file_idxs[0]][1], files[file_idxs[1]][1]]
        self.open_next_idxs = None
        self.open_next_hashes = (None, None)
        self.difflibparser = self.difflibparser_bak = None
        self.diff_items = self.diff_items_bak = None

        self.half_width = 0
        self.l_offset = 0
        self.status_bar_size = 1
        self.error_bar = ''

        self.search = ''
        self.search_items: dict = {}

        # window position (top-left)
        self.wpos = self.wpos_bak = Position(0, 0)
        self.rpos = self.rpos_bak = Position(0, 0)
        self.cpos = Position(0, 0)

        self.displaying_overview = False
        self.difflibparser_cutoff = 0.75

        self._setup_file()

    def _setup_file(self) -> None:
        """
        setup the diffviewer content screen by reading the given file.
        """
        self.displaying_overview = False
        try:
            if self.file_commit_hashes[0] is None:
                text1 = IoHelper.read_file(
                    self.diff_files[0], False, DiffViewer.file_encoding, errors='replace'
                ).splitlines()
            else:
                try:
                    text1 = get_git_file_content_at_commit(
                        self.diff_files[0], self.file_commit_hashes[0]
                    )
                    self.display_names[0] = f"GIT: {self.display_names[0]}"
                except (OSError, subprocess.CalledProcessError) as exc:
                    text1 = []
                    self.display_names[0] = f'<GIT_ERROR> {str(exc)}'
            if self.file_commit_hashes[1] is None:
                text2 = IoHelper.read_file(
                    self.diff_files[1], False, DiffViewer.file_encoding, errors='replace'
                ).splitlines()
            else:
                try:
                    text2 = get_git_file_content_at_commit(
                        self.diff_files[1], self.file_commit_hashes[1]
                    )
                    self.display_names[1] = f"GIT: {self.display_names[1]}"
                except (OSError, subprocess.CalledProcessError) as exc:
                    text1 = []
                    self.display_names[0] = f'<GIT_ERROR> {str(exc)}'

            self.difflibparser = self.difflibparser_bak = DifflibParser(
                text1,
                text2,
                self.difflibparser_cutoff-0.01, self.difflibparser_cutoff
            )

            self.diff_items = self.diff_items_bak = self.difflibparser.get_diff()
            self.l_offset = len(self.diff_items[0].lineno)+1 if self.diff_items else 0
            self.error_bar = ''
            self.status_bar_size = 1
            if self.diff_items:
                self.rpos.row = min(max(self.rpos.row, 0), len(self.diff_items)-1)
        except (OSError, UnicodeError) as exc:
            self.error_bar = str(exc)
            self.status_bar_size = 2
            if self.debug_mode:
                err_print(self.error_bar, priority=err_print.WARNING)
            self.difflibparser = self.difflibparser_bak = DifflibParser(
                [],
                [],
            )
            self.diff_items = self.diff_items_bak = self.difflibparser.get_diff()
            self.rpos.row = 0

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

    def _move_key_mouse(self) -> None:
        """
        handles mouse events.
        """
        m_state = curses.getmouse()[4]
        if m_state & curses.BUTTON4_PRESSED:
            for _ in range(3):
                self._move_key_up()
        elif m_state & curses.BUTTON5_PRESSED:
            for _ in range(3):
                self._move_key_down()

    def _move_key_left(self) -> None:
        self.wpos.col -= 1

    def _move_key_right(self) -> None:
        self.wpos.col += 1

    def _move_key_up(self) -> None:
        self.rpos.row = max(self.rpos.row-1, 0)
        self._ensure_rpos_visible()

    def _move_key_down(self) -> None:
        self.rpos.row = min(self.rpos.row+1, len(self.diff_items)-1)
        self._ensure_rpos_visible()

    def _move_key_ctl_left(self) -> None:
        self.wpos.col -= 10

    def _move_key_ctl_right(self) -> None:
        self.wpos.col += 10

    def _move_key_ctl_up(self) -> None:
        self.rpos.row = max(self.rpos.row-10, 0)
        self._ensure_rpos_visible()

    def _move_key_ctl_down(self) -> None:
        self.rpos.row = min(self.rpos.row+10, len(self.diff_items)-1)
        self._ensure_rpos_visible()

    def _move_key_page_up(self) -> None:
        max_y, _ = self.getxymax()
        self.rpos.row = max(self.rpos.row-max_y, 0)
        self._ensure_rpos_visible()

    def _move_key_page_down(self) -> None:
        max_y, _ = self.getxymax()
        self.rpos.row = min(self.rpos.row+max_y, len(self.diff_items)-1)
        self._ensure_rpos_visible()

    def _move_key_end(self) -> None:
        self.wpos.col = self.lllen() - self.half_width

    def _move_key_ctl_end(self) -> None:
        self.rpos.row = max(len(self.diff_items)-1, 0)
        self._ensure_rpos_visible()
        self.wpos.col = self.lllen() - self.half_width

    def _move_key_home(self) -> None:
        self.wpos.col = 0

    def _move_key_ctl_home(self) -> None:
        self.rpos.row = 0
        self._ensure_rpos_visible()
        self.wpos.row = 0
        self.wpos.col = 0

    def _ensure_rpos_visible(self) -> None:
        max_y, _ = self.getxymax()
        if self.rpos.row < self.wpos.row:
            self.wpos.row = self.rpos.row
        elif self.rpos.row >= self.wpos.row + max_y:
            self.wpos.row = self.rpos.row - max_y + 1

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
            elif key == b'_key_ctl_backspace':
                l_jmp = ''
            elif key == b'_key_string' and wchar.isdigit():
                l_jmp += wchar
            elif (key == b'_key_string' and wchar.upper() in ['Y', 'J']) or \
                key == b'_key_enter':
                if l_jmp:
                    l_jmp = max(min(int(l_jmp), self.difflibparser.last_lineno), 1)
                    for i in range(l_jmp-1, len(self.diff_items)):
                        if not self.diff_items[i].lineno.isspace() and int(self.diff_items[i].lineno) == l_jmp:
                            self.rpos.row = i
                            self._ensure_rpos_visible()
                            self.wpos.col = 0
                            break
                break
        return True

    def _action_find(self, find_next: int = 0) -> bool:
        """
        handles the find in diffviewer action.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        wchar, sub_s, tmp_error = '', '', ''
        key, running = b'_key_enter', False
        while str(wchar) != ESC_CODE:
            if not find_next:
                pre_s = ''
                if self.search:
                    pre_s = f" [{repr(self.search)[1:-1]}]"
                self._action_render_scr(
                    f"Confirm: 'ENTER' - Search for{pre_s}: {frepr(sub_s)}␣",
                    tmp_error
                )
                wchar, key = self._get_next_char()
            elif running:
                break
            running = True
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
                # if key == b'_action_paste':
                #     clipboard = self._get_clipboard()
                #     if clipboard is not None:
                #         sub_s += clipboard
                if key == b'_action_find':
                    wchar, key = '', b'_key_enter'
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
                t_p = sub_s[-1:].isalnum()
                while sub_s and sub_s[-1:].isalnum() == t_p:
                    sub_s = sub_s[:-1]
            elif key == b'_key_string':
                sub_s += wchar
            elif key == b'_key_enter':
                self.search = sub_s if sub_s else self.search
                if not self.search:
                    break
                # if Editor.unicode_escaped_search and sub_s:
                #     try:
                #         self.search = sub_s.encode().decode('unicode_escape').encode('latin-1').decode()
                #     except UnicodeError:
                #         pass
                max_y, _ = self.getxymax()
                if (
                    self.cpos.get_pos()[0] < self.wpos.get_pos()[0] or
                    self.cpos.get_pos()[0] >= self.wpos.get_pos()[0]+max_y or
                    self.cpos.get_pos()[1] < self.wpos.get_pos()[1] or
                    self.cpos.get_pos()[1] >= self.wpos.get_pos()[1]+self.half_width
                ):
                    if find_next >= 0:
                        self.cpos.set_pos(self.wpos.get_pos())
                    else:
                        self.cpos.set_pos(
                            (
                                self.wpos.get_pos()[0]+max_y-1,
                                max(
                                    len(self.diff_items[self.wpos.get_pos()[0]+max_y-1].line1),
                                    len(self.diff_items[self.wpos.get_pos()[0]+max_y-1].line2)
                                )
                            )
                        )

                try:
                    try:
                        search = search_iter_diff_factory(
                            self,
                            1,
                            downwards=(find_next >= 0)
                        )
                    except ValueError as exc:
                        tmp_error = str(exc)
                        continue
                    cpos = next(search)
                    self.search_items[(*cpos, search.line2_matched)] = search.s_len
                    if find_next >= 0:
                        self.cpos.set_pos((max(cpos[0]-max_y, 0), 0))
                    else:
                        self.cpos.set_pos((min(cpos[0]+max_y, len(self.diff_items)-1),
                                            max(len(self.diff_items[cpos[0]].line1),
                                                len(self.diff_items[cpos[0]].line2))))
                    search = search_iter_diff_factory(
                        self,
                        1,
                        downwards=(find_next >= 0)
                    )
                    for search_pos in search:
                        if search_pos[0] < cpos[0]-max_y or search_pos[0] > cpos[0]+max_y:
                            break
                        self.cpos.set_pos(search_pos)
                        self.search_items[(*search_pos, search.line2_matched)] = search.s_len
                    self.cpos.set_pos(cpos)
                    if (
                        self.cpos.get_pos()[0] < self.wpos.get_pos()[0] or
                        self.cpos.get_pos()[0] >= self.wpos.get_pos()[0]+max_y or
                        self.cpos.get_pos()[1] < self.wpos.get_pos()[1] or
                        self.cpos.get_pos()[1] >= self.wpos.get_pos()[1]+self.half_width
                    ):
                        if find_next >= 0:
                            self.wpos.row = cpos[0]
                        else:
                            self.wpos.row = max(0, cpos[0]-max_y+1)
                        if cpos[1]+len(self.search) < self.half_width:
                            self.wpos.col = 0
                        else:
                            self.wpos.col = cpos[1]+len(self.search) - self.half_width
                    break
                except StopIteration:
                    tmp_error = 'no matches were found!'
        return True

    def _action_insert(self) -> bool:
        """
        *naming convention only for hotkeys*
        handles the prompt to change the cutoff ratio for the difflibparser.

        Returns:
        (bool):
            indicates if the editor should keep running
        """
        wchar, cutoff = '', ''
        while str(wchar) != ESC_CODE:
            self._action_render_scr(
                f"Confirm: 'ENTER' - Cutoff Ratio [{self.difflibparser_cutoff}]: {cutoff}␣"
            )
            wchar, key = self._get_next_char()
            if key in ACTION_HOTKEYS:
                if key in [b'_action_quit', b'_action_interrupt']:
                    break
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
                cutoff = cutoff[:-1]
            elif key == b'_key_ctl_backspace':
                cutoff = ''
            elif key == b'_key_string':
                if cutoff == '1':
                    continue
                if not cutoff and wchar in '10.':
                    cutoff += wchar
                elif wchar == '.' and '.' not in cutoff:
                    cutoff += wchar
                elif '.' in cutoff[:2] and wchar.isdigit():
                    cutoff += wchar
            elif key == b'_key_enter':
                if cutoff:
                    self.difflibparser_cutoff = float(0 if cutoff=='.' else cutoff)
                    self._setup_file()
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
        if self.displaying_overview and self.open_next_idxs is None:
            self.displaying_overview = False
            self.curse_window.clear()

            self.difflibparser = self.difflibparser_bak
            self.diff_items = self.diff_items_bak
            self.l_offset = len(self.diff_items[0].lineno)+1 if self.diff_items else 0
            self.wpos = self.wpos_bak
            self.rpos = self.rpos_bak
            return True

        return False

    def _action_interrupt(self) -> bool:
        """
        handles the interrupt action.

        Returns:
        (bool):
            indicates if the diffviewer should keep running
        """
        if self.debug_mode:
            err_print('Interrupting...', priority=err_print.INFORMATION)
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
        self.half_width = (self.getxymax()[1]-3-self.l_offset) // 2
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

        selected_idx = [
            _find_current_idx(self.diff_files[0], self.display_names[0]),
            _find_current_idx(self.diff_files[1], self.display_names[1])
        ]

        max_y, max_x = self.getxymax()
        max_y += self.status_bar_size - 2
        nav_x = [0, 0]
        nav_y = [
            max(0, min(selected_idx[0] - max_y // 2, len(self.files) - max_y)),
            max(0, min(selected_idx[1] - max_y // 2, len(self.files) - max_y))
        ]
        active_list = 0

        # Selection mode: 'files' or 'commits'
        mode = 'files'
        file_commits = [None, None]
        file_selected_idxs = None

        wchar, key = '', b''
        while str(wchar) != ESC_CODE:
            list_width = max(1, (max_x - 3) // 2)
            right_x = list_width + 3

            if mode == 'files':
                data_lists = [self.files, self.files]
                maxlen_displayname = [
                    max((len(display_name) for _, display_name in self.files[nav_y[0]:nav_y[0]+max_y]), default=0),
                    max((len(display_name) for _, display_name in self.files[nav_y[1]:nav_y[1]+max_y]), default=0)
                ]
            else:
                data_lists = [file_commits[0] or [], file_commits[1] or []]
                maxlen_displayname = [0, 0]
                for side in (0, 1):
                    if data_lists[side]:
                        maxlen_displayname[side] = max(
                            (len(f"{c['hash'][:7]} | {c['date'][:10]} | {c['author']} | {c['message']}")
                             for c in data_lists[side][nav_y[side]:nav_y[side]+max_y]),
                            default=0
                        )

            self.curse_window.move(max_y, 0)
            self.curse_window.clrtoeol()
            for row in range(max_y):
                for side in (0, 1):
                    entry_idx = row + nav_y[side]
                    if entry_idx >= len(data_lists[side]):
                        continue

                    if mode == 'files':
                        _, display_name = data_lists[side][entry_idx]
                        is_selected = selected_idx[side] == entry_idx
                        is_current = self.files[entry_idx][0] == self.diff_files[side]
                    else:
                        commit = data_lists[side][entry_idx]
                        display_name = f"{commit['hash'][:7]} | {commit['date'][:10]} | {commit['author']} | {commit['message']}"
                        is_selected = selected_idx[side] == entry_idx
                        is_current = False

                    color = 0
                    if is_selected and is_current:
                        color = self._get_color(13) if side == active_list else self._get_color(14)
                    elif is_selected:
                        color = self._get_color(1) if side == active_list else self._get_color(15)
                    elif is_current:
                        color = self._get_color(8)

                    start_x = 0 if side == 0 else right_x
                    offset_x = nav_x[side]
                    text = f"{display_name}"[offset_x:offset_x+list_width]
                    try:
                        self.curse_window.addstr(row, start_x, text.ljust(list_width), color)
                    except curses.error:
                        break

                if row == max_y - 1:
                    if len(data_lists[0]) > max_y + nav_y[0]:
                        self.curse_window.addstr(row + 1, 0, '...')
                    if len(data_lists[1]) > max_y + nav_y[1]:
                        self.curse_window.addstr(row + 1, right_x, '...')
                    self.curse_window.clrtoeol()
                    break

            if mode == 'files':
                status_msg = 'Select two files. Tab/Shift+Tab switch list. Confirm with <Enter> or <Space>.'
            else:
                status_msg = 'Select commits (or go back with <Escape>). Tab/Shift+Tab switch list. Confirm with <Enter> or <Space>.'

            try:
                self.curse_window.addstr(
                    max_y+1, 0,
                    status_msg[:max_x].ljust(max_x),
                    self._get_color(1)
                )
            except curses.error:
                pass

            self.curse_window.refresh()

            wchar, key = self._get_next_char()
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
            if key in [b'_indent_tab', b'_indent_btab', b'_select_key_left', b'_select_key_right']:
                active_list = 1 - active_list
            if key in MOVE_HOTKEYS:
                list_len = len(data_lists[active_list])
                if list_len == 0:
                    continue

                if key == b'_move_key_up':
                    selected_idx[active_list] = max(0, selected_idx[active_list] - 1)
                    nav_y[active_list] = min(nav_y[active_list], selected_idx[active_list])
                elif key == b'_move_key_ctl_up':
                    selected_idx[active_list] = max(0, selected_idx[active_list] - 10)
                    nav_y[active_list] = min(nav_y[active_list], selected_idx[active_list])
                elif key == b'_move_key_down':
                    selected_idx[active_list] = min(list_len - 1, selected_idx[active_list] + 1)
                    if selected_idx[active_list] >= nav_y[active_list] + max_y - 1:
                        nav_y[active_list] = selected_idx[active_list] - max_y + 1
                elif key == b'_move_key_ctl_down':
                    selected_idx[active_list] = min(list_len - 1, selected_idx[active_list] + 10)
                    if selected_idx[active_list] >= nav_y[active_list] + max_y - 1:
                        nav_y[active_list] = selected_idx[active_list] - max_y + 1
                elif key == b'_move_key_left':
                    nav_x[active_list] = max(0, nav_x[active_list] - 1)
                elif key == b'_move_key_ctl_left':
                    nav_x[active_list] = max(0, nav_x[active_list] - 10)
                elif key == b'_move_key_right':
                    nav_x[active_list] = max(0, min(maxlen_displayname[active_list] - list_width, nav_x[active_list] + 1))
                elif key == b'_move_key_ctl_right':
                    nav_x[active_list] = max(0, min(maxlen_displayname[active_list] - list_width, nav_x[active_list] + 10))

            if key == b'_key_enter' or (key == b'_key_string' and wchar == ' '):
                if mode == 'files':
                    file_selected_idxs = [selected_idx[0], selected_idx[1]]

                    for side in (0, 1):
                        file_path = self.files[file_selected_idxs[side]][0]
                        try:
                            commits = get_git_file_history(file_path)
                            file_commits[side] = [{'hash': '_LOCAL_', 'date': 'Current', 'author': 'Local', 'message': 'Use local file (not git)'}] + commits
                        except (OSError, subprocess.CalledProcessError):
                            file_commits[side] = None

                    if file_commits[0] or file_commits[1]:
                        mode = 'commits'
                        selected_idx = [0, 0]
                        nav_x = [0, 0]
                        nav_y = [0, 0]
                        active_list = 0
                        self.curse_window.clear()
                    else:
                        current_idxs = (
                            _find_current_idx(self.diff_files[0], self.display_names[0]),
                            _find_current_idx(self.diff_files[1], self.display_names[1])
                        )
                        if file_selected_idxs != current_idxs:
                            self.open_next_idxs = file_selected_idxs
                        break
                else:
                    current_idxs = (
                        _find_current_idx(self.diff_files[0], self.display_names[0]),
                        _find_current_idx(self.diff_files[1], self.display_names[1])
                    )
                    if file_selected_idxs != current_idxs:
                        self.open_next_idxs = file_selected_idxs

                    self.open_next_hashes = (
                        None if (
                            file_commits[0] and file_commits[0][selected_idx[0]]['hash'] == '_LOCAL_'
                        ) else (
                            file_commits[0][selected_idx[0]] if file_commits[0] else None
                        ),
                        None if (
                            file_commits[1] and file_commits[1][selected_idx[1]]['hash'] == '_LOCAL_'
                        ) else (
                            file_commits[1][selected_idx[1]] if file_commits[1] else None
                        )
                    )
                    break

            if mode == 'commits' and str(wchar) == ESC_CODE:
                mode = 'files'
                wchar = ''
                selected_idx = file_selected_idxs if file_selected_idxs else selected_idx

        return self.open_next_idxs is None

    def _function_help(self) -> None:
        self.curse_window.clear()
        coff = 20

        help_text = [
            f"{'F1':<{coff}}help",
            f"{'Shift+F1 / F13':<{coff}}info overview",
            '',
            f"{'^E':<{coff}}jump to line",
            f"{'^N':<{coff}}change the diff cutoff ratio",
            f"{'^F':<{coff}}find strings",
            f"{'(Shift-)F3':<{coff}}find next/(previous)",
            f"{'(Shift-)F2':<{coff}}jump to next/(previous) change",
            '',
            f"{'^R':<{coff}}reload file",
            f"{'Ctrl+F1':<{coff}}open file manager",
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
        self._get_next_char()

    def _function_overview(self) -> None:
        """
        shows an overview of the diffviewer.
        """
        if self.displaying_overview:
            self._action_quit()
            return
        self.curse_window.clear()

        text1_similarity = self.difflibparser_bak.count_equal + sum(
            (len(item.line1)-len(item.changes1))/len(item.line1)
            for item in self.diff_items if item.code == DifflibID.CHANGED and item.line1
        )
        text1_similarity /= max(
            1,
            self.difflibparser_bak.count_equal + self.difflibparser_bak.count_delete + self.difflibparser_bak.count_changed
        )
        text2_similarity = self.difflibparser_bak.count_equal + sum(
            (len(item.line2)-len(item.changes2))/len(item.line2)
            for item in self.diff_items if item.code == DifflibID.CHANGED and item.line2
        )
        text2_similarity /= max(
            1,
            self.difflibparser_bak.count_equal + self.difflibparser_bak.count_insert + self.difflibparser_bak.count_changed
        )

        data_list1 = [
            'Filename:',
            self.display_names[0],
            '',
            'Filepath:',
            'GIT: ' * (self.file_commit_hashes[0] is not None) + str(self.diff_files[0]),
            '',
            'Size:',
            (
                f"{get_file_size(self.diff_files[0])} Bytes - {_convert_size(get_file_size(self.diff_files[0]))}"
                if self.file_commit_hashes[0] is None else 'N/A'
            ),
            '',
            'Line count:',
            f"{self.difflibparser_bak.count_equal + self.difflibparser_bak.count_delete + self.difflibparser_bak.count_changed}",
            '',
            'Time modified:',
            (
                f"{datetime.fromtimestamp(get_file_mtime(self.diff_files[0]))}"
                if self.file_commit_hashes[0] is None else 'N/A'
            ),
            '',
            'Time created:',
            (
                f"{datetime.fromtimestamp(get_file_ctime(self.diff_files[0]))}"
                if self.file_commit_hashes[0] is None else 'N/A'
            ),
            '',
            'Similiarity (%):',
            f"{(text1_similarity * 100):.2f}",
        ]
        if self.file_commit_hashes[0] is not None:
            commit = self.file_commit_hashes[0]
            data_list1.insert(6, '')
            if isinstance(commit, dict):
                data_list1.insert(6, f"{commit['hash'][:7]} | {commit['date'][:19]} | {commit['author']} | {commit['message']}")
            else:
                data_list1.insert(6, commit[:7])
            data_list1.insert(6, 'Git commit:')
        data_list2 = [
            'Filename:',
            self.display_names[1],
            '',
            'Filepath:',
            'GIT: ' * (self.file_commit_hashes[1] is not None) + str(self.diff_files[1]),
            '',
            'Size:',
            (
                f"{get_file_size(self.diff_files[1])} Bytes - {_convert_size(get_file_size(self.diff_files[1]))}"
                if self.file_commit_hashes[1] is None else 'N/A'
            ),
            '',
            'Line count:',
            f"{self.difflibparser_bak.count_equal + self.difflibparser_bak.count_insert + self.difflibparser_bak.count_changed}",
            '',
            'Time modified:',
            (
                f"{datetime.fromtimestamp(get_file_mtime(self.diff_files[1]))}"
                if self.file_commit_hashes[1] is None else 'N/A'
            ),
            '',
            'Time created:',
            (
                f"{datetime.fromtimestamp(get_file_ctime(self.diff_files[1]))}"
                if self.file_commit_hashes[1] is None else 'N/A'
            ),
            '',
            'Similiarity (%):',
            f"{(text2_similarity * 100):.2f}",
        ]
        if self.file_commit_hashes[1] is not None:
            commit = self.file_commit_hashes[1]
            data_list2.insert(6, '')
            if isinstance(commit, dict):
                data_list2.insert(6, f"{commit['hash'][:7]} | {commit['date'][:19]} | {commit['author']} | {commit['message']}")
            else:
                data_list2.insert(6, commit[:7])
            data_list2.insert(6, 'Git commit:')

        self.difflibparser = DifflibParser( data_list1, data_list2, -0.01, 0.0)
        self.diff_items = self.difflibparser.get_diff()
        self.l_offset = len(self.diff_items[0].lineno)+1 if self.diff_items else 0
        self.wpos = Position(0, 0)
        self.rpos = Position(0, 0)


        self.displaying_overview = True

    def _function_search(self) -> None:
        if not self.search:
            return
        self._action_find(1)

    def _function_search_r(self) -> None:
        if not self.search:
            return
        self._action_find(-1)

    def _function_replace(self) -> None:
        """
        *naming convention only for hotkeys*
        jumps the view-window to the next change
        """
        max_y, _ = self.getxymax()
        skip_final_page = False
        if self.wpos.row == max(0, len(self.diff_items) - max_y):
            skip_final_page = True

        for i in range(1, len(self.diff_items)):
            row = (self.rpos.row + i) % len(self.diff_items)
            if skip_final_page and row > self.rpos.row:
                continue
            if self.diff_items[row].code != DifflibID.EQUAL:
                self.rpos.row = row
                self._ensure_rpos_visible()
                break

    def _function_replace_r(self) -> None:
        """
        *naming convention only for hotkeys*
        jumps the view-window to the previous change
        """
        for i in range(1, len(self.diff_items)):
            row = self.rpos.row - i
            if row < 0:
                row += len(self.diff_items)
            if self.diff_items[row].code != DifflibID.EQUAL:
                self.rpos.row = row
                self._ensure_rpos_visible()
                break

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

    def _get_diff_ratio(self, row: int) -> float:
        item = self.diff_items[row]

        if item.code in (DifflibID.INSERT, DifflibID.DELETE):
            return 0.0
        if item.code == DifflibID.CHANGED:
            ratio1 = len(item.changes1) / len(item.line1) * 100 if item.line1 else 0
            ratio2 = len(item.changes2) / len(item.line2) * 100 if item.line2 else 0
            return 100.0 - (ratio1 + ratio2) / 2
        return 100.0

    def _render_status_bar(self, max_y: int, max_x: int) -> None:
        # display status/error_bar
        try:
            if self.error_bar:
                self.curse_window.addstr(max_y + self.status_bar_size - 2, 0,
                                         self.error_bar[:max_x].ljust(max_x), self._get_color(2))

            status_bar = f"Equal: {self.difflibparser.count_equal} | "
            status_bar+= f"Insertions: {self.difflibparser.count_insert} | "
            status_bar+= f"Deletions: {self.difflibparser.count_delete} | "
            status_bar+= f"Modifications: {self.difflibparser.count_changed} | "
            similarity = self._get_diff_ratio(self.rpos.row)
            status_bar+= f"Similarity: {similarity:6.2f}% | "
            status_bar+= 'Help: F1'
            if self.debug_mode:
                status_bar += f" - Win: {self.wpos.col+1} {self.wpos.row+1} | {max_y}x{max_x}"
            # this throws an error (should be max_x-1), but looks better:
            status_bar = status_bar[:max_x].ljust(max_x)
            self.curse_window.addstr(max_y + self.status_bar_size - 1, 0,
                                     status_bar, self._get_color(1))
        except curses.error:
            pass

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

            sep_color    = self._get_color(8)
            equal_color  = self._get_color(7)
            empty_color  = self._get_color(9)
            delete_color = self._get_color(6)
            insert_color = self._get_color(4)
            if brow == self.rpos.row:
                self.curse_window.chgat(row, 0, max_x, self._get_color(1))
                sep_color    = self._get_color(1)
                equal_color  = self._get_color(1)
                empty_color  = self._get_color(1)
                delete_color = self._get_color(1)
                insert_color = self._get_color(1)

            self.curse_window.addstr(
                row, 0,
                f"{self.diff_items[brow].lineno} ",
                sep_color
            )
            if self.diff_items[brow].code == DifflibID.EQUAL:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    equal_color
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    sep_color
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    equal_color
                )
            elif self.diff_items[brow].code == DifflibID.DELETE:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    ' ' * self.half_width,
                    empty_color
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    sep_color
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    ' ' * self.half_width,
                    delete_color
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width],
                    self._get_color(5) | curses.A_UNDERLINE
                )
            elif self.diff_items[brow].code == DifflibID.INSERT:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    ' ' * self.half_width,
                    insert_color
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width],
                    self._get_color(3) | curses.A_UNDERLINE
                )
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width,
                    ' | ',
                    sep_color
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    ' ' * self.half_width,
                    empty_color
                )
            elif self.diff_items[brow].code == DifflibID.CHANGED:
                self.curse_window.addstr(
                    row, self.l_offset + self.half_width + 3,
                    self.diff_items[brow].line2[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    insert_color
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
                    sep_color
                )
                self.curse_window.addstr(
                    row, self.l_offset,
                    self.diff_items[brow].line1[self.wpos.col:self.wpos.col+self.half_width].ljust(self.half_width),
                    delete_color
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

        for (row, col, s_idx), s_len in self.search_items.items():
            if row < self.wpos.row or row >= self.wpos.row + max_y:
                continue
            if col + s_len < self.wpos.col or col >= self.wpos.col + self.half_width:
                continue
            if col < self.wpos.col:
                s_len -= self.wpos.col - col
                col = self.wpos.col
            self.curse_window.chgat(
                row - self.wpos.row,
                self.l_offset + (self.half_width + 3 if s_idx else 0) +
                col - self.wpos.col,
                s_len,
                self._get_color(11)
            )
        if (*self.cpos.get_pos(), False) in self.search_items:
            self.curse_window.chgat(
                self.cpos.row-self.wpos.row,
                self.l_offset + self.cpos.col-self.wpos.col,
                self.search_items[(*self.cpos.get_pos(), False)],
                self._get_color(12)
            )
        if (*self.cpos.get_pos(), True) in self.search_items:
            self.curse_window.chgat(
                self.cpos.row-self.wpos.row,
                self.l_offset + self.half_width + 3 +
                self.cpos.col-self.wpos.col,
                self.search_items[(*self.cpos.get_pos(), True)],
                self._get_color(12)
            )
        self.search_items.clear()

        self._render_status_bar(max_y, max_x)
        self.curse_window.refresh()

    def _run(self) -> None:
        """
        main loop for the diffviewer.
        """
        self.half_width = (self.getxymax()[1]-3-self.l_offset) // 2
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

        curses.mousemask(-1)
        curses.mouseinterval(0)

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
                if os.isatty(sys.stdout.fileno()):
                    curses.use_default_colors()
                # status_bar
                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
                # error_bar
                curses.init_pair(2, curses.COLOR_RED  , curses.COLOR_WHITE)
                # green background
                curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
                # light green background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN+8)
                    except curses.error:
                        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
                else:
                    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
                # red background
                curses.init_pair(5, curses.COLOR_BLACK  , curses.COLOR_RED)
                # light red background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED+8)
                    except curses.error:
                        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)
                else:
                    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)
                # default color
                curses.init_pair(7, curses.COLOR_WHITE  , -1)
                # lineno color & file-selector, active file selected
                curses.init_pair(8, curses.COLOR_MAGENTA, -1)
                # gray background
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK+8)
                    except curses.error:
                        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)
                else:
                    curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)
                # prompts
                curses.init_pair(10, curses.COLOR_WHITE  , curses.COLOR_RED  )
                # find
                curses.init_pair(11, curses.COLOR_WHITE  , curses.COLOR_BLUE )
                # current match
                curses.init_pair(12, curses.COLOR_WHITE  , curses.COLOR_CYAN )
                # file-selector, active file
                curses.init_pair(13, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
                # file-selector, active file (selected) inactive page
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(14, curses.COLOR_MAGENTA, curses.COLOR_BLACK+8)
                    except curses.error:
                        curses.init_pair(14, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                else:
                    curses.init_pair(14, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                # file-selector, selected inactive page
                if curses.COLORS >= 16:
                    try:
                        curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_BLACK+8)
                    except curses.error:
                        curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_BLACK)
                else:
                    curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_BLACK)

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
                err_print('Oops..! Something went wrong.', priority=err_print.IMPORTANT)
            raise e
        finally:
            curses.endwin()

    @classmethod
    def open(cls, files: list) -> None:
        """
        simple diffviewer to view the contents/differences of two provided files.

        Parameters:
        files (list):
            list of tuples (file, display_name)
        """
        if DiffViewer.loading_failed:
            return

        if CURSES_MODULE_ERROR:
            err_print("The Diffviewer could not be loaded. No Module 'curses' was found.", priority=err_print.INFORMATION)
            if on_windows_os:
                err_print('If you are on Windows OS, try pip-installing ', end='', priority=err_print.INFORMATION)
                err_print("'windows-curses'.", priority=err_print.INFORMATION)
            err_print(priority=err_print.INFORMATION)
            DiffViewer.loading_failed = True
            return

        diffviewer = cls(files)

        if on_windows_os:
            # disable background feature on windows
            diffviewer._action_background = lambda *_: True
        else:
            # ignore background signals on UNIX, since a custom background implementation exists
            signal.signal(signal.SIGTSTP, signal.SIG_IGN)

        diffviewer._open()
        while diffviewer.open_next_idxs is not None:
            diffviewer = cls(files, file_idxs = diffviewer.open_next_idxs, file_commit_hashes = diffviewer.open_next_hashes)
            if on_windows_os:
                # disable background feature on windows
                diffviewer._action_background = lambda *_: True
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
