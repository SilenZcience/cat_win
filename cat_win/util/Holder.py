from cat_win.util.ArgConstants import *


class Holder():
    files = []
    args = []
    args_id = []
    temp_file = None
    reversed = False
    lineSum = 0
    fileLineMaxLength = 0
    fileMaxLength = 0
    clipBoard = ""

    def setFiles(self, files: list) -> None:
        self.files = files

    def setArgs(self, args: list) -> None:
        self.args = args
        self.args_id = [x[0] for x in self.args]
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

    def __getFileLinesSum__(self, file) -> int:
        with open(file, 'rb') as fp:
            c_generator = self.__count_generator__(fp.raw.read)
            count = sum(buffer.count(b'\n') for buffer in c_generator)
            return count + 1

    def __calcFilesLineSum__(self) -> None:
        self.lineSum = max([self.__getFileLinesSum__(file) for file in self.files])

    def __calcFileLineMaxLength__(self) -> None:
        self.fileLineMaxLength = len(str(self.lineSum))

    def __calcFileMaxLength__(self) -> None:
        self.fileMaxLength = len(str(len(self.files)))

    def generateValues(self) -> None:
        self.__calcFilesLineSum__()
        self.__calcFileLineMaxLength__()
        self.__calcFileMaxLength__()
