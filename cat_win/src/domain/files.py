"""
files
"""

from functools import lru_cache
import heapq

from cat_win.src.domain.file import File
from cat_win.src.service.helper.iohelper import IoHelper


class Files:
    """
    define a holder object to store useful meta information
    about the user defined files
    """
    def __init__(self) -> None:
        self.files: list = []  # all files, including tmp-file from stdin
        self.temp_files = {
            'stdin': None,
            'echo' : None,
            'url'  : {}  ,
            }

        # the amount of chars neccessary to display the last file
        self.file_number_place_holder = 0
        # the sum of all lines of all files
        self.all_files_lines_sum = 0
        # the sum of lines for each file individually
        self.all_files_lines = {}
        # the amount of chars neccessary to display the last line (breaks on base64 decoding)
        self.all_line_number_place_holder = 0
        # the amount of chars neccessary to display the longest line within all files
        # (breaks on base64 decoding)
        self.file_line_length_place_holder = 0

    def get_file_display_name(self, file: str) -> str:
        """
        return the display name of a file. Expects self.temp_files to be set already.
        
        Parameters_
        file (str):
            a path of a file
            
        Returns:
        (str):
            the display name for the file. Either the path itself
            or a special identifier von stdin or echo inputs
        """
        if file == self.temp_files['stdin']:
            return '<STDIN>'
        if file == self.temp_files['echo']:
            return '<ECHO>'
        if file in self.temp_files['url']:
            display_url = self.temp_files['url'][file]
            if len(display_url) > 30:
                display_url = f"{display_url[:20]}...{display_url[-10:]}"
            return f"<URL {display_url}>"
        return file

    def is_temp_file(self, file_index: int) -> bool:
        """
        determine if a file is a temporary file.
        
        Parameters_
        file_index (int):
            the index of the file in self.files
            
        Returns:
        (bool):
            indicates if the file is a temp_file.
        """
        return self.files[file_index].path in self.temp_files.values()

    def set_files(self, files: list) -> None:
        """
        set the files to display.
        """
        self.files = [File(path, self.get_file_display_name(path)) for path in files]

    def set_temp_file_stdin(self, file: str) -> None:
        """
        set the tempfile used for stdin.
        """
        self.temp_files['stdin'] = file

    def set_temp_file_echo(self, file: str) -> None:
        """
        set the tempfile used for the echo arg.
        """
        self.temp_files['echo'] = file

    def set_temp_files_url(self, files: dict) -> None:
        """
        set the tempfiles used for urls.
        """
        self.temp_files['url'] = files

    def _calc_file_number_place_holder_(self) -> None:
        self.file_number_place_holder = len(str(len(self.files)))

    def _count_generator_(self, reader):
        """
        Parameters:
        reader (method):
            the method to read from
        
        Yields:
        byt (bytes):
            the bytes in chunks read from the reader
        """
        byt = reader(1024 * 1024)
        while byt:
            yield byt
            byt = reader(1024 * 1024)

    @lru_cache(maxsize=10)
    def _get_file_lines_sum_(self, file: str) -> int:
        try:
            with open(file, 'rb') as raw_f:
                c_generator = self._count_generator_(raw_f.raw.read)
                lines_sum = sum(buffer.count(b'\n') for buffer in c_generator) + 1
            return lines_sum
        except OSError:
            return 0

    def _calc_place_holder_(self) -> None:
        file_lines = []
        for file in self.files:
            file_line_sum = self._get_file_lines_sum_(file.path)
            file_lines.append(file_line_sum)
            self.all_files_lines[file.path] = file_line_sum
        self.all_files_lines_sum = sum(file_lines)
        self.all_line_number_place_holder = len(str(max(file_lines)))

    @lru_cache(maxsize=10)
    def _calc_max_line_length_(self, file: str) -> int:
        """
        Calculate self.file_line_length_place_holder for a single file.
        
        Parameters:
        file (str):
            a string representation of a file (-path)
            
        Returns:
        (int):
            the length of the placeholder to represent
            the longest line within the file
        """
        try:
            lines = IoHelper.read_file(file, True).splitlines()
        except OSError:
            return 0
        heap = heapq.nlargest(1, lines, len)
        if not heap:
            return 0
        return len(str(len(heap[0])))

    def _calc_file_line_length_place_holder_(self) -> None:
        self.file_line_length_place_holder = max(self._calc_max_line_length_(file.path)
                                             for file in self.files)

    def generate_values(self, calc_l_: bool, calc_ll_: bool) -> None:
        """
        generate the metadata for all files
        """
        self._calc_file_number_place_holder_()
        if calc_l_:
            self._calc_place_holder_()
        if calc_ll_:
            self._calc_file_line_length_place_holder_()

    def __getitem__(self, o: int) -> str:
        return self.files[o]

    def __iter__(self):
        return iter(self.files)

    def __len__(self) -> int:
        return len(self.files)
