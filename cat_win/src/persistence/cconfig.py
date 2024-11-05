"""
cconfig
"""

import configparser
import os
import shutil
import sys

from cat_win.src.const.colorconstants import ColorOptions, CKW
from cat_win.src.const.escapecodes import ESC_CODE, color_code_256, color_code_truecolor
from cat_win.src.const.regex import CONFIG_VALID_COLOR, CONFIG_VALID_ANSI
from cat_win.src.service.helper.iohelper import err_print


class CConfig:
    """
    manages the color configuration. Displays the user interface,
    allows for reading and writing the config file.
    """
    default_dic = {
        CKW.RESET_ALL           : ColorOptions.Style['RESET'],
        CKW.RESET_FOUND         : ColorOptions.Fore['RESET'],
        CKW.RESET_MATCHED       : ColorOptions.Back['RESET'],
        CKW.LINE_LENGTH         : ColorOptions.Fore['LIGHTBLUE'],
        CKW.NUMBER              : ColorOptions.Fore['GREEN'],
        CKW.FILE_PREFIX         : ColorOptions.Fore['LIGHTMAGENTA'],
        CKW.ENDS                : ColorOptions.Back['YELLOW'],
        CKW.CHARS               : ColorOptions.Fore['YELLOW'],
        CKW.SUMMARY             : ColorOptions.Fore['CYAN'],
        CKW.ATTRIB              : ColorOptions.Fore['CYAN'],
        CKW.ATTRIB_POSITIVE     : ColorOptions.Fore['LIGHTGREEN'],
        CKW.ATTRIB_NEGATIVE     : ColorOptions.Fore['LIGHTRED'],
        CKW.CHECKSUM            : ColorOptions.Fore['CYAN'],
        CKW.EVALUATION          : ColorOptions.Fore['BLUE'],
        CKW.CONVERSION          : ColorOptions.Fore['CYAN'],
        CKW.RAWVIEWER           : ColorOptions.Fore['LIGHTBLACK'],
        CKW.FOUND               : ColorOptions.Fore['RED'],
        CKW.FOUND_MESSAGE       : ColorOptions.Fore['MAGENTA'],
        CKW.MATCHED             : ColorOptions.Back['CYAN'],
        CKW.MATCHED_MESSAGE     : ColorOptions.Fore['LIGHTCYAN'],
        CKW.REPLACE             : ColorOptions.Fore['YELLOW'],
        CKW.PROGRESSBAR_DONE    : ColorOptions.Fore['LIGHTGREEN'],
        CKW.PROGRESSBAR_MISSING : ColorOptions.Fore['LIGHTMAGENTA'],
        CKW.REPL_PREFIX         : ColorOptions.Fore['MAGENTA'],
        CKW.MESSAGE_INFORMATION : ColorOptions.Fore['LIGHTBLACK'],
        CKW.MESSAGE_IMPORTANT   : ColorOptions.Fore['YELLOW'],
        CKW.MESSAGE_WARNING     : ColorOptions.Fore['RED'],
    }
    elements = [k for k in default_dic.keys() if 'reset' not in k]

    def __init__(self, working_dir: str) -> None:
        """
        Initialise the CConfig() object to load and save
        the color configs.
        
        Parameters:
        working_dir (str):
            the working directory path of the package
        """
        self.working_dir = working_dir
        self.config_file = os.path.join(self.working_dir, 'cat.config')

        self.exclusive_definitions = {'Fore': [CKW.FOUND],  # can only be Foreground
                                      'Back': [CKW.MATCHED]}  # can only be Background
        self.config_parser = configparser.ConfigParser()
        self.color_dic = {}

    def convert_config_element(self, value: str, element: str) -> str:
        """
        Parameters:
        value (str):
            the value to convert
        element (str):
            the element of the const_dict
        
        Returns:
        color_code (str):
            the ansi escape code for the color
        """
        if CONFIG_VALID_COLOR.match(value):
            color_ground = value[0]
            color_split = value[1:].split(';')
            if len(color_split) == 1:
                return color_code_256(int(color_split[0]),
                                            color_ground == 'f')
            return color_code_truecolor(*[int(c) for c in color_split],
                                                  color_ground == 'f')
        if CONFIG_VALID_ANSI.match(value):
            return f"{ESC_CODE}{value}"
        if value.count('.') == 1:
            color_type, color = value.split('.')
            return ColorOptions.Fore[color] if color_type == 'Fore' else ColorOptions.Back[color]
        err_print(f"invalid config value {repr(value)} for '{element}'")
        err_print(f"resetting to {repr(self.default_dic[element][1:])} ...")
        self._save_config(element, self.default_dic[element][1:])
        sys.exit(1)

    def load_config(self) -> dict:
        """
        Load the Color Configuration from the config file.
        
        Returns:
        color_dic (dict):
            a dictionary translating from CKW-keywords to ANSI-Colorcodes
        On Error: Return the default color config
        """
        try:
            self.config_parser.read(self.config_file, encoding='utf-8')
            config_colors = dict(self.config_parser.items('COLORS'))
            for element in self.elements:
                try:
                    self.color_dic[element] = self.convert_config_element(
                        config_colors[element],
                        element
                    )
                except (KeyError, ValueError):
                    self.color_dic[element] = self.default_dic[element]
        except configparser.NoSectionError:
            self.config_parser.add_section('COLORS')
            # If an error occures we simply use the default colors
            self.color_dic = self.default_dic.copy()

        # The Reset Codes should always be the same
        self.color_dic[CKW.RESET_ALL] = ColorOptions.Style['RESET']
        self.color_dic[CKW.RESET_FOUND] = ColorOptions.Fore['RESET']
        self.color_dic[CKW.RESET_MATCHED] = ColorOptions.Back['RESET']

        return self.color_dic

    def _print_get_all_available_colors(self) -> list:
        """
        prints all available color options to choose from.
        
        Returns:
        options (list):
            the same list containing all available colors.
        """
        print('Here is a list of all available default color options you may choose:')

        fore_options = list(ColorOptions.Fore.items())
        fore_options = [(k, v) for k, v in fore_options if k != 'RESET']
        back_options = list(ColorOptions.Back.items())
        back_options = [(k, v) for k, v in back_options if k != 'RESET']

        h_width, _ = shutil.get_terminal_size()
        index_offset = max(len(str(len(fore_options) + len(back_options))),
                           len(str(len(self.elements))))

        longest_char_count = max(max(map(len, fore_options+back_options))+5,
                                 max(map(len, self.elements)))
        column_width = index_offset+4 + longest_char_count
        columns = max(h_width // column_width, 1)
        element_offset = longest_char_count + max(
            (h_width - columns * column_width) // columns,
            1
        )

        config_menu = ''
        options = []

        for index, fore_option in enumerate(fore_options):
            key, value = fore_option
            f_key = f"Fore.{key}"
            config_menu += f"{index+1: <{index_offset}}: {value}"
            if key == 'BLACK':
                config_menu += f"{ColorOptions.Back['LIGHTBLACK']}"
                config_menu += f"{f_key}{ColorOptions.Style['RESET']}"
                config_menu += f"{' ' * (element_offset-len(f_key))} "
            else:
                config_menu += f"{f_key: <{element_offset}}"
                config_menu += f"{ColorOptions.Style['RESET']} "
            if index % columns == columns-1:
                config_menu += '\n'
            options.append('Fore.' + key)
        config_menu += '\n'
        for index, back_option in enumerate(back_options):
            key, value = back_option
            b_key = f"Back.{key}"
            config_menu += f"{len(fore_options)+index+1: <{index_offset}}: {value}"
            if key not in ['NONE', 'BLACK']:
                config_menu += f"{ColorOptions.Fore['BLACK']}"
            config_menu += f"{b_key: <{element_offset}}"
            config_menu += f"{ColorOptions.Style['RESET']} "
            if index % columns == columns-1:
                config_menu += '\n'
            options.append('Back.' + key)
        config_menu += '\n'

        print(config_menu)
        return options

    def _print_all_available_elements(self) -> None:
        """
        print all available elements that can be changed.
        """
        print('Here is a list of all available elements you may change:')

        h_width, _ = shutil.get_terminal_size()
        index_offset = len(str(len(self.elements)))

        longest_char_count = max(map(len, self.elements))
        column_width = index_offset+4 + longest_char_count
        columns = max(h_width // column_width, 1)
        element_offset = longest_char_count + max(
            (h_width - columns * column_width) // columns,
            1
        )
        config_menu = ''

        for index, element in enumerate(self.elements):
            config_menu += f"{index+1: <{index_offset}}: {self.color_dic[element]}"
            if self.color_dic[element] == ColorOptions.Fore['BLACK']:
                config_menu += f"{ColorOptions.Back['LIGHTBLACK']}"
                config_menu += f"{element}{ColorOptions.Style['RESET']}"
                config_menu += f"{' ' * (element_offset-len(element))} "
            else:
                if self.color_dic[element] in [
                    c for k,c in ColorOptions.Back.items() if k not in ['NONE', 'BLACK']
                ]:
                    config_menu += f"{ColorOptions.Fore['BLACK']}"
                config_menu += f"{element: <{element_offset}}"
                config_menu += f"{ColorOptions.Style['RESET']} "
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
            self.config_parser.set('COLORS', keyword, f"{value}")
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
                print(f"Something went wrong. Unknown keyword '{keyword}'")
            try:
                keyword = input('Input name or id of the element to change: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return
            if keyword.isdigit():
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)
                ) else keyword
        print('Successfully selected element ', end='')
        print(f"'{self.color_dic[keyword]}{keyword}{ColorOptions.Style['RESET']}'", end=' ')
        print(f"[Default: '{self.default_dic[keyword]}{keyword}{ColorOptions.Style['RESET']}']")

        color_options = self._print_get_all_available_colors()
        print('You may enter 8-bit colors using the following format: <f/b>[0-255]')
        print('You may enter 24-bit (truecolor) colors using the following format: ', end='')
        print('<f/b>[0-255];[0-255];[0-255]')
        higher_bit_color, custom_ansi_color = False, False
        color = ''
        while color not in color_options:
            if color != '':
                print(f"Something went wrong. Unknown option '{color}'.")
            try:
                color = input('Input new color: ')
            except EOFError:
                err_print('\nAborting due to End-of-File character...')
                return
            if color.isdigit():
                color = color_options[int(color)-1] if (
                    0 < int(color) <= len(color_options)
                ) else color
                continue
            if CONFIG_VALID_COLOR.match(color):
                higher_bit_color = True
                color = color.lower()
                break
            if CONFIG_VALID_ANSI.match(color):
                custom_ansi_color = True
                break

        if keyword in self.exclusive_definitions['Fore'] and (
            color.startswith('Back') or
            (higher_bit_color and color.startswith('b'))
        ):
            err_print(f"An Error occured: '{keyword}' can only be of style 'Fore'")
            return
        if keyword in self.exclusive_definitions['Back'] and (
            color.startswith('Fore') or
            (higher_bit_color and color.startswith('f'))
        ):
            err_print(f"An Error occured: '{keyword}' can only be of style 'Back'")
            return

        if higher_bit_color:
            color_ground = color[0]
            color_split = color[1:].split(';')
            if len(color_split) == 1:
                color_code = color_code_256(int(color_split[0]),
                                            color_ground == 'f')
            else:
                color_code = color_code_truecolor(*[int(c) for c in color_split],
                                                  color_ground == 'f')
            print('Successfully selected element ', end='')
            print(f"{color_code}{color}{ColorOptions.Style['RESET']}.")
        elif custom_ansi_color:
            print('Successfully selected element ', end='')
            print(f"{ESC_CODE}{color}ESC{color}{ColorOptions.Style['RESET']}.")
        else:
            color_split = color.split('.')
            print('Successfully selected element ', end='')
            print(f"'{getattr(ColorOptions, color_split[0])[color_split[1]]}", end='')
            print(f"{color}{ColorOptions.Style['RESET']}'.")

        self._save_config(keyword, color)

    def reset_config(self) -> None:
        """
        reset the cconfig to default by simply deleting the config section.
        """
        self.config_parser.remove_section('COLORS')
        self._save_config(None)
