#!/usr/bin/python
import os
import sys
sys.path.append('../cat_win')

from cat_win import __version__

CAT_WIN_VERSION = '0.' + __version__
CAT_WIN_VERSION_SEP = CAT_WIN_VERSION.replace('.', ',')
print('Current Version:', CAT_WIN_VERSION, CAT_WIN_VERSION_SEP)


script_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
CATversionFileDIR = os.path.abspath(os.path.join(root_dir, 'bin_'))
CATWversionFile = os.path.abspath(os.path.join(root_dir, 'bin_', 'catwversionfile'))
CATSversionFile = os.path.abspath(os.path.join(root_dir, 'bin_', 'catsversionfile'))
print('VersionFile Path:', CATWversionFile)
print('VersionFile Path:', CATSversionFile)

def get_version_file_content(cat_win_v_sep: str, cat_win_v: str, suffix: str) -> str:
    return f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({cat_win_v_sep}),
    prodvers=({cat_win_v_sep}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'OS Independent cat Command-line Tool.'),
        StringStruct(u'FileVersion', u'{cat_win_v}'),
        StringStruct(u'InternalName', u'cat_win'),
        StringStruct(u'LegalCopyright', u''),
        StringStruct(u'OriginalFilename', u'cat{suffix}.exe'),
        StringStruct(u'ProductName', u'cat_win'),
        StringStruct(u'ProductVersion', u'{cat_win_v}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""


if not os.path.exists(CATversionFileDIR):
    os.makedirs(CATversionFileDIR)

with open(CATWversionFile, 'w', encoding='utf-8') as vF:
    vF.write(get_version_file_content(CAT_WIN_VERSION_SEP, CAT_WIN_VERSION, 'w'))

with open(CATSversionFile, 'w', encoding='utf-8') as vF:
    vF.write(get_version_file_content(CAT_WIN_VERSION_SEP, CAT_WIN_VERSION, 's'))
