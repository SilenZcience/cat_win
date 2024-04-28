"""
config
"""

import codecs
import configparser
import os
import shlex
import sys

from cat_win.src.const.defaultconstants import DKW
from cat_win.src.service.helper.iohelper import err_print


BOOL_POS_RESPONSE = ['TRUE','YES','Y','1']
BOOL_NEG_RESPONSE = ['FALSE','NO','N','0']
BOOL_RESPONSE = BOOL_POS_RESPONSE + BOOL_NEG_RESPONSE


def validator_string(_, d_h: bool=False):
    if d_h:
        err_print('Any UTF-8 String (unicode-escaped)')
        return False
    return True

def validator_int(value: str, d_h: bool=False):
    if d_h:
        err_print('Integers greater than Zero or Zero')
        return False
    return value.isdigit() and int(value) >= 0

def validator_int_pos(value: str, d_h: bool=False):
    if d_h:
        err_print('Integers greater than Zero')
        return False
    return value.isdigit() and int(value) > 0

def validator_bool(value: str, d_h: bool=False):
    if d_h:
        err_print(BOOL_RESPONSE, '(not case sensitive)')
        return False
    return value.upper() in BOOL_RESPONSE

def validator_encoding(value: str, d_h: bool=False):
    if d_h:
        err_print('Valid Encoding Formats defined by the current Python Interpreter')
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
        DKW.IGNORE_UNKNOWN_BYTES: False,
        DKW.PEEK_SIZE: 5,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: 4,
        DKW.STRINGS_DELIMETER: '\n',
        DKW.EDITOR_INDENTATION: '\t',
        DKW.EDITOR_AUTO_INDENT: False,
        DKW.HEX_EDITOR_COLUMNS: 16,
        DKW.MORE_STEP_LENGTH: 0,
        DKW.UNICODE_ESCAPED_ECHO: True,
        DKW.UNICODE_ESCAPED_FIND: True,
        DKW.UNICODE_ESCAPED_REPLACE: True,
    }

    v_validation = {
        DKW.DEFAULT_COMMAND_LINE: validator_string,
        DKW.DEFAULT_FILE_ENCODING: validator_encoding,
        DKW.LARGE_FILE_SIZE: validator_int,
        DKW.STRIP_COLOR_ON_PIPE: validator_bool,
        DKW.IGNORE_UNKNOWN_BYTES: validator_bool,
        DKW.PEEK_SIZE: validator_int_pos,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: validator_int_pos,
        DKW.STRINGS_DELIMETER: validator_string,
        DKW.EDITOR_INDENTATION: validator_string,
        DKW.EDITOR_AUTO_INDENT: validator_bool,
        DKW.HEX_EDITOR_COLUMNS: validator_int_pos,
        DKW.MORE_STEP_LENGTH: validator_int,
        DKW.UNICODE_ESCAPED_ECHO: validator_bool,
        DKW.UNICODE_ESCAPED_FIND: validator_bool,
        DKW.UNICODE_ESCAPED_REPLACE: validator_bool,
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
            c_value_rep = repr(self.default_dic[element])
            if c_value_rep[0] not in ['"', "'"]:
                c_value_rep = f"'{c_value_rep}'"
            err_print(f"invalid config value '{value}' for '{element}'")
            err_print(f"resetting to {c_value_rep} ...")
            self._save_config(element, self.default_dic[element])
            sys.exit(1)

        value = value[1:-1] # strip the quotes

        # check validity and possibly reset to default:
        if not self.v_validation[element](value):
            fix_invalid_value(value, element)
        try:
            value.encode().decode('unicode_escape').encode('latin-1').decode()
        except UnicodeError:
            fix_invalid_value(value, element)

        element_type = type(self.default_dic[element])
        if element_type == bool:
            if value.upper() in BOOL_POS_RESPONSE:
                return True
            return False
        return element_type(value.encode().decode('unicode_escape').encode('latin-1').decode())

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
            self.config_parser.read(self.config_file, encoding='utf-8')
            config_consts = dict(self.config_parser.items('CONSTS'))
            for element in self.elements:
                try:
                    self.const_dic[element] = self.convert_config_element(
                        config_consts[element],
                        element)
                except KeyError:
                    self.const_dic[element] = self.default_dic[element]
        except configparser.NoSectionError:
            self.config_parser.add_section('CONSTS')
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

    def _save_config(self, keyword: str, value: str = ''):
        """
        write the value to the config-file
        
        Parameters:
        keyword (str):
            the keyword in self.elements
        value (str):
            the value to write
        """
        if keyword is not None:
            self.config_parser.set('CONSTS', keyword, f'"{value}"')
        try:
            with open(self.config_file, 'w', encoding='utf-8') as conf:
                self.config_parser.write(conf)
            print(f"Successfully updated config file:\n\t{self.config_file}")
        except OSError:
            err_print(f"Could not write to config file:\n\t{self.config_file}")


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
                err_print(f"Something went wrong. Unknown keyword '{keyword}'")
            try:
                keyword = input('Input name or id of keyword to change: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return
            if keyword.isdigit():
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)) else keyword
        print(f"Successfully selected element '{keyword}'")
        c_value_rep = repr(self.const_dic[keyword])
        if c_value_rep[0] not in ['"', "'"]:
            c_value_rep = f"'{c_value_rep}'"
        d_value_rep = repr(self.default_dic[keyword])
        if d_value_rep[0] not in ['"', "'"]:
            d_value_rep = f"'{d_value_rep}'"
        print(f"The current value of '{keyword}' is {c_value_rep}", end=' ')
        print(f"[Default: {d_value_rep}]")

        value = None
        while not self.is_valid_value(value, keyword):
            if value is not None:
                err_print(f"Something went wrong. Invalid option: '{value}'.")
                err_print('Valid Options are: ', end='')
                self.v_validation[keyword](None, True)
            try:
                value = input('Input new value: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return

        self._save_config(keyword, value)

    def reset_config(self) -> None:
        """
        reset the config to default by simply deleting the config section.
        """
        self.config_parser.remove_section('CONSTS')
        self._save_config(None)

    def remove_config(self) -> None:
        """
        remove the config file.
        """
        try:
            os.remove(self.config_file)
            print('The config file has successfully been removed!')
        except FileNotFoundError:
            err_print('No active config file has been found.')
        except PermissionError:
            err_print('Permission denied! The config file could not be deleted.')
        except OSError:
            err_print('An unexpected error occured.')
