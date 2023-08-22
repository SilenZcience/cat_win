
SPECIAL_CHARS = {
     0: ( 0, 'NUL', '␀', True), # ^@ \0 null
    #  1: ( 1, 'SOH', '␁', False), # ^A start of heading
    #  2: ( 2, 'STX', '␂', False), # ^B start of text
    #  3: ( 3, 'ETX', '␃', False), # ^C end of text
     4: ( 4, 'EOT', '␄', True), # ^D end of transmission
    #  5: ( 5, 'ENQ', '␅', False), # ^E enquiry
    #  6: ( 6, 'ACK', '␆', False), # ^F acknowledge
     7: ( 7, 'BEL', '␇', True), # ^G \a bell
     8: ( 8, 'BS' , '␈', True), # ^H \b backspace
     9: ( 9, 'TAB', '␉', True), # ^I \t horizontal tab
    10: (10, 'LF' , '␤', False), # ^J \n line feed, new line
    11: (11, 'VT' , '␋', False), # ^K \v vertical tab
    12: (12, 'FF' , '␌', False), # ^L \f form feed, new page
    13: (13, 'CR' , '␍', False), # ^M \r carriage return
    # 14: (14, 'SO' , '␎', False), # ^N shift out
    # 15: (15, 'SI' , '␏', False), # ^O shift in
    # 16: (16, 'DLE', '␐', False), # ^P data link escape
    # 17: (17, 'DC1', '␑', False), # ^Q device control 1
    # 18: (18, 'DC2', '␒', False), # ^R device control 2
    # 19: (19, 'DC3', '␓', False), # ^S device control 3
    # 20: (20, 'DC4', '␔', False), # ^T device control 4
    # 21: (21, 'NAK', '␕', False), # ^U negative acknowledge
    # 22: (22, 'SYN', '␖', False), # ^V synchronous idle
    # 23: (23, 'ETC', '␗', False), # ^W end of trans. block
    # 24: (24, 'CAN', '␘', False), # ^X cancel
    # 25: (25, 'EM' , '␙', False), # ^Y end of mediunm
    26: (26, 'SUB', '␚', True), # ^Z substitute
    27: (27, 'Esc', '␛', False), # ^[ escape # needed for colors
    # 28: (28, 'FS' , '␜', False), # ^\ file seperator
    # 29: (29, 'GS' , '␝', False), # ^] group seperator
    # 30: (30, 'RS' , '␞', False), # ^^ record seperator
    # 31: (31, 'US' , '␟', False), # ^_ unit seperator
}


def get_raw_view_lines_gen(file: str = '', mode: str = 'X', colors = None,
                           file_encoding: str = 'utf-8'):
    """
    return the raw byte representation of a file in hexadecimal or binary
    line by line
    
    Parameters:
    file (str):
        the file to use
    mode (str):
        either 'x', 'X' for hexadecimal (lower- or upper case letters),
        or 'b' for binary
    colors (list):
        a list of two elements. Index 0 holds the color CKW.RAWVIEWER,
        Index 1 holds the color CKW.RESET_ALL
    file_encoding (str):
        the encoding used (possibly for stdout)
        
    Yields:
    current_line (str):
        a string representation that, when put together, forms the hexviewer
        output containing the header and line information aswell
        as the bytes themselves
    """
    if colors is None or len(colors) < 2:
        colors = ['', '']
    if mode not in ['x', 'X', 'b']:
        mode = 'X'

    CRLF = dict(map(lambda x: (x[0], x[2]), SPECIAL_CHARS.values()))
    CRLF[-1] = '·' # default fallback symbol
    try:
        if len(CRLF[0].encode(file_encoding)) != 3:
            raise UnicodeEncodeError('', '', -1, -1, '')
    except UnicodeEncodeError:
        CRLF = dict.fromkeys(CRLF, '.')

    def get_display_char(byte: int) -> str:
        # 32 - 126 => ' ' - '~' (ASCII)
        if 32 <= byte <= 126:
            return chr(byte)
        if byte in CRLF.keys():
            return CRLF[byte]
        return CRLF[-1]

    try:
        with open(file, 'rb') as raw_file:
            raw_file_content = raw_file.read()
            raw_file_content_length = len(raw_file_content)
    except OSError as exc:
        yield type(exc).__name__
        return ''

    repr_length = 2 * (mode.upper() == 'X') + 8 * (mode == 'b')

    current_line = f"{colors[0]}Address  "
    for i in range(16):
        current_line += f"{i:0{2}X} " + '      ' * (mode == 'b')
    current_line += f"# Decoded Text                   {colors[1]}"
    yield current_line

    current_line = f"{colors[0]}{0:0{8}X}{colors[1]} "
    line = []
    for i, byte in enumerate(raw_file_content, start=1):
        line.append(byte)
        if not i % 16:
            current_line +=  ' '.join([f"{b:0{repr_length}{mode}}" for b in line]) + \
                            f" {colors[0]}#{colors[1]} " + \
                            ' '.join(map(get_display_char, line))
            yield current_line
            if i < raw_file_content_length:
                current_line = f"{colors[0]}{i:0{8}X}{colors[1]} "
            line = []
    if line:
        current_line +=  ' '.join([f"{b:0{repr_length}{mode}}" for b in line]) + ' ' + \
                        ' ' * ((repr_length + 1) * (16-len(line)) - 1) + \
                        f" {colors[0]}#{colors[1]} " + \
                        ' '.join(map(get_display_char, line))
        yield current_line
