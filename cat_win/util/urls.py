import re
import urllib.request
import urllib.parse

DEFAULT_SCHEME = 'https://'
DJANGO_VALID_URL_PATTERN = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


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
        r_result = re.match(DJANGO_VALID_URL_PATTERN, s_url) is not None
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
        if is_valid_uri(url):
            valid_urls.append(url)
        else:
            not_valid_urls.append(url)
    
    return (valid_urls, not_valid_urls)

def read_url(url: str, _rec: bool = False):
    """
    Simply reads the contents of an url.
    
    Parameters (str):
        the url to open
    _rec (bool):
        indicates recursion depth 0/1
        
    Returns
    (bytes):
        the contents of the url
    (str):
        on error; a custom error message
    """
    try:
        with urllib.request.urlopen(url, timeout=4) as _response:
            response = _response.read()
        return response
    except ValueError:
        if _rec:
            return f"Error at opening the following url:\n{url}"
        return read_url(DEFAULT_SCHEME+url, True)
    except OSError:
        return f"Error at opening the following url:\n{url}"
