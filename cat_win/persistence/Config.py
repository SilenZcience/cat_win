from os.path import join as path_join
from configparser import ConfigParser
from cat_win.const.ColorConstants import ColorOptions, C_KW


class Config:
    default_dic = {C_KW.NUMBER: ColorOptions.Fore['GREEN'],
                   C_KW.LINE_LENGTH: ColorOptions.Fore['LIGHTBLUE'],
                   C_KW.ENDS: ColorOptions.Back['YELLOW'],
                   C_KW.TABS: ColorOptions.Back['YELLOW'],
                   C_KW.CONVERSION: ColorOptions.Fore['CYAN'],
                   C_KW.REPLACE: ColorOptions.Fore['YELLOW'],
                   C_KW.FOUND: ColorOptions.Fore['RED'],
                   C_KW.FOUND_MESSAGE: ColorOptions.Fore['MAGENTA'],
                   C_KW.MATCHED: ColorOptions.Back['CYAN'],
                   C_KW.MATCHED_MESSAGE: ColorOptions.Fore['LIGHTCYAN'],
                   C_KW.CHECKSUM: ColorOptions.Fore['CYAN'],
                   C_KW.COUNT_AND_FILES: ColorOptions.Fore['CYAN'],
                   C_KW.ATTRIB_POSITIVE: ColorOptions.Fore['LIGHTGREEN'],
                   C_KW.ATTRIB_NEGATIVE: ColorOptions.Fore['LIGHTRED'],
                   C_KW.ATTRIB: ColorOptions.Fore['CYAN'],
                   C_KW.MESSAGE_INFORMATION: ColorOptions.Fore['LIGHTBLACK'],
                   C_KW.MESSAGE_IMPORTANT: ColorOptions.Fore['YELLOW'],
                   C_KW.MESSAGE_WARNING: ColorOptions.Fore['RED']}
    elements = list(default_dic.keys())

    def __init__(self, workingDir) -> None:
        self.workingDir = workingDir
        self.configFile = path_join(self.workingDir, "cat.config")
        
        self.exclusive_definitions = {'Fore': [C_KW.FOUND],  # can only be Foreground
                                      'Back': [C_KW.MATCHED]}  # can only be Background
        self.configParser = ConfigParser()
        self.color_dic = {}
        
        self.longestCharCount = 30
        self.ROWS = 3

    def loadConfig(self) -> dict:
        """
        Load the Color Configuration from the config file and return it.
        On Error: Return the default color config.
        """
        try:
            self.configParser.read(self.configFile)
            configColors = self.configParser['COLORS']
            for element in self.elements:
                try:
                    type, color = configColors[element].split(".")
                    self.color_dic[element] = (
                        ColorOptions.Fore[color] if type == 'Fore' else ColorOptions.Back[color])
                except KeyError:
                    self.color_dic[element] = self.default_dic[element]
        except KeyError:
            self.configParser['COLORS'] = {}
            # If an error occures we simplfy use the default colors
            self.color_dic = self.default_dic

        # The Reset Codes should always be the same
        self.color_dic[C_KW.RESET_ALL] = ColorOptions.Style['RESET']
        self.color_dic[C_KW.RESET_FOUND] = ColorOptions.Fore['RESET']
        self.color_dic[C_KW.RESET_MATCHED] = ColorOptions.Back['RESET']

        return self.color_dic

    def _printGetAllAvailableColors(self) -> list:
        print("Here is a list of all available color options you may choose:")
        
        ForeOptions = list(ColorOptions.Fore.items())
        ForeOptions = [(k, v) for k, v in ForeOptions if k != 'RESET']
        BackOptions = list(ColorOptions.Back.items())
        BackOptions = [(k, v) for k, v in BackOptions if k != 'RESET']
        indexOffset = len(str(len(ForeOptions) + len(BackOptions) + 1))
        
        configMenu = ''
        options = []
        
        for index in range(len(ForeOptions)):
            key, value = ForeOptions[index]
            coloredOption = f"{value}Fore.{key}{ColorOptions.Style['RESET']}"
            configMenu += f"{index+1: <{indexOffset}}: {coloredOption: <{self.longestCharCount+len(value)}}"
            if index % self.ROWS == self.ROWS-1:
                configMenu += '\n'
            options.append("Fore." + key)
        configMenu += '\n'
        for index in range(len(BackOptions)):
            key, value = BackOptions[index]
            coloredOption = f"{value}Back.{key}{ColorOptions.Style['RESET']}"
            configMenu += f"{len(ForeOptions)+index+1: <{indexOffset}}: {coloredOption: <{self.longestCharCount+len(value)}}"
            if index % self.ROWS == self.ROWS-1:
                configMenu += '\n'
            options.append("Back." + key)
        configMenu += '\n'
        
        print(configMenu)
        return options

    def _printAllAvailableElements(self) -> None:
        print("Here is a list of all available elements you may change:")
        
        self.longestCharCount = max(map(len, self.elements)) + 12
        indexOffset = len(str(len(self.elements) + 1))

        configMenu = ''
        for index in range(len(self.elements)):
            element = self.elements[index]
            coloredElement = f"{self.color_dic[element]}{element}{ColorOptions.Style['RESET']}"
            configMenu += f"{index+1: <{indexOffset}}: {coloredElement: <{self.longestCharCount+len(self.color_dic[element])}}"
            if index % self.ROWS == self.ROWS-1:
                configMenu += '\n'
        
        print(configMenu)

    def saveConfig(self) -> None:
        """
        Guide the User through the configuration options and save the changes.
        Assume, that the current config is already loaded/the method loadConfig() was already called.
        """
        self._printAllAvailableElements()
        keyword = ''
        while (not keyword in self.elements):
            if keyword != '':
                print(f"Something went wrong. Unknown keyword '{keyword}'")
            keyword = input("Input name of keyword to change: ")
            if keyword.isdigit():
                keyword = self.elements[int(keyword)-1] if (
                    0 < int(keyword) <= len(self.elements)) else keyword
        print(f"Successfully selected element '{keyword}'.")

        color_options = self._printGetAllAvailableColors()
        color = ''
        while (not color in color_options):
            if color != '':
                print(f"Something went wrong. Unknown option '{color}'.")
            color = input("Input color: ")
            if color.isdigit():
                color = color_options[int(color)-1] if (
                    0 < int(color) <= len(color_options)) else color

        if keyword in self.exclusive_definitions['Fore'] and color.startswith('Back'):
            print(f"An Error occured: '{keyword}' can only be of style 'Fore'")
            return
        if keyword in self.exclusive_definitions['Back'] and color.startswith('Fore'):
            print(f"An Error occured: '{keyword}' can only be of style 'Back'")
            return

        print(f"Successfully selected element '{color}'.")

        self.configParser['COLORS'][keyword] = color
        try:
            with open(self.configFile, 'w') as conf:
                self.configParser.write(conf)
            print(f"Successfully updated config file:\n\t{self.configFile}")
        except OSError:
            print(f"Could not write to config file:\n\t{self.configFile}")
