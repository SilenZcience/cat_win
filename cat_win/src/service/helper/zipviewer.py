"""
zipviewer & tarviewer
"""

import zipfile
import tarfile

from cat_win.src.service.helper.iohelper import err_print


def display_archive(file: str, size_converter) -> bool:
    """
    Parameters:
    file (str):
        a string representation of a file (-path)
    size_converter (method)
        a method to convert bytes to more readable size values
        
    Returns:
    (bool):
        indicates if the given file could successfully be openend as a zip/tar file.
    """
    try:
        if tarfile.is_tarfile(file):
            file_info_list = [('FileName', 'FileSize')]
            with tarfile.open(file) as tar_file:
                for file_info in tar_file:
                    file_info_list.append((file_info.name, str(size_converter(file_info.size))))
            err_print(f"The file '{file}' has been detected to be a tar-file. ", end='')
            err_print('The archive contains the following files:')
            length_list = [max(len(_f) for _f in f_info) for f_info in zip(*file_info_list)]
            for name, size in file_info_list:
                err_print(f"{name.ljust(length_list[0])} {size.rjust(length_list[1])}")
            return True
    except (tarfile.TarError, OSError, ValueError):
        pass
    try:
        if zipfile.is_zipfile(file):
            file_info_list = [('FileName', 'FileSize', 'CompressedFileSize')]
            with zipfile.ZipFile(file, 'r') as zip_file:
                for file_info in zip_file.infolist():
                    file_info_list.append((file_info.filename,
                                        str(size_converter(file_info.file_size)),
                                        str(size_converter(file_info.compress_size))))
            err_print(f"The file '{file}' has been detected to be a zip-file. ", end='')
            err_print('The archive contains the following files:')
            length_list = [max(len(_f) for _f in f_info) for f_info in zip(*file_info_list)]
            for name, size, csize in file_info_list:
                err_print(f"{name.ljust(length_list[0])} " + \
                    f"{size.rjust(length_list[1])} {csize.rjust(length_list[2])}")
            return True
    except (zipfile.BadZipfile, OSError):
        pass

    return False
