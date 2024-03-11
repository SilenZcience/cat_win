"""
stdinhelper
"""

import os
import sys


def write_file(content: str, src_file: str, file_encoding: str) -> str:
    """
    Writes content into a generated temp-file.
    
    Parameters:
    content (str):
        the content to write in a file
    src_file (str):
        a string representation of a file (-path)
    file_encoding (str):
        an encoding the open the file with
    
    Returns:
    src_file (str):
        the path to the temporary file written
    """
    if not isinstance(content, str): # in case the content is of types bytes
        content = content.decode(file_encoding)
    with open(src_file, 'w', encoding=file_encoding, errors='replace') as raw_f:
        raw_f.write(content)
    return src_file


def get_stdin_content(one_line: bool = False):
    """
    read the stdin.
    
    Parameters:
    one_line (bool):
        determines if only the first stdin line should be read
        
    Yields:
    line (str):
        the input (line by line) delivered by stdin
        until the first EOF (Chr(26)) character
    """
    if one_line:
        first_line = sys.stdin.readline().rstrip('\n')
        if first_line[-1:] == chr(26):
            first_line = first_line[:-1]
        yield first_line
        return
    for line in sys.stdin:
        if line[-2:-1] == chr(26):
            yield line[:-2]
            break
        yield line


def path_parts(path: str) -> list:
    """
    split a path recursively into its parts.
    
    Parameters:
    path (str):
        a file/dir path
        
    Returns:
    (list):
        contains each drive/directory/file in the path seperated
        "C:/a/b/c/d.txt" -> ['C:/', 'a', 'b', 'c', 'd.txt']
    """
    _p, _f = os.path.split(path)
    return path_parts(_p) + [_f] if _f and _p else [_p] if _p else []


def create_file(file: str, content: str, file_encoding: str) -> bool:
    """
    create the directory path to a file, and the file itself.
    on error: cleanup all created subdirectories
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    content (str):
        the content to write into the files
    file_encoding (str):
        the encoding to open the files with
    
    Returns:
    (bool):
        True if the operation was successful.
    """
    file_dir = os.path.dirname(file)
    splitted_path = path_parts(file_dir)
    subpaths = [os.path.join(*splitted_path[:i]) for i in range(2, len(splitted_path)+1)]
    unknown_subpaths = [s for s in subpaths[::-1] if not os.path.exists(s)]
    try:
        os.makedirs(file_dir, exist_ok=True)
    except OSError:
        print(f"Error: The path '{file_dir}' could not be created.", file=sys.stderr)
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    try:
        write_file(content, file, file_encoding)
    except OSError:
        print(f"Error: The file '{file}' could not be written.", file=sys.stderr)
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    return True


def write_files(file_list: list, content: str, file_encoding: str) -> list:
    """
    write to multiple files. ask if an empty file should be created
    when there is nothing to write.
    try to create the path to the files if it does not yet exist.
    delete the created path again (cleanup) if the file still could
    not be written.
    
    Parameters:
    file_list (list):
        all files that should be written
    content (str):
        the content to write into the files
    file_encoding (str):
        the encoding to open the files with
    
    Returns:
    (list):
        containing all files, that could succesfully be written.
    """
    if not file_list:
        return file_list

    if content == '':
        user_input = ''
        try:
            print('You are about to create an empty file. ', end='', file=sys.stderr)
            print('Do you want to continue?', file=sys.stderr)
            enter_char = '⏎'

            try:
                if len(enter_char.encode(file_encoding)) != 3:
                    raise UnicodeEncodeError('', '', -1, -1, '')
            except UnicodeEncodeError:
                enter_char = 'ENTER'
            print(f"[Y/{enter_char}] Yes, Continue       [N] No, Abort :", end='', file=sys.stderr)
            user_input = input()
        except EOFError:
            pass
        except UnicodeError:
            print('Input is not recognized in the given encoding: ', end='', file=sys.stderr)
            print(file_encoding, file=sys.stderr)
            user_input = 'N'
        finally:
            if user_input and user_input.upper() != 'Y':
                print('Aborting...', file=sys.stderr)
                file_list.clear()

    success_file_list = []

    for file in file_list:
        file = os.path.realpath(file)
        try:
            write_file(content, file, file_encoding)
            success_file_list.append(file)
        except FileNotFoundError: # the os.pardir path to the file does not exist
            if create_file(file, content, file_encoding):
                success_file_list.append(file)
        except OSError:
            print(f"Error: The file '{file}' could not be written.", file=sys.stderr)

    return success_file_list


def read_write_files_from_stdin(file_list: list, file_encoding: str, on_windows_os: bool,
                                one_line: bool = False) -> list:
    """
    Write stdin input to multiple files.
    
    Parameters:
    file_list (list):
        all files that should be written
    file_encoding (str):
        the encoding to use for writing the files
    on_windows_os (bool):
        indicates if the user is on windows OS using
        platform.system() == 'Windows'
    one_line (bool):
        determines if only the first stdin line should be read
        
    Returns:
    (list):
        containing all files, that could succesfully be written.
    """
    if not file_list:
        return file_list

    print('The given FILE(s)', end='', file=sys.stderr)
    print('', *file_list, sep='\n\t', file=sys.stderr)
    eof_control_char = 'Z' if on_windows_os else 'D'
    print('do/does not exist. Write the FILE(s) and finish with the ', end='', file=sys.stderr)
    print(f"^{eof_control_char}-suffix (Ctrl + {eof_control_char}):", file=sys.stderr)

    std_input = ''.join(get_stdin_content(one_line))

    return write_files(file_list, std_input, file_encoding)
