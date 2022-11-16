from os import path
from colorama import Fore, Back, Style
from configparser import ConfigParser


class ColoramaOptions:
    C_Fore = {"BLACK": Fore.BLACK,
              "RED": Fore.RED,
              "GREEN": Fore.GREEN,
              "YELLOW": Fore.YELLOW,
              "BLUE": Fore.BLUE,
              "MAGENTA": Fore.MAGENTA,
              "CYAN": Fore.CYAN,
              "WHITE": Fore.WHITE,
              "LIGHTBLACK_EX": Fore.LIGHTBLACK_EX,
              "LIGHTRED_EX": Fore.LIGHTRED_EX,
              "LIGHTGREEN_EX": Fore.LIGHTGREEN_EX,
              "LIGHTYELLOW_EX": Fore.LIGHTYELLOW_EX,
              "LIGHTBLUE_EX": Fore.LIGHTBLUE_EX,
              "LIGHTMAGENTA_EX": Fore.LIGHTMAGENTA_EX,
              "LIGHTCYAN_EX": Fore.LIGHTCYAN_EX,
              "LIGHTWHITE_EX": Fore.LIGHTWHITE_EX
              }
    C_Back = {"BLACK": Back.BLACK,
              "RED": Back.RED,
              "GREEN": Back.GREEN,
              "YELLOW": Back.YELLOW,
              "BLUE": Back.BLUE,
              "MAGENTA": Back.MAGENTA,
              "CYAN": Back.CYAN,
              "WHITE": Back.WHITE,
              "LIGHTBLACK_EX": Back.LIGHTBLACK_EX,
              "LIGHTRED_EX": Back.LIGHTRED_EX,
              "LIGHTGREEN_EX": Back.LIGHTGREEN_EX,
              "LIGHTYELLOW_EX": Back.LIGHTYELLOW_EX,
              "LIGHTBLUE_EX": Back.LIGHTBLUE_EX,
              "LIGHTMAGENTA_EX": Back.LIGHTMAGENTA_EX,
              "LIGHTCYAN_EX": Back.LIGHTCYAN_EX,
              "LIGHTWHITE_EX": Back.LIGHTWHITE_EX
              }


class Config:
    configParser = ConfigParser()
    workingDir = ""
    configFile = ""

    exclusive_definitions = {"Fore": ["found_keyword"],  # can only be Foreground
                             "Back": ["matched_keyword"]}  # can only be Background
    default_dic = {'number': Fore.GREEN, 'ends': Back.YELLOW,
                   'tabs': Back.YELLOW, 'conversion': Fore.CYAN, 'replace': Fore.YELLOW,
                   'found_keyword': Fore.RED, 'found_message': Fore.MAGENTA,
                   'matched_keyword': Back.CYAN, 'matched_message': Fore.LIGHTCYAN_EX,
                   'checksum': Fore.CYAN, 'count_and_files': Fore.CYAN, 'attrib_positive': Fore.LIGHTGREEN_EX,
                   'attrib_negative': Fore.LIGHTRED_EX, 'attrib': Fore.CYAN}
    elements = default_dic.keys()
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

        self.color_dic["reset"] = Style.RESET_ALL
        self.color_dic["found_reset"] = Fore.RESET
        self.color_dic["matched_reset"] = Back.RESET

        return self.color_dic

    def _printAllAvailableColors(self):
        print("Here is a list of all available color options you may choose:")
        for key, value in ColoramaOptions.C_Fore.items():
            print(value, "Fore.", key, Fore.RESET, sep="")
        print(Fore.BLACK, end="")
        for key, value in ColoramaOptions.C_Back.items():
            print(value, "Back.", key, Back.RESET, sep="")
        print(Style.RESET_ALL, end="")
        return

    def _printAllAvailableElements(self):
        print("Here is a list of all available elements you may change:")
        for element in self.elements:
            print(self.color_dic[element], element, Style.RESET_ALL, sep="")
        return

    def saveConfig(self):
        # Assume, that the current config is already loaded/the method loadConfig() was already called.
        self._printAllAvailableElements()
        keyword = input("Input name of keyword to change: ")
        while (not keyword in self.elements):
            print(f"Something went wrong. Unknown keyword '{keyword}'")
            keyword = input("Input name of keyword to change: ")

        print(f"Successfully selected element '{keyword}'.")

        self._printAllAvailableColors()
        color = input("Input color: ")
        while (not color in ["Fore."+key for key in ColoramaOptions.C_Fore.keys()]
               and not color in ["Back."+key for key in ColoramaOptions.C_Back.keys()]):
            print(f"Something went wrong. Unknown option '{color}'")
            color = input("Input color: ")

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
