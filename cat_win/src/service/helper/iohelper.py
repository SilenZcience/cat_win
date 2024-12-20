"""
iohelper
"""

from pathlib import Path
import contextlib
import ctypes
import io
import os
import sys

from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.progressbar import PBar


def err_print(*args, **kwargs) -> None:
    """
    print to stderr.
    """
    kwargs['file']  = sys.stderr
    kwargs['flush'] = True
    print(*args, **kwargs)


def path_parts(path: str) -> list:
    """
    split a path recursively into its parts.

    Parameters:
    path (str):
        a file/dir path

    Returns:
    (list):
        contains each drive/directory/file in the path seperated
        "C:/a/b/c/d.txt" -> ['C:/', 'a', 'b', 'c', 'd.txt']
    """
    _p, _f = os.path.split(path)
    return path_parts(_p) + [_f] if _f and _p else [_p] if _p else []


def create_file(file: Path, content: str, file_encoding: str) -> bool:
    """
    create the directory path to a file, and the file itself.
    on error: cleanup all created subdirectories

    Parameters:
    file (Path):
        a string representation of a file (-path)
    content (str):
        the content to write into the files
    file_encoding (str):
        the encoding to open the files with

    Returns:
    (bool):
        True if the operation was successful.
    """
    file_dir = os.path.dirname(file)
    splitted_path = path_parts(file_dir)
    subpaths = [os.path.join(*splitted_path[:i]) for i in range(2, len(splitted_path)+1)]
    unknown_subpaths = [s for s in subpaths[::-1] if not os.path.exists(s)]
    try:
        os.makedirs(file_dir, exist_ok=True)
    except OSError:
        err_print(f"Error: The path '{file_dir}' could not be created.")
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    try:
        IoHelper.write_file(file, content, file_encoding)
    except OSError:
        err_print(f"Error: The file '{file}' could not be written.")
        # cleanup (delete the folders that have been created)
        for subpath in unknown_subpaths:
            try:
                os.rmdir(subpath)
            except OSError:
                continue
        return False
    return True


class IoHelper:
    """
    IoHelper
    """

    @staticmethod
    def read_file(src_file: Path, binary: bool = False,
                  file_encoding: str = 'utf-8', errors: str = 'strict',
                  file_length: int = -1):
        """
        Reades content from a given file.

        Parameters:
        src_file (Path):
            a string representation of a file (-path)
        binary (bool):
            indicates if the file should be opened in binary mode
        file_encoding (str):
            an encoding to open the file with
        errors (str):
            the type of error handling when opening the file
        file_length (int):
            the size of the file for the total value of the progress bar
            in case the progress bar is being displayed

        Returns:
        src_content (str|bytes):
            the content of the given file
        """
        if file_length >= 0 and not binary:
            src_content, src_length = '', 0
            with PBar(
                file_length, 'Reading file',
                length=50, fill_l='━', fill_r='╺', erase=True
            ).init() as p_bar, open(src_file, 'rb') as file:
                buf_reader = io.BufferedReader(file, buffer_size=262144000) # 250MB
                while True:
                    byte_chunk = buf_reader.read(262144000)
                    src_length += 262144000
                    if not byte_chunk:
                        break
                    p_bar(src_length)
                    src_content += byte_chunk.decode(file_encoding, errors)
                p_bar(file_length)
            return src_content
        if not binary:
            with open(src_file, 'r', encoding=file_encoding, errors=errors) as file:
                src_content = file.read()
            return src_content
        # in case the file should be opened in binary mode:
        with open(src_file, 'rb') as file:
            src_content = file.read()
        return src_content


    @staticmethod
    def yield_file(src_file: Path, binary: bool = False,
                   file_encoding: str = 'utf-8', errors: str = 'strict'):
        """
        Yields content from a given file. Appends an empty line if the last
        line ends with a newline, so the lines can be joined.

        Parameters:
        src_file (Path):
            a string representation of a file (-path)
        binary (bool):
            indicates if the file should be opened in binary mode
        file_encoding (str):
            an encoding to open the file with
        errors (str):
            the type of error handling when opening the file

        Yields:
        line (str):
            the content of the given file
        byte (int):
            the next byte of the binary file
        """
        if not binary:
            last_line = None
            file = open(src_file, 'r', encoding=file_encoding, errors=errors, newline='')
            try:
                for line in file:
                    last_line = line
                    yield line.rstrip('\r\n')
                if last_line is not None and last_line.endswith('\n'):
                    yield ''
            except StopIteration:
                pass
            finally:
                file.close()
            return
        file = open(src_file, 'rb')
        try:
            for line in file:
                yield from line
        except StopIteration:
            pass
        finally:
            file.close()

    @staticmethod
    def get_newline(file: Path, default: str = '\n') -> str:
        """
        determines the line ending of a given file.

        Parameters:
        file (Path):
            a file (-path) as string representation

        Returns:
        (str):
            the line ending that the given file is using
            (\r or \n or \r\n)
        """
        try:
            with open(file, 'rb') as _f:
                _l = _f.readline()
                _l+= default.encode() * (not _l[-1:] or _l[-1:] not in b'\r\n')
                return _l[-1-(_l[-2:] == b'\r\n'):].decode()
        except OSError:
            return default


    @staticmethod
    def write_file(src_file: Path, content,
                   file_encoding: str = 'utf-8', errors: str = 'strict') -> Path:
        """
        Writes content into a given file.

        Parameters:
        src_file (Path):
            a string representation of a file (-path)
        content (str|bytes):
            the content to write in a file
        file_encoding (str):
            an encoding to open the file with
        errors (str):
            the type of error handling when opening the file

        Returns:
        src_file (Path):
            the path to the temporary file written
        """
        if isinstance(content, str):
            with open(src_file, 'w', encoding=file_encoding, errors=errors, newline='') as file:
                file.write(content)
            return src_file
        # in case the content is of types bytes:
        # important for the editor, so the encoding errors do not get replaced!
        with open(src_file, 'wb') as raw_f:
            raw_f.write(content)
        return src_file


    @staticmethod
    def get_stdin_content(one_line: bool = False, raw: bool = False):
        """
        read the stdin.

        Parameters:
        one_line (bool):
            determines if only the first stdin line should be read
        raw (bool):
            indicates if the raw stdin buffer should be read

        Yields:
        line (str):
            the input (line by line) delivered by stdin
            until the first EOF (Chr(26)) character
        """
        s_in = sys.stdin.buffer if raw else sys.stdin
        if one_line:
            first_line = s_in.readline().rstrip('\r\n')
            if first_line.endswith(chr(26)):
                first_line = first_line[:-1]
            yield first_line
            return
        for line in s_in:
            if line[-2:-1] == chr(26):
                yield line[:-2]
                break
            yield line


    @staticmethod
    def write_files(file_list: list, content: str, file_encoding: str) -> list:
        """
        write to multiple files. ask if an empty file should be created
        when there is nothing to write.
        try to create the path to the files if it does not yet exist.
        delete the created path again (cleanup) if the file still could
        not be written.

        Parameters:
        file_list (list):
            all files that should be written
        content (str):
            the content to write into the files
        file_encoding (str):
            the encoding to open the files with

        Returns:
        (list):
            containing all files, that could succesfully be written.
        """
        if not file_list:
            return file_list

        if content == '':
            user_input = ''
            try:
                err_print('You are about to create an empty file. ', end='')
                err_print('Do you want to continue?')
                enter_char = '⏎'

                try:
                    if len(enter_char.encode(file_encoding)) != 3:
                        raise UnicodeEncodeError('', '', -1, -1, '')
                except UnicodeEncodeError:
                    enter_char = 'ENTER'
                err_print(f"[Y/{enter_char}] Yes, Continue       [N] No, Abort :", end='')
                user_input = input()
            except EOFError:
                pass
            except UnicodeError:
                err_print('Input is not recognized in the given encoding: ', end='')
                err_print(file_encoding)
                user_input = 'N'
            finally:
                if user_input and user_input.upper() != 'Y':
                    err_print('Aborting...')
                    file_list.clear()

        success_file_list = []

        for file in file_list:
            try:
                IoHelper.write_file(file, content, file_encoding)
                success_file_list.append(file)
            except FileNotFoundError: # the os.pardir path to the file does not exist
                if create_file(file, content, file_encoding):
                    success_file_list.append(file)
            except OSError:
                err_print(f"Error: The file '{file}' could not be written.")

        return success_file_list


    @staticmethod
    def read_write_files_from_stdin(file_list: list, file_encoding: str,
                                    one_line: bool = False) -> list:
        """
        Write stdin input to multiple files.

        Parameters:
        file_list (list):
            all files that should be written
        file_encoding (str):
            the encoding to use for writing the files
        one_line (bool):
            determines if only the first stdin line should be read

        Returns:
        (list):
            containing all files, that could succesfully be written.
        """
        if not file_list:
            return file_list

        err_print('The given FILE(s)', end='')
        err_print('', *file_list, sep='\n\t')
        eof_control_char = 'Z' if on_windows_os else 'D'
        err_print('do/does not exist. Write the FILE(s) and finish with the ', end='')
        err_print(f"^{eof_control_char}-suffix (Ctrl + {eof_control_char}):")

        std_input = ''.join(IoHelper.get_stdin_content(one_line))

        return IoHelper.write_files(file_list, std_input, file_encoding)


    @staticmethod
    @contextlib.contextmanager
    def dup_stdin(dup: bool = True):
        """
        dup the stdin so the user can interact while also piping into cat.

        Parameters:
        dup (bool):
            is this is false the function will not do anything.
            only implemented to eliminate repeated code somewhere else
        """
        if not dup:
            yield
            return
        stdin_backup = os.dup(sys.stdin.fileno())
        try:
            tty = os.open('CONIN$' if on_windows_os else '/dev/tty', os.O_RDONLY)
            os.dup2(tty, sys.stdin.fileno())
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') and on_windows_os:
                # for pyinstaller:
    # stdin, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
    # None security, OPEN_EXISTING, 0 flags, None template
                conin_handle = ctypes.windll.kernel32.CreateFileW(
                    "CONIN$", 0x80000000, 3, None, 3, 0, None
                ) # os.dup2 does not work on pyinstaller
                ctypes.windll.kernel32.SetStdHandle(-10, conin_handle) # -10 = stdin
                # if this fails it is better to let the exception raise than to be stuck
                # without user interaction being recognized
            yield
        finally:
            os.dup2(stdin_backup, sys.stdin.fileno())
