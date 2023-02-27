import os
import subprocess
from sys import exit
from shutil import rmtree
from glob import iglob

script_dir = os.path.dirname(__file__)
package_dir = os.path.abspath(os.path.join(script_dir, '..', 'cat_win'))
entry_dir = os.path.join(package_dir, 'cat.py')
print('script directory:', script_dir)
print('package directory:', package_dir)
print('entry directory:', entry_dir)

# add the pyclip import to the cat.py main file, since pyinstaller will not
# detect the import statement hidden in the middle of the file
cat = ''
with open(entry_dir, 'r', encoding='utf-8') as f:
    cat = f.read()

if cat == '':
    exit(1)

with open(entry_dir, 'w', encoding='utf-8') as f:
    f.write('import pyperclip as pc\n' + cat)

# clear pycache
for path in iglob(package_dir + '/**/__pycache__', recursive=True):
    try:
        print('deleting: ', path)
        rmtree(path)
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}.")

# pyinstaller is more reliable without the __init__ files, they will be created again later.
# temporarily delete all __init__ files except the main one containing information.
_initFiles = []
for path in iglob(package_dir + '/*/__init__.py', recursive=True):
    _initFiles.append(path)
    try:
        print('deleting: ', path)
        os.remove(path)
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}.")

status = 1
command = 'pyinstaller ./cat_win/cat.py --onefile --clean --dist ./bin --version-file ./exeVersionFile -n catw'.split(' ')
# try pyinstaller 3 times at most...
for _ in range(3):
    try:
        sub = subprocess.run(command, check=True)
        print(sub)
        status = sub.returncode
        if status == 0:
            break
    except:
        pass


for _init in _initFiles:
    print('creating: ', _init)
    f = open(_init, 'x', encoding='utf-8')
    f.close()
    
exit(status)
