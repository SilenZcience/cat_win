"""
strings
"""

def get_strings(content: list, min_seq_len: int, delim: str) -> list:
    """
    find all strings in any given file content.

    Parameters:
    content (list):
        the file content [('', line), ...]
    min_seq_len (int):
        the minimum required length of a string
    delim (str):
        the delimeter to display the found strings on the same line

    Returns:
    new_content (list):
        the new file content containing all found strings [('', string), ...]
    """
    content_type_raw = bool(content) and isinstance(content[0][1], bytes)
    new_content = []
    new_string = ''
    for _, line in content:
        if content_type_raw:
            line = line.decode(errors='replace')
        new_line = []
        for char in line:
            if 32 <= ord(char) <= 126: # if it is printable ascii
                new_string += char
                continue
            if len(new_string) >= min_seq_len:
                new_line.append(new_string)
            new_string = ''
        if len(new_string) >= min_seq_len:
            new_line.append(new_string)
        new_string = ''
        for line in delim.join(new_line).splitlines():
            new_content.append(('', line))

    return new_content
