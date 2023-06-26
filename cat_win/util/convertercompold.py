"""
A collection of methods for list comprehension in regard to the converter.py module
for Python < 3.8 (not using the Walrus operator).
"""

from cat_win.util.converter import Converter


def comp_eval(converter: Converter, content: list, param: str, colors = None) -> list:
    """
    comprehend the content list for the eval parameter
    
    Parameters:
    converter (Converter):
        the converter object instance to use
    content (list):
        the file content to comprehend
    param (str):
        the parameter used
    colors (list):
        a list with 2 elements like [COLOR_EVALUATION, COLOR_RESET]
        containing the ANSI-Colorcodes used in the returned string.
        
    Returns:
    (list):
        the new comprehended content list with all equations evaluated
    """
    new_content = []
    for prefix, line in content:
        evaluated = converter.evaluate(line, (param == param.lower()), colors)
        if evaluated is not None:
            new_content.append((prefix, evaluated))
    return new_content

def comp_conv(converter: Converter, content: list, param: str, base: str, cleaner: object, colors = None):
    """
    comprehend the content list for the dec/hex/bin parameters
    
    Parameters:
    converter (Converter):
        the converter object instance to use
    content (list):
        the file content to comprehend
    param (str):
        the parameter used
    base (str):
        the number base to work with, options are 'dec', 'hex' or 'bin'
    cleaner (function):
        the method to call on each line in order to strip ansi color codes
    colors (list):
        a list with 2 elements like [COLOR_EVALUATION, COLOR_RESET]
        containing the ANSI-Colorcodes used in the returned string.
        
    Returns:
    (list):
        the new comprehended content list with all numbers converted
    """
    method_is_convertable = getattr(converter, 'is_' + base, lambda _: False)
    method_convert = getattr(converter, 'c_from_' + base, lambda x: x)
    
    new_content = []
    for prefix, line in content:
        cleaned = cleaner(line)
        if cleaned and method_is_convertable(cleaned):
            new_content.append((prefix, f"{line} {colors[0]}{method_convert(cleaned, (param == param.lower()))}{colors[1]}"))
    return new_content
