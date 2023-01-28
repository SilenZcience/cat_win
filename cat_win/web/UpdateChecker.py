from requests import get as getRequest
from cat_win.const.ColorConstants import ColoramaOptions


def getLastestPackageVersion(package: str) -> str:
    try:
        response = getRequest(f'https://pypi.org/pypi/{package}/json', timeout=2)
        return response.json()['info']['version']
    except:
        return "0"


def newVersionAvailable(currentVersion: str, latestVersion: str) -> bool:
    currentVersion = ''.join(c for c in currentVersion if c.isdigit())
    latestVersion = ''.join(c for c in latestVersion if c.isdigit())
    return int(latestVersion) > int(currentVersion)


def printUpdateInformation(package: str, currentVersion: str):
    latestVersion = getLastestPackageVersion(package)
    if newVersionAvailable(currentVersion, latestVersion):
        print(ColoramaOptions.C_Fore['YELLOW'])
        print(f"A new release of {package} is available: {latestVersion}")
        print("To update, run:")
        print(f"python -m pip install --upgrade {package}")
        print(ColoramaOptions.C_Style_Reset)
