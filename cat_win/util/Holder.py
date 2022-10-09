from cat_win.util.ArgConstants import *

class Holder():
    files = []
    args = []
    args_id = []
    reversed = False
    lineSum = 0
    fileCount = 0
    fileLineMaxLength = 0
    fileMaxLength = 0
    clipBoard = ""
    
    def setFiles(self, files: list):
        self.files = files
    
    def setArgs(self, args: list):
        self.args = args
        self.args_id = [x[0] for x in self.args]
        self.reversed = ARGS_REVERSE in self.args_id
    
    def __count_generator__(self, reader):
        b = reader(1024 * 1024)
        while b:
            yield b
            b = reader(1024 * 1024)
        
    def __getFileLinesSum__(self, file):
        with open(file, 'rb') as fp:
            c_generator = self.__count_generator__(fp.raw.read)
            count = sum(buffer.count(b'\n') for buffer in c_generator)
            return count + 1
    
    def __calcFilesLineSum__(self):
        self.lineSum = sum([self.__getFileLinesSum__(file) for file in self.files])
        self.fileCount = self.lineSum if self.reversed else 0
        
    def __calcFileLineMaxLength__(self):
        self.fileLineMaxLength = len(str(self.fileCount)) if self.reversed else len(str(self.lineSum))

    def __calcFileMaxLength__(self):
        self.fileMaxLength = len(str(len(self.files)))
        
    def generateValues(self):
        self.__calcFilesLineSum__()
        self.__calcFileLineMaxLength__()
        self.__calcFileMaxLength__()