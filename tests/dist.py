#!/usr/bin/python
from glob import glob
from os import system
from sys import exit

target_package = glob("..\\dist\\*.tar.gz")
error_code = 0
if len(target_package) > 0:
    error_code = system('pip install --upgrade ' + target_package[-1])

exit(error_code)