"""
argparser-related test mocks
"""


class DummyArgParser:
    def __init__(self, file_encoding='utf-8'):
        self.file_encoding = file_encoding


class DummyReplArgParser(DummyArgParser):
    def __init__(self, file_encoding='utf-8'):
        super().__init__(file_encoding=file_encoding)
        self._args = []
        self.file_queries = []
        self.file_queries_replacement = []
        self.reset_called = False
        self.gen_calls = []

    def gen_arguments(self, argv, delete=False):
        self.gen_calls.append((list(argv), bool(delete)))

    def get_args(self):
        return list(self._args)

    def set_args(self, args):
        self._args = list(args)

    def reset_values(self):
        self.reset_called = True
