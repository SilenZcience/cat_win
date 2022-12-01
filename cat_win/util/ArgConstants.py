class ArgConstant():
    def __init__(self, shortForm, longForm, help, id):
        self.shortForm = shortForm
        self.longForm = longForm
        self.help = help
        self.id = id


ARGS_HELP, ARGS_NUMBER, ARGS_ENDS, ARGS_TABS, ARGS_SQUEEZE = range(0, 5)
ARGS_REVERSE, ARGS_COUNT, ARGS_BLANK, ARGS_FILES, ARGS_INTERACTIVE = range(5, 10)
ARGS_CLIP, ARGS_CHECKSUM, ARGS_DEC, ARGS_HEX, ARGS_BIN = range(10, 15)
ARGS_VERSION, ARGS_DEBUG, ARGS_CUT, ARGS_REPLACE, ARGS_DATA = range(15, 20)
ARGS_CONFIG, ARGS_LLENGTH, ARGS_ONELINE = range(20, 23)

ALL_ARGS = [[["-h", "--help"], "show this help message and exit", ARGS_HELP],
            [["-n", "--number"], "number all output lines", ARGS_NUMBER],
            [["-x", "--linelength"], "display the length of each line", ARGS_LLENGTH],
            [["-e", "--ends"], "display $ at the end of each line", ARGS_ENDS],
            [["-t", "--tabs"], "display TAB characters as ^I", ARGS_TABS],
            [["-s", "--squeeze"], "suppress repeated output lines", ARGS_SQUEEZE],
            [["-r", "--reverse"], "reverse output", ARGS_REVERSE],
            [["-c", "--count"], "show sum of lines", ARGS_COUNT],
            [["-b", "--blank"], "hide empty lines", ARGS_BLANK],
            [["-f", "--files"], "list applied files", ARGS_FILES],
            [["-i", "--interactive"], "use stdin", ARGS_INTERACTIVE],
            [["-o", "--oneline"], "take only the first stdin-line", ARGS_ONELINE],
            [["-l", "--clip"], "copy output to clipboard", ARGS_CLIP],
            [["-m", "--checksum"], "show the checksums of all files", ARGS_CHECKSUM],
            [["-a", "--attributes"], "show meta-information about the files", ARGS_DATA],
            [["-dec", "--dec"], "convert decimal numbers to hexadecimal and binary", ARGS_DEC],
            [["-hex", "--hex"], "convert hexadecimal numbers to decimal and binary", ARGS_HEX],
            [["-bin", "--bin"], "convert binary numbers to decimal and hexadecimal", ARGS_BIN],
            [["-v", "--version"], "output version information and exit", ARGS_VERSION],
            [["-d", "--debug"], "show debug information", ARGS_DEBUG],
            [["--config", "--config"], "change color configuration", ARGS_CONFIG]]

ALL_ARGS = [ArgConstant(x[0][0], x[0][1], x[1], x[2]) for x in ALL_ARGS]
HIGHEST_ARG_ID = max([m.id for m in ALL_ARGS])
