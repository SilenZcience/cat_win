class ArgConstant():
    def __init__(self, shortForm, longForm, help, id):
        self.shortForm = shortForm
        self.longForm = longForm
        self.help = help
        self.id = id

ARGS_HELP = 0
ARGS_NUMBER = 1
ARGS_ENDS = 2
ARGS_TABS = 3
ARGS_SQUEEZE = 4
ARGS_REVERSE = 5
ARGS_COUNT = 6
ARGS_BLANK = 7
ARGS_FILES = 9
ARGS_INTERACTIVE = 10
ARGS_CLIP = 11
ARGS_CHECKSUM = 12
ARGS_DEC = 13
ARGS_HEX = 14
ARGS_BIN = 15
ARGS_VERSION = 16
ARGS_DEBUG = 17

ALL_ARGS = [[["-h", "--help"], "show this help message and exit", ARGS_HELP],
            [["-n", "--number"], "number all output lines", ARGS_NUMBER],
            [["-e", "--ends"], "display $ at end of each line", ARGS_ENDS],
            [["-t", "--tabs"], "display TAB characters as ^I", ARGS_TABS],
            [["-s", "--squeeze"], "suppress repeated output lines", ARGS_SQUEEZE],
            [["-r", "--reverse"], "reverse output", ARGS_REVERSE],
            [["-c", "--count"], "show sum of lines", ARGS_COUNT],
            [["-b", "--blank"], "hide empty lines", ARGS_BLANK],
            [["-f", "--files"], "list applied files", ARGS_FILES],
            [["-i", "--interactive"], "use stdin", ARGS_INTERACTIVE],
            [["-l", "--clip"], "copy output to clipboard", ARGS_CLIP],
            [["-m", "--checksum"], "show the checksums of all files", ARGS_CHECKSUM],
            [["-dec", "--dec"], "convert decimal number to hexadecimal and binary", ARGS_DEC],
            [["-hex", "--hex"], "convert hexadecimal number to decimal and binary", ARGS_HEX],
            [["-bin", "--bin"], "convert binary number to decimal and hexadecimal", ARGS_BIN],
            [["-v", "--version"], "output version information and exit", ARGS_VERSION],
            [["-d", "--debug"], "show debug information", ARGS_DEBUG]]

ALL_ARGS = [ArgConstant(x[0][0], x[0][1], x[1], x[2]) for x in ALL_ARGS]
HIGHEST_ARG_ID = max([m.id for m in ALL_ARGS])