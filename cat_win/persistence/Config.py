from configparser import ConfigParser
from cat_win.util.ColorConstants import ColoramaOptions, C_KW


class Config:
    configParser = ConfigParser()
    workingDir = ""
    configFile = ""

    exclusive_definitions = {"Fore": [C_KW.FOUND],  # can only be Foreground
                             "Back": [C_KW.MATCHED]}  # can only be Background
    default_dic = {C_KW.NUMBER: ColoramaOptions.C_Fore['GREEN'],
                   C_KW.ENDS: ColoramaOptions.C_Back['YELLOW'],
                   C_KW.TABS: ColoramaOptions.C_Back['YELLOW'],
                   C_KW.CONVERSION: ColoramaOptions.C_Fore['CYAN'],
                   C_KW.REPLACE: ColoramaOptions.C_Fore['YELLOW'],
                   C_KW.FOUND: ColoramaOptions.C_Fore['RED'],
                   C_KW.FOUND_MESSAGE: ColoramaOptions.C_Fore['MAGENTA'],
                   C_KW.MATCHED: ColoramaOptions.C_Back['CYAN'],
                   C_KW.MATCHED_MESSAGE: ColoramaOptions.C_Fore['LIGHTCYAN_EX'],
                   C_KW.CHECKSUM: ColoramaOptions.C_Fore['CYAN'],
                   C_KW.COUNT_AND_FILES: ColoramaOptions.C_Fore['CYAN'],
                   C_KW.ATTRIB_POSITIVE: ColoramaOptions.C_Fore['LIGHTGREEN_EX'],
                   C_KW.ATTRIB_NEGATIVE: ColoramaOptions.C_Fore['LIGHTRED_EX'],
                   C_KW.ATTRIB: ColoramaOptions.C_Fore['CYAN']}
    elements = list(default_dic.keys())
    color_dic = {}

    def __init__(self, workingDir):
        self.workingDir = workingDir
        self.configFile = self.workingDir + "/cat.config"

    def loadConfig(self):
        try:
            self.configParser.read(self.configFile)
            configColors = self.configParser['COLORS']
            for element in self.elements:
                try:
                    type, color = configColors[element].split(".")
                    self.color_dic[element] = (
                        ColoramaOptions.C_Fore[color] if type == 'Fore' else ColoramaOptions.C_Back[color])
                except:
                    self.color_dic[element] = self.default_dic[element]
        except:
            self.color_dic = self.default_dic

        self.color_dic[C_KW.RESET_ALL] = ColoramaOptions.C_Style_Reset
        self.color_dic[C_KW.RESET_FOUND] = ColoramaOptions.C_Fore_Reset
        self.color_dic[C_KW.RESET_MATCHED] = ColoramaOptions.C_Back_Reset

        return self.color_dic

    def _printGetAllAvailableColors(self):
        options = []
        index = 0
        print("Here is a list of all available color options you may choose:")
        for key, value in ColoramaOptions.C_Fore.items():
            option = "Fore." + key
            print(f"{index: <2}: ", value, option, ColoramaOptions.C_Fore_Reset, sep="")
            options.append(option)
            index += 1
        for key, value in ColoramaOptions.C_Back.items():
            option = "Back." + key
            print(f"{index: <2}: ", value, option, ColoramaOptions.C_Back_Reset, sep="")
            options.append(option)
            index += 1
        return options

    def _printAllAvailableElements(self):
        print("Here is a list of all available elements you may change:")
        for index, element in enumerate(self.elements):
            print(f"{index: <2}: ", self.color_dic[element], element,
                  ColoramaOptions.C_Style_Reset, sep="")

    def saveConfig(self):
        # Assume, that the current config is already loaded/the method loadConfig() was already called.
        self._printAllAvailableElements()
        keyword = input("Input name of keyword to change: ")
        if keyword.isdigit():
            keyword = self.elements[int(keyword)] if (0 <= int(keyword) < len(self.elements)) else keyword
        while (not keyword in self.elements):
            print(f"Something went wrong. Unknown keyword '{keyword}'")
            keyword = input("Input name of keyword to change: ")
            if keyword.isdigit():
                keyword = self.elements[int(color)] if (0 <= int(keyword) < len(self.elements)) else keyword

        print(f"Successfully selected element '{keyword}'.")

        color_options = self._printGetAllAvailableColors()
        color = input("Input color: ")
        if color.isdigit():
            color = color_options[int(color)] if (0 <= int(color) < len(color_options)) else color
        while (not color in color_options):
            print(f"Something went wrong. Unknown option '{color}'.")
            color = input("Input color: ")
            if color.isdigit():
                color = color_options[int(color)] if (0 <= int(color) < len(color_options)) else color
                

        if keyword in self.exclusive_definitions["Fore"] and color.startswith("Back"):
            print(f"An Error occured: '{keyword}' can only be of style 'Fore'")
            return
        if keyword in self.exclusive_definitions["Back"] and color.startswith("Fore"):
            print(f"An Error occured: '{keyword}' can only be of style 'Back'")
            return

        print(f"Successfully selected element '{color}'.")

        self.configParser['COLORS'][keyword] = color
        try:
            with open(self.configFile, 'w') as conf:
                self.configParser.write(conf)
            print(f"Successfully updated config file:\n\t{self.configFile}")
        except:
            print(f"Could not write to config file:\n\t{self.configFile}")
            pass

        return
