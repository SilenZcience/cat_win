import pyperclip3 as pc
import sys
import os
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from colorama import init as coloramaInit

import cat_win.persistence.Config as Config
import cat_win.util.ArgParser as ArgParser
import cat_win.util.checksum as checksum
import cat_win.util.Converter as Converter
import cat_win.util.Holder as Holder
import cat_win.util.StdInHelper as StdInHelper
import cat_win.util.StringFinder as StringFinder
from cat_win.util.ArgConstants import *
from cat_win.util.ColorConstants import C_KW
from cat_win.util.FileAttributes import getFileMetaData
from cat_win.web.UpdateChecker import printUpdateInformation

from cat_win import __version__, __author__, __sysversion__
workingDir = os.path.dirname(os.path.realpath(__file__))

coloramaInit()
config = Config.Config(workingDir)

color_dic = config.loadConfig()

converter = Converter.Converter()
holder = Holder.Holder()


def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if holder.args_id[ARGS_DEBUG]:
        debug_hook(exception_type, exception, traceback)
        return
    print("\nError: {} {}".format(exception_type.__name__, exception))


sys.excepthook = exception_handler


def _showHelp() -> None:
    """
    Show the Help message and exit.
    """
    print("Usage: cat [FILE]... [OPTION]...")
    print("Concatenate FILE(s) to standard output.")
    print()
    for x in ALL_ARGS:
        print("%-25s" % str("\t" + x.shortForm + ", " + x.longForm), end=x.help + "\n")
    print()
    print("%-25s" % str("\t'enc=X':"), end="set file encoding to X\n")
    print("%-25s" % str("\t'find=X':"), end="find substring X in the given files\n")
    print("%-25s" % str("\t'match=X':"), end="find pattern X in the given files\n")
    print("%-25s" % str("\t'trunc=X:Y':"), end="truncate file to lines X and Y (python-like)\n")
    print()
    print("%-25s" % str("\t'[a,b]':"), end="replace a with b in every line\n")
    print("%-25s" % str("\t'[a:b]':"), end="python-like string manipulation syntax\n")
    print()
    print("Examples:")
    print("%-25s" % str("\tcat f g -r"), end="Output g's contents in reverse order, then f's content in reverse order\n")
    print("%-25s" % str("\tcat f g -ne"), end="Output f's, then g's content, while numerating and showing the end of lines\n")
    printUpdateInformation('cat_win', __version__)
    sys.exit(0)


def _showVersion() -> None:
    """
    Show the Version message and exit.
    """
    print()
    print("------------------------------------------------------------")
    print(f"Cat {__version__} - from {workingDir}")
    print("------------------------------------------------------------")
    print()
    print(f"Python: \t{__sysversion__}")  # sys.version
    print(f"Build time: \t{datetime.fromtimestamp(os.path.getctime(os.path.realpath(__file__)))} CET")
    print(f"Author: \t{__author__}")
    printUpdateInformation('cat_win', __version__)
    sys.exit(0)


def _showDebug(args: list, known_files: list, unknown_files: list) -> None:
    """
    Print all neccassary debug information
    """
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
    print(ArgParser.FILE_MATCH)
    print("truncate file: ", end="")
    print(ArgParser.FILE_TRUNCATE)


def _printMeta(file: str) -> None:
    metaData = getFileMetaData(file, {C_KW.RESET_ALL: color_dic[C_KW.RESET_ALL],
                                      C_KW.ATTRIB: color_dic[C_KW.ATTRIB],
                                      C_KW.ATTRIB_POSITIVE: color_dic[C_KW.ATTRIB_POSITIVE],
                                      C_KW.ATTRIB_NEGATIVE: color_dic[C_KW.ATTRIB_NEGATIVE]})
    print(metaData)


def _printChecksum(file: str) -> None:
    print(color_dic[C_KW.CHECKSUM], end="")
    print("Checksum of '" + file + "':")
    print(checksum.getChecksumFromFile(file))
    print(color_dic[C_KW.RESET_ALL], end="")


def _printMetaAndChecksum(showMeta: bool, showChecksum: bool) -> None:
    for file in holder.files:
        if showMeta:
            _printMeta(file)
        if showChecksum:
            _printChecksum(file)
    if showMeta or showChecksum:
        sys.exit(0)


@lru_cache(maxsize=None)
def _CalculateLinePrefixSpacing(fileCharLength: int, lineCharLength: int, includeFilePrefix: bool) -> str:
    line_prefix = (" " * (holder.fileLineNumberPlaceHolder - lineCharLength)) + "%i) "

    if includeFilePrefix:
        file_prefix = (" " * (holder.fileNumberPlaceHolder - fileCharLength)) + "%i."
        return color_dic[C_KW.NUMBER] + file_prefix + line_prefix + color_dic[C_KW.RESET_ALL]

    return color_dic[C_KW.NUMBER] + line_prefix + color_dic[C_KW.RESET_ALL]


def _getLinePrefix(index: int, line_num: int) -> str:
    """
    returns the new line prefix including the line number.
    """
    if len(holder.files) > 1:
        return _CalculateLinePrefixSpacing(len(str(index)), len(str(line_num)), True) % (index, line_num)
    return _CalculateLinePrefixSpacing(len(str(index)), len(str(line_num)), False) % (line_num)


@lru_cache(maxsize=None)
def _CalculateLineLengthPrefixSpacing(lineCharLength: int) -> str:
    lengthPrefix = '[' + ' ' * (holder.fileLineLengthPlaceHolder - lineCharLength) + '%i] '
    return '%s' + color_dic[C_KW.LINE_LENGTH] + lengthPrefix + color_dic[C_KW.RESET_ALL]


def _getLineLengthPrefix(prefix: str, line) -> str:
    """
    prefix is the current prefix.
    line is of type string or bytes.
    returns the new line prefix including the line length.
    """
    return _CalculateLineLengthPrefixSpacing(len(str(len(line)))) % (prefix, len(line))


def printFile(content: list, bytecode: bool) -> None:
    if not (ArgParser.FILE_SEARCH or ArgParser.FILE_MATCH) or bytecode:
        print(*[prefix + line for prefix, line in content], sep="\n")
        return

    stringFinder = StringFinder.StringFinder(
        ArgParser.FILE_SEARCH, ArgParser.FILE_MATCH)

    for line_prefix, line in content:
        intervals, fKeyWords, mKeywords = stringFinder.findKeywords(line)

        if not holder.args_id[ARGS_NOCOL]:
            for kw_pos, kw_code in intervals:
                line = line[:kw_pos] + color_dic[kw_code] + line[kw_pos:]

        print(line_prefix + line)

        found_sth = False
        if fKeyWords:
            print(color_dic[C_KW.FOUND_MESSAGE], end="")
            print("--------------- Found", fKeyWords, "---------------")
            print(color_dic[C_KW.RESET_ALL], end="")
            found_sth = True
        if mKeywords:
            print(color_dic[C_KW.MATCHED_MESSAGE], end="")
            print("--------------- Matched", mKeywords, "---------------")
            print(color_dic[C_KW.RESET_ALL], end="")
            found_sth = True

        if found_sth:
            try:  # fails when using -i mode, because the stdin will send en EOF char to input without prompting the user
                input()
            except EOFError:
                pass


def printExcludedByPeek(excludedByPeek: int, prefixLenght: int) -> None:
    if not excludedByPeek:
        return
    excludedByPeekLength = (len(str(excludedByPeek))-1)//2
    excludedByPeekIndent = " " * (prefixLenght - excludedByPeekLength + 10)
    excludedByPeekIndentAdd = " " * excludedByPeekLength
    print(color_dic[C_KW.NUMBER], end="")
    print(excludedByPeekIndent, excludedByPeekIndentAdd, " •", sep="")
    print(excludedByPeekIndent, "(", excludedByPeek, ")", sep="")
    print(excludedByPeekIndent, excludedByPeekIndentAdd, " •", sep="", end="")
    print(color_dic[C_KW.RESET_ALL])


def editFile(fileIndex: int = 1) -> None:
    show_bytecode = False
    excludedByPeek = 0
    content = [('', '')]
    try:
        with open(holder.files[fileIndex-1], 'r', encoding=ArgParser.FILE_ENCODING) as f:
            content = [('', line) for line in f.read().splitlines()]
    except:
        print("Failed to open:", holder.files[fileIndex-1])
        print("Do you want to open the file as a binary without parameters? [Y]")
        try:
            inp = input()
            if not 'Y' in inp.upper():
                return
        except EOFError:
            pass
        try:
            with open(holder.files[fileIndex-1], 'rb') as f:
                content = [('', line) for line in f.read().splitlines()]
            show_bytecode = True
        except:
            print("Operation failed! Try using the enc=X parameter.")
            return
    
    if holder.args_id[ARGS_NUMBER]:
        content = [(_getLinePrefix(fileIndex, j), c[1])
                   for j, c in enumerate(content, start=1)]
    content = content[ArgParser.FILE_TRUNCATE[0]:ArgParser.FILE_TRUNCATE[1]:ArgParser.FILE_TRUNCATE[2]]
    if holder.args_id[ARGS_PEEK] and len(content) > 10:
        excludedByPeek = len(content) - 10
        content = content[:5] + content[-5:]

    if not show_bytecode:
        for arg, param in holder.args:
            if arg == ARGS_CUT:
                try:
                    content = [(prefix, eval(repr(line) + param))
                                for prefix, line in content]
                except:
                    print("Error at operation: ", param)
                    return
        
        for arg, param in holder.args:
            if arg == ARGS_ENDS:
                content = [(prefix, line + color_dic[C_KW.ENDS] + "$" + color_dic[C_KW.RESET_ALL])
                           for prefix, line in content]
            elif arg == ARGS_TABS:
                content = [(prefix, line.replace("\t", color_dic[C_KW.TABS] + "^I" + color_dic[C_KW.RESET_ALL]))
                           for prefix, line in content]
            elif arg == ARGS_SQUEEZE:
                content = [list(group)[0] for _, group in groupby(content, lambda x: x[1])]
            elif arg == ARGS_REVERSE:
                content.reverse()
            elif arg == ARGS_BLANK:
                content = [c for c in content if c[1]]
            elif arg == ARGS_DEC:
                content = [(prefix, line + color_dic[C_KW.CONVERSION] + converter._fromDEC(int(line), (param == "-dec")) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_dec(line)]
            elif arg == ARGS_HEX:
                content = [(prefix, line + color_dic[C_KW.CONVERSION] + converter._fromHEX(line, (param == "-hex")) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_hex(line)]
            elif arg == ARGS_BIN:
                content = [(prefix, line + color_dic[C_KW.CONVERSION] + converter._fromBIN(line, (param == "-bin")) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_bin(line)]
            elif arg == ARGS_REPLACE:
                replace_values = param[1:-1].split(",")
                content = [(prefix, line.replace(replace_values[0], color_dic[C_KW.REPLACE] + replace_values[1] + color_dic[C_KW.RESET_ALL]))
                           for prefix, line  in content]
                
    if holder.args_id[ARGS_LLENGTH]:
        content = [(_getLineLengthPrefix(c[0], c[1]), c[1]) for c in content]
    if show_bytecode:
        content = [(prefix, str(line)) for prefix, line in content]
    
    printFile(content[:5], show_bytecode)
    if excludedByPeek:
        prefix = content[0][0]
        prefix = prefix.replace(color_dic[C_KW.NUMBER], '')
        prefix = prefix.replace(color_dic[C_KW.LINE_LENGTH], '')
        prefix = prefix.replace(color_dic[C_KW.RESET_ALL], '')
        printExcludedByPeek(excludedByPeek, len(prefix))
    printFile(content[5:], show_bytecode)

    if not show_bytecode:
        if holder.args_id[ARGS_CLIP]:
            holder.clipBoard += "\n".join([prefix + line for prefix, line in content])


def editFiles() -> None:
    start = len(holder.files)-1 if holder.reversed else 0
    end = -1 if holder.reversed else len(holder.files)

    for i in range(start, end, -1 if holder.reversed else 1):
        editFile(i+1)
    print(color_dic[C_KW.COUNT_AND_FILES], end="")
    if holder.args_id[ARGS_COUNT]:
        print()
        print("Lines: " + str(holder.allFilesLinesSum))
    if holder.args_id[ARGS_FILES]:
        print()
        print("applied FILE(s):", end="")
        print("", *holder.getAppliedFiles(), sep="\n\t")
    print(color_dic[C_KW.RESET_ALL], end="")
    if holder.args_id[ARGS_CLIP]:
        pc.copy(holder.clipBoard)


def main():
    piped_input = temp_file = ""

    # read parameter-args
    args, known_files, unknown_files = ArgParser.getArguments()

    holder.setArgs(args)

    sys.stdout.reconfigure(encoding=ArgParser.FILE_ENCODING)
    sys.stdin.reconfigure(encoding=ArgParser.FILE_ENCODING)
    
    # check for special cases
    if holder.args_id[ARGS_DEBUG]:
        _showDebug(args, known_files, unknown_files)
    if (len(known_files) + len(unknown_files) + len(holder.args) == 0) or holder.args_id[ARGS_HELP]:
        _showHelp()
    if holder.args_id[ARGS_VERSION]:
        _showVersion()
    if holder.args_id[ARGS_CONFIG]:
        config.saveConfig()
        sys.exit(0)
    if holder.args_id[ARGS_INTERACTIVE]:
        piped_input = StdInHelper.getStdInContent(holder.args_id[ARGS_ONELINE])
        temp_file = StdInHelper.writeTemp(piped_input, ArgParser.FILE_ENCODING)
        known_files.append(temp_file)
        StdInHelper.writeFiles(unknown_files, piped_input, ArgParser.FILE_ENCODING)
        holder.setTempFile(temp_file)
    else:
        StdInHelper.readWriteFilesFromStdIn(
            unknown_files, ArgParser.FILE_ENCODING, holder.args_id[ARGS_ONELINE])

    if (len(known_files) + len(unknown_files) == 0):
        sys.exit(0)
    
    if holder.args_id[ARGS_NOCOL]:
        global color_dic
        color_dic = dict.fromkeys(color_dic, "")

    # fill holder object with neccessary values
    holder.setFiles([*known_files, *unknown_files])

    _printMetaAndChecksum(holder.args_id[ARGS_DATA], holder.args_id[ARGS_CHECKSUM])

    holder.generateValues()

    try:
        editFiles()  # print the cat-output
    except Exception as exception:
        if isinstance(exception, IOError):  # catch broken-pipe error
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)  # Python exits with error code 1 on EPIPE
        pass

    # clean-up
    if temp_file and os.path.exists(temp_file):
        os.remove(temp_file)


if __name__ == "__main__":
    main()
# pyinstaller cat.py --onefile --clean --dist ../bin
