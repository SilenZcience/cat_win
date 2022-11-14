import pyperclip3 as pc
import sys
from os import path, remove, stat
from datetime import datetime
from functools import cache
from itertools import groupby
from colorama import init as coloramaInit
from colorama import Fore, Back, Style
from math import log, pow, floor
from datetime import datetime
from re import finditer

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
             'found_keyword': Fore.RED, 'found_message': Fore.MAGENTA, 'found_reset': Fore.RESET,
             'rfound_keyword': Back.LIGHTCYAN_EX, 'rfound_message': Fore.LIGHTCYAN_EX, 'rfound_reset': Back.RESET,
             'checksum': Fore.CYAN, 'count_and_files': Fore.CYAN}
converter = Converter.Converter()
holder = Holder.Holder()

def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if ARGS_DEBUG in holder.args_id:
        debug_hook(exception_type, exception, traceback)
        return
    print("\nError: {} {}".format(exception_type.__name__, exception))

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
    print("search match(es): ", end="")
    print(ArgParser.RFILE_SEARCH)
    print("colored output: ", end="")
    print(ArgParser.COLOR_ENCODING)

def _convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def _showMeta(files: list):
    stats = 0
    for file in files:
        try:
            stats = stat(file)
            print(file)
            
            print(f'{"Size:": <16}{_convert_size(stats.st_size)}')
            print(f'{"AccessTime:": <16}{  datetime.fromtimestamp(stats.st_atime)}')
            print(f'{"ModifiedTime:": <16}{datetime.fromtimestamp(stats.st_mtime)}')
            print(f'{"CreationTime:": <16}{datetime.fromtimestamp(stats.st_ctime)}')
            print()
        except OSError:
            continue
        
    sys.exit(0)

@cache
def _CalculatePrefixSpacing(fileCharLength: int, lineCharLength: int, includeFilePrefix: bool) -> str:
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


def _optimizeIntervals(intervals: list[list]) -> list[list]:
    """\
        Merge overlapping intervalls for partially
        color encoded lines. Needed when multiple
        search-keywords apply to the same line.
    """
    if not intervals:
        return []
    intervals.sort()
    stack = []
    stack.append(intervals[0])
    for interval in intervals:
        if stack[-1][0] <= interval[0] <= stack[-1][-1]:
            stack[-1][-1] = max(stack[-1][-1], interval[-1])
        else:
            stack.append(interval)
    # stack.reverse()
    return stack

def _mergeKeywordIntervals(fList: list[list], rfList: list[list]) -> list[list]:
    kwList = []
    for f in fList:
        kwList.append([f[0], "found_keyword"])
        kwList.append([f[1], "found_reset"])
    for rf in rfList:
        kwList.append([rf[0], "rfound_keyword"])
        kwList.append([rf[1], "rfound_reset"])
    kwList.sort()
    kwList.reverse()
    return kwList

def printFile(content: list, bytecode: bool):
    if (not ArgParser.FILE_SEARCH and not ArgParser.RFILE_SEARCH) or bytecode:
        print(*[(c[0] if bytecode else c[1] + c[0]) for c in content], sep="\n")
        return
    
    for line, line_number in content:
        found_list = []
        found_position = []
        rfound_list = []
        rfound_positions = []
        for keyword in ArgParser.FILE_SEARCH:
            if not keyword in line:
                continue
            found_list.append(keyword)
            if not ArgParser.COLOR_ENCODING:
                continue
            search_location = line.find(keyword)
            found_position.append([search_location, search_location+len(keyword)])
        
        found_position = _optimizeIntervals(found_position)
        
        for keyword in ArgParser.RFILE_SEARCH:
            try:
                for match in finditer(fr'{keyword}', line):
                    rfound_list.append(keyword)
                    rfound_positions.append(list(match.span()))
            except:
                print()
                raise Exception("RegEx Error")
                
        rfound_positions = _optimizeIntervals(rfound_positions)
        
        kw_positions = _mergeKeywordIntervals(found_position, rfound_positions)
        
        for kw_pos, kw_code in kw_positions:
            line = line[:kw_pos] + color_dic[kw_code] + line[kw_pos:]
        
        print(line_number + line)
        
        found_sth = False
        if found_list:
            print(color_dic["found_message"], end="")
            print("--------------- Found", found_list, "---------------")
            print(color_dic["reset"], end="")
            found_sth = True
        if rfound_list:
            print(color_dic["rfound_message"], end="")
            print("--------------- RFound", rfound_list, "---------------")
            print(color_dic["reset"], end="")
            found_sth = True

        if found_sth:
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
    
    if ARGS_DATA in holder.args_id:
        _showMeta(holder.files)
    # print the cat-output
    editFiles()

    # clean-up
    if path.exists(temp_file):
        remove(temp_file)


if __name__ == "__main__":
    main()
# pyinstaller cat.py --onefile --clean --dist ../bin
