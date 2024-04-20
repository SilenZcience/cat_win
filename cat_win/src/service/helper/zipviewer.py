"""
zipviewer
"""

import zipfile

from cat_win.src.service.helper.iohelper import err_print


def display_zip(file: str, size_converter) -> bool:
    """
    Parameters:
    file (str):
        a string representation of a file (-path)
    size_converter (method)
        a method to convert bytes to more readable size values
        
    Returns:
    (bool):
        indicates if the given file could succesfully be openend as a zip file.
    """
    try:
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
        return False
