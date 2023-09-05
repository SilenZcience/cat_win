import zipfile


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
        print(f"The file '{file}' has been detected to be a zip-file. The archive contains the following files:")
        length_list = [max(map(lambda c: len(c[i]), file_info_list)) for i in range(len(file_info_list[0]))]
        for name, size, csize in file_info_list:
            print(f"{name.ljust(length_list[0])} {size.rjust(length_list[1])} {csize.rjust(length_list[2])}")
        return True
    except zipfile.BadZipfile:
        return False
