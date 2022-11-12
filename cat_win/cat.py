import pyperclip3 as pc
import sys
from os import path, remove
from datetime import datetime
from functools import cache
from itertools import groupby
from colorama import init as coloramaInit
from colorama import Fore, Back, Style

import cat_win.util.ArgParser as ArgParser
import cat_win.util.checksum as checksum
import cat_win.util.Converter as Converter
import cat_win.util.Holder as Holder
import cat_win.util.StdInHelper as StdInHelper
from cat_win.util.ArgConstants import *

from cat_win import __version__, __author__, __sysversion__

coloramaInit()
color_dic = {'reset': Style.RESET_ALL, 'number': Fore.GREEN, 'ends': Back.YELLOW, 
             'tabs': Back.YELLOW, 'conversion': Fore.CYAN, 'replace': Fore.YELLOW, 
             'found_keyword': Fore.RED, 'found_message': Fore.MAGENTA,
             'checksum': Fore.CYAN, 'count_and_files': Fore.CYAN}
converter = Converter.Converter()
holder = Holder.Holder()

def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if ARGS_DEBUG in holder.args_id:
        debug_hook(exception_type, exception, traceback)
        return
    print("\nError: {}".format(exception_type.__name__))

sys.excepthook = exception_handler

def _showHelp():
    print("Usage: cat [FILE]... [OPTION]...")
    print("Concatenate FILE(s) to standard output.")
    print()
    for x in ALL_ARGS:
        print("%-25s" % str("\t" + x.shortForm + ", " + x.longForm), end=x.help + "\n")
    print()
    print("%-25s" % str("\t-col, --color:"), end="show colored output\n")
    print()
    print("%-25s" % str("\t'enc=X':"), end="set file encoding to X\n")
    print("%-25s" % str("\t'find=X':"), end="find X in the given files\n")
    print()
    print("%-25s" % str("\t'[a;b]':"), end="replace a with b in every line\n")
    print("%-25s" % str("\t'[a:b]':"), end="python-like string manipulation syntax\n")
    print()
    print("Examples:")
    print("%-25s" % str("\tcat f g -r"), end="Output g's contents in reverse order, then f's content in reverse order\n")
    print("%-25s" % str("\tcat f g -ne"), end="Output f's, then g's content, while numerating and showing the end of lines\n")
    sys.exit(0)


def _showVersion():
    print()
    print("------------------------------------------------------------")
    print(f"Cat {__version__} - from {path.dirname(path.realpath(__file__))}")
    print("------------------------------------------------------------")
    print()
    print(f"Python: \t{__sysversion__}")  # sys.version
    print(f"Build time: \t{datetime.fromtimestamp(path.getctime(path.realpath(__file__)))} CET")
    print(f"Author: \t{__author__}")
    sys.exit(0)


def _showDebug(args, known_files, unknown_files):
    print("Debug Information:")
    print("args: ", end="")
    print(args)
    print("known_files: ", end="")
    print(known_files)
    print("unknown_files: ", end="")
    print(unknown_files)
    print("file encoding: ", end="")
    print(ArgParser.FILE_ENCODING)
    print("search keyword(s): ", end="")
    print(ArgParser.FILE_SEARCH)
    print("colored output: ", end="")
    print(ArgParser.COLOR_ENCODING)

@cache
def _CalculatePrefixSpacing(fileCharLength, lineCharLength, includeFilePrefix):
    file_prefix = color_dic["number"]
    if includeFilePrefix:
        file_prefix += "%i"
        file_prefix += (" " * (holder.fileMaxLength - fileCharLength)) + "."

    line_prefix = "%i) " + (" " * (holder.fileLineMaxLength - lineCharLength))

    return file_prefix + line_prefix + color_dic["reset"]

def _getLinePrefix(index: int, line_num: int) -> str:
    if len(holder.files) > 1:
        return _CalculatePrefixSpacing(len(str(index)), len(str(line_num)), True)  % (index, line_num)
    return _CalculatePrefixSpacing(len(str(index)), len(str(line_num)), False)  % (line_num)


def printFile(content: list, bytecode: bool):
    if not ArgParser.FILE_SEARCH or bytecode:
        print(*[(c[0] if bytecode else c[1] + c[0]) for c in content], sep="\n")
        return
    
    for line, line_number in content:
        found_list = []
        for keyword in ArgParser.FILE_SEARCH:
            if not keyword in line:
                continue
            found_list.append(keyword)
            if not ArgParser.COLOR_ENCODING:
                continue
            search_location = line.find(keyword)
            line = line[:search_location] + color_dic["found_keyword"] + keyword + \
                color_dic["reset"] + line[search_location+len(keyword):]

        print(line_number + line)
        if found_list:
            print(color_dic["found_message"], end="")
            print("--------------- Found", found_list, "---------------")
            print(color_dic["reset"], end="")

            try:  # fails when using -i mode, because the stdin will send en EOF char to input without prompting the user
                input()
            except EOFError:
                pass


def editFile(fileIndex: int = 1):
    show_bytecode = False
    content = [["",""]]
    try:
        with open(holder.files[fileIndex-1], 'r', encoding=ArgParser.FILE_ENCODING) as f:
            content = [[line, ""] for line in f.read().splitlines()]
    except:
        print("Failed to open:", holder.files[fileIndex-1])
        print(
            "Do you want to open the file as a binary without parameters? [Y]")
        try:
            inp = input()
            if not 'y' in inp and not 'Y' in inp:
                return
        except EOFError:
            pass
        try:
            with open(holder.files[fileIndex-1], 'rb') as f:
                content = [[line, ""] for line in f.read().splitlines()]
            show_bytecode = True
        except:
            print("Operation failed! Try using the enc=X parameter.")
            return

    if not show_bytecode:     
        if ARGS_NUMBER in holder.args_id:
            content = [[c[0], _getLinePrefix(fileIndex, j)] for j, c in enumerate(content, start=1)]
        for i, arg in enumerate(holder.args_id):
            if arg == ARGS_ENDS:
                content = [[c[0] + color_dic["ends"] + "$" +
                           color_dic["reset"], c[1]] for c in content]
            if arg == ARGS_TABS:
                content = [[c[0].replace("\t", color_dic["tabs"] + "^I" +
                                     color_dic["reset"]), c[1]] for c in content]
            if arg == ARGS_SQUEEZE:
                content = [list(group)[0] for _, group in groupby(content, lambda x: x[0])]
            if arg == ARGS_REVERSE:
                content.reverse()
            if arg == ARGS_BLANK:
                content = [[c[0], c[1]] for c in content if c[0]]
            if arg == ARGS_DEC:
                if holder.args[i][1] == "-dec":
                    content = [[c[0] + color_dic["conversion"] + converter._fromDEC(int(c[0]), True) +
                               color_dic["reset"], c[1]] for c in content if converter.is_dec(c[0])]
                else:
                    content = [[c[0] + color_dic["conversion"] + converter._fromDEC(int(c[0])) +
                               color_dic["reset"], c[1]] for c in content if converter.is_dec(c[0])]
            if arg == ARGS_HEX:
                if holder.args[i][1] == "-hex":
                    content = [[c[0] + color_dic["conversion"] + converter._fromHEX(c[0], True) +
                               color_dic["reset"], c[1]] for c in content if converter.is_hex(c[0])]
                else:
                    content = [[c[0] + color_dic["conversion"] + converter._fromHEX(c[0]) +
                               color_dic["reset"], c[1]] for c in content if converter.is_hex(c[0])]
            if arg == ARGS_BIN:
                if holder.args[i][1] == "-bin":
                    content = [[c[0] + color_dic["conversion"] + converter._fromBIN(c[0], True) +
                               color_dic["reset"], c[1]] for c in content if converter.is_bin(c[0])]
                else:
                    content = [[c[0] + color_dic["conversion"] + converter._fromBIN(c[0]) +
                               color_dic["reset"], c[1]] for c in content if converter.is_bin(c[0])]
            if arg == ARGS_CUT:
                try:
                    content = [[eval(repr(c[0]) + holder.args[i][1]), c[1]]
                               for c in content]
                except:
                    print("Error at operation: ", holder.args[i][1])
                    return
            if arg == ARGS_REPLACE:
                replace_values = holder.args[i][1][1:-1].split(";")
                content = [[c[0].replace(replace_values[0], color_dic["replace"] + replace_values[1] + color_dic["reset"]), c[1]]
                           for c in content]

    printFile(content, show_bytecode)

    if not show_bytecode:
        if ARGS_CLIP in holder.args_id:
            holder.clipBoard += "\n".join([c[1] + c[0] for c in content])


def editFiles():
    if not ArgParser.COLOR_ENCODING:
        global color_dic
        color_dic = dict.fromkeys(color_dic, "")
        
    start = len(holder.files)-1 if holder.reversed else 0
    end = -1 if holder.reversed else len(holder.files)
    if ARGS_CHECKSUM in holder.args_id:
        for file in holder.files:
            print(color_dic["checksum"], end="")
            print("Checksum of '" + file + "':")
            print(checksum.getChecksumFromFile(file))
            print(color_dic["reset"], end="")
    else:
        for i in range(start, end, -1 if holder.reversed else 1):
            editFile(i+1)
        print(color_dic["count_and_files"], end="")
        if ARGS_COUNT in holder.args_id:
            print()
            print("Lines: " + str(holder.lineSum))
        if ARGS_FILES in holder.args_id:
            print()
            print("applied FILE(s):", end="")
            print("", *holder.getAppliedFiles(), sep="\n\t")
        print(color_dic["reset"], end="")
        if ARGS_CLIP in holder.args_id:
            pc.copy(holder.clipBoard)


def main():
    piped_input = temp_file = ""

    # read parameter-args
    args, known_files, unknown_files = ArgParser.getArguments()
    global holder
    holder.setArgs(args)

    sys.stdout.reconfigure(encoding=ArgParser.FILE_ENCODING)
    sys.stdin.reconfigure(encoding=ArgParser.FILE_ENCODING)

    # check for special cases
    if (len(known_files) == 0 and len(unknown_files) == 0 and len(holder.args) == 0) or ARGS_HELP in holder.args_id:
        _showHelp()
    if ARGS_VERSION in holder.args_id:
        _showVersion()
    if ARGS_DEBUG in holder.args_id:
        _showDebug(args, known_files, unknown_files)
    if ARGS_INTERACTIVE in holder.args_id:
        piped_input = StdInHelper.getStdInContent()
        temp_file = StdInHelper.writeTemp(piped_input, ArgParser.FILE_ENCODING)
        known_files.append(temp_file)
        StdInHelper.writeFiles(unknown_files, piped_input,
                               ArgParser.FILE_ENCODING)
        holder.setTempFile(temp_file)
    else:
        StdInHelper.readWriteFilesFromStdIn(
            unknown_files, ArgParser.FILE_ENCODING)

    # fill holder object with neccessary values
    holder.setFiles([*known_files, *unknown_files])
    holder.generateValues()
    
    # print the cat-output
    editFiles()

    # clean-up
    if path.exists(temp_file):
        remove(temp_file)


if __name__ == "__main__":
    main()
# pyinstaller cat.py --onefile --clean --dist ../bin
