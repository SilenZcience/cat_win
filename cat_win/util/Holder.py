from cat_win.util.ArgConstants import *
from heapq import nlargest


class Holder():
    def __init__(self) -> None:
        self.files = []  # all files, including tmp-file from stdin
        self.args = []  # list of all used parameters: format [[id, param]]
        self.args_id = []
        self.temp_file = None  # if stdin is used, this temp_file will contain the stdin-input
        self.reversed = False

        self.allFilesLinesSum = 0
        self.fileLineNumberPlaceHolder = 0
        self.fileNumberPlaceHolder = 0
        # the amount of chars neccessary to display the longest line within all files
        self.fileLineLengthPlaceHolder = 0

        self.clipBoard = ""
    
    def setFiles(self, files: list) -> None:
        self.files = files

    def setArgs(self, args: list) -> None:
        self.args = args
        self.args_id = [False] * (HIGHEST_ARG_ID + 1)
        for id, _ in self.args:
            self.args_id[id] = True
        if self.args_id[ARGS_B64E]:
            self.args_id[ARGS_NOCOL] = True
        self.reversed = ARGS_REVERSE in self.args_id

    def setTempFile(self, file: str) -> None:
        self.temp_file = file

    def getAppliedFiles(self) -> list:
        return ["<STDIN>" if f == self.temp_file else f for f in self.files]

    def __count_generator__(self, reader) -> bytes:
        b = reader(1024 * 1024)
        while b:
            yield b
            b = reader(1024 * 1024)

    def __getFileLinesSum__(self, file: str) -> int:
        with open(file, 'rb') as fp:
            c_generator = self.__count_generator__(fp.raw.read)
            linesSum = sum(buffer.count(b'\n') for buffer in c_generator) + 1
        return linesSum

    def __calcPlaceHolder__(self) -> None:
        fileLines = [self.__getFileLinesSum__(file) for file in self.files]
        self.allFilesLinesSum = sum(fileLines)
        self.fileLineNumberPlaceHolder = len(str(max(fileLines)))
        self.fileNumberPlaceHolder = len(str(len(self.files)))

    def __calcMaxLine__(self, file: str) -> int:
        heap = []
        lines = []
        with open(file, "rb") as fp:
            lines = fp.readlines()
        heap = nlargest(1, lines, len)
        if len(heap) == 0:
            return 0
        longest_line = heap[0][:-1]

        if longest_line.endswith(b'\r'):
            longest_line = longest_line[:-1]
        return len(str(max(len(longest_line), len(lines[-1]))))

    def __calcfileLineLengthPlaceHolder__(self) -> None:
        self.fileLineLengthPlaceHolder = max(self.__calcMaxLine__(file)
                                             for file in self.files)

    def generateValues(self) -> None:
        self.__calcPlaceHolder__()
        self.__calcfileLineLengthPlaceHolder__()
