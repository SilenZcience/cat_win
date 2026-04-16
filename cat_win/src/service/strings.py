"""
strings
"""

from cat_win.src.domain.contentbuffer import ContentBuffer


def get_strings(content: ContentBuffer, min_seq_len: int, delim: str) -> ContentBuffer:
    """
    find all strings in any given file content.

    Parameters:
    content (ContentBuffer):
        the file contentbuffer object to search for strings in
    min_seq_len (int):
        the minimum required length of a string
    delim (str):
        the delimeter to display the found strings on the same line

    Returns:
    new_content (ContentBuffer):
        the new file contentbuffer containing all found strings [('', string), ...]
    """
    content_type_raw = bool(content) and isinstance(content[0][0], bytes)
    new_content = ContentBuffer()
    new_string = ''
    for line, _, _ in content:
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
            new_content.append(line)

    return new_content
