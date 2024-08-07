#!/usr/bin/python
# import glob
import os
import platform
# import shutil
import subprocess
import sys

script_dir = os.path.dirname(__file__)
package_dir = os.path.abspath(os.path.join(script_dir, '..', 'cat_win'))
entry_dir = os.path.join(package_dir, 'cat.py')
init_dir = os.path.join(package_dir, '__init__.py')
print('script directory:', script_dir)
print('package directory:', package_dir)
print('entry directory:', entry_dir)
print('init directory:', init_dir)

# # add the pyclip import to the cat.py main file, since pyinstaller will not
# # detect the import statement hidden in the middle of the file
# cat = ''
# with open(entry_dir, 'r', encoding='utf-8') as f:
#     cat = f.read()

# if cat == '':
#     sys.exit(1)

# with open(entry_dir, 'w', encoding='utf-8') as f:
#     f.write('import pyperclip as pc\n' + cat)


# change the __sysversion__ to the current sys.version
# to display the correct information in the executable
init = ''
with open(init_dir, 'r', encoding='utf-8') as f:
    init = f.readlines()

if init == '':
    sys.exit(2)

with open(init_dir, 'w', encoding='utf-8') as f:
    for line in init:
        if line.startswith('__sysversion__'):
            f.write(f"__sysversion__ = '{sys.version}'\n")
        else:
            f.write(line)

# # clear pycache
# for path in glob.iglob(package_dir + '/**/__pycache__', recursive=True):
#     try:
#         print('deleting: ', path)
#         shutil.rmtree(path)
#     except OSError as e:
#         print(f"Error: {e.filename} - {e.strerror}.")

# # pyinstaller is more reliable without the __init__ files, they will be created again later.
# # temporarily delete all __init__ files except the main one containing information.
# _initFiles = []
# for path in glob.iglob(package_dir + '/*/__init__.py', recursive=True):
#     _initFiles.append(path)
#     try:
#         print('deleting: ', path)
#         os.remove(path)
#     except OSError as e:
#         print(f"Error: {e.filename} - {e.strerror}.")

status = 1
platform_name = platform.system().lower()
command = f'pyinstaller ./cat_win/__main__.py --onefile --clean --dist ./temp/{platform_name} --icon ./temp/cat_icon.ico --version-file ./temp/catwversionfile -n catw'.split(' ')
# try pyinstaller 3 times at most...
for _ in range(3):
    try:
        sub = subprocess.run(command, check=True)
        print(sub)
        status = sub.returncode
        if status == 0:
            break
    except Exception:
        pass

if status > 0:
    sys.exit(status)

command = f'pyinstaller ./cat_win/repl.py --onefile --clean --dist ./temp/{platform_name} --icon ./temp/cat_icon.ico --version-file ./temp/catsversionfile -n cats'.split(' ')
# try pyinstaller 3 times at most...
for _ in range(3):
    try:
        sub = subprocess.run(command, check=True)
        print(sub)
        status = sub.returncode
        if status == 0:
            break
    except Exception:
        pass


# for _init in _initFiles:
#     print('creating: ', _init)
#     f = open(_init, 'x', encoding='utf-8')
#     f.close()

sys.exit(status)
