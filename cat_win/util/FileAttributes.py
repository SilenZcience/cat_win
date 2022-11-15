from math import log, pow, floor
from datetime import datetime
from os import stat

def _convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def printFileMetaData(files):
    stats = 0
    for file in files:
        try:
            stats = stat(file)
            print(file)
            
            print(f'{"Size:": <16}{_convert_size(stats.st_size)}')
            print(f'{"AccessTime:": <16}{  datetime.fromtimestamp(stats.st_atime)}')
            print(f'{"ModifiedTime:": <16}{datetime.fromtimestamp(stats.st_mtime)}')
            print(f'{"CreationTime:": <16}{datetime.fromtimestamp(stats.st_ctime)}')
            print()
        except OSError:
            continue