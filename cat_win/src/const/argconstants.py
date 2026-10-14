"""
argconstants
"""

class ArgConstant:
    """
    defines an argument
    """
    def __init__(
            self, short_form: str, long_form: str,
            arg_help: str,
            arg_id: int,
            show_arg: bool = True, show_arg_on_repl: bool = True,
            section: int = -1, takes_value: str = None, metavar: str = None
    ) -> None:
        self.short_form = short_form
        self.long_form = long_form
        self.arg_help = arg_help
        self.arg_id = arg_id
        self.show_arg = show_arg
        self.show_arg_on_repl = show_arg_on_repl

        self.section = section
        self.takes_value = takes_value
        # display-only value placeholder (e.g. '<STREAM>'), independent of parsing
        self.metavar = metavar


# informational
ARGS_HELP, ARGS_VERSION, ARGS_DEBUG, ARGS_DEBUG_LOG = range(0, 4)
# prefix
ARGS_LLENGTH, ARGS_NUMBER, ARGS_FILE_PREFIX, ARGS_FFILE_PREFIX = range(100, 104)
# simple replacements
ARGS_ENDS, ARGS_CHR, ARGS_EOL = range(200, 203)
# line manipulation
ARGS_BLANK, ARGS_PEEK, ARGS_REVERSE, ARGS_SQUEEZE = range(300, 304)
ARGS_SORT, ARGS_SSORT, ARGS_SPECIFIC_FORMATS      = range(304, 307)
# different content types
ARGS_ECHO, ARGS_STDIN, ARGS_ONELINE, ARGS_URI = range(400, 404)
# summary
ARGS_FILES, ARGS_FFILES, ARGS_DIRECTORIES, ARGS_DDIRECTORIES = range(500, 504)
ARGS_SUM, ARGS_SSUM, ARGS_WORDCOUNT, ARGS_WWORDCOUNT         = range(504, 508)
ARGS_CHARCOUNT, ARGS_CCHARCOUNT                              = range(508, 510)
# search and match
ARGS_GREP, ARGS_GREP_ONLY, ARGS_NOKEYWORD, ARGS_NOBREAK = range(600, 604)
# meta information
ARGS_DATA, ARGS_CHECKSUM, ARGS_STRINGS = range(700, 703)
# numbers
ARGS_B64D, ARGS_B64E, ARGS_EVAL, ARGS_HEX = range(800, 804)
ARGS_DEC, ARGS_OCT, ARGS_BIN              = range(804, 807)
# raw-view
ARGS_BINVIEW, ARGS_HEXVIEW = range(900, 902)
# display & edit
ARGS_EDITOR, ARGS_HEX_EDITOR, ARGS_DIFF = range(1000, 1003)
ARGS_MORE, ARGS_LESS, ARGS_RAW          = range(1003, 1006)
# visualize
ARGS_VISUALIZE_B, ARGS_VISUALIZE_Z, ARGS_VISUALIZE_H = range(1100, 1103)
ARGS_VISUALIZE_E, ARGS_VISUALIZE_D                   = range(1103, 1105)
# behavioural
ARGS_CLIP, ARGS_WATCH, ARGS_DOTFILES, ARGS_PLAIN_ONLY = range(1200, 1204)
ARGS_NOCOL, = range(1204, 1205)
# configuration
ARGS_CONFIG, ARGS_CCONFIG, ARGS_CONFIG_FLUSH = range(1300, 1303)
ARGS_CCONFIG_FLUSH, ARGS_CONFIG_REMOVE       = range(1303, 1305)
# streams
ARGS_RECONFIGURE, ARGS_RECONFIGURE_IN      = range(1400, 1402)
ARGS_RECONFIGURE_OUT, ARGS_RECONFIGURE_ERR = range(1402, 1404)
# installation
ARGS_SUDO_ALLOW, ARGS_MAN, ARGS_COMPLETION = range(1500, 1503)

ARGS_CUT, ARGS_REPLACE = range(1600, 1602)

DIFFERENTIABLE_ARGS = [ARGS_CUT, ARGS_REPLACE]

ALL_ARGS = [
    # informational
    ArgConstant('-h', '--help', 'show this help message and exit',
                ARGS_HELP, section=0),
    ArgConstant('-v', '--version', 'output version information and exit',
                ARGS_VERSION, section=0),
    ArgConstant('--debug', '', 'show debug information',
                ARGS_DEBUG, show_arg=False, section=0),
    ArgConstant('--debuglog', '--debug-log', 'log debug information to file',
                ARGS_DEBUG_LOG, show_arg=False, section=0),

    # prefix
    ArgConstant('-l', '--linelength', 'display the length of each line',
                ARGS_LLENGTH, section=1),
    ArgConstant('-n', '--number', 'number all output lines',
                ARGS_NUMBER, section=1),
    ArgConstant('--fp', '--file-prefix', 'include the file in every line prefix',
                ARGS_FILE_PREFIX, show_arg_on_repl=False, section=1),
    ArgConstant('--FP', '--FILE-PREFIX', 'include the file protocol in every line prefix',
                ARGS_FFILE_PREFIX, show_arg=False, section=1),

    # simple replacements
    ArgConstant('-e', '--ends', 'mark the end of each line',
                ARGS_ENDS, section=2),
    ArgConstant('--chr', '--char', 'display special characters',
                ARGS_CHR, section=2),
    ArgConstant('--eol', '--end-of-line', 'display end-of-line characters',
                ARGS_EOL, section=2),

    # line manipulation
    ArgConstant('-b', '--blank', 'hide empty lines',
                ARGS_BLANK, section=3),
    ArgConstant('-p', '--peek', 'only print the first and last lines',
                ARGS_PEEK, show_arg_on_repl=False, section=3),
    ArgConstant('-r', '--reverse', 'reverse output',
                ARGS_REVERSE, show_arg_on_repl=False, section=3),
    ArgConstant('-u', '--unique', 'suppress repeated output lines',
                ARGS_SQUEEZE, show_arg_on_repl=False, section=3),
    ArgConstant('--sort', '', 'sort all lines alphabetically',
                ARGS_SORT, show_arg_on_repl=False, section=3),
    ArgConstant('--sortl', '--sortlength', 'sort all lines by length',
                ARGS_SSORT, show_arg_on_repl=False, section=3),
    ArgConstant('--sf', '--specific-format', 'automatically format specific file types',
                ARGS_SPECIFIC_FORMATS, show_arg_on_repl=False, section=3),

    # different content types
    ArgConstant('-E', '--echo', 'handle every following parameter as stdin',
                ARGS_ECHO, show_arg_on_repl=False, section=4),
    ArgConstant('-', '--stdin', 'use stdin',
                ARGS_STDIN, show_arg_on_repl=False, section=4),
    ArgConstant('-o', '--oneline', 'take only the first stdin-line',
                ARGS_ONELINE, section=4),
    ArgConstant('-U', '--url', 'display the contents of any provided url',
                ARGS_URI, show_arg_on_repl=False, section=4),

    # summary
    ArgConstant('-f', '--files', 'list applied files and file sizes',
                ARGS_FILES, show_arg_on_repl=False, section=5),
    ArgConstant('-F', '--FILES', 'ONLY list applied files and file sizes',
                ARGS_FFILES, show_arg=False, section=5),
    ArgConstant('-d', '--dirs', 'list found directories',
                ARGS_DIRECTORIES, show_arg_on_repl=False, section=5),
    ArgConstant('-D', '--DIRS', 'ONLY list found directories',
                ARGS_DDIRECTORIES, show_arg=False, section=5),
    ArgConstant('-s', '--sum', 'show sum of lines',
                ARGS_SUM, show_arg_on_repl=False, section=5),
    ArgConstant('-S', '--SUM', 'ONLY show sum of lines',
                ARGS_SSUM, show_arg=False, section=5),
    ArgConstant('--wc', '--wordcount', 'display the wordcount',
                ARGS_WORDCOUNT, show_arg_on_repl=False, section=5),
    ArgConstant('--WC', '--WORDCOUNT', 'ONLY display the wordcount',
                ARGS_WWORDCOUNT, show_arg=False, section=5),
    ArgConstant('--cc', '--charcount', 'display the charcount',
                ARGS_CHARCOUNT, show_arg_on_repl=False, section=5),
    ArgConstant('--CC', '--CHARCOUNT', 'ONLY display the charcount',
                ARGS_CCHARCOUNT, show_arg=False, section=5),

    # search and match
    ArgConstant('find=X', 'find:X', 'find/query a substring X in the given files',
                -1, section=6),
    ArgConstant('match=X', 'match:X', 'find/query a pattern X in the given files',
                -1, section=6),
    ArgConstant('replace=X', 'replace:X', 'replace queried substrings/patterns in the given files',
                -1, section=6),
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
                ARGS_DATA, show_arg_on_repl=False, section=7),
    ArgConstant('-m', '--checksum', 'show the checksums of all files',
                ARGS_CHECKSUM, show_arg_on_repl=False, section=7),
    ArgConstant('--strings', '', 'print the sequences of printable characters',
                ARGS_STRINGS, section=7),

    # numbers
    ArgConstant('--b64d', '', 'decode the input from base64',
                ARGS_B64D, section=8),
    ArgConstant('--b64e', '', 'encode the input to base64',
                ARGS_B64E, section=8),
    ArgConstant('--eval', '--EVAL', 'evaluate simple mathematical equations',
                ARGS_EVAL, section=8),
    ArgConstant('--hex', '--HEX', 'convert hexadecimal numbers to binary, octal, decimal, utf-8',
                ARGS_HEX, section=8),
    ArgConstant('--dec', '--DEC', 'convert decimal numbers to binary, octal, hexadecimal, utf-8',
                ARGS_DEC, section=8),
    ArgConstant('--oct', '--OCT', 'convert octal numbers to binary, decimal, hexadecimal, utf-8',
                ARGS_OCT, section=8),
    ArgConstant('--bin', '--BIN', 'convert binary numbers to octal, decimal, hexadecimal, utf-8',
                ARGS_BIN, section=8),

    # raw-view
    ArgConstant('--binview', '', 'display the raw byte representation in binary',
                ARGS_BINVIEW, show_arg_on_repl=False, section=9),
    ArgConstant('--hexview', '--HEXVIEW', 'display the raw byte representation in hexadecimal',
                ARGS_HEXVIEW, show_arg_on_repl=False, section=9),

    # display & edit
    ArgConstant('-!', '--edit', 'open each file in a simple editor',
                ARGS_EDITOR, show_arg_on_repl=False, section=10),
    ArgConstant('-#', '--hexedit', 'open each file in a simple hex-editor',
                ARGS_HEX_EDITOR, show_arg_on_repl=False, section=10),
    ArgConstant('-?', '--diff', 'open two files in a simple side-by-side diff-viewer',
                ARGS_DIFF, show_arg_on_repl=False, section=10),
    ArgConstant('fg', '', 'continue a previously backgrounded session',
                -1, show_arg_on_repl=False, section=10),
    ArgConstant('-M', '--more', 'page through the file step by step',
                ARGS_MORE, show_arg_on_repl=False, section=10),
    ArgConstant('-L', '--less', 'page through the file step by step (lazy)',
                ARGS_LESS, show_arg_on_repl=False, section=10),
    ArgConstant('-B', '--raw', 'open the file as raw bytes',
                ARGS_RAW, show_arg_on_repl=False, section=10),

    # visualize
    ArgConstant('--vis', '--visualize', 'visualize the data using space-filling curves',
                -1, show_arg_on_repl=False, section=11, metavar='CURVE'),
    ArgConstant('--visb', '--visualizeb', 'visualize the data using scan curve byte view',
                ARGS_VISUALIZE_B, show_arg=False, section=11),
    ArgConstant('--visz', '--visualizez', 'visualize the data using z-order curve byte view',
                ARGS_VISUALIZE_Z, show_arg=False, section=11),
    ArgConstant('--vish', '--visualizeh', 'visualize the data using hilbert curve byte view',
                ARGS_VISUALIZE_H, show_arg=False, section=11),
    ArgConstant('--vise', '--visualizee', 'visualize the data entropy',
                ARGS_VISUALIZE_E, show_arg_on_repl=False, section=11),
    ArgConstant('--visd', '--visualized', 'visualize the data using digraph dot plot view',
                ARGS_VISUALIZE_D, show_arg_on_repl=False, section=11),

    # behavioural
    ArgConstant('-c', '--clip', 'copy output to clipboard',
                ARGS_CLIP, section=12),
    ArgConstant('-w', '--watch', 'watch files for changes and continuously update the output',
                ARGS_WATCH, section=12),
    ArgConstant('--dot', '--dotfiles', 'additionally query and edit dotfiles',
                ARGS_DOTFILES, show_arg_on_repl=False, section=12),
    ArgConstant('--plain', '--plain-only', 'ignore non-plaintext files automatically',
                ARGS_PLAIN_ONLY, show_arg_on_repl=False, section=12),
    ArgConstant('--nc', '--nocolor', 'disable colored output',
                ARGS_NOCOL, section=12),

    # configuration
    ArgConstant('--config', '', 'change default parameters',
                ARGS_CONFIG, section=13),
    ArgConstant('--cconfig', '', 'change color configuration',
                ARGS_CCONFIG, section=13),
    ArgConstant('--config-clear', '--config-reset', 'reset the config to default settings',
                ARGS_CONFIG_FLUSH, section=13),
    ArgConstant('--cconfig-clear', '--cconfig-reset', 'reset the color config to default settings',
                ARGS_CCONFIG_FLUSH, section=13),
    ArgConstant('--config-remove', '--cconfig-remove', 'remove the config-file',
                ARGS_CONFIG_REMOVE, section=13),

    # (stream) encoding
    ArgConstant('enc=X', 'enc:X', 'set file encoding to X (default is utf-8)',
                -1, section=14),
    ArgConstant('-R', '--R', 'reconfigure the std-streams with the parsed encoding',
                ARGS_RECONFIGURE, section=14, metavar='STREAM'),
    ArgConstant('--Rin', '--Rin', 'reconfigure the stdin with the parsed encoding',
                ARGS_RECONFIGURE_IN, show_arg=False, section=14),
    ArgConstant('--Rout', '--Rout', 'reconfigure the stdout with the parsed encoding',
                ARGS_RECONFIGURE_OUT, show_arg=False, section=14),
    ArgConstant('--Rerr', '--Rerr', 'reconfigure the stderr with the parsed encoding',
                ARGS_RECONFIGURE_ERR, show_arg=False, section=14),

    # installation
    ArgConstant('--generate-man', '', 'print the man page and how to install it',
                ARGS_MAN, show_arg_on_repl=False, section=15),
    ArgConstant('--generate-completion', '',
                'print a shell completion script and how to install it',
                ARGS_COMPLETION, takes_value='SHELL',
                show_arg_on_repl=False, section=15),
    ArgConstant('--generate-sudoshim', '',
                'print a shim so sudo can find cat_win and how to install it',
                ARGS_SUDO_ALLOW, takes_value='SCRIPT',
                show_arg_on_repl=False, section=15),

    # text transforms
    ArgConstant('trunc=X:Y', 'trunc:X:Y', 'truncate file to lines X and Y (python-like)',
                -1, show_arg_on_repl=False, section=16),
    ArgConstant('[A,B]', '', 'replace A with B in every line',
                -1, section=16),
    ArgConstant('[A:B:C]', '', 'python-like string indexing syntax (line by line)',
                -1, section=16),
]
ALL_ARGS.sort(key=lambda x:x.section)

SECTION_NAMES = {
     0: 'General Information',
     1: 'Line Prefix',
     2: 'Special Characters',
     3: 'Line Manipulation',
     4: 'Input Types',
     5: 'Summaries',
     6: 'Search & Match',
     7: 'Meta Information',
     8: 'Mathematical',
     9: 'Byte Representation',
    10: 'Editors & Pagers',
    11: 'Visualization',
    12: 'Behavioural',
    13: 'Configuration',
    14: '(Stream) Encoding',
    15: 'Installation',
    16: 'Text Transforms',
}

VALUE_DESCRIPTIONS = {
    'SHELL' : ("the target shell", ('bash', 'fish', 'zsh')),
    'SCRIPT': ("the target script", ('catw', 'cats')),
    'STREAM': ("the target stream (default: stdin & stdout)", ('in', 'out', 'err')),
    'CURVE' : ("the target curve (scan, z-order, hilbert)", ('b', 'z', 'h')),
}
