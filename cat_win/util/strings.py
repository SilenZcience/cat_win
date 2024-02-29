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
    new_content = []
    min_seq_len = max(min_seq_len, 1)
    new_string = ''
    for _, line in content:
        new_line = []
        for char in line:
            if isinstance(char, int): # in case of a binary file
                char = chr(char)
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
