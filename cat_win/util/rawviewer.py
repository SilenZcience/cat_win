
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

    # \0 ASCII Null (NULL) 0 ␀
    # \a ASCII Bell (BEL) 7 ␇
    # \b ASCII Backspace (BS) 8 ␈
    # \t ASCII Horizontal Tab (TAB) 9 ␉
    # \n ASCII Linefeed (LF) 10 ␤
    # \v ASCII Vertical Tab (VT) 11 ␋
    # \f ASCII Formfeed (FF) 12 ␌
    # \r ASCII Carriage Return (CR) 13 ␍
    CRLF = {
        -1: '·', # default fallback symbol
         0: '␀',
         7: '␇',
         8: '␈',
         9: '␉',
        10: '␤',
        11: '␋',
        12: '␌',
        13: '␍',
        }

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
