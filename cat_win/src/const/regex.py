"""
regex
"""

import re


ANSI_CSI_RE = re.compile(r"\001?\033\[(?:\d|;)*[a-zA-Z]\002?") # Control Sequence Introducer
# ANSI_OSC_RE = re.compile(r"\001?\033\]([^\a]*)(\a)\002?")    # Operating System Command

DJANGO_VALID_URL_PATTERN = re.compile(
    r"^(?:http|ftp)s?://" # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|" #domain...
    r"localhost|" #localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})" # ...or ip
    r"(?::\d+)?" # optional port
    r"(?:/?|[/?]\S+)$", re.IGNORECASE)

RE_ENCODING      = re.compile(r"\Aenc[\=\:].+\Z",   re.IGNORECASE)
RE_MATCH         = re.compile(r"\Amatch[\=\:].+\Z", re.IGNORECASE)
RE_M_ATCH        = re.compile(r"\Am[\=\:].+\Z",     re.IGNORECASE)
RE_FIND          = re.compile(r"\Afind[\=\:].*\Z",  re.IGNORECASE)
RE_F_IND         = re.compile(r"\Af[\=\:].*\Z",     re.IGNORECASE)
RE_TRUNC         = re.compile(r"\Atrunc[\=\:][0-9\(\)\+\-\*\/]*"
                              r"\:[0-9\(\)\+\-\*\/]*\:?"
                              r"[0-9\(\)\+\-\*\/]*\Z")
RE_CUT           = re.compile(r"\A\[[0-9\(\)\+\-\*\/]*\:"
                              r"[0-9\(\)\+\-\*\/]*\:?"
                              r"[0-9\(\)\+\-\*\/]*\]\Z")
RE_REPLACE       = re.compile(r"\A\[(.*?(?<!\\)(?:\\\\)*),(.*)\]\Z")
RE_REPLACE_COMMA = re.compile(r"(?<!\\)((?:\\\\)*)\\,")
# using simple if-statements (e.g. startwith()) would be faster, but arguably less readable

TOKENIZER = re.compile(r"\w+|[^\s\w]")

CONFIG_VALID_COLOR = re.compile(
    r"\A(?:f|b)"
    r"(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    r"(?:(?:\;(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){2})?\Z", re.IGNORECASE)
CONFIG_VALID_ANSI  = re.compile(r"\[(?:\d|;)*m") # custom ansi escape code

# matches a mathematical expression consisting of
# either hex-numbers = (0x...), binary-numbers (0b...) or
# default decimal numbers
# (these are not allowed to have a leading zero
# before the decimal point, yet something like "-.06" is allowed).
# between every number has to be a valid operator (*,/,+,-,%,**,//)
# before every number there may be opening parenthesis,
# after every number there may be closing parenthesis
# (it is not validated that all parenthesis
# match each other to a valid expression ...)
RE_EVAL = re.compile(
    r"(?:\(\s*)*"
    r"(?:"
        r"(?:\-?0"
            r"(?:"
                r"(?:x[0-9a-fA-F]+)"
                r"|(?:o[0-7]+)"
            r"|b[01]+)"
        r"|(?:\-?(?:(?:0|[1-9][0-9]*)\.[0-9]*|\.[0-9]+|0|[1-9][0-9]*)))"
    r"[\)\s]*[%\-\/\+\*][\/\*]?[\(\s]*)+"
    r"(?:\-?0"
        r"(?:"
            r"(?:x[0-9a-fA-F]+)"
            r"|(?:o[0-7]+)"
        r"|b[01]+)"
    r"|(?:\-?(?:(?:0|[1-9][0-9]*)\.[0-9]*|\.[0-9]+|0|[1-9][0-9]*)))"
    r"(?:\s*\))*"
    )

def compile_re(pattern: str, ignore_case: bool):
    return re.compile(pattern, (re.IGNORECASE if ignore_case else 0) | re.DOTALL)
