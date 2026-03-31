"""
temporary-file-helper test mocks
"""


class DummyTmpFileHelper:
    def __init__(self, names):
        self._names = list(names)
        self._idx = 0

    def generate_temp_file_name(self):
        value = self._names[self._idx]
        self._idx += 1
        return value
