"""
zipviewer, tarviewer, rarviewer
"""

import struct
import tarfile
import zipfile
from pathlib import Path

from cat_win.src.service.helper.iohelper import logger

# ------------------------------ RAR v5 File Spec ------------------------------
# 0x0000  +8  Signature (Magic)                 52 61 72 21 1A 07 01 00

# Main Header
# 0x0008  +4  Header CRC32
#         +v  Header Size
#         +v  Header Type (1 = Main)
#         +v  Header Flags
#         +v  Extra Area Size (if HeaderFlags & 0x0001)
#         +v  Data Size (if HeaderFlags & 0x0002)
#         +v  Archive Flags
#         +v  Volume Number (if ArchiveFlags & 0x0002)
#         +n  Extra Area (optional)
#         +n  Data Area (optional)

# File Header
#         +4  Header CRC32
#         +v  Header Size
#         +v  Header Type (2 = File)
#         +v  Header Flags
#         +v  Extra Area Size (if HeaderFlags & 0x0001)
#         +v  Data Size (compressed file size, if HeaderFlags & 0x0002)
#         +v  File Flags
#         +v  Unpacked Size
#         +v  File Attributes
#         +4  Modification Time (if FileFlags & 0x0002)
#         +4  File CRC32 (if FileFlags & 0x0004)
#         +v  Compression Information
#         +v  Host OS
#         +v  File Name Length
#         +n  File Name (UTF-8)
#         +n  Extra Area (optional)
#         +n  Compressed File Data (Data Size bytes)

# Service Header
#         +4  Header CRC32
#         +v  Header Size
#         +v  Header Type (3 = Service)
#         ... Same layout as File Header ...

# Encryption Header
#         +4  Header CRC32
#         +v  Header Size
#         +v  Header Type (4 = Encryption)
#         +v  Header Flags
#         +v  Encryption Version
#         +v  Encryption Flags
#         +v  KDF Count
#         +16 Salt
#         +12 Password Check Value

# End Archive Header
#         +4  Header CRC32
#         +v  Header Size
#         +v  Header Type (5 = End Archive)
#         +v  Header Flags
#         +v  End Archive Flags
# ------------------------------------------------------------------------------

# ------------------------------ RAR v4 File Spec ------------------------------
# 0x0000  +7  Signature (Magic)                 52 61 72 21 1A 07 00

# Main Archive Header
# 0x0007  +2  Header CRC16
#         +1  Header Type (0x73 = Main)
#         +2  Header Flags
#         +2  Header Size
#         +2  Reserved1
#         +4  Reserved2
#         +n  Additional Data (if HeaderFlags indicate)

# File Header
#         +2  Header CRC16
#         +1  Header Type (0x74 = File)
#         +2  Header Flags
#         +2  Header Size
#         +4  Packed Size
#         +4  Unpacked Size
#         +1  Host OS
#         +4  File CRC32
#         +4  DOS File Time
#         +1  RAR Version Needed
#         +1  Compression Method
#         +2  File Name Size
#         +4  File Attributes
#         +8  High Packed/Unpacked Size (if HeaderFlags & 0x0100)
#         +n  File Name
#         +n  Salt (8 bytes, if HeaderFlags & 0x0400)
#         +n  Extended Time Data (if HeaderFlags & 0x1000)
#         +n  Compressed File Data (Packed Size bytes)

# Comment Header
#         +2  Header CRC16
#         +1  Header Type (0x75 = Comment)
#         +2  Header Flags
#         +2  Header Size
#         +2  Unpacked Size
#         +1  RAR Version Needed
#         +1  Compression Method
#         +2  Comment CRC16
#         +n  Compressed Comment Data

# Extra Information Header
#         +2  Header CRC16
#         +1  Header Type (0x76 = AV)
#         +2  Header Flags
#         +2  Header Size
#         +n  AV Data

# Subblock Header
#         +2  Header CRC16
#         +1  Header Type (0x77 = Subblock)
#         +2  Header Flags
#         +2  Header Size
#         +2  Subblock Type
#         +1  Level
#         +4  Data Size
#         +n  Subblock Data

# Recovery Record Header
#         +2  Header CRC16
#         +1  Header Type (0x78 = Recovery)
#         +2  Header Flags
#         +2  Header Size
#         +n  Recovery Record Data

# Authentication Header
#         +2  Header CRC16
#         +1  Header Type (0x79 = Authentication)
#         +2  Header Flags
#         +2  Header Size
#         +n  Authentication Data

# End Archive Header
#         +2  Header CRC16
#         +1  Header Type (0x7B = End Archive)
#         +2  Header Flags
#         +2  Header Size
#         +4  Archive CRC32 (optional)
#         +2  Volume Number (optional)
# ------------------------------------------------------------------------------

_RAR_MAGIC = b'Rar!\x1a\x07'
_RAR4_EXTRA = b'\x00'
_RAR5_EXTRA = b'\x01\x00'


def _rar5_decode_vint(data: bytes, offset: int) -> tuple:
    """
    Decode a RAR 5.x variable-length integer.

    Parameters:
    data (bytes):
        a bytes object containing the encoded variable-length integer
    offset (int):
        the offset in the data where the variable-length integer starts

    Returns:
    value, offset (int, int):
        (decoded value, new offset)
    """
    if offset >= len(data):
        return 0, offset
    value = 0
    shift = 0
    while True:
        b = data[offset]
        value |= (b & 0x7F) << shift
        offset += 1
        if not (b & 0x80):
            break
        shift += 7
        if offset >= len(data):
            break
    return value, offset


def _rar5_read_vint(fh) -> int:
    """
    Read a RAR 5.x variable-length integer from a file handle.

    Parameters:
    fh (file handle):
        a file handle opened in binary mode

    Returns:
    value (int):
        the decoded variable-length integer
    """
    value = 0
    shift = 0
    while True:
        raw = fh.read(1)
        if len(raw) < 1:
            return 0
        b = raw[0]
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return value


def _parse_rar(file: Path) -> list:
    """
    Parse a RAR-archive (v4 and v5).

    Parameters:
    file (Path):
        a string representation of a file (-path)

    Returns:
    entries (list):
        list of (name, size, compressed_size) tuples,
        or an empty list on failure.
    """
    with open(file, 'rb') as fh:
        magic = fh.read(8)
        if len(magic) < 7 or magic[:6] != _RAR_MAGIC:
            return []

        if magic[6:7] == _RAR4_EXTRA:
            is_rar5 = False
            fh.seek(7)
        elif len(magic) >= 8 and magic[6:8] == _RAR5_EXTRA:
            is_rar5 = True
        else:
            return []

        entries = []
        if is_rar5:
            _RAR5_HEAD_FILE = 2
            while True:
                crc_raw = fh.read(4)
                if len(crc_raw) < 4:
                    break
                header_size = _rar5_read_vint(fh)
                if header_size == 0:
                    break
                hdr_body = fh.read(header_size)
                if len(hdr_body) < header_size:
                    break
                htype, off = _rar5_decode_vint(hdr_body, 0)
                hflags, off = _rar5_decode_vint(hdr_body, off)
                extra_size = 0
                if hflags & 0x0001:
                    extra_size, off = _rar5_decode_vint(hdr_body, off)
                data_size = 0
                if hflags & 0x0002:
                    data_size, off = _rar5_decode_vint(hdr_body, off)
                fh.read(data_size)
                if htype != _RAR5_HEAD_FILE:
                    continue
                file_flags, off = _rar5_decode_vint(hdr_body, off)
                unp_size, off = _rar5_decode_vint(hdr_body, off)
                attrs, off = _rar5_decode_vint(hdr_body, off)
                if file_flags & 0x0002:
                    off += 4
                if file_flags & 0x0004:
                    off += 4
                _, off = _rar5_decode_vint(hdr_body, off)
                _, off = _rar5_decode_vint(hdr_body, off)
                name_len, off = _rar5_decode_vint(hdr_body, off)
                name_raw = hdr_body[off:off + name_len]
                try:
                    name = name_raw.decode('utf-8')
                except UnicodeDecodeError:
                    name = name_raw.decode('cp437', errors='replace')
                if attrs & 0x10:
                    name = name + '/'
                entries.append((name, unp_size, data_size))

            return entries


        _RAR4_HEAD_ARCHIVE = 0x73
        _RAR4_HEAD_FILE = 0x74

        archive_hdr = fh.read(7)
        if len(archive_hdr) < 7:
            return []
        _ar_crc, ar_type, _ar_flags, ar_size = struct.unpack('<HBHH', archive_hdr)
        if ar_type != _RAR4_HEAD_ARCHIVE:
            return []
        if ar_size > 7:
            fh.read(ar_size - 7)

        while True:
            hdr = fh.read(7)
            if len(hdr) < 7:
                break
            _crc, htype, _hflags, hsize = struct.unpack('<HBHH', hdr)
            if hsize < 7:
                break
            body = fh.read(hsize - 7)
            if len(body) < hsize - 7:
                break
            if htype != _RAR4_HEAD_FILE:
                continue

            if len(body) < 25:
                continue
            pack_size = struct.unpack('<I', body[0:4])[0]
            unp_size = struct.unpack('<I', body[4:8])[0]
            name_len = struct.unpack('<H', body[19:21])[0]

            hi_present = bool(_hflags & 0x100)
            name_off = 33 if hi_present else 25
            if len(body) < name_off + name_len:
                continue
            name_raw = body[name_off:name_off + name_len]

            full_pack = pack_size
            if hi_present and len(body) >= 33:
                hi_pack = struct.unpack('<I', body[25:29])[0]
                full_pack = (hi_pack << 32) | pack_size

            is_dir = (_hflags >> 5) & 0x07 == 0x07

            try:
                name = name_raw.decode('utf-8')
            except UnicodeDecodeError:
                name = name_raw.decode('cp437', errors='replace')
            if is_dir:
                name = name + '\\'
            entries.append((name, unp_size, full_pack))
            fh.read(full_pack)

        return entries


def display_archive(file: Path, size_converter) -> bool:
    """
    Parameters:
    file (Path):
        a string representation of a file (-path)
    size_converter (method)
        a method to convert bytes to more readable size values

    Returns:
    (bool):
        indicates if the given file could successfully be openend
        as a zip/tar/rar file.
    """
    try:
        if tarfile.is_tarfile(file):
            file_info_list = [('FileName', 'FileSize')]
            with tarfile.open(file) as tar_file:
                for file_info in tar_file:
                    file_info_list.append((file_info.name, str(size_converter(file_info.size))))
            logger(
                f"The file '{file}' has been detected to be a tar-file.",
                priority=logger.INFO
            )
            logger('The archive contains the following files:', priority=logger.INFO)
            length_list = [max(len(_f) for _f in f_info) for f_info in zip(*file_info_list)]
            for name, size in file_info_list:
                logger(
                    f"{name.ljust(length_list[0])} {size.rjust(length_list[1])}",
                    priority=logger.INFO
                )
            return True
    except (tarfile.TarError, OSError, ValueError):
        pass
    try:
        if zipfile.is_zipfile(file):
            file_info_list = [('FileName', 'FileSize', 'CompressedSize')]
            with zipfile.ZipFile(file, 'r') as zip_file:
                for file_info in zip_file.infolist():
                    file_info_list.append((file_info.filename,
                                        str(size_converter(file_info.file_size)),
                                        str(size_converter(file_info.compress_size))))
            logger(
                f"The file '{file}' has been detected to be a zip-file.",
                priority=logger.INFO
            )
            logger('The archive contains the following files:', priority=logger.INFO)
            length_list = [max(len(_f) for _f in f_info) for f_info in zip(*file_info_list)]
            for name, size, csize in file_info_list:
                logger(
                    f"{name.ljust(length_list[0])} " + \
                    f"{size.rjust(length_list[1])} {csize.rjust(length_list[2])}",
                    priority=logger.INFO
                )
            return True
    except (zipfile.BadZipfile, OSError):
        pass
    try:
        rar_entries = _parse_rar(file)
        if rar_entries:
            file_info_list = [('FileName', 'FileSize', 'CompressedSize')]
            for name, size, csize in rar_entries:
                file_info_list.append((name,
                                    str(size_converter(size)),
                                    str(size_converter(csize))))
            logger(
                f"The file '{file}' has been detected to be a rar-file.",
                priority=logger.INFO
            )
            logger('The archive contains the following files:', priority=logger.INFO)
            length_list = [max(len(_f) for _f in f_info) for f_info in zip(*file_info_list)]
            for name, size, csize in file_info_list:
                logger(
                    f"{name.ljust(length_list[0])} " + \
                    f"{size.rjust(length_list[1])} {csize.rjust(length_list[2])}",
                    priority=logger.INFO
                )
            return True
    except (OSError, struct.error):
        pass

    return False
