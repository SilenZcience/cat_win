"""
fileattributes
"""

from datetime import datetime
from pathlib import Path
from stat import (
    FILE_ATTRIBUTE_ARCHIVE as A,
    FILE_ATTRIBUTE_SYSTEM as S,
    FILE_ATTRIBUTE_HIDDEN as H,
    FILE_ATTRIBUTE_READONLY as R,
    FILE_ATTRIBUTE_NOT_CONTENT_INDEXED as I,
    FILE_ATTRIBUTE_COMPRESSED as C,
    FILE_ATTRIBUTE_ENCRYPTED as E,
    S_IRUSR,
    S_IWUSR,
    S_IXUSR,
    S_IRGRP,
    S_IWGRP,
    S_IXGRP,
    S_IROTH,
    S_IWOTH,
    S_IXOTH,
    S_ISDIR,
)
import json
import math
import os
try:
    from pwd import getpwuid
    from grp import getgrgid
except ImportError:
    pass

from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.winstreams import WinStreams


class Signatures:
    """
    Signatures
    """
    signatures = None

    @staticmethod
    def match(file_prefix_: str, signature_: str) -> bool:
        """
        check if a signature (magic number) matches

        Parameters:
        file_prefix_ (str):
            the prefix of the current file
        signature_ (str):
            the signature to compare

        Returns:
        (bool):
            indicates if the signature matches
        """
        file_prefix = [file_prefix_[i:i+2] for i in range(0, len(signature_), 2)]
        signature = [signature_[i:i+2] for i in range(0, len(signature_), 2)]
        for fp, sp in zip(file_prefix, signature):
            if sp == '??':
                continue
            if fp != sp:
                return False
        return True

    @staticmethod
    def read_signature(res_path: str, file: Path) -> str:
        """
        read a file and compare its signature to known signatures.

        Parameters:
        res_path (str):
            the path to the signatures database
        file (Path):
            a string representation of a file (-path)

        Returns:
        (str):
            the possible signatures of the file
        """
        file_signature_primary = ''
        file_signature_secondary = []
        encountered_sig = set()

        file_ext = os.path.splitext(file)[1][1:]
        file_ = None
        try:
            file_ = open(file, 'rb')
            file_prefix = file_.read(348).hex().upper()

            if Signatures.signatures is None:
                with open(res_path, 'r', encoding='utf-8') as sig:
                    Signatures.signatures = json.load(sig)
            signatures_json = Signatures.signatures
        except OSError:
            if file_ is not None:
                file_.close()
            return 'lookup failed!'
        for ext, signature in signatures_json.items():
            for sign in signature['signs']:
                offset, sig = sign.split(',')
                sig_distance = len(sig) - len(file_prefix) + int(offset)*2
                if sig_distance > 0: # adjust prefix in case not enough was read
                    file_prefix += file_.read(sig_distance//2).hex().upper()
                if Signatures.match(file_prefix[int(offset)*2:], sig):
                    signature_option = f"{signature['mime']}({ext})"
                    if ext == file_ext:
                        file_signature_primary = signature_option
                    elif sig not in encountered_sig:
                        file_signature_secondary.append((signature_option, len(sig)))
                    encountered_sig.add(sig)
                    break
        file_.close()
        # sort by matched signature length
        file_signature_secondary.sort(key=lambda x: x[1], reverse=True)
        file_signature_secondary = [fs for fs, _ in file_signature_secondary]
        if file_signature_primary and file_signature_secondary:
            return file_signature_primary + ' [' + ';'.join(file_signature_secondary) + ']'
        if file_signature_primary:
            return file_signature_primary
        if file_signature_secondary:
            return '[' + ';'.join(file_signature_secondary) + ']'
        return '-'

def _convert_size(size_bytes: int) -> str:
    """
    convert a size value to a more compact representation

    Parameters:
    size_bytes (int):
        a size value in bytes

    Returns:
    (str):
        a string representation with a size value suffix
    """
    if size_bytes == 0:
        return '0  B'
    size_name = (' B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    power = pow(1024, i)
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[i] if i < len(size_name) else '?'}"


def read_attribs(file: Path) -> list:
    """
    check which attributes a file has set.

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    (list):
        a list of lists containing attributes and a
        boolean value describing if it is set
        [[ATTRIBUTE, True/False], ...]
    """
    try:
        attrs = os.stat(file, follow_symlinks=False).st_file_attributes
    except AttributeError:
        return []

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

def get_file_size(file: Path) -> int:
    """
    calculate the size of a file

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    (int):
        the size in bytes or 0 if an (OS-)error occurs
    """
    try:
        return os.stat(file).st_size
    except OSError:
        return 0

def get_dir_size(directory: str) -> int:
    """
    calculate the size of a directory

    Parameters:
    directory (str):
        a string representation of a dir (-path)

    Returns:
    total (int):
        the size in bytes or 0 if an (OS-)error occurs
    """
    total = 0
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
    except OSError:
        pass
    return total

def get_file_mtime(file: Path) -> float:
    """
    get the modified time of a file

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    (float):
        the modified time of a file
    """
    try:
        return os.stat(file).st_mtime
    except OSError:
        return 0.0

def get_file_meta_data(file: Path, res_path: str, colors = None) -> str:
    """
    calculate file metadata information.

    Parameters:
    file (Path):
        a string representation of a file (-path)
    res_path (str);
        the path to the signatures database
    colors (list):
        a list containing the ANSI-Colorcodes to display
        the attributes like [RESET_ALL, ATTRIB, +ATTRIB, -ATTRIB]

    Returns:
    meta_data (str):
        representation containing file size, creation/modified/accessed time.
        on windows: also contains file attribute information
    """
    if colors is None or len(colors) < 4:
        colors = ['', '', '', '']
    try:
        stats = os.stat(file)

        meta_data = f"{colors[1]}{file}{colors[0]}\n"

        meta_data += f"{colors[1]}{'Signature:' : <16}"
        meta_data += f"{Signatures.read_signature(res_path, file)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'Size:' : <16}"
        meta_data += f"{_convert_size(stats.st_size)} ({stats.st_size}){colors[0]}\n"
        meta_data += f"{colors[1]}{'ATime:': <16}"
        meta_data += f"{datetime.fromtimestamp(stats.st_atime)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'MTime:': <16}"
        meta_data += f"{datetime.fromtimestamp(stats.st_mtime)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'CTime:': <16}"
        meta_data += f"{datetime.fromtimestamp(stats.st_ctime)}{colors[0]}\n"

        if not on_windows_os:
            perms = [
                (S_IRUSR, 'r'), (S_IWUSR, 'w'), (S_IXUSR, 'x'),  # User
                (S_IRGRP, 'r'), (S_IWGRP, 'w'), (S_IXGRP, 'x'),  # Group
                (S_IROTH, 'r'), (S_IWOTH, 'w'), (S_IXOTH, 'x'),  # Others
            ]
            meta_data += f"{colors[1]}{'d' if S_ISDIR(stats.st_mode) else '-'}"
            meta_data += f"{''.join([per if stats.st_mode & bit else '-' for bit, per in perms])} "
            meta_data += f"{stats.st_nlink} {getpwuid(stats.st_uid).pw_name} "
            meta_data += f"{getgrgid(stats.st_gid).gr_name}{colors[0]}\n"

            return meta_data

        file_handle = WinStreams(file)
        if file_handle.streams:
            meta_data += f"{colors[1]}Alternate Data Streams:{colors[0]}\n"
            for stream in file_handle.streams:
                meta_data += f"\t{colors[1]}- {stream}{colors[0]}\n"

        attribs = read_attribs(file)
        if attribs:
            meta_data += f"{colors[2]}+{', '.join(x for x, y in attribs if y)}{colors[0]}\n"
            meta_data += f"{colors[3]}-{', '.join(x for x, y in attribs if not y)}{colors[0]}\n"
        return meta_data
    except OSError:
        return ''

def print_meta(file: Path, res_path: str, colors: list) -> None:
    """
    print the information retrieved by get_file_meta_data()

    Parameters:
    file (Path):
        a string representation of a file (-path)
    colors (list):
        [reset, attributes, positive_attr, negative_attr] color codes
    """
    meta_data = get_file_meta_data(file, res_path, colors)
    print(meta_data)
