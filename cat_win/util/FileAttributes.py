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
    convert a size value to a more compact representation
    
    Parameters_
    size_bytes (int):
        a size value in bytes
        
    Returns:
    (str):
        a string representation with a size value suffix
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
    check which attributes a file has set.
    
    Parameters:
    file (str):
        a string representation of a file (-path)
        
    Returns:
    (list):
        a list of lists containing attributes and a
        boolean value describing if it is set
        [[ATTRIBUTE, True/False], ...]
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


def getFileSize(file: str) -> int:
    """
    calculate the size of a file
    
    Parameters:
    file (str):
        a string representation of a file (-path)
        
    Returns:
    (int):
        the size in bytes or 0 if an (OS-)error occurs
    """
    try:
        return stat(file).st_size
    except OSError:
        return 0


def getFileMetaData(file: str, colors: list = None) -> str:
    """
    calculate file metadata information.
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    colors (list):
        a list containing the ANSI-Colorcodes to display
        the attributes like [RESET_ALL, ATTRIB, +ATTRIB, -ATTRIB]
    
    Returns:
    metaData (str):
        representation containing file size, creation/modified/accessed time.
        on windows: also contains file attribute information
    """
    if colors == None or len(colors) < 4:
        colors = ['', '', '', '']
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
