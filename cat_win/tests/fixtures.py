"""
os-independent test-fixtures.
"""


import os
import tempfile


# The sample text used throughout the test suite.
# It matches 'texts/test.txt', but is defined in code so that the line
# endings are known and reproducible on every operating system.
SAMPLE_TEXT_LINES = (
    'Sample Text:',
    'This is a Tab-Character: >\t<',
    'These are Special Chars: \u00e4\u00f6\u00fc\u00c4\u00d6\u00dc',
    'N-Ary Summation: \u2211',
    'The following Line is Empty:',
    '',
    'This Line is a Duplicate!',
    'This Line is a Duplicate!',
)


def sample_text(newline: str = '\r\n') -> str:
    """
    creates the sample text used by the test suite.

    Parameters:
    newline (str):
        the line ending to join the lines with
        (\\r\\n, \\n or \\r)

    Returns:
    (str):
        the sample text using the given line ending
    """
    return newline.join(SAMPLE_TEXT_LINES)


def _remove_quietly(file_path: str) -> None:
    try:
        os.remove(file_path)
    except OSError:
        pass


def write_temp_file(content, suffix: str = '.txt', encoding: str = 'utf-8') -> str:
    """
    writes the given content into a newly created temporary file.

    The file is always written in binary mode, so that no newline
    translation can take place and the resulting bytes are identical
    on every operating system.

    Parameters:
    content (str|bytes):
        the content to write into the file
    suffix (str):
        the file name suffix (including the leading dot)
    encoding (str):
        the encoding to use if the content is given as string

    Returns:
    (str):
        the path to the temporary file
    """
    if isinstance(content, str):
        content = content.encode(encoding)
    file_desc, file_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(file_desc, 'wb') as _file:
            _file.write(content)
    except BaseException:
        _remove_quietly(file_path)
        raise
    return file_path


def create_temp_file(test_case, content, suffix: str = '.txt', encoding: str = 'utf-8') -> str:
    """
    creates a temporary file with a deterministic content for a single test.

    The file is deleted automatically as soon as the given test case is
    done, even if the test failed.

    Parameters:
    test_case (TestCase):
        the test case the file belongs to
    content (str|bytes):
        the content to write into the file
    suffix (str):
        the file name suffix (including the leading dot)
    encoding (str):
        the encoding to use if the content is given as string

    Returns:
    (str):
        the path to the temporary file
    """
    file_path = write_temp_file(content, suffix, encoding)
    test_case.addCleanup(_remove_quietly, file_path)
    return file_path


def create_sample_file(test_case, newline: str = '\r\n', suffix: str = '.txt') -> str:
    """
    creates a temporary file containing the sample text for a single test.

    Parameters:
    test_case (TestCase):
        the test case the file belongs to
    newline (str):
        the line ending the sample text should use
    suffix (str):
        the file name suffix (including the leading dot)

    Returns:
    (str):
        the path to the temporary file
    """
    return create_temp_file(test_case, sample_text(newline), suffix)
