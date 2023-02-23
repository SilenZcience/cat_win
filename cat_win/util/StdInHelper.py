import os
from sys import stdin


def writeTemp(content: str, tmp_file: str, file_encoding: str) -> str:
    """
    Writes content into a generated temp-file and
    returns the path in type String.
    """
    with open(tmp_file, 'w', encoding=file_encoding) as f:
        f.write(content)
    return tmp_file


def getStdInContent(oneLine: bool = False) -> str:
    """
    returns a String delivered by the standard input.
    """
    if oneLine:
        first_line = stdin.readline()
        return first_line.rstrip('\n')
    input = ''
    for line in stdin:
        if line[-2:] == chr(26) + '\n':
            input += line[:-2]
            break
        input += line
    return input


def path_parts(path: str) -> list:
    p, f = os.path.split(path)
    return path_parts(p) + [f] if f and p else [p] if p else []


def createFile(file: str, content: str, file_encoding: str) -> bool:
    """
    create the directory path to a file, and the file itself.
    on error: cleanup all created subdirectories in the process
    return True if the operation was successful.
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
    Simply writes the content into every file in the given list
    if there is a valid content,
    returns a list of all files, that could succesfully be written.
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
    Takes a list of files, waits for a String from
    the standard input and writes it into every file.
    returns a list of all files, that could succesfully be written.
    """
    if len(file_list) == 0:
        return file_list

    print('The given FILE(s)', end='')
    print('', *file_list, sep='\n\t')
    print("do/does not exist. Write the FILE(s) and finish with the '^Z'-suffix ((Ctrl + Z) + Enter):")

    input = getStdInContent(oneLine)

    return writeFiles(file_list, input, file_encoding)
