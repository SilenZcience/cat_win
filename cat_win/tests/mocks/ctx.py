"""
context-oriented test mocks
"""

from cat_win.src.const.argconstants import ARGS_FILE_PREFIX, ARGS_NOCOL, ARGS_NUMBER, ARGS_EOL
from cat_win.src.const.colorconstants import CKW


class DummyFile:
    def __init__(self, displayname, path=None, file_size=10):
        self.displayname = displayname
        self.path = displayname if path is None else path
        self.file_size = file_size
        self.plaintext_calls = []
        self.contains_queried = None

    def set_plaintext(self, plain=True):
        self.plaintext_calls.append(plain)

    def set_contains_queried(self, value):
        self.contains_queried = value


class DummyFiles(list):
    def __init__(self, files, all_line=3, file_num=2, line_len=4):
        super().__init__(files)
        self.all_line_number_place_holder = all_line
        self.file_number_place_holder = file_num
        self.file_line_length_place_holder = line_len

    def is_temp_file(self, _idx):
        return False


class DummyCtx:
    def __init__(
        self,
        u_args=None,
        u_files=None,
        color_dic=None,
        const_dic=None,
        arg_parser=None,
        content=None,
    ):
        default_args = {
            ARGS_FILE_PREFIX: False,
            ARGS_NOCOL: False,
            ARGS_NUMBER: True,
            ARGS_EOL: False,
        }
        if u_args is None:
            self.u_args = default_args
        elif hasattr(u_args, 'find_first') or hasattr(u_args, 'args'):
            self.u_args = u_args
            for key, value in default_args.items():
                self.u_args.setdefault(key, value)
        else:
            merged = dict(default_args)
            merged.update(u_args)
            self.u_args = merged

        self.u_files = u_files if u_files is not None else DummyFiles([DummyFile('file.txt')])
        self.color_dic = color_dic if color_dic is not None else {
            CKW.NUMBER: '<NUM>',
            CKW.RESET_ALL: '<RST>',
            CKW.LINE_LENGTH: '<LEN>',
            CKW.FILE_PREFIX: '<FP>',
        }
        self.const_dic = {} if const_dic is None else const_dic
        self.arg_parser = arg_parser
        self.content = content
