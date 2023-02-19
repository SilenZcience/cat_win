import hashlib
from zlib import crc32 as crc32_hash


def getChecksumFromFile(file: str, colors: list = ['', '']) -> str:
    """
    Takes a filepath of type String and
    returns a String representation of the
    CRC32, MD5, SHA1, SHA256, SHA512
    hashes corresponding to the given file.
    Takes a colors-list containing 2 elements:
    colors = [COLOR_CHECKSUM, COLOR_RESET]
    """
    BUF_SIZE = 65536  # 64kb
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    crc32 = 0

    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
            sha512.update(data)
            crc32 = crc32_hash(data, crc32)

    crc32 = "%08X" % (crc32 & 0xFFFFFFFF)
    
    checksum =  f'\t{colors[0]}{"CRC32:" : <9}{str(crc32)}{colors[1]}\n'
    checksum += f'\t{colors[0]}{"MD5:"   : <9}{str(md5.hexdigest())}{colors[1]}\n'
    checksum += f'\t{colors[0]}{"SHA1:"  : <9}{str(sha1.hexdigest())}{colors[1]}\n'
    checksum += f'\t{colors[0]}{"SHA256:": <9}{str(sha256.hexdigest())}{colors[1]}\n'
    checksum += f'\t{colors[0]}{"SHA512:": <9}{str(sha512.hexdigest())}{colors[1]}\n'
    return checksum
