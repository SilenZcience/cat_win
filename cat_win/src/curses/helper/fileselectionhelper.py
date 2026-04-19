"""
fileselectionhelper
"""

import os
import sys
from pathlib import Path

try:
    import curses
    CURSES_MODULE_ERROR = False
except ImportError:
    CURSES_MODULE_ERROR = True

from cat_win.src.const.escapecodes import ESC_CODE
from cat_win.src.curses.helper.editorhelper import ACTION_HOTKEYS, MOVE_HOTKEYS
from cat_win.src.curses.helper.githelper import GitHelper


def _format_commit(commit: dict) -> str:
    return f"{commit['hash'][:7]} | {commit['date'][:10]} | {commit['author']} | {commit['message']}"


def _current_hash(hash_value) -> str:
    if isinstance(hash_value, dict):
        return hash_value.get('hash')
    return hash_value


def _commit_selection_index(commits: list, current_hash) -> int:
    if current_hash is None:
        return 0
    try:
        if isinstance(current_hash, dict):
            return commits.index(current_hash)
        return [item['hash'] for item in commits].index(current_hash)
    except ValueError:
        return 0


def run_file_selection(
    owner,
    split_panel: bool = False,
    status_bar_offset: int = None,
    color_map: dict = None
) -> bool:
    """
    handles the shared file selection action.

    Parameters:
    owner (HexEditor | Editor | Diffviewer):
        the curses application instance that owns the selection state
    split_panel (bool):
        use the diffviewer style two-panel selector instead of the single panel list
    status_bar_offset (int):
        override the vertical offset used to compute the selector height
    color_map (dict):
        override the color ids used for selection states

    Returns:
    (bool):
        indicates if a new file/commit selection was chosen
    """
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    owner.curse_window.clear()
    owner_module = sys.modules.get(owner.__class__.__module__)
    owner_curses = getattr(owner_module, 'curses', curses) if owner_module else curses
    curses_error = getattr(owner_curses, 'error', curses.error)

    def _find_current_idx(target_file: Path, target_display: str) -> int:
        try:
            return owner.files.index((target_file, target_display))
        except ValueError:
            for idx, (file_path, _) in enumerate(owner.files):
                if file_path == target_file:
                    return idx
        return 0

    def _path_parts(path_value) -> tuple:
        parts = Path(str(path_value)).parts
        return tuple(parts) if parts else (str(path_value),)

    def _entry_sort_key(name: str) -> tuple:
        # Keep stable, case-insensitive ordering that works for mixed path styles.
        return (name.casefold(), name)

    owner_file_parts = [_path_parts(file_path) for file_path, _ in owner.files]

    use_path_parts = len(owner.files) >= 15

    def _build_flat_entries() -> list:
        entries = []
        for owner_idx, (file_path, display_name) in enumerate(owner.files):
            file_path = Path(str(file_path))
            file_name = file_path.name
            label = display_name if display_name else file_name
            if display_name and os.path.exists(display_name):
                label = f"{file_name} | {file_path.parent}{os.sep}"
            entries.append({
                'kind': 'file',
                'owner_idx': owner_idx,
                'name': file_name,
                'label': label,
                'parts': owner_file_parts[owner_idx],
            })
        return entries

    def _build_file_entries(current_dir_parts: tuple) -> list:
        dirs = set()
        files = []

        for owner_idx, parts in enumerate(owner_file_parts):
            if len(parts) <= len(current_dir_parts):
                continue
            if parts[:len(current_dir_parts)] != current_dir_parts:
                continue

            next_part = parts[len(current_dir_parts)]
            if len(parts) == len(current_dir_parts) + 1:
                display_name = owner.files[owner_idx][1]
                label = display_name if display_name else next_part
                if display_name and os.path.exists(display_name):
                    label = f"{next_part} | {Path(display_name).parent}{os.sep}"

                files.append((next_part, {
                    'kind': 'file',
                    'owner_idx': owner_idx,
                    'name': next_part,
                    'label': label,
                }))
            else:
                dirs.add(next_part)

        entries = []
        if current_dir_parts:
            entries.append({
                'kind': 'up',
                'owner_idx': None,
                'name': '..',
                'label': '..',
                'parts': current_dir_parts[:-1],
            })

        for dir_name in sorted(dirs, key=_entry_sort_key):
            entries.append({
                'kind': 'dir',
                'owner_idx': None,
                'name': dir_name,
                'label': f"{dir_name}{os.sep}",
                'parts': current_dir_parts + (dir_name,),
            })

        files.sort(key=lambda item: _entry_sort_key(item[0]))
        for _, entry in files:
            entry['parts'] = owner_file_parts[entry['owner_idx']]
            entries.append(entry)
        return entries

    selection_changed = False

    def _get_next_char() -> tuple:
        if hasattr(owner, '_get_next_char'):
            return owner._get_next_char()
        return next(owner.get_char)
    panel_count = 1 + split_panel
    if status_bar_offset is None:
        status_bar_offset = -2 if split_panel else 1
    if color_map is None:
        color_map = {
            'selected_current_active': 13,
            'selected_current_inactive': 14,
            'selected_active': 1,
            'selected_inactive': 15,
            'current': 8,
        } if split_panel else {
            'selected_current': 8,
            'selected': 1,
            'current': 9,
        }

    def _current_file(side: int) -> Path:
        return owner.diff_files[side] if split_panel else owner.file

    def _current_display(side: int) -> str:
        return owner.display_names[side] if split_panel else owner.display_name

    def _current_commit_hash(side: int):
        return owner.file_commit_hashes[side] if split_panel else owner.file_commit_hash

    file_dirs = []
    if use_path_parts:
        for side in range(panel_count):
            file_parts = _path_parts(_current_file(side))
            # Start in the current file's directory, similar to a file explorer.
            file_dirs.append(file_parts[:-1])

        for side in range(panel_count):
            if not _build_file_entries(file_dirs[side]):
                file_dirs[side] = ()
        file_view_entries = [_build_file_entries(file_dirs[side]) for side in range(panel_count)]
    else:
        file_dirs = [() for _ in range(panel_count)]
        file_view_entries = [_build_flat_entries() for _ in range(panel_count)]

    def _find_entry_idx_by_owner_idx(entries: list, owner_idx: int) -> int:
        for idx, entry in enumerate(entries):
            if entry['kind'] == 'file' and entry['owner_idx'] == owner_idx:
                return idx
        return 0

    selected_idx = []
    for side in range(panel_count):
        current_owner_idx = _find_current_idx(_current_file(side), _current_display(side))
        selected_idx.append(_find_entry_idx_by_owner_idx(file_view_entries[side], current_owner_idx))
    max_y, max_x = owner.getxymax()
    max_y += owner.status_bar_size + status_bar_offset
    nav_x = [0 for _ in range(panel_count)]
    nav_y = [
        max(0, min(selected_idx[side] - max_y // 2, len(file_view_entries[side]) - max_y))
        for side in range(panel_count)
    ]
    active_list = 0
    mode = 'files'
    file_commits = [None for _ in range(panel_count)]
    file_selected_idxs: list = None

    def _selection_changed(selected: list, current: list) -> bool:
        if split_panel:
            return tuple(selected) != tuple(current)
        return selected[0] != current[0]

    def _clamp_file_selection(side: int) -> None:
        list_len = len(file_view_entries[side])
        if list_len == 0:
            selected_idx[side] = 0
            nav_y[side] = 0
            nav_x[side] = 0
            return
        selected_idx[side] = min(max(selected_idx[side], 0), list_len - 1)
        if selected_idx[side] < nav_y[side]:
            nav_y[side] = selected_idx[side]
        elif selected_idx[side] >= nav_y[side] + max_y - 1:
            nav_y[side] = selected_idx[side] - max_y + 1
        nav_y[side] = max(0, nav_y[side])

    def _refresh_file_entries(side: int, selected_owner_idx: int = None) -> None:
        file_view_entries[side] = _build_file_entries(file_dirs[side])
        if selected_owner_idx is not None:
            selected_idx[side] = _find_entry_idx_by_owner_idx(file_view_entries[side], selected_owner_idx)
        _clamp_file_selection(side)

    def _hash_selection_changed(current_hashes: list) -> bool:
        if split_panel:
            return tuple(owner.file_commit_hashes) != tuple(current_hashes)
        return owner.file_commit_hash != current_hashes[0]

    def _set_pending_selection(selected: list, hashes: list = None) -> None:
        if split_panel:
            owner.open_next_idxs = selected
            if hashes is not None:
                owner.open_next_hashes = tuple(hashes)
        else:
            owner.open_next_idx = selected[0]
            if hashes is not None:
                owner.open_next_hash = hashes[0]

    def _resolve_color(side: int, is_selected: bool, is_current: bool) -> int:
        if split_panel:
            if is_selected and is_current:
                return owner._get_color(
                    color_map['selected_current_active'] if side == active_list else color_map['selected_current_inactive']
                )
            if is_selected:
                return owner._get_color(
                    color_map['selected_active'] if side == active_list else color_map['selected_inactive']
                )
            if is_current:
                return owner._get_color(color_map['current'])
            return 0
        if is_selected and is_current:
            return owner._get_color(color_map['selected_current'])
        if is_selected:
            return owner._get_color(color_map['selected'])
        if is_current:
            return owner._get_color(color_map['current'])
        return 0

    def _hint_parts_for_target(current_dir_parts: tuple, target_parts: tuple):
        if not target_parts:
            return None
        if target_parts[:len(current_dir_parts)] == current_dir_parts:
            if len(target_parts) > len(current_dir_parts):
                return current_dir_parts + (target_parts[len(current_dir_parts)],)
            return None
        if current_dir_parts:
            return current_dir_parts[:-1]
        return None

    wchar, key = '', b''
    while str(wchar) != ESC_CODE:
        if split_panel:
            list_width = max(1, (max_x - 3) // 2)
            panel_starts = [0, list_width + 3]
            panel_widths = [list_width, list_width]
        else:
            panel_starts = [0]
            panel_widths = [max_x]

        if mode == 'files':
            data_lists = [file_view_entries[side] for side in range(panel_count)]
        else:
            data_lists = [file_commits[side] or [] for side in range(panel_count)]

        selected_hint_parts = [None for _ in range(panel_count)]
        current_hint_parts = [None for _ in range(panel_count)]
        if mode == 'files' and use_path_parts:
            for side in range(panel_count):
                current_target_parts = _path_parts(_current_file(side))
                selected_target_parts = None

                if data_lists[side] and selected_idx[side] < len(data_lists[side]):
                    selected_entry = data_lists[side][selected_idx[side]]
                    if selected_entry['kind'] == 'file':
                        selected_target_parts = owner_file_parts[selected_entry['owner_idx']]

                selected_hint_parts[side] = _hint_parts_for_target(file_dirs[side], selected_target_parts)
                current_hint_parts[side] = _hint_parts_for_target(file_dirs[side], current_target_parts)

        maxlen_displayname = []
        for side in range(panel_count):
            visible = data_lists[side][nav_y[side]:nav_y[side]+max_y]
            if mode == 'files':
                maxlen_displayname.append(max((len(entry['label']) for entry in visible), default=0))
            else:
                maxlen_displayname.append(max((len(_format_commit(commit)) for commit in visible), default=0))

        owner.curse_window.move(max_y, 0)
        owner.curse_window.clrtoeol()
        for row in range(max_y):
            for side in range(panel_count):
                entry_idx = row + nav_y[side]
                if entry_idx >= len(data_lists[side]):
                    try:
                        owner.curse_window.addstr(
                            row,
                            panel_starts[side],
                            ' ' * panel_widths[side],
                            0
                        )
                    except curses_error:
                        pass
                    continue

                if mode == 'files':
                    entry = data_lists[side][entry_idx]
                    display_name = entry['label']
                    is_selected = selected_idx[side] == entry_idx
                    is_current = (
                        entry['kind'] == 'file' and
                        owner.files[entry['owner_idx']][0] == _current_file(side) and
                        owner.files[entry['owner_idx']][1] == _current_display(side)
                    )

                    if use_path_parts and entry['kind'] in ('up', 'dir'):
                        entry_parts = entry.get('parts')
                        if selected_hint_parts[side] is not None and entry_parts == selected_hint_parts[side]:
                            is_selected = True
                        if current_hint_parts[side] is not None and entry_parts == current_hint_parts[side]:
                            is_current = True
                else:
                    commit = data_lists[side][entry_idx]
                    display_name = _format_commit(commit)
                    is_selected = selected_idx[side] == entry_idx
                    current_hash = _current_hash(_current_commit_hash(side))
                    source_idx = file_selected_idxs[side] if file_selected_idxs else selected_idx[side]
                    is_current = (
                        owner.files[source_idx][0] == _current_file(side) and (
                            (commit['hash'] == '_LOCAL_' and current_hash is None) or
                            (commit['hash'] == current_hash)
                        )
                    )

                color = _resolve_color(side, is_selected, is_current)
                start_x = panel_starts[side]
                width = panel_widths[side]
                offset_x = nav_x[side]
                text = f"{display_name}"[offset_x:offset_x+width].ljust(width)
                try:
                    owner.curse_window.addstr(row, start_x, text, color)
                    if not split_panel:
                        owner.curse_window.clrtoeol()
                except curses_error:
                    break

            if row == max_y - 1:
                for side in range(panel_count):
                    if len(data_lists[side]) > max_y + nav_y[side]:
                        owner.curse_window.addstr(row + 1, panel_starts[side], '...')
                owner.curse_window.clrtoeol()
                break

        owner.curse_window.clrtobot()

        if mode == 'files':
            status_msg = (
                'Select two files. Tab/Shift+Tab switch list. Confirm with <Enter> or <Space>.'
                if split_panel else
                'Select file to open. Confirm with <Enter> or <Space>.'
            )
        else:
            status_msg = (
                'Select commits (or go back with <Escape>). Tab/Shift+Tab switch list. Confirm with <Enter> or <Space>.'
                if split_panel else
                'Select commit (or go back with <Escape>). Confirm with <Enter> or <Space>.'
            )

        try:
            owner.curse_window.addstr(
                max_y+1, 0,
                status_msg[:max_x].ljust(max_x),
                owner._get_color(1)
            )
        except curses_error:
            pass

        owner.curse_window.refresh()

        wchar, key = _get_next_char()
        if key in ACTION_HOTKEYS:
            if key in [b'_action_quit', b'_action_interrupt']:
                break
            if key == b'_action_file_selection':
                wchar, key = ' ', b'_key_string'
            if key == b'_action_background':
                getattr(owner, key.decode(), lambda *_: False)()
            if key == b'_action_resize':
                getattr(owner, key.decode(), lambda *_: False)()
                max_y, max_x = owner.getxymax()
                max_y += owner.status_bar_size + status_bar_offset

        if split_panel and key in [b'_indent_tab', b'_indent_btab']:
            active_list = 1 - active_list

        if split_panel and key in [b'_select_key_left', b'_select_key_right']:
            active_list = 1 - active_list
            selected_idx[active_list] = min(
                selected_idx[1 - active_list],
                len(data_lists[active_list]) - 1
            )
            nav_y[active_list] = min(nav_y[active_list], selected_idx[active_list])
            if selected_idx[active_list] >= nav_y[active_list] + max_y - 1:
                nav_y[active_list] = selected_idx[active_list] - max_y + 1

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
                nav_x[active_list] = max(
                    0,
                    min(maxlen_displayname[active_list] - panel_widths[active_list], nav_x[active_list] + 1)
                )
            elif key == b'_move_key_ctl_right':
                nav_x[active_list] = max(
                    0,
                    min(maxlen_displayname[active_list] - panel_widths[active_list], nav_x[active_list] + 10)
                )
            elif key == b'_move_key_mouse':
                _, x, y, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_PRESSED or bstate & curses.BUTTON1_CLICKED or bstate & curses.BUTTON1_DOUBLE_CLICKED:
                    for side in range(panel_count):
                        if (
                            panel_starts[side] <= x < panel_starts[side] + panel_widths[side]
                         ) and (
                             y <= max_y
                         ):
                            active_list = side
                            selected_idx[side] = min(nav_y[side] + y, len(data_lists[side]) - 1)
                            if selected_idx[side] >= nav_y[side] + max_y - 1:
                                nav_y[side] = selected_idx[side] - max_y + 1
                            if bstate & curses.BUTTON1_DOUBLE_CLICKED:
                                key = b'_key_enter'
                            break
                elif bstate & curses.BUTTON4_PRESSED:
                    selected_idx[active_list] = max(0, selected_idx[active_list] - 1)
                    nav_y[active_list] = min(nav_y[active_list], selected_idx[active_list])
                elif bstate & curses.BUTTON5_PRESSED:
                    selected_idx[active_list] = min(list_len - 1, selected_idx[active_list] + 1)
                    if selected_idx[active_list] >= nav_y[active_list] + max_y - 1:
                        nav_y[active_list] = selected_idx[active_list] - max_y + 1

        if key == b'_key_enter' or (key == b'_key_string' and wchar == ' '):
            if mode == 'files':
                active_entries = data_lists[active_list]
                active_entry = None
                if active_entries:
                    active_entry = active_entries[selected_idx[active_list]]

                if use_path_parts and active_entry and active_entry['kind'] in ('dir', 'up'):
                    if active_entry['kind'] == 'up':
                        file_dirs[active_list] = file_dirs[active_list][:-1]
                    else:
                        file_dirs[active_list] = file_dirs[active_list] + (active_entry['name'],)
                    nav_x[active_list] = 0
                    nav_y[active_list] = 0
                    selected_idx[active_list] = 0
                    _refresh_file_entries(active_list)
                    continue

                if split_panel and use_path_parts:
                    if not all(
                        data_lists[side] and data_lists[side][selected_idx[side]]['kind'] == 'file'
                        for side in range(panel_count)
                    ):
                        for side in range(panel_count):
                            if not data_lists[side] or data_lists[side][selected_idx[side]]['kind'] != 'file':
                                active_list = side
                                break
                        continue

                file_selected_idxs = [
                    data_lists[side][selected_idx[side]]['owner_idx']
                    for side in range(panel_count)
                ]

                for side in range(panel_count):
                    file_path = owner.files[file_selected_idxs[side]][0]
                    try:
                        file_commits[side] = GitHelper.get_git_file_history(file_path)
                    except OSError:
                        file_commits[side] = None

                if any(file_commits):
                    for side in range(panel_count):
                        if file_commits[side]:
                            file_commits[side] = [
                                {
                                    'hash': '_LOCAL_', 'date': ' _Latest_ ',
                                    'author': '_Local_', 'message': 'Use local file (not git)'
                                }
                            ] + file_commits[side]
                    mode = 'commits'
                    selected_idx = [0 for _ in range(panel_count)]
                    for side in range(panel_count):
                        current_hash = _current_commit_hash(side)
                        if current_hash is not None and file_commits[side] is not None:
                            selected_idx[side] = _commit_selection_index(file_commits[side], current_hash)
                    nav_x = [0 for _ in range(panel_count)]
                    nav_y = [0 for _ in range(panel_count)]
                    active_list = 0 if file_commits[0] else 1
                    owner.curse_window.clear()
                else:
                    current_idxs = [
                        _find_current_idx(_current_file(side), _current_display(side))
                        for side in range(panel_count)
                    ]
                    if _selection_changed(file_selected_idxs, current_idxs):
                        _set_pending_selection(file_selected_idxs)
                        selection_changed = True
                    break
            else:
                current_idxs = [
                    _find_current_idx(_current_file(side), _current_display(side))
                    for side in range(panel_count)
                ]

                current_hashes = []
                for side in range(panel_count):
                    current_hashes.append(
                        None if (
                            file_commits[side] and file_commits[side][selected_idx[side]]['hash'] == '_LOCAL_'
                        ) else (
                            file_commits[side][selected_idx[side]] if file_commits[side] else None
                        )
                    )

                if _selection_changed(file_selected_idxs, current_idxs) or _hash_selection_changed(current_hashes):
                    _set_pending_selection(file_selected_idxs, current_hashes)
                    selection_changed = True
                break

        if mode == 'commits' and str(wchar) == ESC_CODE:
            mode = 'files'
            wchar = ''
            if use_path_parts and file_selected_idxs:
                for side in range(panel_count):
                    _refresh_file_entries(side, selected_owner_idx=file_selected_idxs[side])
            nav_x = [0 for _ in range(panel_count)]
            nav_y = [
                max(0, min(selected_idx[side] - max_y // 2, len(file_view_entries[side]) - max_y))
                for side in range(panel_count)
            ]

    owner.curse_window.clear()
    return selection_changed
