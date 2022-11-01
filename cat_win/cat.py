import pyperclip3 as pc
import sys
from os import path, remove
from datetime import datetime
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


def _getLinePrefix(index, line_num):
    file_prefix = Fore.GREEN if ArgParser.COLOR_ENCODING else ""
    if len(holder.files) > 1:
        file_prefix += (str(index) + (" " * (holder.fileMaxLength - len(str(index)))) + ".")

    line_prefix = str(line_num) + ") " + (" " * (holder.fileLineMaxLength - len(str(line_num))))

    return file_prefix + line_prefix + Style.RESET_ALL


def printFile(content):
    if not ArgParser.FILE_SEARCH:
        print(*content, sep="\n")
        return

    for line in content:
        found_list = []
        for keyword in ArgParser.FILE_SEARCH:
            if not keyword in line:
                continue
            found_list.append(keyword)
            if ArgParser.COLOR_ENCODING:
                search_location = line.find(keyword)
                line = line[:search_location] + Fore.RED + keyword + \
                    Style.RESET_ALL + line[search_location+len(keyword):]

        print(line)
        if found_list:
            if ArgParser.COLOR_ENCODING:
                print(Fore.MAGENTA)
            print("--------------- Found", found_list, "---------------")
            print(Style.RESET_ALL)

            try:  # fails when using -i mode, because the stdin will send en EOF char to input without prompting the user
                input()
            except EOFError:
                pass


def editFile(fileIndex=1):
    show_bytecode = False
    content = []
    try:
        with open(holder.files[fileIndex-1], 'r', encoding=ArgParser.FILE_ENCODING) as f:
            content = f.read().splitlines()
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
                content = f.read().splitlines()
            show_bytecode = True
        except:
            print("Operation failed! Try using the enc=X parameter.")
            return
    fLength = len(content)
    if not show_bytecode:
        for i, arg in enumerate(holder.args_id):
            if arg == ARGS_NUMBER:
                content = [_getLinePrefix(fileIndex, holder.fileCount -
                                          j if holder.reversed else holder.fileCount+j+1) + c for j, c in enumerate(content)]
                holder.fileCount += (-fLength if holder.reversed else fLength)
            if arg == ARGS_ENDS:
                content = [c + (Back.YELLOW if ArgParser.COLOR_ENCODING else "") + "$" +
                           Style.RESET_ALL for c in content]
            if arg == ARGS_TABS:
                content = [c.replace("\t", (Back.YELLOW if ArgParser.COLOR_ENCODING else "") + "^I" +
                                     Style.RESET_ALL) for c in content]
            if arg == ARGS_SQUEEZE:
                content = [g[0] for g in groupby(content)]
            if arg == ARGS_REVERSE:
                content.reverse()
            if arg == ARGS_BLANK:
                content = [c for c in content if c]
            if arg == ARGS_DEC:
                if holder.args[i][1] == "-dec":
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromDEC(int(c), True) +
                               Style.RESET_ALL for c in content if converter.is_dec(c)]
                else:
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromDEC(int(c)) +
                               Style.RESET_ALL for c in content if converter.is_dec(c)]
            if arg == ARGS_HEX:
                if holder.args[i][1] == "-hex":
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromHEX(c, True) +
                               Style.RESET_ALL for c in content if converter.is_hex(c)]
                else:
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromHEX(c) +
                               Style.RESET_ALL for c in content if converter.is_hex(c)]
            if arg == ARGS_BIN:
                if holder.args[i][1] == "-bin":
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromBIN(c, True) +
                               Style.RESET_ALL for c in content if converter.is_bin(c)]
                else:
                    content = [c + (Fore.CYAN if ArgParser.COLOR_ENCODING else "") + converter._fromBIN(c) +
                               Style.RESET_ALL for c in content if converter.is_bin(c)]
            if arg == ARGS_CUT:
                try:
                    content = [eval(repr(c) + holder.args[i][1])
                               for c in content]
                except:
                    print("Error at operation: ", holder.args[i][1])
                    return
            if arg == ARGS_REPLACE:
                replace_values = holder.args[i][1][1:-1].split(";")
                content = [c.replace(replace_values[0], (Fore.YELLOW if ArgParser.COLOR_ENCODING else "") + replace_values[1] + Style.RESET_ALL)
                           for c in content]

    printFile(content)

    if not show_bytecode:
        if ARGS_CLIP in holder.args_id:
            holder.clipBoard += "\n".join(content)


def editFiles():
    start = len(holder.files)-1 if holder.reversed else 0
    end = -1 if holder.reversed else len(holder.files)
    if ARGS_CHECKSUM in holder.args_id:
        for file in holder.files:
            if ArgParser.COLOR_ENCODING:
                print(Fore.CYAN)
            print("Checksum of '" + file + "':")
            print(checksum.getChecksumFromFile(file))
            print(Style.RESET_ALL)
    else:
        for i in range(start, end, -1 if holder.reversed else 1):
            editFile(i+1)
        if ArgParser.COLOR_ENCODING:
            print(Fore.CYAN)
        if ARGS_COUNT in holder.args_id:
            print()
            print("Lines: " + str(holder.lineSum))
        if ARGS_FILES in holder.args_id:
            print()
            print("applied FILE(s):", end="")
            print("", *holder.files, sep="\n\t")
        print(Style.RESET_ALL)
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
