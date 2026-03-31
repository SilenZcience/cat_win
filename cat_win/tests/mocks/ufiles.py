"""
ufiles-related test mocks
"""


class DummyUFiles(list):
    def __init__(self, files=None):
        super().__init__(files or [])
        self.set_files_calls = []
        self.generate_values_calls = []

    def set_files(self, files):
        files = list(files)
        self.set_files_calls.append(files)
        self.clear()
        self.extend(files)

    def generate_values(self, show_numbering, show_line_length):
        self.generate_values_calls.append((show_numbering, show_line_length))
