from io import StringIO


class StdOutMock(StringIO):
    pass
    # def reconfigure(self, encoding = None) -> None:
    #     return

    # def fileno(self) -> int:
    #     return 0


class StdInMockIter:
    def __init__(self, mock: object) -> None:
        self.input_value = mock.input_value
        self.splitted_input_value = self.input_value.split('\n')
        self.index = -1
    
    # def __iter__(self):
    #     return self
    
    def __next__(self) -> str:
        if self.index < len(self.splitted_input_value)-1:
            self.index += 1
            return self.splitted_input_value[self.index] + '\n'
        raise StopIteration


class StdInMock:
    def __init__(self, input_value: str = '') -> None:
        self.input_value = input_value
    
    # def reconfigure(self, encoding = None) -> None:
    #     return
    
    def readline(self) -> str:
        return self.input_value.split('\n')[0] + '\n'
    
    def __iter__(self) -> StdInMockIter:
        return StdInMockIter(self)