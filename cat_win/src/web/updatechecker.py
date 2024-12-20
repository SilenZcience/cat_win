"""
updatechecker
"""

import json
import urllib.request

from cat_win.src.const.colorconstants import CKW
from cat_win.src.service.helper.environment import get_py_executable
from cat_win.src.service.helper.iohelper import err_print
from cat_win import __url__


# UNSAFE:
# UPDATE MAY INCLUDE FUNDAMENTAL CHANGES
# recognized by a higher version number in earlier position
# !.!._
# SAFE:
# recognized by a higher version number in the last position
# _._.!
STATUS_UP_TO_DATE = 0
STATUS_STABLE_RELEASE_AVAILABLE = 1
STATUS_UNSAFE_STABLE_RELEASE_AVAILABLE = -1
STATUS_PRE_RELEASE_AVAILABLE = 2
STATUS_UNSAFE_PRE_RELEASE_AVAILABLE = -2


def get_stable_package_version(package: str) -> str:
    """
    retrieve the official PythonPackageIndex information regarding
    a package.

    Parameters:
    package (str):
        the package name to check

    Returns:
    (str):
        a version representation (latest stable package)
        on Error: a zero version '0.0.0
    """
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json",
                                    timeout=2) as _response:
            response = _response.read()
        return json.loads(response)['info']['version']
    except (ValueError, OSError, KeyError):
        return '0.0.0'


def get_latest_package_version(package: str) -> str:
    """
    retrieve the official PythonPackageIndex information regarding
    a package.

    Parameters:
    package (str):
        the package name to check

    Returns:
    (str):
        a version representation (includes pre-releases)
        on Error: a zero version '0.0.0
    """
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json",
                                    timeout=2) as _response:
            response = _response.read()
        return sorted(
            json.loads(response)['releases'].items(),
            key=lambda x: x[1][0]['upload_time'] if x[1] else '1970-01-01T00:00:00',
            reverse=True
        )[0][0]
    except (ValueError, OSError, KeyError, IndexError):
        return '0.0.0'


def only_numeric(_s: str) -> int:
    """
    strips every non-numeric character of a string.

    Parameters:
    s (str):
        the string to filter.

    Returns:
    (int):
        the resulting number of the string containing
        only numeric values
    """
    return int('0' + ''.join(filter(str.isdigit, _s)))


def only_alpha(_s: str) -> str:
    """
    strips every numeric character of a string and
    appends 'z' for comparison.

    Parameters:
    s (str):
        the string to filter.

    Returns:
    (str):
        the resulting string of the string containing
        only alpha chars and 'z'
    """
    x = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join(filter(lambda c: c in x, _s.lower()))


def gen_version_tuples(_v: str, _w: str) -> tuple:
    """
    create comparable version tuples.

    Parameters:
    v (str):
        a version representation like '1.0.33.0'
    w (str):
        a version representation like '1.1.0a'

    Returns:
    (tuple(tuple, tuple)):
        the version tuples of both inputs like
        (('01', '00', '33', '00'), ('01', '01', '0a', '00'))
    """
    v_split, w_split = _v.split('.'), _w.split('.')
    max_split_length = max(map(len, v_split + w_split))
    v_list = [s.zfill(max_split_length) for s in v_split]
    w_list = [s.zfill(max_split_length) for s in w_split]
    max_length = max(len(v_list), len(w_list))
    v_list += [''.zfill(max_split_length)] * (max_length - len(v_list))
    w_list += [''.zfill(max_split_length)] * (max_length - len(w_list))
    return (tuple(v_list), tuple(w_list))

def new_version_available(current_version: str, latest_version: str) -> int:
    """
    Checks whether or not a new version is available.

    Parameters:
    current_version (str):
        a version representation as string
    latest_version (str):
        a version representation as string

    Returns:
    (int):
        a global status code describing the situation
    """
    if current_version.startswith('v'):
        current_version = current_version[1:]
    if latest_version.startswith('v'):
        latest_version = latest_version[1:]
    status = STATUS_UP_TO_DATE
    current, latest = gen_version_tuples(current_version, latest_version)
    i = 0
    for _c, _l in zip(current, latest):
        i += 1
        c_num, l_num = only_numeric(_c), only_numeric(_l)
        c_alpha, l_alpha = only_alpha(_c), only_alpha(_l)
        if c_num > l_num:
            break
        if c_num < l_num:
            status = STATUS_STABLE_RELEASE_AVAILABLE
            for j in range(i-1, len(latest)):
                if not latest[j].isdigit():
                    status = STATUS_PRE_RELEASE_AVAILABLE
                    break
            break
        if c_alpha < l_alpha:
            status = STATUS_PRE_RELEASE_AVAILABLE
            break
        if c_alpha > l_alpha and all(l.isdigit() for l in latest[i-1:]):
            status = STATUS_STABLE_RELEASE_AVAILABLE
            break
    if i < len(current):
        status *= -1
    return status


def print_update_information(package: str, current_version: str, color_dic: dict) -> None:
    """
    prints update information if there are any.

    Parameters:
    package (str):
        the package name to check
    current_version (str):
        a version representation as string of the current version
    color_dic (dict):
        a dictionary translating the color-keywords to ANSI-Colorcodes
    """
    latest_stable_version = get_stable_package_version(package)
    if latest_stable_version == current_version:
        latest_version = get_latest_package_version(package)
        if '0.0.0' != latest_version != latest_stable_version:
            latest_stable_version = latest_version
    status = new_version_available(current_version, latest_stable_version)

    if status == STATUS_UP_TO_DATE:
        return

    message, warning, info = '', '', ''

    if abs(status) == STATUS_STABLE_RELEASE_AVAILABLE:
        message += f"{color_dic[CKW.MESSAGE_IMPORTANT]}"
        message += f"A new stable release of {package} is available: v{latest_stable_version}"
        message += f"{color_dic[CKW.RESET_ALL]}\n{color_dic[CKW.MESSAGE_IMPORTANT]}"
        message += 'To update, run:'
        message += f"{color_dic[CKW.RESET_ALL]}\n{color_dic[CKW.MESSAGE_IMPORTANT]}"
        message += f"{get_py_executable()} -m pip install --upgrade {package}"
    elif abs(status) == STATUS_PRE_RELEASE_AVAILABLE:
        message += f"{color_dic[CKW.MESSAGE_INFORMATION]}"
        message += f"A new pre-release of {package} is available: v{latest_stable_version}"
    message += f"{color_dic[CKW.RESET_ALL]}"
    if status < STATUS_UP_TO_DATE:
        warning += f"{color_dic[CKW.MESSAGE_WARNING]}"
        warning += 'Warning: Due to the drastic version increase, '
        warning += 'backwards compatibility is no longer guaranteed!'
        warning += f"{color_dic[CKW.RESET_ALL]}\n{color_dic[CKW.MESSAGE_WARNING]}"
        warning += 'You may experience fundamental differences.'
        warning += f"{color_dic[CKW.RESET_ALL]}"
    info += f"{color_dic[CKW.MESSAGE_INFORMATION]}Take a look at the changelog here:"
    info += f"{color_dic[CKW.RESET_ALL]}\n{color_dic[CKW.MESSAGE_INFORMATION]}"
    info += f"{__url__}/blob/main/CHANGELOG.md{color_dic[CKW.RESET_ALL]}"

    print(message)
    err_print(warning)
    print(info)
