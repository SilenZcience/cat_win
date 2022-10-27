#!/usr/bin/python
import os
from sys import exit

error_code = 1

script_dir = os.path.dirname(__file__)
dist_dir = os.path.join(script_dir, "../dist/" )
print(script_dir)
print(dist_dir)

target_package = os.listdir(dist_dir)
print("Found packages:", target_package)

if len(target_package) > 0:
    target_package_whl = [package for package in target_package if package[-4:] == ".whl"]
    print(target_package_whl)
    target_package_tar = [package for package in target_package if package[-7:] == ".tar.gz"]
    print(target_package_tar)
    for package in target_package_whl:
        print("Package:", dist_dir + package)
        error_code = os.system('pip install --upgrade ' + dist_dir + package)
    for package in target_package_tar:
        print("Package:", dist_dir + package)
        error_code = os.system('pip install --upgrade ' + dist_dir + package)

exit(error_code)