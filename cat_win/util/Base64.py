from base64 import b64encode, b64decode

def encodeBase64(content: list) -> list:
    # concatenate all lines and join them with line breaks
    contentLines = list(map(lambda x: x[1], content))
    contentLine = '\n'.join(contentLines)
    # encode the string to bytes and encode with base64
    contentBytes = contentLine.encode()
    base64_bytes = b64encode(contentBytes)
    encoded_content = base64_bytes.decode('ascii')
    # return as a single line
    return [('', encoded_content)]

def decodeBase64(content: list) -> list:
    # concatenate all lines and join them
    contentLines = list(map(lambda x: x[1], content))
    contentLine = ''.join(contentLines)
    # encode the string to bytes and decode with base64
    base64_bytes = contentLine.encode("ascii")
    decoded_content = b64decode(base64_bytes)
    decoded_content = decoded_content.decode()
    # return as content list, split at line breaks
    decoded_content = decoded_content.split('\n')
    return [('', line) for line in decoded_content]
