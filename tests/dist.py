#!/usr/bin/python
import os
from sys import exit
from re import search, IGNORECASE

error_code = 1

script_dir = os.path.dirname(__file__)
dist_dir = os.path.join(script_dir, "../dist/" )
print(script_dir)
print(dist_dir)

setup_file_dir = os.path.join(script_dir, "../setup.py")
print(setup_file_dir)
file = open(setup_file_dir, encoding="utf-8")
version_search = search('version.*[\"\'](.*)[\"\']', file.read(), IGNORECASE)
if not version_search:
    exit(error_code)
version_setup = version_search.group(1)
print("setup.py - version:", version_setup)

init_file_dir = os.path.join(script_dir, "../cat_win/__init__.py")
print(init_file_dir)
file = open(init_file_dir, encoding="utf-8")
version_search = search('version.*[\"\'](.*)[\"\']', file.read(), IGNORECASE)
if not version_search:
    exit(error_code)
version_init = version_search.group(1)
print("__init__.py - version:", version_init)

if not version_setup == version_init:
    print("version mismatch!")
    exit(error_code)

target_package = os.listdir(dist_dir)

if len(target_package) > 0:
    print("Found package:", target_package[-1])
    print(dist_dir + target_package[-1])
    error_code = os.system('pip install --upgrade ' + dist_dir + target_package[-1])
    
exit(error_code)