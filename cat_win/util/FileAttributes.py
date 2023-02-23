from math import log, pow, floor
from datetime import datetime
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
    """
    Takes an integer representing a file size in bytes.
    Returns a string representation containing the
    appropriate Suffix.
    """
    if size_bytes == 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i] if i < 9 else '?'}"


def read_attribs(file: str) -> list:
    """
    Read the Windows file attributes and return them
    in a list of lists.
    """
    attrs = stat(file, follow_symlinks=False).st_file_attributes

    return (
        [['Archive', bool(attrs & A)],
         ['System', bool(attrs & S)],
         ['Hidden', bool(attrs & H)],
         ['Readonly', bool(attrs & R)],
         # Because this attribute is true when the file is _not_ indexed
         ['Indexed', not bool(attrs & I)],
         ['Compressed', bool(attrs & C)],
         ['Encrypted', bool(attrs & E)]]
    )


def getFileMetaData(file: str, colors: list) -> str:
    """
    Takes a file and returns a string representation
    containing file size, creation/modified/accessed time.
    On Windows OS also return the file attributes.
    colors: [RESET_ALL, ATTRIB, +ATTRIB, -ATTRIB]
    """
    try:
        stats = stat(file)
        
        metaData = colors[1] + file + colors[0] + '\n'
        
        metaData += f"{colors[1]}{'Size:' : <16}{_convert_size(stats.st_size)}{colors[0]}\n"
        metaData += f"{colors[1]}{'ATime:': <16}{datetime.fromtimestamp(stats.st_atime)}{colors[0]}\n"
        metaData += f"{colors[1]}{'MTime:': <16}{datetime.fromtimestamp(stats.st_mtime)}{colors[0]}\n"
        metaData += f"{colors[1]}{'CTime:': <16}{datetime.fromtimestamp(stats.st_ctime)}{colors[0]}\n"
        
        if system() != 'Windows':
            metaData += '\n'
            return metaData
        
        attribs = read_attribs(file)
        metaData += colors[2]
        metaData += '+' + ", ".join([x for x, y in attribs if y])
        metaData += colors[0] + '\n'
        metaData += colors[3]
        metaData += '-' + ", ".join([x for x, y in attribs if not y])
        metaData += colors[0] + '\n'
        return metaData
    except OSError:
        pass
