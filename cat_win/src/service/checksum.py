"""
checksum
"""

from pathlib import Path
import hashlib
import zlib

from cat_win.src.const.colorconstants import CKW


def get_checksum_from_file(file: Path, color_dic: dict) -> str:
    """
    Calculates and returns the CRC32, MD5, SHA1, SHA256, SHA512
    hashes of a file.

    Parameters:
    file (Path):
        a string representation of a file (-path)
    color_dic (dict):
        color dictionary containing all configured ANSI color values

    Returns:
    checksum (str):
        a formatted string representation of all checksums calculated
    """
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
                crc32 = zlib.crc32(data, crc32)
    except OSError as exc:
        return type(exc).__name__
    crc32 = f"{(crc32 & 0xFFFFFFFF):08X}"

    template = f"\t{color_dic[CKW.CHECKSUM]}%s{color_dic[CKW.RESET_ALL]}\n"
    checksum =  template % f"{'CRC32:' : <9}{str(crc32)}"
    checksum += template % f"{'MD5:'   : <9}{str(md5.hexdigest())}"
    checksum += template % f"{'SHA1:'  : <9}{str(sha1.hexdigest())}"
    checksum += template % f"{'SHA256:': <9}{str(sha256.hexdigest())}"
    checksum += template % f"{'SHA512:': <9}{str(sha512.hexdigest())}"
    return checksum

def print_checksum(file: Path, color_dic: dict) -> None:
    """
    print the information retrieved by get_checksum_from_file()

    Parameters:
    file (Path):
        a string representation of a file (-path)
    color_dic (dict):
        color dictionary containing all configured ANSI color values
    """
    print(f"{color_dic[CKW.CHECKSUM]}Checksum of '{file}':{color_dic[CKW.RESET_ALL]}")
    print(get_checksum_from_file(file, color_dic))
