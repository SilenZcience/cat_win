"""
config
"""

import codecs
import configparser
import os
import shlex
import sys

from cat_win.const.defaultconstants import DKW


BOOL_POS_RESPONSE = ['TRUE','YES','Y','1']
BOOL_NEG_RESPONSE = ['FALSE','NO','N','0']
BOOL_RESPONSE = BOOL_POS_RESPONSE + BOOL_NEG_RESPONSE


def validator_string(_, d_h: bool=False):
    if d_h:
        print('Any Utf-8 String', file=sys.stderr)
        return False
    return True

def validator_int(value: str, d_h: bool=False):
    if d_h:
        print('Integers greater than Zero', file=sys.stderr)
        return False
    return value.isdigit() and int(value) >= 0

def validator_bool(value: str, d_h: bool=False):
    if d_h:
        print(BOOL_RESPONSE, '(not case sensitive)', file=sys.stderr)
        return False
    return value.upper() in BOOL_RESPONSE

def validator_encoding(value: str, d_h: bool=False):
    if d_h:
        print('Valid Encoding Formats defined by the current Python Interpreter', file=sys.stderr)
        return False
    try:
        return codecs.lookup(value) is not None
    except LookupError:
        return False


class Config:
    """
    manages the constant configuration. Displays the user interface,
    allows for reading and writing the config file.
    """
    default_dic = {
        DKW.DEFAULT_COMMAND_LINE: '',
        DKW.DEFAULT_FILE_ENCODING: 'utf-8',
        DKW.LARGE_FILE_SIZE: 1024 * 1024 * 100,  # 100 Megabytes
        DKW.STRIP_COLOR_ON_PIPE: True,
        DKW.EDITOR_INDENTATION: '\t',
        DKW.EDITOR_AUTO_INDENT: False,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: 4,
        DKW.STRINGS_DELIMETER: '\n',
    }

    v_validation = {
        DKW.DEFAULT_COMMAND_LINE: validator_string,
        DKW.DEFAULT_FILE_ENCODING: validator_encoding,
        DKW.LARGE_FILE_SIZE: validator_int,
        DKW.STRIP_COLOR_ON_PIPE: validator_bool,
        DKW.EDITOR_INDENTATION: validator_string,
        DKW.EDITOR_AUTO_INDENT: validator_bool,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: validator_int,
        DKW.STRINGS_DELIMETER: validator_string,
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

    def convert_config_element(self, value: str, element: str):
        """
        Parameters:
        value (str):
            the value to convert
        element (str):
            the element of the const_dict
        
        Returns:
        (element_type):
            whatever the element got converted to
        """
        def fix_invalid_value(value: str, element: str):
            print(f"invalid config value '{value}' for '{element}'", file=sys.stderr)
            print(f"resetting to '{self.default_dic[element]}' ...", file=sys.stderr)
            self._save_config(element, self.default_dic[element])
            sys.exit(1)

        value = value[1:-1] # strip the quotes
        if not self.v_validation[element](value):
            fix_invalid_value(value, element)
        element_type = type(self.default_dic[element])
        if element_type == bool:
            if value.upper() in BOOL_POS_RESPONSE:
                return True
            return False
        return element_type(value.encode().decode('unicode_escape'))

    def is_valid_value(self, value: str, element: str) -> bool:
        """
        check if a given value is a valid argument for an element
        in the constant dict.
        
        Parameters:
        value (str):
            the value to check
        element (str):
            the element of the const_dict
        
        Returns
        (bool):
            indicates whether the value is valid.
        """
        if value is None:
            return False

        try:
            value.encode().decode('unicode_escape')
        except UnicodeError:
            return False
        return self.v_validation[element](value)

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
            config_consts = self.config_parser['CONSTS']
            for element in self.elements:
                try:
                    self.const_dic[element] = self.convert_config_element(
                        config_consts[element],
                        element)
                except KeyError:
                    self.const_dic[element] = self.default_dic[element]
        except KeyError:
            self.config_parser['CONSTS'] = {}
            # If an error occures we simply use the default colors
            self.const_dic = self.default_dic.copy()

        return self.const_dic

    def _print_all_available_elements(self) -> None:
        """
        print all available elements that can be changed.
        """
        print('Here is a list of all available elements you may change:')

        h_width, _ = os.get_terminal_size()
        index_offset = len(str(len(self.elements)))

        longest_char_count = max(map(len, self.elements))
        column_width = index_offset+3 + longest_char_count
        columns = max(h_width // column_width, 1)
        element_offset = longest_char_count + max(
            (h_width - columns * column_width) // columns,
            1
        )

        config_menu = ''
        for index, element in enumerate(self.elements):
            config_menu += f"{index+1: <{index_offset}}: "
            config_menu += f"{element: <{element_offset}}"
            if index % columns == columns-1:
                config_menu += '\n'

        print(config_menu)

    def _save_config(self, keyword: str, value: str):
        """
        write the value to the config-file
        
        Parameters:
        keyword (str):
            the keyword in self.elements
        value (str):
            the value to write
        """
        self.config_parser['CONSTS'][keyword] = f'"{value}"'
        try:
            with open(self.config_file, 'w', encoding='utf-8') as conf:
                self.config_parser.write(conf)
            print(f"Successfully updated config file:\n\t{self.config_file}")
        except OSError:
            print(f"Could not write to config file:\n\t{self.config_file}", file=sys.stderr)


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
                print(f"Something went wrong. Unknown keyword '{keyword}'", file=sys.stderr)
            try:
                keyword = input('Input name or id of keyword to change: ')
            except EOFError:
                print('\nAborting due to End-of-File character...', file=sys.stderr)
                return
            if keyword.isdigit():
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)) else keyword
        print(f"Successfully selected element '{keyword}'")
        c_value_rep = repr(self.const_dic[keyword])
        if c_value_rep[0] not in ['"', "'"]:
            c_value_rep = f"'{c_value_rep}'"
        print(f"The current value of '{keyword}' is {c_value_rep}")

        value = None
        while not self.is_valid_value(value, keyword):
            if value is not None:
                print(f"Something went wrong. Invalid option: '{value}'.", file=sys.stderr)
                print('Valid Options are: ', end='', file=sys.stderr)
                self.v_validation[keyword](None, True)
            try:
                value = input('Input new value: ')
            except EOFError:
                print('\nAborting due to End-of-File character...', file=sys.stderr)
                return

        self._save_config(keyword, value)
