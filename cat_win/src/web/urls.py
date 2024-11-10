"""
urls
"""

import urllib.request
import urllib.parse

from cat_win.src.const.regex import DJANGO_VALID_URL_PATTERN

DEFAULT_SCHEME = 'https://'


def is_valid_uri(s_url: str, _rec: bool = False) -> bool:
    """
    check if a string is a valid uri, by matching the general pattern,
    aswell as parsing it.

    Parameters:
    s_url (str):
        a possibly valid uri
    _rec (bool):
        indicates recursion depth 0/1

    Returns:
    (bool):
        indicates whether or not the url is valid
    """
    try:
        parse_result = urllib.parse.urlparse(s_url)
        p_result = all([parse_result.scheme, parse_result.netloc])
        r_result = DJANGO_VALID_URL_PATTERN.match(s_url) is not None
        valid = r_result and p_result
        if not (valid or _rec):
            return is_valid_uri(DEFAULT_SCHEME+s_url, True)
        return valid
    except ValueError:
        return False

def sep_valid_urls(to_check: list) -> tuple:
    """
    seperates valid from not-valid urls.

    Parameters:
    to_check (list):
        a list of possible urls to check

    Returns:
    (tuple):
        a tuple containing two lists, the first list contains
        all valid urls, the second one the not-valid urls.
    """
    valid_urls, not_valid_urls = [], []
    for url in to_check:
        if is_valid_uri(str(url)):
            valid_urls.append(str(url))
        else:
            not_valid_urls.append(url)

    return (valid_urls, not_valid_urls)

def read_url(url: str, _rec: bool = False) -> bytes:
    """
    Simply reads the contents of an url.

    Parameters (str):
        the url to open
    _rec (bool):
        indicates recursion depth 0/1

    Returns
    (bytes):
        the contents of the url; on error: a custom error message
    """
    return_msg = f"Error at opening the following url:\n{url}".encode()
    try:
        with urllib.request.urlopen(url, timeout=4) as _response:
            return_msg = _response.read()
    except ValueError:
        if not _rec:
            return_msg = read_url(DEFAULT_SCHEME+url, True)
    except OSError:
        pass
    return return_msg
