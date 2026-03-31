"""
A collection of methods for list comprehension in regard to the converter.py module
for Python < 3.8 (not using the Walrus operator).
"""

from cat_win.src.domain.contentbuffer import ContentBuffer
from cat_win.src.service.converter import Converter


def comp_eval(content: ContentBuffer, param: str, cleaner: object) -> ContentBuffer:
    """
    comprehend the content list for the eval parameter

    Parameters:
    content (ContentBuffer):
        the file content to comprehend
    param (str):
        the parameter used
    cleaner (function):
        the method to call on each line in order to strip ansi color codes

    Returns:
    (ContentBuffer):
        the new comprehended content list with all equations evaluated
    """
    new_content = ContentBuffer()
    for line, prefix, suffix in content:
        evaluated = Converter.evaluate(cleaner(line), (param.islower()))
        if evaluated is not None:
            new_content.append(evaluated, prefix, suffix)
    return new_content

def comp_conv(content: ContentBuffer, param: str, cleaner: object) -> ContentBuffer:
    """
    comprehend the content list for the dec/hex/bin parameters

    Parameters:
    content (ContentBuffer):
        the file content to comprehend
    param (str):
        the parameter used
    base (str):
        the number base to work with, options are 'dec', 'hex' or 'bin'
    cleaner (function):
        the method to call on each line in order to strip ansi color codes

    Returns:
    (ContentBuffer):
        the new comprehended content list with all numbers converted
    """
    base = param.lstrip('-').lower()
    method_is_convertable = getattr(Converter, 'is_' + base, lambda _: False)
    method_convert = getattr(Converter, 'c_from_' + base, lambda x: x)

    new_content = ContentBuffer()
    for line, prefix, suffix in content:
        cleaned = cleaner(line)
        if cleaned and method_is_convertable(cleaned):
            new_content.append(
                line, prefix, suffix + f" {method_convert(cleaned, param.islower())}"
            )
    return new_content
