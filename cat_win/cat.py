try:
    from colorama import init as coloramaInit
except ImportError:
    nop = lambda *_, **__: None; coloramaInit = nop
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from platform import system
from re import sub as resub
import os
import sys

from cat_win.const.ArgConstants import *
from cat_win.const.ColorConstants import C_KW
from cat_win.util.Base64 import decodeBase64, encodeBase64
from cat_win.util.FileAttributes import getFileMetaData, getFileSize, _convert_size
from cat_win.util.RawViewer import getRawViewLinesGen
from cat_win.web.UpdateChecker import printUpdateInformation
import cat_win.persistence.Config as Config
import cat_win.util.ArgParser as ArgParser
import cat_win.util.checksum as checksum
import cat_win.util.Converter as Converter
import cat_win.util.Holder as Holder
import cat_win.util.StdInHelper as StdInHelper
import cat_win.util.StringFinder as StringFinder
import cat_win.util.TmpFileHelper as TmpFileHelper

from cat_win import __project__, __version__, __sysversion__, __author__, __url__
workingDir = os.path.dirname(os.path.realpath(__file__))

coloramaInit()
config = Config.Config(workingDir)

default_color_dic = config.loadConfig()
color_dic = default_color_dic.copy()

converter = Converter.Converter()
holder = Holder.Holder()
tmpFileHelper = TmpFileHelper.TmpFileHelper()

on_windows_os = (system() == 'Windows')

def exception_handler(exception_type: type, exception, traceback, debug_hook=sys.excepthook) -> None:
    try:
        print(color_dic[C_KW.RESET_ALL])
        if holder.args_id[ARGS_DEBUG]:
            debug_hook(exception_type, exception, traceback)
            return
        print(f"\n{exception_type.__name__}{':' * bool(str(exception))} {exception}")
        if exception_type != KeyboardInterrupt:
            print(f"If this Exception is unexpected, please raise an official Issue at:\n{__url__}/issues")
    except:
        debug_hook(exception_type, exception, traceback)


sys.excepthook = exception_handler


def _showHelp() -> None:
    """
    Show the Help message and exit.
    """
    helpMessage = 'Usage: catw [FILE]... [OPTION]...\n'
    helpMessage += 'Concatenate FILE(s) to standard output.\n\n'
    for arg in ALL_ARGS:
        if arg.showArg:
            helpMessage += f"\t{f'{arg.shortForm}, {arg.longForm}': <25}{arg.help}\n"
    helpMessage += '\n'
    helpMessage += f"\t{'-R, --R<stream>': <25}reconfigure the std-stream(s) with the parsed encoding\n"
    helpMessage += "\t<stream> == 'in'/'out'/'err' (default is stdin & stdout)\n"
    helpMessage += '\n'
    helpMessage += f"\t{'enc=X, enc:X'    : <25}set file encoding to X (default is utf-8)\n"
    helpMessage += f"\t{'find=X, find:X'  : <25}find/query a substring X in the given files\n"
    helpMessage += f"\t{'match=X, match:X': <25}find/query a pattern X in the given files\n"
    helpMessage += f"\t{'trunc=X:Y, trunc:X:Y': <25}truncate file to lines x and y (python-like)\n"
    helpMessage += '\n'
    helpMessage += f"\t{'[a,b]': <25}replace a with b in every line\n"
    helpMessage += f"\t{'[a:b:c]': <25}python-like string indexing syntax (line by line)\n"
    helpMessage += '\n'
    helpMessage += 'Examples:\n'
    helpMessage += f"\t{'cat f g -r' : <25}Output g's contents in reverse order, then f's content in reverse order\n"
    helpMessage += f"\t{'cat f g -ne': <25}Output f's, then g's content, while numerating and showing the end of lines\n"
    helpMessage += f"\t{'cat f trunc=a:b:c': <25}Output f's content starting at line a, ending at line b, stepping c\n"
    print(helpMessage)
    printUpdateInformation(__project__, __version__, color_dic)


def _showVersion() -> None:
    """
    Show the Version message and exit.
    """
    catVersion = f"Catw {__version__} - from {workingDir}\n"
    versionMessage = '\n'
    versionMessage += '-' * len(catVersion) + '\n'
    versionMessage += catVersion
    versionMessage += '-' * len(catVersion) + '\n'
    versionMessage += '\n'
    versionMessage += f"Built with: \tPython {__sysversion__}\n"  # sys.version
    try:
        versionMessage += f"Install time: \t{datetime.fromtimestamp(os.path.getctime(os.path.realpath(__file__)))}\n"
    except OSError: # fails on pyinstaller executable
        versionMessage += f"Install time: \t-\n"
    versionMessage += f"Author: \t{__author__}\n"
    print(versionMessage)
    printUpdateInformation(__project__, __version__, color_dic)


def _showDebug(args: list, unknown_args: list, known_files: list, unknown_files: list, echo_args: list) -> None:
    """
    Print all neccassary debug information
    """
    print('Debug Information:')
    print('args: ', end='')
    print([(arg[0], arg[1], holder.args_id[arg[0]]) for arg in args])
    print('unknown_args: ', end='')
    print(unknown_args)
    print('known_files: ', end='')
    print(known_files)
    print('unknown_files: ', end='')
    print(unknown_files)
    print('echo_args: ', end='')
    print(echo_args)
    print('file encoding: ', end='')
    print(ArgParser.FILE_ENCODING)
    print('search keyword(s): ', end='')
    print(ArgParser.FILE_SEARCH)
    print('search match(es): ', end='')
    print(ArgParser.FILE_MATCH)
    print('truncate file: ', end='')
    print(ArgParser.FILE_TRUNCATE)


def _showCount() -> None:
    """
    display the line sum of each file individually if
    ARGS_CCOUNT is specified.
    display the line sum of all files
    """
    if holder.args_id[ARGS_CCOUNT]:
        longestFileName = max(map(len, holder.allFilesLines.keys())) + 1
        print(f"{color_dic[C_KW.COUNT_AND_FILES]}{'File': <{longestFileName}}LineCount{color_dic[C_KW.RESET_ALL]}")
        for file in holder.allFilesLines.keys():
            print(f"{color_dic[C_KW.COUNT_AND_FILES]}{file: <{longestFileName}}{holder.allFilesLines[file]: >{holder.fileLineNumberPlaceHolder}}{color_dic[C_KW.RESET_ALL]}")
        print('')
    print(f"{color_dic[C_KW.COUNT_AND_FILES]}Lines (Sum): {holder.allFilesLinesSum}{color_dic[C_KW.RESET_ALL]}")


def _showFiles() -> None:
    """
    displays holder.files including their size and calculates
    their size sum.
    """
    if len(holder.files) == 0:
        return
    file_sizes = []
    msg = 'found' if holder.args_id[ARGS_FFILES] else 'applied'
    print(color_dic[C_KW.COUNT_AND_FILES], end='')
    print(f"{msg} FILE(s):", end='')
    print(color_dic[C_KW.RESET_ALL])
    for file in holder.files:
        size = getFileSize(file.path)
        file_sizes.append(size)
        print(f"\t{color_dic[C_KW.COUNT_AND_FILES]}{_convert_size(size): <10}{'*' if file.containsQueried else ' '}{file.displayname}{color_dic[C_KW.RESET_ALL]}")
    print(color_dic[C_KW.COUNT_AND_FILES], end='')
    print(f"Sum:\t{_convert_size(sum(file_sizes))}", end='')
    print(color_dic[C_KW.RESET_ALL])
    print(color_dic[C_KW.COUNT_AND_FILES], end='')
    print(f"Amount:\t{len(holder.files)}", end='')
    print(color_dic[C_KW.RESET_ALL])


def _printMeta(file: str) -> None:
    """
    print the information retrieved by getFileMetaData()
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    """
    metaData = getFileMetaData(file, on_windows_os,
                               [color_dic[C_KW.RESET_ALL],
                               color_dic[C_KW.ATTRIB],
                               color_dic[C_KW.ATTRIB_POSITIVE],
                               color_dic[C_KW.ATTRIB_NEGATIVE]])
    print(metaData)


def _printChecksum(file: str) -> None:
    """
    print the information retrieved by getChecksumFromFile()
    
    Parameters:
    file (str):
        a string representation of a file (-path)
    """
    print(f"{color_dic[C_KW.CHECKSUM]}Checksum of '{file}':{color_dic[C_KW.RESET_ALL]}")
    print(checksum.getChecksumFromFile(file, [color_dic[C_KW.CHECKSUM], color_dic[C_KW.RESET_ALL]]))


def _printMetaAndChecksum(showMeta: bool, showChecksum: bool) -> None:
    """
    calls _printMeta() and _printChecksum() on every file.
    
    Parameters:
    showMeta (bool):
        decides if the metadata of the files should be displayed
    showChecksum (bool):
        decides if the checksum of the files should be displayed
    """
    for file in holder.files:
        if showMeta:
            _printMeta(file.path)
        if showChecksum:
            _printChecksum(file.path)


def removeAnsiCodesFromLine(line: str) -> str:
    """
    Parameters:
    line (str):
        the string to clean ANSI-Colorcodes from
        
    Returns:
    (str):
        the cleaned string
    """
    # version 1: efficiency is about the same, and does not have any dependency
    # however it is not as safe in case of unusual/broken escape sequences.
    # while (codePosStart := line.find(ESC_CODE)) != -1:
    #     codePosEnd = line[codePosStart:].find('m')
    #     # here should be checks like 'codePosEnd' != -1 and
    #     # 'codePosEnd' <= 5 to make sure we found a valid EscapeSequence
    #     # for a better performance let's assume all EscapeSequences are valid...
    #     line = line[:codePosStart] + line[codePosStart+codePosEnd+1:]
    # return line
    # version 2:
    return resub(r'\x1b\[[0-9\;]*m', '', line)


# def removeAnsiCodes(content: list) -> list:
#     return [(removeAnsiCodesFromLine(prefix), removeAnsiCodesFromLine(line)) for prefix, line in content]


@lru_cache(maxsize=None)
def _CalculateLinePrefixSpacing(lineCharLength: int,
                                includeFilePrefix: bool = False, fileCharLength: int = 0) -> str:
    """
    calculate a string template for the line prefix.
    
    Parameters:
    lineCharLength (int):
        the length of the line number
    includeFilePrefix (bool):
        should the file be included in the prefix
    fileCharLength (int):
        the length of the file number
    
    Returns:
    (str):
        a non-finished but correctly formatted string template to insert line number
        and file index into
    """
    line_prefix = (' ' * (holder.fileLineNumberPlaceHolder - lineCharLength)) + '%i)'

    if includeFilePrefix:
        file_prefix = (' ' * (holder.fileNumberPlaceHolder - fileCharLength)) + '%i.'
        return color_dic[C_KW.NUMBER] + file_prefix + line_prefix + color_dic[C_KW.RESET_ALL] + ' '

    return color_dic[C_KW.NUMBER] + line_prefix + color_dic[C_KW.RESET_ALL] + ' '


def _getLinePrefix(line_num: int, index: int) -> str:
    """
    calculates the line prefix in regard to the line number and file count.
    
    Parameters:
    line_num (int):
        the current number identifying the line
    index (int):
        the current number identifying the file
    
    Returns:
    (str):
        the new line prefix including the line number.
    """
    if len(holder.files) > 1:
        return _CalculateLinePrefixSpacing(len(str(line_num)), True, len(str(index))) % (index, line_num)
    return _CalculateLinePrefixSpacing(len(str(line_num))) % (line_num)


@lru_cache(maxsize=None)
def _CalculateLineLengthPrefixSpacing(lineCharLength: int) -> str:
    """
    calculate a string template for the line prefix.
    
    Parameters:
    lineCharLength (int):
        the length of the line
    
    Returns:
    (str):
        a non-finished but correctly formatted string template to insert line length into
    """
    lengthPrefix = '[' + ' ' * (holder.fileLineLengthPlaceHolder - lineCharLength) + '%i]'
    return '%s' + color_dic[C_KW.LINE_LENGTH] + lengthPrefix + color_dic[C_KW.RESET_ALL] + ' '


def _getLineLengthPrefix(prefix: str, line) -> str:
    """
    calculates the line prefix in regard to the line length.
    
    Parameters:
    prefix (str):
        the current prefix to append to
    line (str|byte):
        a representation of the current line
    
    Returns:
    (str):
        the new line prefix including the line length.
    """
    if not holder.args_id[ARGS_NOCOL] and type(line) == str:
        line = removeAnsiCodesFromLine(line)
    return _CalculateLineLengthPrefixSpacing(len(str(len(line)))) % (prefix, len(line))


def printFile(content: list) -> bool:
    """
    print a file and possibly include the substrings and patterns to search for.
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
        
    Returns:
    (bool):
        identifies if the given content parameter contained any
        queried keyword/pattern.
    """
    if not content:
        return False
    if not (ArgParser.FILE_SEARCH or ArgParser.FILE_MATCH):
        print(*[prefix + line for prefix, line in content], sep='\n')
        return False

    containsQueried = False
    stringFinder = StringFinder.StringFinder(ArgParser.FILE_SEARCH, ArgParser.FILE_MATCH)

    for line_prefix, line in content:
        cleanedLine = removeAnsiCodesFromLine(line)
        intervals, fKeyWords, mKeywords = stringFinder.findKeywords(cleanedLine)
        
        if len(fKeyWords + mKeywords) == 0:
            if not holder.args_id[ARGS_GREP]:
                print(line_prefix + line)
            continue
        
        containsQueried = True
        if holder.args_id[ARGS_NOKEYWORD]:
            continue
        
        if not holder.args_id[ARGS_NOCOL]:
            for kw_pos, kw_code in intervals:
                cleanedLine = cleanedLine[:kw_pos] + color_dic[kw_code] + cleanedLine[kw_pos:]

        print(line_prefix + cleanedLine)

        if holder.args_id[ARGS_GREP] or holder.args_id[ARGS_NOBREAK]:
            continue
        
        found_sth = False
        if fKeyWords:
            print(color_dic[C_KW.FOUND_MESSAGE], end='')
            print('--------------- Found', fKeyWords, '---------------', end='')
            print(color_dic[C_KW.RESET_ALL])
            found_sth = True
        if mKeywords:
            print(color_dic[C_KW.MATCHED_MESSAGE], end='')
            print('--------------- Matched', mKeywords, '---------------', end='')
            print(color_dic[C_KW.RESET_ALL])
            found_sth = True

        if found_sth:
            try:  # fails when using -i mode, because the stdin will send en EOF char to input without prompting the user
                input()
            except (EOFError, UnicodeDecodeError):
                pass
            
    return containsQueried


def printExcludedByPeek(content: list, excludedByPeek: int) -> None:
    """
    print a paragraph about how many lines have been excluded.
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    excludedByPeek (int):
        the amount of lines that have been excluded
    """
    if not excludedByPeek or len(content) <= 5:
        return
    excludedByPeek = excludedByPeek + 10 - len(content)
    prefix = content[0][0]
    prefix = prefix.replace(color_dic[C_KW.NUMBER], '')
    prefix = prefix.replace(color_dic[C_KW.LINE_LENGTH], '')
    prefix = prefix.replace(color_dic[C_KW.RESET_ALL], '')
    excludedByPeekLength = (len(str(excludedByPeek))-1)//2
    excludedByPeekIndent = ' ' * (len(prefix) - excludedByPeekLength + 10)
    excludedByPeekIndentAdd = ' ' * excludedByPeekLength
    print(color_dic[C_KW.NUMBER], end='')
    print(excludedByPeekIndent, excludedByPeekIndentAdd, ' •', sep='')
    print(excludedByPeekIndent, '(', excludedByPeek, ')', sep='')
    print(excludedByPeekIndent, excludedByPeekIndentAdd, ' •', sep='', end='')
    print(color_dic[C_KW.RESET_ALL])


def editContent(content: list, show_bytecode: bool, fileIndex: int = 0, lineOffset: int = 0) -> None:
    """
    apply all parameters to a string (file Content).
    
    Parameters:
    content (list):
        the content of a file like [(prefix, line), ...]
    show_bytecode (bool).
        indicates if the content lines are string or bytes
    fileIndex (int):
        the index of the holder.files list, pointing to the file that
        is currently being processed. a negative value can be used for
        the shell mode
    """
    excludedByPeek = 0
    
    if not show_bytecode and holder.args_id[ARGS_B64D]:
        content = decodeBase64(content, ArgParser.FILE_ENCODING)
    
    if holder.args_id[ARGS_NUMBER]:
        content = [(_getLinePrefix(j+lineOffset, fileIndex+1), c[1])
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
                    print('Error at operation: ', param)
                    return
        
        for arg, param in holder.args:
            if arg == ARGS_ENDS:
                content = [(prefix, line + color_dic[C_KW.ENDS] + '$' + color_dic[C_KW.RESET_ALL])
                           for prefix, line in content]
            elif arg == ARGS_TABS:
                content = [(prefix, line.replace('\t', color_dic[C_KW.TABS] + '^I' + color_dic[C_KW.RESET_ALL]))
                           for prefix, line in content]
            elif arg == ARGS_SQUEEZE:
                content = [list(group)[0] for _, group in groupby(content, lambda x: x[1])]
            elif arg == ARGS_REVERSE:
                content.reverse()
            elif arg == ARGS_BLANK:
                content = [c for c in content if c[1]]
            elif arg == ARGS_DEC:
                content = [(prefix, line + ' ' + color_dic[C_KW.CONVERSION] + converter._fromDEC(int(line), (param == param.lower())) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_dec(line)]
            elif arg == ARGS_HEX:
                content = [(prefix, line + ' ' + color_dic[C_KW.CONVERSION] + converter._fromHEX(line, (param == param.lower())) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_hex(line)]
            elif arg == ARGS_BIN:
                content = [(prefix, line + ' ' + color_dic[C_KW.CONVERSION] + converter._fromBIN(line, (param == param.lower())) +
                            color_dic[C_KW.RESET_ALL]) for prefix, line in content if converter.is_bin(line)]
            elif arg == ARGS_REPLACE:
                replace_values = param[1:-1].split(",")
                content = [(prefix, line.replace(replace_values[0], color_dic[C_KW.REPLACE] + replace_values[1] + color_dic[C_KW.RESET_ALL]))
                           for prefix, line  in content]
            elif arg == ARGS_EOF:
                content = [(prefix, line.replace(chr(26), color_dic[C_KW.REPLACE] + '^EOF' + color_dic[C_KW.RESET_ALL]))
                           for prefix, line in content]
            
    if holder.args_id[ARGS_LLENGTH]:
        content = [(_getLineLengthPrefix(c[0], c[1]), c[1]) for c in content]
    if holder.args_id[ARGS_B64E]:
        content = encodeBase64(content, ArgParser.FILE_ENCODING)

    foundQueried = printFile(content[:len(content)//2])
    if fileIndex >= 0:
        holder.files[fileIndex].setContainsQueried(foundQueried)
    printExcludedByPeek(content, excludedByPeek)
    foundQueried = printFile(content[len(content)//2:])
    if fileIndex >= 0:
        holder.files[fileIndex].setContainsQueried(foundQueried)
    
    if not show_bytecode:
        if holder.args_id[ARGS_CLIP]:
            holder.clipBoard += '\n'.join([prefix + line for prefix, line in content])


def editFile(fileIndex: int = 0) -> None:
    """
    apply all parameters to a file.
    
    Parameters:
    fileIndex (int):
        the index regarding which file is currently being edited
    """
    show_bytecode = False
    
    content = [('', '')]
    try:
        with open(holder.files[fileIndex].path, 'r', encoding=ArgParser.FILE_ENCODING) as f:
            # splitlines() gives a slight inaccuracy, in case the last line is empty.
            # the alternative would be worse: split('\n') would increase the linecount each
            # time catw touches a file.
            content = [('', line) for line in f.read().splitlines()]
    except:
        print('Failed to open:', holder.files[fileIndex].displayname)
        try:
            enterChar = '⏎'
            try:
                if len(enterChar.encode(ArgParser.FILE_ENCODING)) != 3:
                    raise UnicodeEncodeError('', '', -1, -1, '')
            except UnicodeEncodeError:
                enterChar = 'ENTER'
            print(f"Do you want to open the file as a binary, without parameters? [Y/{enterChar}]:", end='')
            inp = input()
            if not 'Y' in inp.upper() and inp:
                print('Aborting...')
                return
        except EOFError:
            pass
        except UnicodeError:
            print(f"Input is not recognized in the given encoding: {ArgParser.FILE_ENCODING}")
            print('Aborting...')
            return
        try:
            with open(holder.files[fileIndex].path, 'rb') as f:
                # in binary splitlines() is our only option
                content = [('', repr(line)[2:-1]) for line in f.read().splitlines()]
            show_bytecode = True
        except:
            print('Operation failed! Try using the enc=X parameter.')
            return
    
    editContent(content, show_bytecode, fileIndex)


def _copyToClipboard(content: str, __dependency: int = 3, __clipBoardError: bool = False) -> None:
    """
    copy a string to the clipboard, by recursively checking which module exists and could
    be used, this function should only be called by copyToClipboard()
    
    Parameters:
    content (str):
        the string to copy
    __dependency (int):
        do not change!
    __clipBoardError (bool):
        do not change!
    """
    if __dependency == 0:
        if __clipBoardError:
            errorMsg = '\n'
            errorMsg += "ClipBoardError: You can use either 'pyperclip3', 'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
            errorMsg += "Try to install a different one using 'python -m pip install ...'"
        else:
            errorMsg = '\n'
            errorMsg += "ImportError: You need either 'pyperclip3', 'pyperclip', or 'pyclip' in order to use the '--clip' parameter.\n"
            errorMsg += "Should you have any problem with either module, try to install a different one using 'python -m pip install ...'"
        print(errorMsg)
        return
    try:
        if __dependency == 3:
            import pyperclip as pc
        elif __dependency == 2:
            import pyclip as pc
        elif __dependency == 1:
            import pyperclip3 as pc
        pc.copy(content)
    except ImportError:
        _copyToClipboard(content, __dependency-1, False or __clipBoardError)
    except Exception:
        _copyToClipboard(content, __dependency-1, True or __clipBoardError)
    

def copyToClipboard(content: str) -> None:
    """
    entry point to recursive function _copyToClipboard()
    
    Parameters:
    content (str):
        the string to copy
    """
    _copyToClipboard(content)


def printRawView(fileIndex: int = 0, mode: str = 'X') -> None:
    """
    print the raw byte representation of a file in hexadecimal or binary
    
    Parameters:
    fileIndex (int):
        the index regarding which file is currently being edited
    mode (str):
        either 'x', 'X' for hexadecimal (lower- or upper case letters),
        or 'b' for binary
    """
    print(holder.files[fileIndex].displayname, ':', sep='')
    for line in getRawViewLinesGen(holder.files[fileIndex].path, mode, [color_dic[C_KW.RAWVIEWER], color_dic[C_KW.RESET_ALL]], ArgParser.FILE_ENCODING):
        print(line)
    print('')


def editFiles() -> None:
    """
    manage the calls to editFile() for each file.
    """
    start = len(holder.files)-1 if holder.reversed else 0
    end = -1 if holder.reversed else len(holder.files)

    rawViewMode = None
    if holder.args_id[ARGS_HEXVIEW] or holder.args_id[ARGS_BINVIEW]:
        for arg, param in holder.args:
            if arg == ARGS_HEXVIEW:
                rawViewMode = 'X' if param == param.upper() else 'x'
                break
            elif arg == ARGS_BINVIEW:
                rawViewMode = 'b'
                break
    
    for i in range(start, end, -1 if holder.reversed else 1):
        if rawViewMode:
            printRawView(i, rawViewMode)
        else:
            editFile(i)
    if holder.args_id[ARGS_COUNT]:
        print('')
        _showCount()
    if holder.args_id[ARGS_FILES]:
        print('')
        _showFiles()
    if holder.args_id[ARGS_CLIP]:
        copyToClipboard(removeAnsiCodesFromLine(holder.clipBoard))


def initColors() -> None:
    """
    set the color dictionary to be used. either empty for no colors
    or the default color dictionary.
    """
    # do not use colors if requested, or output will be piped anyways
    global color_dic
    if holder.args_id[ARGS_NOCOL] or (not sys.stdout.isatty() or sys.stdout.closed):
        color_dic = dict.fromkeys(color_dic, '')
    else:
        color_dic = default_color_dic.copy()


def init(shell: bool = False) -> tuple:
    """
    initiate the code by calling the argparser and handling the default
    parameters: -h, -v, -d, --config.
    
    Parameters:
    shell (bool):
        indicates if the shell entry point was used, and the stdin will therefor
        be used by default
        
    Returns:
    (tuple):
        contains (known_files, unknown_files, echo_args) from the argparser
    """
    # read parameter-args
    args, unknown_args, known_files, unknown_files, echo_args = ArgParser.getArguments(sys.argv)

    holder.setArgs(args)

    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_IN]:
        sys.stdin.reconfigure(encoding=ArgParser.FILE_ENCODING)
    if holder.args_id[ARGS_RECONFIGURE] or holder.args_id[ARGS_RECONFIGURE_OUT]:
        sys.stdout.reconfigure(encoding=ArgParser.FILE_ENCODING)
    if holder.args_id[ARGS_RECONFIGURE_ERR]:
        sys.stderr.reconfigure(encoding=ArgParser.FILE_ENCODING)
    
    initColors()   
    
    # check for special cases
    if holder.args_id[ARGS_DEBUG]:
        _showDebug(holder.args, unknown_args, known_files, unknown_files, echo_args)
    if (len(known_files) + len(unknown_files) + len(holder.args) == 0 and not shell) or holder.args_id[ARGS_HELP]:
        _showHelp()
        sys.exit(0)
    if holder.args_id[ARGS_VERSION]:
        _showVersion()
        sys.exit(0)
    if holder.args_id[ARGS_CONFIG]:
        config.saveConfig()
        sys.exit(0)
    
    return (known_files, unknown_files, echo_args)


def main():
    piped_input = temp_file = ''
    known_files, unknown_files, echo_args = init(False)
    
    if holder.args_id[ARGS_ECHO]:
        temp_file = StdInHelper.writeTemp(' '.join(echo_args), tmpFileHelper.generateTempFileName(), ArgParser.FILE_ENCODING)
        known_files.append(temp_file)
        holder.setTempFileEcho(temp_file)
    if holder.args_id[ARGS_INTERACTIVE]:
        piped_input = ''.join(StdInHelper.getStdInContent(holder.args_id[ARGS_ONELINE]))
        temp_file = StdInHelper.writeTemp(piped_input, tmpFileHelper.generateTempFileName(), ArgParser.FILE_ENCODING)
        known_files.append(temp_file)
        unknown_files = StdInHelper.writeFiles(unknown_files, piped_input, ArgParser.FILE_ENCODING)
        holder.setTempFileStdIn(temp_file)
    else:
        unknown_files = StdInHelper.readWriteFilesFromStdIn(
            unknown_files, ArgParser.FILE_ENCODING, on_windows_os, holder.args_id[ARGS_ONELINE])

    if (len(known_files) + len(unknown_files) == 0):
        return

    # fill holder object with neccessary values
    holder.setFiles([*known_files, *unknown_files])
    
    if holder.args_id[ARGS_FFILES]:
        _showFiles()
        return
    if holder.args_id[ARGS_DATA] or holder.args_id[ARGS_CHECKSUM]:
        _printMetaAndChecksum(holder.args_id[ARGS_DATA], holder.args_id[ARGS_CHECKSUM])
        return
    
    if holder.args_id[ARGS_B64D]:
        holder.setDecodingTempFiles([tmpFileHelper.generateTempFileName() for _ in holder.files])
    holder.generateValues(ArgParser.FILE_ENCODING)

    if holder.args_id[ARGS_CCOUNT]:
        _showCount()
        return

    try:
        editFiles()  # print the cat-output
    except IOError: # catch broken-pipe error
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE

    # clean-up
    for tmp_file in tmpFileHelper.getGeneratedTempFiles():
        if holder.args_id[ARGS_DEBUG]:
            print('Cleaning', tmp_file)
        try:
            os.remove(tmp_file)
        except FileNotFoundError:
            if holder.args_id[ARGS_DEBUG]:
                print('FileNotFoundError', tmp_file)


def shell_main():
    init(True)
    
    shellPrefix = '>>> '
    EOFControlChar = 'Z' if on_windows_os else 'D'
    oneline = holder.args_id[ARGS_ONELINE]
    
    class CmdExec:
        exitShell = False
        
        def execColors(self) -> None:
            initColors()
            _CalculateLinePrefixSpacing.cache_clear()
            _CalculateLineLengthPrefixSpacing.cache_clear()
        
        def exec(self, cmd: str) -> bool:
            """
            check if a shell line is an executable command,
            executes it if it is.
            
            Parameters:
            cmd (str):
                the line entered in the cat shell
                
            Returns:
            (bool):
                indicates if a valid command has been found
                and executed
            """
            if cmd[:1] != '!':
                return False
            lineSplit = cmd[1:].split(' ')
            method = getattr(self, '_command_' + lineSplit[0], lambda: False)
            method(lineSplit[1:])
            return True
        
        def _command_help(self, cmd: str) -> None:
            print(f"Type ^{EOFControlChar} (Ctrl + {EOFControlChar}) or '!exit' to exit.")
            print("Type '!add <OPTION>', '!del <OPTION>', '!see' to change/see the active parameters.")
            
        def _command_add(self, cmd: str) -> None:
            args, _, _, _, _ = ArgParser.getArguments([''] + cmd)
            holder.addArgs(args)
            self.execColors()
            print(f"successfully added {[arg for _, arg in args]}")
            
        def _command_del(self, cmd: str) -> None:
            args, _, _, _, _ = ArgParser.getArguments([''] + cmd, True)
            holder.deleteArgs(args)
            self.execColors()
            print(f"successfully removed {[arg for _, arg in args]}")
            
        def _command_see(self, cmd: str) -> None:
            print(f"{'Active Args:': <12} {[arg for _, arg in holder.args]}")
            if ArgParser.FILE_SEARCH:
                print(f"{'Literals:':<12} {ArgParser.FILE_SEARCH}")
            if ArgParser.FILE_MATCH:
                print(f"{'Matches:': <12} {ArgParser.FILE_MATCH}")
                
        def _command_exit(self, cmd: str) -> None:
            self.exitShell = True
    
    
    cmd = CmdExec()
    
    print(__project__, 'v' + __version__, 'shell', '(' + __url__ + ')', end=' - ')
    print(f"Use 'catw' to handle files.")
    print("Type '!help' for more information.")
    
    print(shellPrefix, end='', flush=True)
    for i, line in enumerate(StdInHelper.getStdInContent(oneline)):
        strippedLine = line.rstrip('\n')
        if cmd.exec(strippedLine):
            if cmd.exitShell:
                break
        else:
            editContent([('', strippedLine)], False, -1, i)
        if not oneline:
            print(shellPrefix, end='', flush=True)


if __name__ == '__main__':
    main()
