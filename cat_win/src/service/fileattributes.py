"""
fileattributes
"""

from datetime import datetime
from pathlib import Path
from shutil import which
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
try:
    from pwd import getpwuid
    from grp import getgrgid
except ImportError:
    pass
import json
import math
import os
import subprocess

from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.winstreams import WinStreams


class Signatures:
    """
    Signatures
    """
    signatures = None

    @staticmethod
    def set_res_path(res_path: str) -> None:
        """
        set the path to the signatures database

        Parameters:
        res_path (str):
            the path to the signatures database
        """
        try:
            with open(res_path, 'r', encoding='utf-8') as sig:
                Signatures.signatures = json.load(sig)
        except (OSError, json.JSONDecodeError):
            Signatures.signatures = None

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
    def read_signature(file: Path) -> str:
        """
        read a file and compare its signature to known signatures.

        Parameters:
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
                raise OSError("Signatures not loaded")
        except OSError as e:
            if file_ is not None:
                file_.close()
            return f"lookup failed: {e}"
        for ext, signature in Signatures.signatures.items():
            for sign in signature['signs']:
                offset, sig = sign.split(',')
                sig_distance = len(sig) - len(file_prefix) + int(offset)*2
                if sig_distance > 0: # adjust prefix in case not enough was read
                    file_prefix += file_.read(sig_distance//2).hex().upper()
                if Signatures.match(file_prefix[int(offset)*2:], sig):
                    signature_option = f"{signature['mime']}({ext})"
                    if ext == file_ext:
                        file_signature_primary = signature_option
                    elif sig not in encountered_sig or not file_signature_secondary:
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

def get_libmagic_file(file: Path) -> str:
    """
    get the libmagic file information of a file

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    (str):
        the libmagic file information of a file
    """
    # try to find a native file.exe first
    file_cmd = which('file.exe') or which('file') # should work on windows/unix
    if file_cmd:
        try:
            sub = subprocess.run(
                [str(file_cmd), str(file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            if sub.returncode != 0:
                return ''
            libmagic_out = sub.stdout.decode().strip()
            return libmagic_out.rpartition(':')[-1].lstrip()
        except OSError:
            pass

    # fallback: try to find git.exe and locate file.exe inside the Git installation
    git_cmd = which('git.exe') or which('git')

    if not git_cmd:
        return ''

    try:
        git_path = Path(git_cmd).resolve()
    except OSError:
        return ''

    search_root = git_path.parent.parent if len(git_path.parents) >= 2 else git_path.parent

    found_file = None
    try:
        for file_exe in search_root.rglob('file.exe'):
            found_file = file_exe
            break
        else:
            for file_exe in search_root.rglob('file'):
                found_file = file_exe
                break
    except OSError:
        found_file = None

    if not found_file:
        return ''

    try:
        sub = subprocess.run(
            [str(found_file), str(file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
    except OSError:
        return ""
    libmagic_out = sub.stdout.decode().strip()
    return libmagic_out.rpartition(':')[-1].lstrip()

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

def get_file_ctime(file: Path) -> float:
    """
    get the created time of a file

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    (float):
        the created time of a file
    """
    try:
        return os.stat(file).st_birthtime
    except AttributeError:
        return os.stat(file).st_ctime
    except OSError:
        return 0.0

def get_file_meta_data(file: Path, colors = None) -> str:
    """
    calculate file metadata information.

    Parameters:
    file (Path):
        a string representation of a file (-path)
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
        meta_data += f"{Signatures.read_signature(file)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'LibMagic:' : <16}"
        meta_data += f"{get_libmagic_file(file)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'Size:' : <16}"
        meta_data += f"{_convert_size(stats.st_size)} ({stats.st_size}){colors[0]}\n"
        meta_data += f"{colors[1]}{'ATime:': <16}"
        meta_data += f"{datetime.fromtimestamp(stats.st_atime)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'MTime:': <16}"
        meta_data += f"{datetime.fromtimestamp(stats.st_mtime)}{colors[0]}\n"
        meta_data += f"{colors[1]}{'CTime:': <16}"
        try:
            meta_data += f"{datetime.fromtimestamp(stats.st_birthtime)}{colors[0]}\n"
        except AttributeError:
            meta_data += f"{datetime.fromtimestamp(stats.st_ctime)}{colors[0]}\n"

        perms = [
            (S_IRUSR, 'r'), (S_IWUSR, 'w'), (S_IXUSR, 'x'),  # User
            (S_IRGRP, 'r'), (S_IWGRP, 'w'), (S_IXGRP, 'x'),  # Group
            (S_IROTH, 'r'), (S_IWOTH, 'w'), (S_IXOTH, 'x'),  # Others
        ]
        meta_data += f"{colors[1]}{'d' if S_ISDIR(stats.st_mode) else '-'}"
        meta_data += f"{''.join([per if stats.st_mode & bit else '-' for bit, per in perms])} "
        meta_data += f"({oct(stats.st_mode)[-3:]})"
        if not on_windows_os:
            meta_data += f" {stats.st_nlink} {getpwuid(stats.st_uid).pw_name}"
            meta_data += f" {getgrgid(stats.st_gid).gr_name}{colors[0]}\n"
            return meta_data

        meta_data += f"{colors[0]}\n"

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

def print_meta(file: Path, colors: list) -> None:
    """
    print the information retrieved by get_file_meta_data()

    Parameters:
    file (Path):
        a string representation of a file (-path)
    colors (list):
        [reset, attributes, positive_attr, negative_attr] color codes
    """
    meta_data = get_file_meta_data(file, colors)
    print(meta_data)
