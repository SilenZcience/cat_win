"""
config
"""

import configparser
import os
import shlex
import sys

from cat_win.const.defaultconstants import DKW


class Config:
    """
    manages the constant configuration. Displays the user interface,
    allows for reading and writing the config file.
    """
    default_dic = {DKW.DEFAULT_COMMAND_LINE: '',
                   DKW.DEFAULT_FILE_ENCODING: 'utf-8',
                   DKW.LARGE_FILE_SIZE: 1024 * 1024 * 100,  # 100 Megabytes
                   }

    elements = list(default_dic.keys())

    def __init__(self, working_dir: str) -> None:
        """
        Initialise the Config() object to load and save
        default parameters..
        
        Parameters:
        working_dir (str):
            the working directory path of the package
        """
        self.working_dir = working_dir
        self.config_file = os.path.join(self.working_dir, 'cat.config')

        self.config_parser = configparser.ConfigParser()
        self.const_dic = {}

        self.longest_char_count = 30
        self.rows = 3

    def get_cmd(self) -> list:
        """
        split the default command line string correctly into a parameter list
        """
        return shlex.split(self.const_dic.get(DKW.DEFAULT_COMMAND_LINE, ''))

    def load_config(self) -> dict:
        """
        Load the Const Configuration from the config file.
        
        Returns:
        const_dic (dict):
            a dictionary translating from DKW-keywords to values
        On Error: Return the default const config
        """
        try:
            self.config_parser.read(self.config_file)
            config_colors = self.config_parser['CONSTS']
            for element in self.elements:
                try:
                    type_def = type(self.default_dic[element])
                    self.const_dic[element] = type_def(config_colors[element])
                except KeyError:
                    self.const_dic[element] = self.default_dic[element]
        except KeyError:
            self.config_parser['CONSTS'] = {}
            # If an error occures we simply use the default colors
            self.const_dic = self.default_dic

        return self.const_dic

    def _print_all_available_elements(self) -> None:
        """
        print all available elements that can be changed.
        """
        print('Here is a list of all available elements you may change:')

        self.longest_char_count = max(map(len, self.elements)) + 12
        index_offset = len(str(len(self.elements) + 1))

        config_menu = ''
        for index, element in enumerate(self.elements):
            config_menu += f"{index+1: <{index_offset}}: "
            config_menu += f"{element: <{self.longest_char_count}}"
            if index % self.rows == self.rows-1:
                config_menu += '\n'

        print(config_menu)

    def save_config(self) -> None:
        """
        Guide the User through the configuration options and save the changes.
        Assume, that the current config is already loaded/
        the method load_config() was already called.
        """
        self._print_all_available_elements()
        keyword = ''
        while keyword not in self.elements:
            if keyword != '':
                print(f"Something went wrong. Unknown keyword '{keyword}'")
            try:
                keyword = input('Input name or id of keyword to change: ')
            except EOFError:
                print('\nAborting due to End-of-File character...', file=sys.stderr)
                return
            if keyword.isdigit():
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)) else keyword
        print(f"Successfully selected element '{keyword}'")
        print(f"The current value of '{keyword}' is '{self.const_dic[keyword]}'")

        def is_valid_value(value: str) -> bool:
            type_def = type(self.default_dic[keyword])
            try:
                type_def(value)
                try:
                    return type_def(value) >= 0
                except TypeError:
                    return bool(value)
            except ValueError:
                return False

        value = ''
        while not is_valid_value(value):
            if value != '':
                print(f"Something went wrong. Invalid option '{value}'.")
            try:
                value = input('Input new value: ')
            except EOFError:
                print('\nAborting due to End-of-File character...', file=sys.stderr)
                return

        self.config_parser['CONSTS'][keyword] = value
        try:
            with open(self.config_file, 'w', encoding='utf-8') as conf:
                self.config_parser.write(conf)
            print(f"Successfully updated config file:\n\t{self.config_file}")
        except OSError:
            print(f"Could not write to config file:\n\t{self.config_file}", file=sys.stderr)
