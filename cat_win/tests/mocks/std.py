"""
std
"""

import io
# import re


class OSAttyDefGen:
    """
    generate a function to replace os.isatty()
    """

    @staticmethod
    def get_def(mapping: dict):
        """
        return a function that returns the mapping
        """
        def isatty(no: int, *args, **kwargs) -> bool:
            """
            return the mapped values
            """
            return mapping.get(no, False)
        return isatty

# ansi_escape_8bit = re.compile(r'''
#     (?: # either 7-bit C1, two bytes, ESC Fe (omitting CSI)
#         \x1b
#         [@-Z\\-_]
#     # |   # or a single 8-bit byte Fe (omitting CSI)
#     #     [\x80-\x9A\x9C-\x9F]
#     |   # or CSI + control codes
#         (?: # 7-bit CSI, ESC [
#             \x1b\[
#         |   # 8-bit CSI, 9B
#             \x9B
#         )
#         [0-?]*  # Parameter bytes
#         [ -/]*  # Intermediate bytes
#         [@-~]   # Final byte
#     )
# ''', re.VERBOSE)


class StdOutMock(io.StringIO):
    """
    mock for stdout stream
    """
    # def reconfigure(self, encoding = None) -> None:
    #     return

    # def write(self, s: str = '') -> int:
    #     return super().write(ansi_escape_8bit.sub('', s))

    def fileno(self) -> int:
        return 1


class StdInMockIter:
    """
    mock for stdin stream iterable
    """
    def __init__(self, mock: object) -> None:
        self.input_value = mock.input_value
        self.splitted_input_value = self.input_value.split('\n')
        self.index = -1

    # def __iter__(self):
    #     return self

    # def fileno(self) -> int:
    #     return 0

    def __next__(self) -> str:
        if self.index < len(self.splitted_input_value)-1:
            self.index += 1
            return self.splitted_input_value[self.index] + '\n'
        raise StopIteration


class StdInMock:
    """
    mock for stdin stream
    """
    def __init__(self, input_value: str = '') -> None:
        self.input_value = input_value

    def set_content(self, input_value: str) -> None:
        """
        set the stdin mock content
        """
        self.input_value = input_value

    # def reconfigure(self, encoding = None) -> None:
    #     return

    def fileno(self) -> int:
        return 0

    def readline(self) -> str:
        """
        return the next line from stdin mock
        """
        return self.input_value.split('\n')[0] + '\n'

    def __iter__(self) -> StdInMockIter:
        return StdInMockIter(self)

class IoHelperMock:
    """
    helper for stdin mock
    """
    def __init__(self, content: str = '') -> None:
        self.content = content

    @staticmethod
    def yield_file_gen(content):
        def _yield_file(*args):
            yield from content
        return _yield_file

    def set_content(self, content: str) -> None:
        """
        set stdin content
        """
        self.content = content

    def get_stdin_content(self, *_):
        """
        generate stdin content line by line
        """
        yield from self.content.split('\n')
