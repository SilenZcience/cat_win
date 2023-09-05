"""
A collection of methods for list comprehension in regard to the converter.py module
for Python < 3.8 (not using the Walrus operator).
"""

from cat_win.util.converter import Converter


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
    new_content = []
    for prefix, line in content:
        evaluated = converter.evaluate(cleaner(line), (param == param.lower()))
        if evaluated is not None:
            new_content.append((prefix, evaluated))
    return new_content

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

    new_content = []
    for prefix, line in content:
        cleaned = cleaner(line)
        if cleaned and method_is_convertable(cleaned):
            new_content.append((prefix, f"{line} {method_convert(cleaned, (param == param.lower()))}"))
    return new_content

def split_replace(param: str) -> list:
    """
    create the two elements replace_this and replace_with from
    the given parameter, checking for escaped characters and the
    splitting delimiter.
    An implementation equivalent to split_replace() in utility.py
    without the usage of the walrus operator however.

    Parameters:
    param (str):
        the replace parameter of the form "[a,b]"
        
    Returns:
    (list):
        a list of two elements [replace_this, replace_with]
    """
    rep = ['', '']
    def _c_rep(l: list) -> str:
        l[0] = l[1]
        return ''

    esc_c = False
    for c in param[1:-1]:
        rep[1] += c if esc_c else _c_rep(rep) if c == ',' else c if c != '\\' else ''
        esc_c = False if esc_c else c == '\\'
    rep[1] = rep[1][len(rep[0]):]

    return rep
