from json import loads as loadJSON
from urllib.request import urlopen

from cat_win.const.ColorConstants import C_KW

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


def getLastestPackageVersion(package: str) -> str:
    """
    retrieve the official PythonPackageIndex information regarding
    a package.
    
    Parameters:
    package (str):
        the package name to check
        
    Returns:
    (str):
        a version representation
        on Error: a zero version '0.0.0
    """
    try:
        with urlopen(f"https://pypi.org/pypi/{package}/json", timeout=2) as _response:
            response = _response.read()
        return loadJSON(response)['info']['version']
    except:
        return '0.0.0'


def onlyNumeric(s: str) -> int:
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
    return int('0' + ''.join(filter(str.isdigit, s)))


def genVersionTuples(v: str, w: str) -> tuple:
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
    vSplit, wSplit = v.split('.'), w.split('.')
    maxSplitLen = max(map(len, vSplit + wSplit))
    vList = [s.zfill(maxSplitLen) for s in vSplit]
    wList = [s.zfill(maxSplitLen) for s in wSplit]
    maxLength = max(len(vList), len(wList))
    vList += [''.zfill(maxSplitLen)] * (maxLength - len(vList))
    wList += [''.zfill(maxSplitLen)] * (maxLength - len(wList))
    return (tuple(vList), tuple(wList))

def newVersionAvailable(currentVersion: str, latestVersion: str) -> int:
    """
    Checks whether or not a new version is available.
    
    Parameters:
    currentVersion (str):
        a version representation as string
    latestVersion (str):
        a version representation as string
    
    Returns:
    (int):
        a global status code describing the situation
    """
    if currentVersion.startswith('v'):
        currentVersion = currentVersion[1:]
    if latestVersion.startswith('v'):
        latestVersion = latestVersion[1:]
    status = STATUS_UP_TO_DATE
    current, latest = genVersionTuples(currentVersion, latestVersion)
    i = 0
    for c, l in zip(current, latest):
        i += 1
        cNum, lNum = onlyNumeric(c), onlyNumeric(l)
        if cNum > lNum:
            break
        if cNum < lNum:
            status = STATUS_STABLE_RELEASE_AVAILABLE
            if not l.isdigit():
                status = STATUS_PRE_RELEASE_AVAILABLE
            break
        if c < l:
            status = STATUS_PRE_RELEASE_AVAILABLE
            break
    if i < len(current):
        status *= -1
    return status


def printUpdateInformation(package: str, currentVersion: str, color_dic: dict) -> None:
    """
    prints update information if there are any.
    
    Parameters:
    package (str):
        the package name to check
    currentVersion (str):
        a version representation as string of the current version
    color_dic (dict):
        a dictionary translating the color-keywords to ANSI-Colorcodes
    """
    latestVersion = getLastestPackageVersion(package)
    status = newVersionAvailable(currentVersion, latestVersion)
    if status == STATUS_UP_TO_DATE:
        return
    message = f""
    warning = f""
    info    = f""
    if abs(status) == STATUS_STABLE_RELEASE_AVAILABLE:
        message += f"{color_dic[C_KW.MESSAGE_IMPORTANT]}"
        message += f"A new stable release of {package} is available: v{latestVersion}"
        message += f"{color_dic[C_KW.RESET_ALL]}\n{color_dic[C_KW.MESSAGE_IMPORTANT]}"
        message += f"To update, run:"
        message += f"{color_dic[C_KW.RESET_ALL]}\n{color_dic[C_KW.MESSAGE_IMPORTANT]}"
        message += f"python -m pip install --upgrade {package}"
    elif abs(status) == STATUS_PRE_RELEASE_AVAILABLE:
        message += f"{color_dic[C_KW.MESSAGE_INFORMATION]}"
        message += f"A new pre-release of {package} is available: v{latestVersion}"
    message += f"{color_dic[C_KW.RESET_ALL]}"
    if status < STATUS_UP_TO_DATE:
        warning += f"{color_dic[C_KW.MESSAGE_WARNING]}"
        warning += f"Warning: Due to the drastic version increase, backwards compatibility is no longer guaranteed!"
        warning += f"{color_dic[C_KW.RESET_ALL]}\n{color_dic[C_KW.MESSAGE_WARNING]}"
        warning += f"You may experience fundamental differences."
        warning += f"{color_dic[C_KW.RESET_ALL]}"
    info += f"{color_dic[C_KW.MESSAGE_INFORMATION]}Take a look at the changelog here:"
    info += f"{color_dic[C_KW.RESET_ALL]}\n{color_dic[C_KW.MESSAGE_INFORMATION]}"
    info += f"{__url__}/blob/main/CHANGELOG.md{color_dic[C_KW.RESET_ALL]}"
    print(message)
    print(warning)
    print(info)
