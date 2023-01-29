from tempfile import NamedTemporaryFile

class TmpFileHelper():
    def __init__(self) -> None:
        self.tmpFiles = []
        
    def getGeneratedTempFiles(self) -> list:
        return self.tmpFiles
        
    def generateTempFileName(self) -> str:
        tmp_file = NamedTemporaryFile(delete=False).name
        self.tmpFiles.append(tmp_file)
        return tmp_file