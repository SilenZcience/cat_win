from math import log, pow, floor
from datetime import datetime
from colorama import Fore
from os import stat
from platform import system
from stat import (
    FILE_ATTRIBUTE_ARCHIVE as A,
    FILE_ATTRIBUTE_SYSTEM as S,
    FILE_ATTRIBUTE_HIDDEN as H,
    FILE_ATTRIBUTE_READONLY as R,
    FILE_ATTRIBUTE_NOT_CONTENT_INDEXED as I,
    FILE_ATTRIBUTE_COMPRESSED as C,
    FILE_ATTRIBUTE_ENCRYPTED as E
)


def _convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def read_attribs(file):
    attrs = stat(file, follow_symlinks=False).st_file_attributes

    return (
        [["Archive", bool(attrs & A)],
         ["System", bool(attrs & S)],
         ["Hidden", bool(attrs & H)],
         ["Readonly", bool(attrs & R)],
         # Because this attribute is true when the file is _not_ indexed
         ["Indexed", not bool(attrs & I)],
         ["Compressed", bool(attrs & C)],
         ["Encrypted", bool(attrs & E)]]
    )


def printFileMetaData(files):
    stats = 0
    for file in files:
        try:
            stats = stat(file)
            print(file)

            print(f'{"Size:": <16}{_convert_size(stats.st_size)}')
            print(f'{"ATime:": <16}{  datetime.fromtimestamp(stats.st_atime)}')
            print(f'{"MTime:": <16}{datetime.fromtimestamp(stats.st_mtime)}')
            print(f'{"CTime:": <16}{datetime.fromtimestamp(stats.st_ctime)}')
            if system() != "Windows":
                print()
                continue
            attribs = read_attribs(file)
            print(Fore.LIGHTGREEN_EX, ", ".join(
                [x for x, y in attribs if y]), Fore.RESET, sep="")
            print(Fore.LIGHTRED_EX, ", ".join(
                [x for x, y in attribs if not y]), Fore.RESET, sep="")
            print()
        except OSError:
            continue
