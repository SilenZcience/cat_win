"""
config
"""

import codecs
import configparser
import os
import shlex
import shutil
import sys

from cat_win.src.const.argconstants import ALL_ARGS
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.service.helper.iohelper import err_print


BOOL_POS_RESPONSE = ['TRUE','YES','Y','1']
BOOL_NEG_RESPONSE = ['FALSE','NO','N','0']


def validator_string(_, d_h: bool=False) -> bool:
    if d_h:
        err_print('Any UTF-8 String (unicode-escaped) without Nullbytes')
        return False
    return True

def validator_int(value: str, d_h: bool=False) -> bool:
    if d_h:
        err_print('Integers greater than Zero or Zero')
        return False
    return value.isdigit() and int(value) >= 0

def validator_int_pos(value: str, d_h: bool=False) -> bool:
    if d_h:
        err_print('Integers greater than Zero')
        return False
    return value.isdigit() and int(value) > 0

def validator_bool(value: str, d_h: bool=False) -> bool:
    if d_h:
        err_print(BOOL_POS_RESPONSE, '&', BOOL_NEG_RESPONSE, '(not case sensitive)')
        return False
    return value.upper() in BOOL_POS_RESPONSE + BOOL_NEG_RESPONSE

def validator_encoding(value: str, d_h: bool=False) -> bool:
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
        DKW.END_MARKER_SYMBOL: '$',
        DKW.BLANK_REMOVE_WS_LINES: False,
        DKW.PEEK_SIZE: 5,
        DKW.SUMMARY_UNIQUE_ELEMENTS: False,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: 4,
        DKW.STRINGS_DELIMETER: '\n',
        DKW.EDITOR_INDENTATION: '\t',
        DKW.EDITOR_AUTO_INDENT: False,
        DKW.HEX_EDITOR_COLUMNS: 16,
        DKW.MORE_STEP_LENGTH: 0,
        DKW.UNICODE_ESCAPED_ECHO: True,
        DKW.UNICODE_ESCAPED_EDITOR_SEARCH: True,
        DKW.UNICODE_ESCAPED_EDITOR_REPLACE: True,
        DKW.UNICODE_ESCAPED_FIND: True,
        DKW.UNICODE_ESCAPED_REPLACE: True,
    }

    v_validation = {
        DKW.DEFAULT_COMMAND_LINE: validator_string,
        DKW.DEFAULT_FILE_ENCODING: validator_encoding,
        DKW.LARGE_FILE_SIZE: validator_int,
        DKW.STRIP_COLOR_ON_PIPE: validator_bool,
        DKW.IGNORE_UNKNOWN_BYTES: validator_bool,
        DKW.END_MARKER_SYMBOL: validator_string,
        DKW.BLANK_REMOVE_WS_LINES: validator_bool,
        DKW.PEEK_SIZE: validator_int_pos,
        DKW.SUMMARY_UNIQUE_ELEMENTS: validator_bool,
        DKW.STRINGS_MIN_SEQUENCE_LENGTH: validator_int_pos,
        DKW.STRINGS_DELIMETER: validator_string,
        DKW.EDITOR_INDENTATION: validator_string,
        DKW.EDITOR_AUTO_INDENT: validator_bool,
        DKW.HEX_EDITOR_COLUMNS: validator_int_pos,
        DKW.MORE_STEP_LENGTH: validator_int,
        DKW.UNICODE_ESCAPED_ECHO: validator_bool,
        DKW.UNICODE_ESCAPED_EDITOR_SEARCH: validator_bool,
        DKW.UNICODE_ESCAPED_EDITOR_REPLACE: validator_bool,
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
        self.custom_commands = {}

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
            if '\0' in value.encode().decode('unicode_escape'):
                return False
        except UnicodeError:
            return False
        return self.v_validation[element](value)

    def get_cmd(self) -> list:
        """
        split the default command line string correctly into a parameter list
        
        Returns
        (list):
            the default command line splitted using shell like syntax
        """
        return shlex.split(self.const_dic.get(DKW.DEFAULT_COMMAND_LINE, ''))

    def get_args(self, argv: list) -> list:
        """
        modifies the sys.argv parameter list depending on the custom commands and config settings.
        
        Parameters:
        argv (list):
            sys.argv
        
        Returns
        new_argv (list):
            the modified sys.argv to use
        """
        argv += self.get_cmd()
        new_argv = []
        for arg in argv:
            if arg in self.custom_commands:
                new_argv += self.custom_commands[arg][:]
                continue
            new_argv.append(arg)
        return new_argv

    def load_config(self) -> dict:
        """
        Load the Const Configuration from the config file.
        
        Returns:
        const_dic (dict):
            a dictionary translating from DKW-keywords to values
        On Error: Return the default const config
        """
        self.config_parser.read(self.config_file, encoding='utf-8')
        try:
            self.custom_commands = dict(
                (k, shlex.split(v[1:-1])) for k, v in self.config_parser.items('COMMANDS')
            )
        except configparser.NoSectionError:
            self.config_parser.add_section('COMMANDS')
            self.custom_commands = {}
        try:
            config_consts = dict(self.config_parser.items('CONSTS'))
            for element in self.elements:
                try:
                    self.const_dic[element] = self.convert_config_element(
                        config_consts[element],
                        element
                    )
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

        h_width, _ = shutil.get_terminal_size()
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

        print('-' * columns * (index_offset+element_offset))

        config_menu = ''
        for c_index, (command, value) in enumerate(self.custom_commands.items()):
            config_menu += f"{c_index+len(self.elements)+1: <{index_offset}}: "
            element = f"{command} = {' '.join(value)}"
            config_menu += f"{element: <{element_offset}}"
            if c_index % columns == columns-1:
                config_menu += '\n'
        if config_menu:
            print(config_menu)
        print(f"{len(self.elements)+len(self.custom_commands)+1: <{index_offset}}: ", end='')
        print('<NEW CUSTOM COMMAND>')

    def _save_config(self, keyword: str, value: str = '', section: str = 'CONSTS'):
        """
        write the value to the config-file
        
        Parameters:
        keyword (str):
            the keyword in self.elements
        value (str):
            the value to write
        """
        if keyword is not None:
            self.config_parser.set(section, keyword, f'"{value}"')
        try:
            with open(self.config_file, 'w', encoding='utf-8') as conf:
                self.config_parser.write(conf)
            print(f"Successfully updated config file:\n\t{self.config_file}")
        except OSError:
            err_print(f"Could not write to config file:\n\t{self.config_file}")

    def _save_config_element(self, keyword: str) -> None:
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

    def _save_config_custom_command(self, keyword: str, forwarded: bool = False) -> None:
        if not forwarded:
            print(f"Successfully selected custom command '{keyword}'")
            c_value_rep = repr(' '.join(self.custom_commands[keyword]))
            if c_value_rep[0] not in ['"', "'"]:
                c_value_rep = f"'{c_value_rep}'"
            print(f"The current value of '{keyword}' is {c_value_rep}", end=' ')

        value = None
        try:
            value = input('Input new value: ')
        except EOFError:
            err_print('\nAborting due to End-of-File character...')
            return

        if not value:
            self.config_parser.remove_option('COMMANDS', keyword)
            self._save_config(None)
            return

        self._save_config(keyword, value, 'COMMANDS')

    def _save_config_add_custom_command(self) -> None:
        def validator_custom_command(value: str, d_h: bool=False) -> bool:
            if d_h:
                err_print("The command needs to start with a '-' ", end='')
                err_print('and cannot be a duplicate of an existing command')
                return False
            if not value:
                return False
            if not value.startswith('-'):
                return False
            if value in self.custom_commands:
                return False
            if value in [x.short_form for x in ALL_ARGS] + [x.long_form for x in ALL_ARGS]:
                return False
            return True

        value = None
        while not validator_custom_command(value):
            if value is not None:
                err_print(f"Something went wrong. Invalid option: '{value}'.")
                validator_custom_command(None, True)
            try:
                value = input('Input new custom command: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return

        print(f"Successfully added new custom command '{value}'")
        self._save_config_custom_command(value, True)

    def save_config(self) -> None:
        """
        Guide the User through the configuration options and save the changes.
        Assume, that the current config is already loaded/
        the method load_config() was already called.
        """
        self._print_all_available_elements()
        keyword = ''
        while True:
            if keyword in self.elements:
                return self._save_config_element(keyword)
            if keyword in self.custom_commands:
                return self._save_config_custom_command(keyword)
            if keyword == '<NEW CUSTOM COMMAND>':
                return self._save_config_add_custom_command()
            if keyword != '':
                err_print(f"Something went wrong. Unknown keyword '{keyword}'")
            try:
                keyword = input('Input name or id of keyword to change: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return
            if keyword.isdigit():
                if (
                    len(self.elements) < int(keyword) and
                    int(keyword) <= len(self.elements)+len(self.custom_commands)
                ):
                    for index, key in enumerate(self.custom_commands, start=1):
                        if len(self.elements)+index == int(keyword):
                            keyword = key
                            break
                    continue
                if int(keyword) == len(self.elements)+len(self.custom_commands)+1:
                    keyword = '<NEW CUSTOM COMMAND>'
                    continue
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)
                ) else keyword

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
            print(f"Successfully removed config file:\n\t{self.config_file}")
        except FileNotFoundError:
            err_print('No active config file has been found.')
        except PermissionError:
            err_print(f"Permission denied! Error deleting config file:\n\t{self.config_file}")
        except OSError:
            err_print('An unexpected error occured.')
