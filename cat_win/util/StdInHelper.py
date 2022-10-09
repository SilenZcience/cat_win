from sys import stdin
from tempfile import NamedTemporaryFile

def writeTemp(content: str):
    """
    Writes content into a generated temp-file and
    returns the path in type String.
    """
    tmp_file = NamedTemporaryFile(delete=False).name
    with open(tmp_file, 'w') as f:
        f.write(content)
    return tmp_file

def getStdInContent():
    """
    returns a String delivered by the standard input.
    """
    input = ""
    for line in stdin:
        input += line
    return input
    
def writeFiles(file_list: list, content: str):
    """
    Simply writes the content into every
    file in the given list if there is a
    valid content.
    """
    if content == "": file_list.clear()
    for file in file_list:
        with open(file, 'w') as f:
            f.write(content)
    
    
def readWriteFilesFromStdIn(file_list: list):
    """
    Takes a list of files, waits for a String from
    the standard input and writes it into every file.
    """
    if len(file_list) == 0: return
    
    print("The given FILE(s)", end="")
    print("", *file_list, sep="\n\t")
    print("do/does not exist. Write the FILE(s) and finish with the '^Z'-suffix ((Ctrl + Z) + Enter):")
    
    input =  getStdInContent()
    input = input.rstrip()
    if len(input) > 0 and ord(input[-1:]) == 26: input = input[:-1]
    
    writeFiles(file_list, input)