from zlib import crc32 as crc32_hash
import hashlib


def get_checksum_from_file(file: str, colors = None) -> str:
    """
    Calculates and returns the CRC32, MD5, SHA1, SHA256, SHA512
    hashes of a file.
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    colors (list):
        a list with 2 elements like [COLOR_CHECKSUM, COLOR_RESET]
        containing the ANSI-Colorcodes used in the returned string.
    
    Returns:
    checksum (str):
        a formatted string representation of all checksums calculated
    """
    if colors is None or len(colors) < 2:
        colors = ['', '']
    buf_size = 65536  # 64kb
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    crc32 = 0

    try:
        with open(file, 'rb') as raw_f:
            while True:
                data = raw_f.read(buf_size)
                if not data:
                    break
                md5.update(data)
                sha1.update(data)
                sha256.update(data)
                sha512.update(data)
                crc32 = crc32_hash(data, crc32)
    except OSError as exc:
        return type(exc).__name__

    crc32 = f"{(crc32 & 0xFFFFFFFF):08X}"

    checksum =  f"\t{colors[0]}{'CRC32:' : <9}{str(crc32)}{colors[1]}\n"
    checksum += f"\t{colors[0]}{'MD5:'   : <9}{str(md5.hexdigest())}{colors[1]}\n"
    checksum += f"\t{colors[0]}{'SHA1:'  : <9}{str(sha1.hexdigest())}{colors[1]}\n"
    checksum += f"\t{colors[0]}{'SHA256:': <9}{str(sha256.hexdigest())}{colors[1]}\n"
    checksum += f"\t{colors[0]}{'SHA512:': <9}{str(sha512.hexdigest())}{colors[1]}\n"
    return checksum
