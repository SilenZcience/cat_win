from base64 import b64encode, b64decode


def _encodeBase64(content: str, encoding: str) -> str:
    # encode the string to bytes and encode with base64
    contentBytes = content.encode(encoding=encoding)
    base64_bytes = b64encode(contentBytes)
    encoded_content = base64_bytes.decode(encoding='ascii')
    # return as a single line
    return encoded_content


def encodeBase64(content: list, encoding: str = 'utf-8') -> list:
    # concatenate all lines and join them with line breaks
    contentLines = list(map(lambda x: x[1], content))
    contentLine = '\n'.join(contentLines)
    
    encoded_content = _encodeBase64(contentLine, encoding)
    # return as a list containing a single line
    return [('', encoded_content)]


def _decodeBase64(content: str, encoding: str) -> str:
    # encode the string to bytes and decode with base64
    base64_bytes = content.encode(encoding="ascii")
    decoded_content = b64decode(base64_bytes)
    decoded_content = decoded_content.decode(encoding=encoding)
    # return as a single line
    return decoded_content


def decodeBase64(content: list, encoding: str = 'utf-8') -> list:
    # concatenate all lines and join them
    contentLines = list(map(lambda x: x[1], content))
    contentLine = ''.join(contentLines)
    
    decoded_content = _decodeBase64(contentLine, encoding)
    
    # return as content list, split at line breaks
    decoded_content = decoded_content.split('\n')
    return [('', line) for line in decoded_content]