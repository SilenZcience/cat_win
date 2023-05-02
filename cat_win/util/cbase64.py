from base64 import b64encode, b64decode


def _encode_base64(content: str, encoding: str) -> bytes:
    """
    Encode a string to base64.
    
    Parameters:
    content (str):
        the string to encode
    encoding (str):
        the encoding the string is using
        
    Returns:
    encoded_content (bytes):
        the base64 encoded string
    """
    # encode the string to bytes and encode with base64
    content_bytes = content.encode(encoding=encoding)
    encoded_content = b64encode(content_bytes)

    # return as a single line
    return encoded_content


def encode_base64(content: list, encoding: str = 'utf-8') -> list:
    """
    Encode the file content to base64 by calling _encode_base64()
    
    Parameters:
    content (list):
        the file content represented as [(prefix, line), ...]
    encoding (str):
        the file encoding used
        
    Returns:
    [('', encoded_content)] (list):
        the encoded base64 content as a single line without any prefix
    """
    # concatenate all lines and join them with line breaks
    content_lines = list(map(lambda x: x[1], content))
    content_line = '\n'.join(content_lines)

    encoded_content = _encode_base64(content_line, encoding)
    encoded_content = encoded_content.decode(encoding='ascii')
    # return as a list containing a single line
    return [('', encoded_content)]


def _decode_base64(content: str) -> bytes:
    """
    Decode a string from base64.
    
    Parameters:
    content (str):
        the string to decode
        
    Returns:
    decoded_content (bytes):
        the base64 decoded string
    """
    # encode the string to bytes and decode with base64
    base64_bytes = content.encode(encoding='ascii')
    decoded_content = b64decode(base64_bytes)

    # return as a single line
    return decoded_content


def decode_base64(content: list, encoding: str = 'utf-8') -> list:
    """
    decode the file content from base64 by calling _decode_base64()
    
    Parameters:
    content (list):
        the file content represented as [(prefix, line), ...]
    encoding (str):
        the file encoding used
        
    Returns:
    [('', line), ...] (list):
        the decoded base64 content line by line without any prefix
    """
    # concatenate all lines and join them
    content_lines = list(map(lambda x: x[1], content))
    content_line = ''.join(content_lines)

    decoded_content = _decode_base64(content_line)
    decoded_content = decoded_content.decode(encoding=encoding)

    # return as content list, split at line breaks
    decoded_content = decoded_content.split('\n')
    return [('', line) for line in decoded_content]
