"""
argconstants
"""

class ArgConstant():
    """
    defines an argument
    """
    def __init__(self, short_form: str, long_form: str, arg_help: str, arg_id: int,
                 show_arg: bool = True, show_arg_on_shell: bool = True, section: int = -1):
        self.short_form = short_form
        self.long_form = long_form
        self.arg_help = arg_help
        self.arg_id = arg_id
        self.show_arg = show_arg
        self.show_arg_on_shell = show_arg_on_shell

        self.section = section


ARGS_HELP, ARGS_NUMBER, ARGS_ENDS, ARGS_EDITOR, ARGS_SQUEEZE = range(0, 5)
ARGS_REVERSE, ARGS_COUNT, ARGS_BLANK, ARGS_FILES, ARGS_INTERACTIVE = range(5, 10)
ARGS_CLIP, ARGS_CHECKSUM, ARGS_DEC, ARGS_HEX, ARGS_BIN = range(10, 15)
ARGS_VERSION, ARGS_DEBUG, ARGS_CUT, ARGS_REPLACE, ARGS_DATA = range(15, 20)
ARGS_CONFIG, ARGS_LLENGTH, ARGS_ONELINE, ARGS_PEEK, ARGS_NOCOL = range(20, 25)
ARGS_CHR, ARGS_B64E, ARGS_B64D, ARGS_FFILES, ARGS_GREP = range(25, 30)
ARGS_NOBREAK, ARGS_ECHO, ARGS_CCOUNT, ARGS_HEXVIEW, ARGS_BINVIEW = range(30, 35)
ARGS_NOKEYWORD, ARGS_RECONFIGURE, ARGS_RECONFIGURE_IN = range(35, 38)
ARGS_RECONFIGURE_OUT, ARGS_RECONFIGURE_ERR = range(38, 40)
ARGS_EVAL, ARGS_SORT, ARGS_GREP_ONLY, ARGS_PLAIN_ONLY, ARGS_FILE_PREFIX = range(40, 45)
ARGS_FFILE_PREFIX, ARGS_DOTFILES, ARGS_OCT, ARGS_URI, ARGS_WORDCOUNT = range(45, 50)
ARGS_WWORDCOUNT,  = range(50, 51)

DIFFERENTIABLE_ARGS = [ARGS_CUT, ARGS_REPLACE]

ALL_ARGS = [
    ArgConstant('-h', '--help', 'show this help message and exit',
				ARGS_HELP, section=0),
    ArgConstant('-v', '--version', 'output version information and exit',
				ARGS_VERSION, section=0),
    ArgConstant('--debug', '--debug', 'show debug information',
				ARGS_DEBUG, show_arg=False, section=0),

    # prefix
    ArgConstant('-l', '--linelength', 'display the length of each line',
				ARGS_LLENGTH, section=1),
    ArgConstant('-n', '--number', 'number all output lines',
				ARGS_NUMBER, section=1),
    ArgConstant('--fp', '--file-prefix', 'include the file in every line prefix',
				ARGS_FILE_PREFIX, show_arg_on_shell=False, section=1),
    ArgConstant('--FP', '--FILE-PREFIX', 'include the file protocol in every line prefix',
				ARGS_FFILE_PREFIX, show_arg=False, section=1),

    # simple replacements
    ArgConstant('-e', '--ends', 'display $ at the end of each line',
				ARGS_ENDS, section=2),
    ArgConstant('--chr', '--char', 'display special characters',
				ARGS_CHR, section=2),

    # line manipulation
    ArgConstant('-b', '--blank', 'hide empty lines',
				ARGS_BLANK, section=3),
    ArgConstant('-p', '--peek', 'only print the first and last lines',
				ARGS_PEEK, show_arg_on_shell=False, section=3),
    ArgConstant('-r', '--reverse', 'reverse output',
				ARGS_REVERSE, show_arg_on_shell=False, section=3),
    ArgConstant('-u', '--unique', 'suppress repeated output lines',
				ARGS_SQUEEZE, show_arg_on_shell=False, section=3),
    ArgConstant('--sort', '--sort', 'sort all lines alphabetically',
				ARGS_SORT, show_arg_on_shell=False, section=3),

    # different content types
    ArgConstant('-E', '--echo', 'handle every following parameter as stdin',
				ARGS_ECHO, show_arg_on_shell=False, section=4),
    ArgConstant('-i', '--interactive', 'use stdin',
				ARGS_INTERACTIVE, show_arg_on_shell=False, section=4),
    ArgConstant('-o', '--oneline', 'take only the first stdin-line',
				ARGS_ONELINE, section=4),
    ArgConstant('-U', '--url', 'display the contents of any provided url',
				ARGS_URI, show_arg_on_shell=False, section=4),

    # summary
    ArgConstant('-f', '--files', 'list applied files and file sizes',
				ARGS_FILES, show_arg_on_shell=False, section=5),
    ArgConstant('-F', '--FILES', 'ONLY list applied files and file sizes',
				ARGS_FFILES, show_arg=False, section=5),
    ArgConstant('-s', '--sum', 'show sum of lines',
				ARGS_COUNT, show_arg_on_shell=False, section=5),
    ArgConstant('-S', '--SUM', 'ONLY show sum of lines',
				ARGS_CCOUNT, show_arg=False, section=5),
    ArgConstant('-w', '--wordcount', 'display the wordcount',
                ARGS_WORDCOUNT, section=5),
    ArgConstant('-W', '--WORDCOUNT', 'ONLY display the wordcount',
                ARGS_WWORDCOUNT, section=5),

    # search and match
    ArgConstant('-g', '--grep', 'only show lines containing queried keywords or patterns',
				ARGS_GREP, section=6),
    ArgConstant('-G', '--GREP', 'only show found and matched substrings',
				ARGS_GREP_ONLY, show_arg=False, section=6),
    ArgConstant('--nk', '--nokeyword', 'inverse the grep output',
				ARGS_NOKEYWORD, section=6),
    ArgConstant('--nb', '--nobreak', 'do not interrupt the output',
				ARGS_NOBREAK, section=6),

    # meta information
    ArgConstant('-a', '--attributes', 'show meta-information about the files',
				ARGS_DATA, show_arg_on_shell=False, section=7),
    ArgConstant('-m', '--checksum', 'show the checksums of all files',
				ARGS_CHECKSUM, show_arg_on_shell=False, section=7),

    # numbers
    ArgConstant('--b64d', '--b64d', 'decode the input from base64',
				ARGS_B64D, section=8),
    ArgConstant('--b64e', '--b64e', 'encode the input to base64',
				ARGS_B64E, section=8),
    ArgConstant('--eval', '--EVAL', 'evaluate simple mathematical equations',
				ARGS_EVAL, section=8),
    ArgConstant('--hex', '--HEX', 'convert hexadecimal numbers to binary, octal and decimal',
				ARGS_HEX, section=8),
    ArgConstant('--dec', '--DEC', 'convert decimal numbers to binary, octal and hexadecimal',
				ARGS_DEC, section=8),
    ArgConstant('--oct', '--OCT', 'convert octal numbers to binary, decimal and hexadecimal',
				ARGS_OCT, section=8),
    ArgConstant('--bin', '--BIN', 'convert binary numbers to octal, decimal and hexadecimal',
				ARGS_BIN, section=8),

    # raw
    ArgConstant('--binview', '--binview', 'display the raw byte representation in binary',
				ARGS_BINVIEW, show_arg_on_shell=False, section=9),
    ArgConstant('--hexview', '--HEXVIEW', 'display the raw byte representation in hexadecimal',
				ARGS_HEXVIEW, show_arg_on_shell=False, section=9),

    ArgConstant('-!', '--edit', 'open each file in a simple editor',
				ARGS_EDITOR, section=10),
    ArgConstant('-c', '--clip', 'copy output to clipboard',
				ARGS_CLIP, section=10),
    ArgConstant('--dot', '--dotfiles', 'additionally query and edit dotfiles',
				ARGS_DOTFILES, show_arg_on_shell=False, section=10),
    ArgConstant('--plain', '--plain-only', 'ignore non-plaintext files automatically',
				ARGS_PLAIN_ONLY, show_arg_on_shell=False, section=10),
    ArgConstant('--nc', '--nocolor', 'disable colored output',
				ARGS_NOCOL, section=10),

    ArgConstant('--config', '--config', 'change color configuration',
				ARGS_CONFIG, section=11),

    ArgConstant('-R', '--R', 'reconfigure the stdin and stdout with the parsed encoding',
				ARGS_RECONFIGURE, show_arg=False),
    ArgConstant('--Rin', '--Rin', 'reconfigure the stdin with the parsed encoding',
				ARGS_RECONFIGURE_IN, show_arg=False),
    ArgConstant('--Rout', '--Rout', 'reconfigure the stdout with the parsed encoding',
                ARGS_RECONFIGURE_OUT, show_arg=False),
    ArgConstant('--Rerr', '--Rerr', 'reconfigure the stderr with the parsed encoding',
                ARGS_RECONFIGURE_ERR, show_arg=False),
    ]
ALL_ARGS.sort(key=lambda x:x.section)

HIGHEST_ARG_ID = max([arg.arg_id for arg in ALL_ARGS])
