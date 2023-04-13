from sys import stdin
import os


def writeTemp(content: str, tmp_file: str, file_encoding: str) -> str:
    """
    Writes content into a generated temp-file.
    
    Parameters:
    content (str):
        the content to write in a file
    tmp_file (str):
        a string representation of a file (-path)
    file_encoding (str):
        an encoding the open the file with
    
    Returns:
    tmp_file (str):
        the path to the temporary file written
    """
    with open(tmp_file, 'w', encoding=file_encoding) as f:
        f.write(content)
    return tmp_file


def getStdInContent(oneLine: bool = False):
    """
    read the stdin.
    
    Parameters:
    oneLine (bool):
        determines if only the first stdin line should be read
        
    Yields:
    input (str):
        the input delivered by stdin
        until the first EOF (Chr(26)) character
    """
    if oneLine:
        first_line = stdin.readline()
        yield first_line.rstrip('\n')
    else:
        for line in stdin:
            if line[-2:] == chr(26) + '\n':
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
    p, f = os.path.split(path)
    return path_parts(p) + [f] if f and p else [p] if p else []


def createFile(file: str, content: str, file_encoding: str) -> bool:
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
        print(f"Error: The path '{file_dir}' could not be created.")
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    try:
        with open(file, 'w', encoding=file_encoding) as f:
            f.write(content)
    except OSError:
        print(f"Error: The file '{file}' could not be written.")
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    return True


def writeFiles(file_list: list, content: str, file_encoding: str) -> list:
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
    if len(file_list) == 0:
        return file_list
    
    if content == '':
        abort_command = '' 
        try:
            print('You are about to create an empty file. Do you want to continue?')
            enterChar = '⏎'
            try:
                enterChar.encode(file_encoding)
            except UnicodeError:
                enterChar = 'ENTER'
            abort_command = input(f"[Y/{enterChar}] Yes, Continue       [N] No, Abort :")
        except EOFError:
            pass
        finally:
            if abort_command and abort_command.upper() != 'Y':
                print('Aborting...')
                file_list.clear()
    
    success_file_list = []
    
    for file in file_list:
        try:
            with open(file, 'w', encoding=file_encoding) as f:
                f.write(content)
            success_file_list.append(file)
        except FileNotFoundError: # the os.pardir path to the file does not exist
            if createFile(file, content, file_encoding):
                success_file_list.append(file)
        except OSError:
            print(f"Error: The file '{file}' could not be written.")
            
    return success_file_list


def readWriteFilesFromStdIn(file_list: list, file_encoding: str, oneLine: bool = False) -> list:
    """
    Write stdin input to multiple files.
    
    Parameters:
    file_list (list):
        all files that should be written
    file_encoding (str):
        the encoding to use for writing the files
    oneLine (bool):
        determines if only the first stdin line should be read
        
    Returns:
    (list):
        containing all files, that could succesfully be written.
    """
    if len(file_list) == 0:
        return file_list

    print('The given FILE(s)', end='')
    print('', *file_list, sep='\n\t')
    print("do/does not exist. Write the FILE(s) and finish with the '^Z'-suffix ((Ctrl + Z) + Enter):")

    input = ''.join(getStdInContent(oneLine))

    return writeFiles(file_list, input, file_encoding)
