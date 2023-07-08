
class ArgConstant():
    """
    defines an argument
    """
    def __init__(self, short_form: str, long_form: str, arg_help: str, arg_id: int,
                 show_arg: bool = True, show_arg_on_shell: bool = True):
        self.short_form = short_form
        self.long_form = long_form
        self.arg_help = arg_help
        self.arg_id = arg_id
        self.show_arg = show_arg
        self.show_arg_on_shell = show_arg_on_shell


ARGS_HELP, ARGS_NUMBER, ARGS_ENDS, ARGS_TABS, ARGS_SQUEEZE = range(0, 5)
ARGS_REVERSE, ARGS_COUNT, ARGS_BLANK, ARGS_FILES, ARGS_INTERACTIVE = range(5, 10)
ARGS_CLIP, ARGS_CHECKSUM, ARGS_DEC, ARGS_HEX, ARGS_BIN = range(10, 15)
ARGS_VERSION, ARGS_DEBUG, ARGS_CUT, ARGS_REPLACE, ARGS_DATA = range(15, 20)
ARGS_CONFIG, ARGS_LLENGTH, ARGS_ONELINE, ARGS_PEEK, ARGS_NOCOL = range(20, 25)
ARGS_EOF, ARGS_B64E, ARGS_B64D, ARGS_FFILES, ARGS_GREP = range(25, 30)
ARGS_NOBREAK, ARGS_ECHO, ARGS_CCOUNT, ARGS_HEXVIEW, ARGS_BINVIEW = range(30, 35)
ARGS_NOKEYWORD, ARGS_RECONFIGURE, ARGS_RECONFIGURE_IN, ARGS_RECONFIGURE_OUT, ARGS_RECONFIGURE_ERR = range(35, 40)
ARGS_EVAL, ARGS_SORT, ARGS_GREP_ONLY = range(40, 43)

DIFFERENTIABLE_ARGS = [ARGS_CUT, ARGS_REPLACE]

ALL_ARGS = [
    ArgConstant('-h', '--help', 'show this help message and exit', ARGS_HELP),
    ArgConstant('-v', '--version', 'output version information and exit', ARGS_VERSION),
    ArgConstant('--debug', '--debug', 'show debug information', ARGS_DEBUG, False),
    ArgConstant('-n', '--number', 'number all output lines', ARGS_NUMBER),
    ArgConstant('-l', '--linelength', 'display the length of each line', ARGS_LLENGTH),
    ArgConstant('-e', '--ends', 'display $ at the end of each line', ARGS_ENDS),
    ArgConstant('-t', '--tabs', 'display TAB characters as ^I', ARGS_TABS),
    ArgConstant('--eof', '--eof', 'display EOF characters as ^EOF', ARGS_EOF),
    ArgConstant('-u', '--unique', 'suppress repeated output lines', ARGS_SQUEEZE, True, False),
    ArgConstant('-b', '--blank', 'hide empty lines', ARGS_BLANK),
    ArgConstant('-r', '--reverse', 'reverse output', ARGS_REVERSE, True, False),
    ArgConstant('--sort', '--sort', 'sort all lines alphabetically', ARGS_SORT, True, False),
    ArgConstant('-p', '--peek', 'only print the first and last lines', ARGS_PEEK, True, False),
    ArgConstant('-s', '--sum', 'show sum of lines', ARGS_COUNT, True, False),
    ArgConstant('-S', '--SUM', 'ONLY show sum of lines', ARGS_CCOUNT, True, False),
    ArgConstant('-f', '--files', 'list applied files', ARGS_FILES, True, False),
    ArgConstant('-F', '--FILES', 'ONLY list applied files and file sizes', ARGS_FFILES, True, False),
    ArgConstant('-g', '--grep', 'only show lines containing queried keywords or patterns', ARGS_GREP),
    ArgConstant('-G', '--GREP', 'only show found and matched substrings', ARGS_GREP_ONLY),
    ArgConstant('-i', '--interactive', 'use stdin', ARGS_INTERACTIVE, True, False),
    ArgConstant('-o', '--oneline', 'take only the first stdin-line', ARGS_ONELINE, True, False),
    ArgConstant('-E', '--ECHO', 'handle every following parameter as stdin', ARGS_ECHO, True, False),
    ArgConstant('-c', '--clip', 'copy output to clipboard', ARGS_CLIP),
    ArgConstant('-m', '--checksum', 'show the checksums of all files', ARGS_CHECKSUM, True, False),
    ArgConstant('-a', '--attributes', 'show meta-information about the files', ARGS_DATA, True, False),
    ArgConstant('--dec', '--DEC', 'convert decimal numbers to hexadecimal and binary', ARGS_DEC),
    ArgConstant('--hex', '--HEX', 'convert hexadecimal numbers to decimal and binary', ARGS_HEX),
    ArgConstant('--bin', '--BIN', 'convert binary numbers to decimal and hexadecimal', ARGS_BIN),
    ArgConstant('--eval', '--EVAL', 'evaluate simple mathematical equations', ARGS_EVAL),
    ArgConstant('--b64e', '--b64e', 'encode the input to base64', ARGS_B64E),
    ArgConstant('--b64d', '--b64d', 'decode the input from base64', ARGS_B64D),
    ArgConstant('--hexview', '--HEXVIEW', 'display the raw byte representation in hexadecimal', ARGS_HEXVIEW, True, False),
    ArgConstant('--binview', '--binview', 'display the raw byte representation in binary', ARGS_BINVIEW, True, False),
    ArgConstant('--nc', '--nocolor', 'disable colored output', ARGS_NOCOL),
    ArgConstant('--nb', '--nobreak', 'do not interrupt the output on queried keywords', ARGS_NOBREAK),
    ArgConstant('--nk', '--nokeyword', 'inverse the grep output', ARGS_NOKEYWORD),
    ArgConstant('--config', '--config', 'change color configuration', ARGS_CONFIG),
    ArgConstant('-R', '--R', 'reconfigure the stdin and stdout with the parsed encoding', ARGS_RECONFIGURE, False),
    ArgConstant('--Rin', '--Rin', 'reconfigure the stdin with the parsed encoding', ARGS_RECONFIGURE_IN, False),
    ArgConstant('--Rout', '--Rout', 'reconfigure the stdout with the parsed encoding', ARGS_RECONFIGURE_OUT, False),
    ArgConstant('--Rerr', '--Rerr', 'reconfigure the stderr with the parsed encoding', ARGS_RECONFIGURE_ERR, False),
    ]

HIGHEST_ARG_ID = max([arg.arg_id for arg in ALL_ARGS])
