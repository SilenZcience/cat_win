
def getRawViewLinesGen(file: str = '', mode: str = 'X', colors = None):
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
        a list of two elements. Index 0 holds the color C_KW.RAWVIEWER,
        Index 1 holds the color C_KW.RESET_ALL
        
    Yields:
    currentLine (str):
        a string representation that, when put together, forms the hexviewer
        output containing the header and line information aswell
        as the bytes themselves
    """
    if colors == None or len(colors) < 2:
        colors = ['', '']
    
    CRLF = {10: '␤', 13: '␍'}
    
    def getDisplayChar(byte: int) -> str:
        # 32 - 126 => ' ' - '~' (ASCII)
        if 32 <= byte <= 126:
            return chr(byte)
        elif byte in [10, 13]:
            return CRLF[byte]
        return '·'
    
    rawFile = open(file, 'rb')
    rawFileContent = rawFile.read()
    rawFileContentLength = len(rawFileContent)
    rawFile.close()
    
    reprLength = 2 * (mode.upper() == 'X') + 8 * (mode == 'b')
     
    currentLine = f"{colors[0]}Address  "
    for i in range(16):
        currentLine += f"{i:0{2}X} " + '      ' * (mode == 'b')
    currentLine += f"# Decoded Text                   {colors[1]}"
    yield currentLine
    
    currentLine = f"{colors[0]}{0:0{8}X}{colors[1]} "
    line = []
    for i, byte in enumerate(rawFileContent, start=1):
        line.append(byte)
        if not (i % 16):
            currentLine +=  ' '.join([f"{b:0{reprLength}{mode}}" for b in line]) + \
                            f" {colors[0]}#{colors[1]} " + \
                            ' '.join(map(getDisplayChar, line))
            yield currentLine
            if i < rawFileContentLength:
                currentLine = f"{colors[0]}{i:0{8}X}{colors[1]} "
            line = []
    if line:
        currentLine +=  ' '.join([f"{b:0{reprLength}{mode}}" for b in line]) + ' ' + \
                        ' ' * ((reprLength + 1) * (16-len(line)) - 1) + \
                        f" {colors[0]}#{colors[1]} " + \
                        ' '.join(map(getDisplayChar, line))
        yield currentLine
