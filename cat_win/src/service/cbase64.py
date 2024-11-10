"""
cbase64
"""

import base64


def encode_base64(content, decode_bytes: bool = False,
                  file_encoding: str = 'utf-8'):
    """
    Encode a string to base64.

    Parameters:
    content (bytes|str):
        the content to encode in base64
    decode_bytes (bool):
        indicates if the returned value should be returned as
        an decoded string, or as encoded bytes (default)
    file_encoding (str):
        the encoding to use when decoding the bytes to a string

    Returns:
    encoded_content (bytes|str):
        the base64 encoded content as string or bytes depending on decode_bytes
    """
    if isinstance(content, str):
        content = content.encode(encoding=file_encoding, errors='ignore')

    encoded_content = base64.b64encode(content)

    if decode_bytes:
        return encoded_content.decode(encoding='ascii')
    return encoded_content


def decode_base64(content: str, decode_bytes: bool = False,
                  file_encoding: str = 'utf-8'):
    """
    Decode a string from base64.

    Parameters:
    content (str):
        the string to decode
    decode_bytes (bool):
        indicates if the returned value should be returned as
        an decoded string, or as encoded bytes (default)
    file_encoding (str):
        the encoding to use when decoding the bytes to a string

    Returns:
    decoded_content (bytes|str):
        the base64 decoded content as string or bytes depending on decode_bytes
    """
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    # base64.b64decode() would raise an error on corrupted base64.
    # the following algorithm decodes as much as possible:
    binary_str = ''.join(f"{chars.index(char):06b}" for char in content if char in chars)
    if len(binary_str) % 8 != 0:
        binary_str = binary_str[:-(len(binary_str)%8)]
    decoded_content = bytearray()
    decoded_content.extend([int(binary_str[i:i+8], 2) for i in range(0, len(binary_str), 8)])

    if decode_bytes:
        return decoded_content.decode(file_encoding, errors='ignore')
    return decoded_content
