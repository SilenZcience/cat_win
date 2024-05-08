"""
A collection of methods for list comprehension in regard to the converter.py module
for Python >= 3.8 (using the Walrus operator).
"""

from cat_win.src.service.converter import Converter


def comp_eval(converter: Converter, content: list, param: str, cleaner: object) -> list:
    """
    comprehend the content list for the eval parameter
    
    Parameters:
    converter (Converter):
        the converter object instance to use
    content (list):
        the file content to comprehend
    param (str):
        the parameter used
    cleaner (function):
        the method to call on each line in order to strip ansi color codes
        
    Returns:
    (list):
        the new comprehended content list with all equations evaluated
    """
    return [(prefix, evaluated) for prefix, line in content if
            (evaluated := converter.evaluate(cleaner(line), (param.islower()))) is not None]

def comp_conv(converter: Converter, content: list, param: str, cleaner: object):
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
        
    Returns:
    (list):
        the new comprehended content list with all numbers converted
    """
    base = param.lstrip('-').lower()
    method_is_convertable = getattr(converter, 'is_' + base, lambda _: False)
    method_convert = getattr(converter, 'c_from_' + base, lambda x: x)

    return [(prefix, f"{line} {method_convert(cleaned, param.islower())}")
            for prefix, line in content if (cleaned := cleaner(line)) \
                and method_is_convertable(cleaned)]
