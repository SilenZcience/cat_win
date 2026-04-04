"""
iohelper
"""

from pathlib import Path
import contextlib
import ctypes
import io
import logging
import os
import sys

from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.helper.environment import on_windows_os
from cat_win.src.service.helper.progressbar import PBar


class StatusLogger:
    """Simple logging wrapper with ANSI color support for status/error messages."""

    DEBUG    = logging.DEBUG
    INFO     = logging.INFO
    WARNING  = logging.WARNING
    ERROR    = logging.ERROR
    CRITICAL = logging.CRITICAL

    class _Formatter(logging.Formatter):
        """ANSI color formatter for log messages."""
        def __init__(self, logger_ref: 'StatusLogger') -> None:
            super(StatusLogger._Formatter, self).__init__('%(message)s')
            self.logger_ref = logger_ref

        def format(self, record: logging.LogRecord) -> str:
            message = record.getMessage()
            line_end = getattr(record, 'line_end', '\n')
            color = self.logger_ref.get_color(record.levelno)
            reset = self.logger_ref.colors['reset'] if color else ''
            return f"{color}{message}{reset}{line_end}"

    def __init__(self):
        self.log_to_file = False
        self.file_handle = None
        self.colors = {
            'debug'   : '',
            'info'    : '',
            'warning' : '',
            'error'   : '',
            'critical': '',
            'reset'   : '',
        }
        self.logger = logging.getLogger('cat_win.logger')
        self.logger.propagate = False
        self.logger.setLevel(self.INFO)
        self.handler = None
        self._reconfigure_handler()

    def get_color(self, priority: int) -> str:
        """Get ANSI color code for logging level."""
        return {
            self.DEBUG:    self.colors['debug'],
            self.INFO:     self.colors['info'],
            self.WARNING:  self.colors['warning'],
            self.ERROR:    self.colors['error'],
            self.CRITICAL: self.colors['critical'],
        }.get(priority, '')

    def set_colors(self, color_dic: dict) -> None:
        """Set ANSI colors for different log levels from color dictionary."""
        self.colors['debug']    = color_dic[CKW.DEBUG]
        self.colors['info']     = color_dic[CKW.INFO]
        self.colors['warning']  = color_dic[CKW.WARNING]
        self.colors['error']    = color_dic[CKW.ERROR]
        self.colors['critical'] = color_dic[CKW.CRITICAL]
        self.colors['reset']    = color_dic[CKW.RESET_ALL]
        self.refresh_formatter()

    def clear_colors(self) -> None:
        """Clear all ANSI colors (set to empty strings)."""
        self.colors = dict.fromkeys(self.colors, '')
        self.refresh_formatter()

    def refresh_formatter(self) -> None:
        """Update the formatter on the current handler."""
        if self.handler is not None:
            self.handler.setFormatter(self._Formatter(self))

    def _close_handler(self) -> None:
        """Close and remove the current handler."""
        if self.handler is None:
            return
        self.logger.removeHandler(self.handler)
        if isinstance(self.handler, logging.FileHandler):
            self.handler.close()
        else:
            self.handler.flush()
        if self.file_handle is not None:
            self.file_handle.close()
            self.file_handle = None
        self.handler = None

    def _reconfigure_handler(self) -> None:
        """Reconfigure the logging handler."""
        self._close_handler()

        if self.log_to_file:
            log_file = Path(os.path.join(os.getcwd(), 'catw_debug.log'))
            try:
                self.handler = logging.FileHandler(
                    log_file, mode='a', encoding='utf-8', errors='replace'
                )
            except TypeError:
                # Python < 3.9 does not support the `errors` argument
                self.file_handle = open(
                    log_file, mode='a', encoding='utf-8', errors='replace'
                )
                self.handler = logging.StreamHandler(self.file_handle)
        else:
            self.handler = logging.StreamHandler(sys.stderr)

        self.handler.terminator = ''
        self.refresh_formatter()
        self.logger.addHandler(self.handler)

    def set_level(self, priority: int) -> None:
        """Set the minimum logging level."""
        self.logger.setLevel(priority)

    def set_log_to_file(self, log_to_file: bool = True) -> None:
        """Set logging destination: file (True) or stderr (False)."""
        self.log_to_file = log_to_file
        self._reconfigure_handler()

    def __call__(self, *args, **kwargs) -> None:
        """Log a message (callable interface mimicking print)."""
        priority = kwargs.pop('priority', self.ERROR)
        sep = kwargs.pop('sep', ' ')
        end = kwargs.pop('end', '\n')
        kwargs.pop('file', None)
        kwargs.pop('flush', None)

        if kwargs:
            raise TypeError(f"Unsupported keyword arguments: {', '.join(kwargs.keys())}")

        message = sep.join(str(arg) for arg in args)
        self.logger.log(priority, message, extra={'line_end': end})

    def close(self) -> None:
        """Close the logging handler and clean up resources."""
        self._close_handler()
        self.log_to_file = False
        self._reconfigure_handler()

    def __del__(self) -> None:
        """Ensure cleanup when object is garbage collected."""
        self.close()

logger = StatusLogger()


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
        logger(f"Error: The path '{file_dir}' could not be created.", priority=logger.ERROR)
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
        logger(f"Error: The file '{file}' could not be written.", priority=logger.ERROR)
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
                file_length, prefix='Reading file',
                length=100, fill_l='━', fill_r='╺', erase=True, decimals=5
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
            # Keep original line endings instead of universal-newline normalization.
            with open(src_file, 'r', encoding=file_encoding, errors=errors, newline='') as file:
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
                if file.write(content) != len(content):
                    raise OSError('Not all characters could be written to the file.')
            return src_file
        # in case the content is of types bytes:
        # important for the editor, so the encoding errors do not get replaced!
        with open(src_file, 'wb') as raw_f:
            if raw_f.write(content) != len(content):
                raise OSError('Not all bytes could be written to the file.')
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
                logger('You are about to create an empty file. ', end='', priority=logger.INFO)
                logger('Do you want to continue?', priority=logger.INFO)
                enter_char = '⏎'

                try:
                    if len(enter_char.encode(file_encoding)) != 3:
                        raise UnicodeEncodeError('', '', -1, -1, '')
                except UnicodeEncodeError:
                    enter_char = 'ENTER'
                logger(
                    f"[Y/{enter_char}] Yes, Continue       [N] No, Abort :", end='',
                    priority=logger.INFO
                )
                user_input = input()
            except EOFError:
                pass
            except UnicodeError:
                logger(
                    'Input is not recognized in the given encoding: ', end='',
                    priority=logger.ERROR
                )
                logger(file_encoding, priority=logger.ERROR)
                user_input = 'N'
            finally:
                if user_input and user_input.upper() != 'Y':
                    logger('Aborting...', priority=logger.INFO)
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
                logger(f"Error: The file '{file}' could not be written.", priority=logger.ERROR)

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

        logger('The given FILE(s)', end='', priority=logger.INFO)
        logger('', *file_list, sep='\n\t', priority=logger.INFO)
        eof_control_char = 'Z' if on_windows_os else 'D'
        logger(
            'do/does not exist. Write the FILE(s) and finish with the ', end='',
            priority=logger.INFO
        )
        logger(f"^{eof_control_char}-suffix (Ctrl + {eof_control_char}):", priority=logger.INFO)

        std_input = ''.join(IoHelper.get_stdin_content(one_line))

        return IoHelper.write_files(file_list, std_input, file_encoding)


    @staticmethod
    @contextlib.contextmanager
    def dup_stdstreams():
        """
        dup the std streams so the user can interact while also piping into cat.
        """
        replace_stdin = False
        replace_stdout = False
        stdin_backup = None
        stdout_backup = None
        ttyin = None
        ttyout = None

        try:
            replace_stdin = not os.isatty(sys.stdin.fileno())
        except (OSError, ValueError):
            replace_stdin = False
        try:
            replace_stdout = not os.isatty(sys.stdout.fileno())
        except (OSError, ValueError):
            replace_stdout = False

        try:
            if replace_stdin:
                stdin_backup = os.dup(sys.stdin.fileno())
                ttyin = os.open('CONIN$' if on_windows_os else '/dev/tty', os.O_RDONLY)
                os.dup2(ttyin, sys.stdin.fileno())

            if replace_stdout:
                stdout_backup = os.dup(sys.stdout.fileno())
                ttyout = os.open('CONOUT$' if on_windows_os else '/dev/tty', os.O_WRONLY)
                os.dup2(ttyout, sys.stdout.fileno())

            if replace_stdin and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') and on_windows_os:
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
            if stdin_backup is not None:
                try:
                    os.dup2(stdin_backup, sys.stdin.fileno())
                finally:
                    os.close(stdin_backup)
            if stdout_backup is not None:
                try:
                    os.dup2(stdout_backup, sys.stdout.fileno())
                finally:
                    os.close(stdout_backup)
            if ttyin is not None:
                os.close(ttyin)
            if ttyout is not None:
                os.close(ttyout)
