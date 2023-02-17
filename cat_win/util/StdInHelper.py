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
    input = ""
    for line in stdin:
        if line[-2:] == chr(26) + '\n':
            input += line[:-2]
            break
        input += line
    return input


def writeFiles(file_list: list, content: str, file_encoding: str) -> None:
    """
    Simply writes the content into every
    file in the given list if there is a
    valid content.
    """
    if len(file_list) == 0:
        return
    
    if content == "":
        abort_command = "" 
        try:
            print("You are about to create an empty file. Do you want to continue?")
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
                print("Aborting...")
                file_list.clear()
        
    for file in file_list:
        with open(file, 'w', encoding=file_encoding) as f:
            f.write(content)


def readWriteFilesFromStdIn(file_list: list, file_encoding: str, oneLine: bool = False) -> None:
    """
    Takes a list of files, waits for a String from
    the standard input and writes it into every file.
    """
    if len(file_list) == 0:
        return

    print("The given FILE(s)", end="")
    print("", *file_list, sep="\n\t")
    print("do/does not exist. Write the FILE(s) and finish with the '^Z'-suffix ((Ctrl + Z) + Enter):")

    input = getStdInContent(oneLine)

    writeFiles(file_list, input, file_encoding)
