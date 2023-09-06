UNIFY_HOTKEYS = {
    # newline
    b'^M'           : b'_key_enter', # CR
    b'^J'           : b'_key_enter', # LF
    b'PADENTER'     : b'_key_enter', # numpad
    b'KEY_ENTER'    : b'_key_enter', # 'fn' mode
    # ctrl - newline
    b'CTL_ENTER'    : b'_key_enter', # windows
    b'CTL_PADENTER' : b'_key_enter', # numpad
    # delete
    b'KEY_DC'       : b'_key_dc', # windows & xterm
    b'^D'           : b'_key_dc', # some unix machines
    b'PADSTOP'      : b'_key_dc', # numpad
    # ctrl - del
    b'CTL_DEL'      : b'_key_dl', # windows
    b'kDC5'         : b'_key_dl', # xterm
    b'CTL_PADSTOP'  : b'_key_dl', # numpad
    # backspace
    b'^H'           : b'_key_backspace', # windows (ctrl-backspace on xterm...)
    b'KEY_BACKSPACE': b'_key_backspace', # xterm
    # ctrl-backspace
    b'^?'           : b'_key_ctl_backspace', # windows
    # arrows
    b'KEY_LEFT'     : b'_key_left', # windows & xterm
    b'KEY_RIGHT'    : b'_key_right',
    b'KEY_UP'       : b'_key_up',
    b'KEY_DOWN'     : b'_key_down',
    b'KEY_B1'       : b'_key_left', # numpad
    b'KEY_B3'       : b'_key_right',
    b'KEY_A2'       : b'_key_up',
    b'KEY_C2'       : b'_key_down',
    # ctrl-arrows
    b'CTL_LEFT'     : b'_key_ctl_left', # windows
    b'CTL_RIGHT'    : b'_key_ctl_right',
    b'CTL_UP'       : b'_key_ctl_up',
    b'CTL_DOWN'     : b'_key_ctl_down',
    b'kLFT5'        : b'_key_ctl_left', # xterm
    b'kRIT5'        : b'_key_ctl_right',
    b'kUP5'         : b'_key_ctl_up',
    b'kDN5'         : b'_key_ctl_down',
    b'CTL_PAD4'     : b'_key_ctl_left', # numpad
    b'CTL_PAD6'     : b'_key_ctl_right',
    b'CTL_PAD8'     : b'_key_ctl_up',
    b'CTL_PAD2'     : b'_key_ctl_down',
    # page
    b'KEY_PPAGE'    : b'_key_page_up', # windows & xterm
    b'KEY_NPAGE'    : b'_key_page_down',
    b'KEY_A3'       : b'_key_page_up', # numpad
    b'KEY_C3'       : b'_key_page_down',
    # ctrl - page
    b'CTL_PGUP'     : b'_key_page_up', # windows
    b'CTL_PGDN'     : b'_key_page_down',
    b'kPRV5'        : b'_key_page_up', # xterm
    b'kNXT5'        : b'_key_page_down',
    b'CTL_PAD9'     : b'_key_page_up', # numpad
    b'CTL_PAD3'     : b'_key_page_down',
    # end
    b'KEY_END'      : b'_key_end', # windows & xterm
    b'KEY_C1'       : b'_key_end', # numpad
    # ctrl - end
    b'CTL_END'      : b'_key_ctl_end', # windows
    b'kEND5'        : b'_key_ctl_end', # xterm
    b'CTL_PAD1'     : b'_key_ctl_end', # numpad
    # pos/home
    b'KEY_HOME'     : b'_key_home', # windows & xterm
    b'KEY_A1'       : b'_key_home', # numpad
    # ctrl - pos/home
    b'CTL_HOME'     : b'_key_ctl_home', # windows
    b'kHOM5'        : b'_key_ctl_home', # xterm
    b'CTL_PAD7'     : b'_key_ctl_home', # numpad
    # actions
    b'^S'           : b'_action_save',
    b'^Q'           : b'_action_quit',
    b'^C'           : b'_action_interrupt',
    b'KEY_RESIZE'   : b'_action_resize',
}

KEY_HOTKEYS    = set(v for v in UNIFY_HOTKEYS.values() if v.startswith(b'_key'   ))
ACTION_HOTKEYS = set(v for v in UNIFY_HOTKEYS.values() if v.startswith(b'_action'))
