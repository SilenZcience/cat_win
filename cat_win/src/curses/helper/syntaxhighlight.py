"""
syntaxhighlight
"""

import builtins
import keyword
import re


TOKEN_KEYWORD = 'keyword'
TOKEN_BUILTIN = 'builtin'
TOKEN_NUMBER  = 'number'
TOKEN_COMMENT = 'comment'
TOKEN_STRING  = 'string'

TYPE_DELIMITER     = 'delimiter'
TYPE_COMMENT       = 'comment'
TYPE_SIMPLE_STRING = 'simple_string'


class SyntaxHighlighter:
    """
    Generic syntax highlighter builder and tokenizer.

    Public API:
    - tokenize_line(line, state=None) -> (tokens, new_state)
        where tokens = [(start_idx, end_idx, token_type), ...]
    - get_plugin(language_key/extension) -> SyntaxHighlighter | None

    - @static register(...)
    """
    _plugins_by_name = {}
    _plugins_by_extension = {}
    _extensions_by_name = {}

    def __init__(
        self,
        plain_pattern,
        plain_group_to_token: dict,
        simple_string_pattern,
        line_comment_prefixes: tuple,
        multiline_delimiters: tuple,
        multiline_end_map: dict,
        delimiter_escape_char: str,
        state_token_map: dict,
        token_color_map: dict,
    ) -> None:
        self.plain_pattern = plain_pattern
        self.plain_group_to_token = plain_group_to_token
        self.simple_string_pattern = simple_string_pattern
        self.line_comment_prefixes = line_comment_prefixes
        self.multiline_delimiters = multiline_delimiters
        self.multiline_end_map = multiline_end_map
        self.delimiter_escape_char = delimiter_escape_char
        self.state_token_map = state_token_map
        self.token_color_map = token_color_map

    @staticmethod
    def register(
            name: str,
            extensions: tuple,
            lex_keywords: tuple = (),
            lex_keywords_case_insensitive: bool = False,
            lex_builtins: tuple = (),
            lex_builtins_case_insensitive: bool = False,
            number_pattern: str = None,
            extra_plain_patterns: tuple = (),
            extra_group_to_token: dict = None,
            simple_string_pattern=None,
            line_comment_prefixes: tuple = (),
            multiline_delimiters: tuple = (),
            multiline_end_delimiters: dict = None,
            multiline_delimiters_case_insensitive: bool = False,
            state_token_map: dict = None,
            delimiter_escape_char: str = '\\',
            token_color_map: dict = None,
    ) -> None:
        if not name:
            raise ValueError("register requires 'name'")
        if not extensions:
            raise ValueError("register requires 'extensions'")

        plain_pattern, group_to_token = SyntaxHighlighter._build_plain_regex_and_tokens(
            lex_keywords=lex_keywords,
            lex_keywords_case_insensitive=lex_keywords_case_insensitive,
            lex_builtins=lex_builtins,
            lex_builtins_case_insensitive=lex_builtins_case_insensitive,
            number_pattern=number_pattern,
            extra_plain_patterns=extra_plain_patterns,
            extra_group_to_token=extra_group_to_token or {}
        )

        multiline_end_delimiters = multiline_end_delimiters or {}
        if not multiline_delimiters and multiline_end_delimiters:
            multiline_delimiters = tuple(multiline_end_delimiters.keys())

        _state_token_map_str = state_token_map or {}
        compiled_delimiters = []
        compiled_end_map = {}
        compiled_state_token_map = {}
        for delimiter_str in multiline_delimiters:
            if multiline_delimiters_case_insensitive:
                start_compiled = re.compile(f'(?i:{delimiter_str})')
            else:
                start_compiled = re.compile(delimiter_str)
            end_val = multiline_end_delimiters.get(delimiter_str, delimiter_str)
            if callable(end_val):
                compiled_end_map[start_compiled] = end_val
            elif multiline_delimiters_case_insensitive:
                compiled_end_map[start_compiled] = re.compile(f'(?i:{end_val})')
            else:
                compiled_end_map[start_compiled] = re.compile(end_val)
            compiled_state_token_map[start_compiled] = _state_token_map_str.get(delimiter_str, TOKEN_STRING)
            compiled_delimiters.append(start_compiled)

        tokenizer = SyntaxHighlighter(
            plain_pattern=plain_pattern,
            plain_group_to_token=group_to_token,
            multiline_delimiters=tuple(compiled_delimiters),
            multiline_end_map=compiled_end_map,
            line_comment_prefixes=line_comment_prefixes,
            simple_string_pattern=re.compile(simple_string_pattern) if simple_string_pattern else None,
            state_token_map=compiled_state_token_map,
            delimiter_escape_char=delimiter_escape_char,
            token_color_map=token_color_map or {},
        )

        SyntaxHighlighter._plugins_by_name[name.casefold()] = tokenizer
        SyntaxHighlighter._extensions_by_name[name.casefold()] = extensions
        for extension in extensions:
            SyntaxHighlighter._plugins_by_extension[str(extension).casefold()] = tokenizer

    @staticmethod
    def get_plugin(language_key: str):
        if not language_key:
            return None
        lookup_key = str(language_key).casefold()
        return SyntaxHighlighter._plugins_by_extension.get(lookup_key) or \
            SyntaxHighlighter._plugins_by_name.get(lookup_key)

    @staticmethod
    def get_available_plugins() -> tuple:
        return (
            dict(sorted(SyntaxHighlighter._plugins_by_name.items())),
            SyntaxHighlighter._extensions_by_name
        )

    @staticmethod
    def _build_plain_regex_and_tokens(
            lex_keywords: tuple = (),
            lex_keywords_case_insensitive: bool = False,
            lex_builtins: tuple = (),
            lex_builtins_case_insensitive: bool = False,
            number_pattern: str = None,
            extra_plain_patterns: tuple = (),
            extra_group_to_token: dict = None
    ) -> tuple:
        parts = []
        group_to_token = {
            TOKEN_KEYWORD: TOKEN_KEYWORD,
            TOKEN_BUILTIN: TOKEN_BUILTIN,
            TOKEN_NUMBER: TOKEN_NUMBER,
        }

        if lex_keywords:
            word_pattern = '|'.join(sorted(lex_keywords, key=len, reverse=True))
            i = 'i' * lex_keywords_case_insensitive
            parts.append(fr"(?P<keyword>\b(?{i}:" + word_pattern + r")\b)")

        if lex_builtins:
            word_pattern = '|'.join(sorted(lex_builtins, key=len, reverse=True))
            i = 'i' * lex_builtins_case_insensitive
            parts.append(fr"(?P<builtin>\b(?{i}:" + word_pattern + r")\b(?=\s*\())")

        if number_pattern:
            parts.append(r"(?P<number>(?x:" + number_pattern + r"))")

        for extra_pattern in extra_plain_patterns:
            if extra_pattern:
                parts.append(extra_pattern)

        if extra_group_to_token:
            group_to_token.update(extra_group_to_token)

        if not parts:
            return None, group_to_token
        return re.compile('|'.join(parts)), group_to_token

    def tokenize_line(self, line: str, state=None) -> tuple:
        tokens = []
        idx = 0
        active_state = state

        multiline_delimiters = self.multiline_delimiters
        multiline_end_map = self.multiline_end_map
        state_token_map = self.state_token_map
        line_comment_prefixes = self.line_comment_prefixes
        plain_pattern = self.plain_pattern
        plain_group_to_token = self.plain_group_to_token
        simple_string_pattern = self.simple_string_pattern
        delimiter_escape_char = self.delimiter_escape_char

        if not line and active_state is not None:
            return tokens, active_state

        while idx < len(line):
            if active_state is not None:
                start_pattern, end_pattern = active_state
                end_m = end_pattern.search(line, idx)
                state_token = state_token_map.get(start_pattern, TOKEN_STRING)
                if end_m is None:
                    tokens.append((idx, len(line), state_token))
                    return tokens, active_state
                tokens.append((idx, end_m.end(), state_token))
                idx = end_m.end()
                active_state = None
                continue

            next_special = len(line)
            next_type = None
            next_value = None

            for start_pattern in multiline_delimiters:
                m = start_pattern.search(line, idx)
                if m is not None and m.start() < next_special:
                    if delimiter_escape_char and m.start() > 0 and line[m.start() - 1] == delimiter_escape_char:
                        continue
                    next_special = m.start()
                    next_type = TYPE_DELIMITER
                    next_value = (start_pattern, m)

            for comment_prefix in line_comment_prefixes:
                comment_idx = line.find(comment_prefix, idx)
                if 0 <= comment_idx < next_special:
                    next_special = comment_idx
                    next_type = TYPE_COMMENT
                    next_value = comment_prefix

            simple_string_match = None
            if simple_string_pattern is not None:
                simple_string_match = simple_string_pattern.search(line, idx)
                if simple_string_match is not None and simple_string_match.start() < next_special:
                    next_special = simple_string_match.start()
                    next_type = TYPE_SIMPLE_STRING
                    next_value = simple_string_match

            if next_special > idx:
                plain_segment = line[idx:next_special]
                if plain_pattern is not None and plain_segment:
                    for match in plain_pattern.finditer(plain_segment):
                        match_group = match.lastgroup
                        if match_group is None:
                            continue
                        token_type = plain_group_to_token.get(match_group)
                        if token_type is None:
                            continue
                        start, end = match.span()
                        if start == end:
                            continue
                        tokens.append((idx + start, idx + end, token_type))
                idx = next_special

            if idx >= len(line):
                break

            if next_type == TYPE_COMMENT:
                tokens.append((idx, len(line), TOKEN_COMMENT))
                return tokens, None

            if next_type == TYPE_DELIMITER:
                start_pattern, start_match = next_value
                end_val = multiline_end_map.get(start_pattern, start_pattern)
                if callable(end_val):
                    end_pattern = re.compile(end_val(start_match))
                else:
                    end_pattern = end_val
                state_token = state_token_map.get(start_pattern, TOKEN_STRING)
                end_m = end_pattern.search(line, start_match.end())
                if end_m is None:
                    tokens.append((start_match.start(), len(line), state_token))
                    return tokens, (start_pattern, end_pattern)
                tokens.append((start_match.start(), end_m.end(), state_token))
                idx = end_m.end()
                continue

            if next_type == TYPE_SIMPLE_STRING and next_value is not None:
                tokens.append((next_value.start(), next_value.end(), TOKEN_STRING))
                idx = next_value.end()
                continue

            idx += 1

        return tokens, None


SyntaxHighlighter.register(
    name='python',
    extensions=('.py', '.pyw', '.pyi'),
    lex_keywords=tuple(set(keyword.kwlist) - {'def', 'lambda', 'class'}),
    extra_plain_patterns=(
        r"(?P<decl_keyword>\b(?:def|lambda|class)\b)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\%\<\>\&\|\^\~\.\@])",
    ),
    extra_group_to_token={
        'decl_keyword': 'decl_keyword',
        'symbols': 'symbols',
    },
    lex_builtins=tuple((f for f in dir(builtins) if not f.startswith('_'))),
    number_pattern=r"""
(?<![0-9A-Za-z_.$+\-])
(?:
    0[bB][01](?:_?[01])* |
    0[oO][0-7](?:_?[0-7])* |
    0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])* |
    [1-9](?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)? |
    \.\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)? |
    (?:
        (?:[1-9](?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?)?
        [+-]?
        \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?
        [jJ]
    )
)
(?![0-9A-Za-z_.$+\-])
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('#',),
    multiline_delimiters=(r'"""', r"'''"),
    state_token_map={
        r'"""': TOKEN_STRING,
        r"'''": TOKEN_STRING,
    },
    token_color_map={
        'decl_keyword': 'magenta',
        'symbols': 'yellow',
    }
)

SyntaxHighlighter.register(
    name='java',
    extensions=('.java',),
    lex_keywords=(
        'assert', 'break', 'case', 'catch',
        'const', 'continue', 'default', 'do', 'else', 'enum',
        'finally', 'for', 'goto', 'if',
        'instanceof', 'native', 'new',
        'return',
        'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
        'transient', 'try', 'volatile',
        'while', 'true', 'false', 'null',
        'var', 'record', 'sealed', 'permits', 'non-sealed',
    ),
    lex_builtins=(
        'toString', 'equals', 'hashCode', 'getClass', 'clone', 'wait', 'notify', 'notifyAll',
        'currentTimeMillis', 'nanoTime', 'exit', 'gc', 'getProperty', 'getenv', 'arraycopy',
        'lineSeparator',
        'abs', 'max', 'min', 'sqrt', 'pow', 'round', 'ceil', 'floor', 'random', 'sin', 'cos',
        'tan', 'log', 'log10', 'exp',
        'length', 'isEmpty', 'charAt', 'substring', 'indexOf', 'lastIndexOf', 'contains',
        'equalsIgnoreCase', 'toUpperCase', 'toLowerCase', 'trim', 'replace', 'replaceAll',
        'split', 'startsWith', 'endsWith', 'valueOf', 'format',
        'parseInt', 'parseDouble', 'parseLong', 'compareTo',
        'print', 'println', 'printf',
    ),
    extra_plain_patterns=(
        r"(?P<import_keyword>\b(?:import|package)\b)",
        r"(?P<object_keyword>\b(?:boolean|double|float|char|long|int|short|byte|void|public|private|protected|final|static|abstract|class|extends|implements|interface)\b)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\%\<\>\&\|\^\~\.\@])",
    ),
    extra_group_to_token={
        'import_keyword': 'import_keyword',
        'object_keyword': 'object_keyword',
        'symbols': 'symbols',
    },
    number_pattern=r"""
(?<![0-9A-Za-z_$+\-.])
(?:
    0[bB][01](?:_?[01])*[lL]? |
    0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*[lL]? |
    \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?[fFdDlL]? |
    \.\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?[fFdD]?
)
(?![0-9A-Za-z_$+\-.])
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('//',),
    multiline_delimiters=(r'/\*', r'"""'),
    multiline_end_delimiters={
        r'/\*': r'\*/',
    },
    state_token_map={
        r'/\*': TOKEN_COMMENT,
        r'"""': TOKEN_STRING,
    },
    token_color_map={
        'import_keyword': 'red',
        'object_keyword': 'magenta',
        'symbols': 'yellow',
    }
)

SyntaxHighlighter.register(
    name='autoit',
    extensions=('.au3',),
    lex_keywords=(
        'False', 'True', 'ContinueCase', 'ContinueLoop', 'Default', 'Dim', 'Global',
        'Local', 'Const', 'Do', 'Until', 'Enum', 'Exit', 'ExitLoop', 'For', 'To',
        'Step', 'Next', 'In', 'Func', 'Return', 'EndFunc', 'If', 'Then', 'ElseIf', 'Else',
        'EndIf', 'Null', 'ReDim', 'Select', 'Case', 'EndSelect', 'Static', 'Switch', 'EndSwitch',
        'Volatile', 'While', 'WEnd', 'With', 'EndWith', 'ByRef', 'And', 'Or', 'Not',
    ),
    lex_keywords_case_insensitive=True,
    lex_builtins=(
        'Function', 'Abs', 'ACos', 'AdlibRegister', 'AdlibUnRegister', 'Asc', 'AscW', 'ASin', 'Assign',
        'ATan', 'AutoItSetOption', 'AutoItWinGetTitle', 'AutoItWinSetTitle', 'Beep', 'Binary', 'BinaryLen',
        'BinaryMid', 'BinaryToString', 'BitAND', 'BitNOT', 'BitOR', 'BitRotate', 'BitShift', 'BitXOR', 'BlockInput',
        'Break', 'Call', 'CDTray', 'Ceiling', 'Chr', 'ChrW', 'ClipGet', 'ClipPut', 'ConsoleRead', 'ConsoleWrite',
        'ConsoleWriteError', 'ControlClick', 'ControlCommand', 'ControlDisable', 'ControlEnable', 'ControlFocus',
        'ControlGetFocus', 'ControlGetHandle', 'ControlGetPos', 'ControlGetText', 'ControlHide', 'ControlListView',
        'ControlMove', 'ControlSend', 'ControlSetText', 'ControlShow', 'ControlTreeView', 'Cos', 'Dec', 'DirCopy',
        'DirCreate', 'DirGetSize', 'DirMove', 'DirRemove', 'DllCall', 'DllCallAddress', 'DllCallbackFree', 'DllCallbackGetPtr',
        'DllCallbackRegister', 'DllClose', 'DllOpen', 'DllStructCreate', 'DllStructGetData', 'DllStructGetPtr', 'DllStructGetSize',
        'DllStructSetData', 'DriveGetDrive', 'DriveGetFileSystem', 'DriveGetLabel', 'DriveGetSerial', 'DriveGetType',
        'DriveMapAdd', 'DriveMapDel', 'DriveMapGet', 'DriveSetLabel', 'DriveSpaceFree', 'DriveSpaceTotal', 'DriveStatus',
        'EnvGet', 'EnvSet', 'EnvUpdate', 'Eval', 'Execute', 'Exp', 'FileChangeDir', 'FileClose', 'FileCopy', 'FileCreateNTFSLink',
        'FileCreateShortcut', 'FileDelete', 'FileExists', 'FileFindFirstFile', 'FileFindNextFile', 'FileFlush', 'FileGetAttrib',
        'FileGetEncoding', 'FileGetLongName', 'FileGetPos', 'FileGetShortcut', 'FileGetShortName', 'FileGetSize', 'FileGetTime',
        'FileGetVersion', 'FileInstall', 'FileMove', 'FileOpen', 'FileOpenDialog', 'FileRead', 'FileReadLine', 'FileReadToArray',
        'FileRecycle', 'FileRecycleEmpty', 'FileSaveDialog', 'FileSelectFolder', 'FileSetAttrib', 'FileSetEnd', 'FileSetPos',
        'FileSetTime', 'FileWrite', 'FileWriteLine', 'Floor', 'FtpSetProxy', 'FuncName', 'GUICreate', 'GUICtrlCreateAvi',
        'GUICtrlCreateButton', 'GUICtrlCreateCheckbox', 'GUICtrlCreateCombo', 'GUICtrlCreateContextMenu', 'GUICtrlCreateDate',
        'GUICtrlCreateDummy', 'GUICtrlCreateEdit', 'GUICtrlCreateGraphic', 'GUICtrlCreateGroup', 'GUICtrlCreateIcon', 'GUICtrlCreateInput',
        'GUICtrlCreateLabel', 'GUICtrlCreateList', 'GUICtrlCreateListView', 'GUICtrlCreateListViewItem', 'GUICtrlCreateMenu',
        'GUICtrlCreateMenuItem', 'GUICtrlCreateMonthCal', 'GUICtrlCreateObj', 'GUICtrlCreatePic', 'GUICtrlCreateProgress',
        'GUICtrlCreateRadio', 'GUICtrlCreateSlider', 'GUICtrlCreateTab', 'GUICtrlCreateTabItem', 'GUICtrlCreateTreeView',
        'GUICtrlCreateTreeViewItem', 'GUICtrlCreateUpdown', 'GUICtrlDelete', 'GUICtrlGetHandle', 'GUICtrlGetState', 'GUICtrlRead',
        'GUICtrlRecvMsg', 'GUICtrlRegisterListViewSort', 'GUICtrlSendMsg', 'GUICtrlSendToDummy', 'GUICtrlSetBkColor', 'GUICtrlSetColor',
        'GUICtrlSetCursor', 'GUICtrlSetData', 'GUICtrlSetDefBkColor', 'GUICtrlSetDefColor', 'GUICtrlSetFont', 'GUICtrlSetGraphic',
        'GUICtrlSetImage', 'GUICtrlSetLimit', 'GUICtrlSetOnEvent', 'GUICtrlSetPos', 'GUICtrlSetResizing', 'GUICtrlSetState',
        'GUICtrlSetStyle', 'GUICtrlSetTip', 'GUIDelete', 'GUIGetCursorInfo', 'GUIGetMsg', 'GUIGetStyle', 'GUIRegisterMsg',
        'GUISetAccelerators', 'GUISetBkColor', 'GUISetCoord', 'GUISetCursor', 'GUISetFont', 'GUISetHelp', 'GUISetIcon', 'GUISetOnEvent',
        'GUISetState', 'GUISetStyle', 'GUIStartGroup', 'GUISwitch', 'Hex', 'HotKeySet', 'HttpSetProxy', 'HttpSetUserAgent', 'HWnd',
        'InetClose', 'InetGet', 'InetGetInfo', 'InetGetSize', 'InetRead', 'IniDelete', 'IniRead', 'IniReadSection',
        'IniReadSectionNames', 'IniRenameSection', 'IniWrite', 'IniWriteSection', 'InputBox', 'Int', 'IsAdmin', 'IsArray', 'IsBinary',
        'IsBool', 'IsDeclared', 'IsDllStruct', 'IsFloat', 'IsFunc', 'IsHWnd', 'IsInt', 'IsKeyword', 'IsMap', 'IsNumber', 'IsObj',
        'IsPtr', 'IsString', 'Log', 'MapAppend', 'MapExists', 'MapKeys', 'MapRemove', 'MemGetStats', 'Mod', 'MouseClick', 'MouseClickDrag',
        'MouseDown', 'MouseGetCursor', 'MouseGetPos', 'MouseMove', 'MouseUp', 'MouseWheel', 'MsgBox', 'Number', 'ObjCreate',
        'ObjCreateInterface', 'ObjEvent', 'ObjGet', 'ObjName', 'OnAutoItExitRegister', 'OnAutoItExitUnRegister', 'Ping', 'PixelChecksum',
        'PixelGetColor', 'PixelSearch', 'ProcessClose', 'ProcessExists', 'ProcessGetStats', 'ProcessList', 'ProcessSetPriority', 'ProcessWait',
        'ProcessWaitClose', 'ProgressOff', 'ProgressOn', 'ProgressSet', 'Ptr', 'Random', 'RegDelete', 'RegEnumKey', 'RegEnumVal', 'RegRead',
        'RegWrite', 'Round', 'Run', 'RunAs', 'RunAsWait', 'RunWait', 'Send', 'SendKeepActive', 'SetError', 'SetExtended', 'ShellExecute',
        'ShellExecuteWait', 'Shutdown', 'Sin', 'Sleep', 'SoundPlay', 'SoundSetWaveVolume', 'SplashImageOn', 'SplashOff', 'SplashTextOn', 'Sqrt',
        'SRandom', 'StatusbarGetText', 'StderrRead', 'StdinWrite', 'StdioClose', 'StdoutRead', 'String', 'StringAddCR', 'StringCompare', 'StringFormat',
        'StringFromASCIIArray', 'StringInStr', 'StringIsAlNum', 'StringIsAlpha', 'StringIsASCII', 'StringIsDigit', 'StringIsFloat', 'StringIsInt',
        'StringIsLower', 'StringIsSpace', 'StringIsUpper', 'StringIsXDigit', 'StringLeft', 'StringLen', 'StringLower', 'StringMid', 'StringRegExp',
        'StringRegExpReplace', 'StringReplace', 'StringReverse', 'StringRight', 'StringSplit', 'StringStripCR', 'StringStripWS', 'StringToASCIIArray',
        'StringToBinary', 'StringTrimLeft', 'StringTrimRight', 'StringUpper', 'Tan', 'TCPAccept', 'TCPCloseSocket', 'TCPConnect', 'TCPListen',
        'TCPNameToIP', 'TCPRecv', 'TCPSend', 'TCPShutdown', 'TCPStartup', 'TimerDiff', 'TimerInit', 'ToolTip', 'TrayCreateItem', 'TrayCreateMenu',
        'TrayGetMsg', 'TrayItemDelete', 'TrayItemGetHandle', 'TrayItemGetState', 'TrayItemGetText', 'TrayItemSetOnEvent', 'TrayItemSetState',
        'TrayItemSetText', 'TraySetClick', 'TraySetIcon', 'TraySetOnEvent', 'TraySetPauseIcon', 'TraySetState', 'TraySetToolTip', 'TrayTip',
        'UBound', 'UDPBind', 'UDPCloseSocket', 'UDPOpen', 'UDPRecv', 'UDPSend', 'VarGetType', 'WinActivate', 'WinActive', 'WinClose', 'WinExists',
        'WinFlash', 'WinGetCaretPos', 'WinGetClassList', 'WinGetClientSize', 'WinGetHandle', 'WinGetPos', 'WinGetProcess', 'WinGetState',
        'WinGetText', 'WinGetTitle', 'WinKill', 'WinList', 'WinMenuSelectItem', 'WinMinimizeAll', 'WinMinimizeAllUndo', 'WinMove',
        'WinSetOnTop', 'WinSetState', 'WinSetTitle', 'WinSetTrans', 'WinWait', 'WinWaitActive', 'WinWaitClose', 'WinWaitNotActive',
    ),
    lex_builtins_case_insensitive=True,
    extra_plain_patterns=(
        r"(?P<hashtag_keywords>(?i:#(?:include-once|include|NoTrayIcon|OnAutoItStartRegister|pragma|RequireAdmin))\b)",
        r"(?P<preproccesing>(?i:#(?:Region|EndRegion|AutoIt3Wrapper.*))\b)",
        r"(?P<at_keywords>(?i:@(?:AppDataCommonDir|AppDataDir|AutoItExe|AutoItPID|AutoItVersion|AutoItX64|COM_EventObj|CommonFilesDir|Compiled|ComputerName|ComSpec|primary|CPUArch|CR|CRLF|DesktopCommonDir|DesktopDepth|DesktopDir|DesktopHeight|DesktopRefresh|DesktopWidth|DocumentsCommonDir|error|exitCode|exitMethod|extended|FavoritesCommonDir|FavoritesDir|GUI_CtrlHandle|GUI_CtrlId|GUI_DragFile|GUI_DragId|GUI_DropId|GUI_WinHandle|HomeDrive|HomePath|HomeShare|HotKeyPressed|HOUR|IPAddress1|IPAddress2|IPAddress3|IPAddress4|KBLayout|LF|LocalAppDataDir|LogonDNSDomain|LogonDomain|LogonServer|MDAY|MIN|MON|MSEC|MUILang|MyDocumentsDir|NumParams|OSArch|OSBuild|OSLang|OSServicePack|OSType|OSVersion|ProgramFilesDir|ProgramsCommonDir|ProgramsDir|ScriptDir|ScriptFullPath|ScriptLineNumber|ScriptName|SEC|StartMenuCommonDir|StartMenuDir|StartupCommonDir|StartupDir|SW_DISABLE|SW_ENABLE|SW_HIDE|SW_LOCK|SW_MAXIMIZE|SW_MINIMIZE|SW_RESTORE|SW_SHOW|SW_SHOWDEFAULT|SW_SHOWMAXIMIZED|SW_SHOWMINIMIZED|SW_SHOWMINNOACTIVE|SW_SHOWNA|SW_SHOWNOACTIVATE|SW_SHOWNORMAL|SW_UNLOCK|SystemDir|TAB|TempDir|TRAY_ID|TrayIconFlashing|TrayIconVisible|UserName|UserProfileDir|WDAY|WindowsDir|WorkingDir|YDAY|YEAR))\b)",
        r"(?P<variable>(?i:\$\w+)\b)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\<\>\&\|\^\?\:])",
    ),
    extra_group_to_token={
        'hashtag_keywords': 'hashtag_keywords',
        'preproccesing': 'preproccesing',
        'at_keywords': 'at_keywords',
        'variable': 'variable',
        'symbols': 'symbols',
    },
    number_pattern=r"""
(?<![0-9A-Za-z_+\-.])
(?:
    0[xX][0-9a-fA-F]* |
    \d+(?:\.\d*)?(?:[eE][+-]?\d*)? |
    \.\d+(?:[eE][+-]?\d*)?
)
(?![0-9A-Za-z_+\-.])
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=(';',),
    multiline_delimiters=(r'#comments-start', r'#cs'),
    multiline_end_delimiters={
        r'#comments-start': r'#comments-end',
        r'#cs': r'#ce',
    },
    multiline_delimiters_case_insensitive=True,
    state_token_map={
        r'#comments-start' : TOKEN_COMMENT,
        r'#cs': TOKEN_COMMENT,
    },
    token_color_map={
        TOKEN_KEYWORD: 'lightblue',
        TOKEN_BUILTIN: 'blue',
        TOKEN_NUMBER: 'lightblue',
        TOKEN_COMMENT: 'green',
        TOKEN_STRING: 'red',
        'hashtag_keywords': 'yellow',
        'preproccesing': 'red',
        'at_keywords': 'yellow',
        'variable': 'lightblack',
        'symbols': 'yellow',
    }
)

SyntaxHighlighter.register(
    name='c/c++',
    extensions=(
        '.c', '.h',
        '.cpp', '.cxx', '.cc', '.hpp', '.hxx', '.hh', '.h++', '.c++'
    ),
    lex_keywords=(
        'auto', 'break', 'case', 'continue', 'default', 'do',
        'else', 'for', 'goto', 'if',
        'return', 'sizeof', 'switch',
        'while', 'asm', 'typeof', 'inline', 'false', 'true',
        'co_await', 'co_return', 'co_yield', 'try', 'throw', 'this',
        'static_cast', 'reinterpret_cast', 'nullptr', 'new', 'noexcept',
        'dynamic_cast', 'catch',  'const_cast', 'delete',
        'operator', 'static_assert', 'typeid', 'typename', 'alignas', 'alignof', 'decltype',
        'and', 'and_eq', 'atomic_cancel', 'atomic_commit', 'atomic_noexcept', 'bitand',
        'bitor', 'compl', 'contract_assert', 'not', 'not_eq', 'or', 'or_eq', 'reflexpr',
        'synchronized', 'typename', 'xor', 'xor_eq',

    ),
    lex_builtins=(
        'printf', 'scanf', 'fprintf', 'fscanf', 'sprintf', 'sscanf', 'snprintf',
        'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell', 'rewind',
        'fgets', 'fputs', 'fputc', 'fgetc', 'getchar', 'putchar', 'puts', 'gets',
        'malloc', 'calloc', 'realloc', 'free',
        'exit', 'abort', 'atexit',
        'strlen', 'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp',
        'strchr', 'strrchr', 'strstr', 'strtok',
        'memset', 'memcpy', 'memmove', 'memcmp', 'memchr',
        'atoi', 'atof', 'atol', 'strtol', 'strtod', 'strtoul',
        'rand', 'srand', 'abs', 'labs', 'div', 'ldiv',
        'ceil', 'floor', 'sqrt', 'pow', 'fabs', 'sin', 'cos', 'tan',
        'asin', 'acos', 'atan', 'atan2', 'exp', 'log', 'log10',
        'assert', 'perror',
        'isalpha', 'isdigit', 'isalnum', 'isspace', 'isupper', 'islower',
        'toupper', 'tolower',
        'qsort', 'bsearch', 'NULL',
    ),
    extra_plain_patterns=(
        r"(?P<type_keyword>\b(?:unsigned|double|signed|float|short|void|char|long|int|bool|friend|mutable|explicit|volatile|namespace|public|protected|private|union|const|enum|virtual|template|extern|static|register|restrict|class|final|override|thread_local|consteval|constexpr|wchar_t)\b)",
        r"(?P<red_keyword>\b(?:concept|requires|constinit|using|export|import|module)\b)",
        r"(?P<preprocessor>#(?:include|define|defined|undef|ifdef|ifndef|elifdef|elifndef|elif|endif|pragma|error|warning|line|embed|if|else)\b)",
        r"(?P<typedef>\b(?:typedef|struct)\b)",
        r"(?P<charclass>\b(?:char8_t|char16_t|char32_t)\b)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\%\<\>\&\|\^\~\.\!\?\:\,\;])",
    ),
    extra_group_to_token={
        'type_keyword': 'type_keyword',
        'red_keyword': 'red_keyword',
        'preprocessor': 'preprocessor',
        'symbols': 'symbols',
        'typedef': 'typedef',
        'charclass': 'charclass',
    },
    number_pattern=r"""
(?<![0-9A-Za-z_.$+\-])
(?:
    0[bB][01](?:_?[01])*(?:[uU](?:ll?|LL?)?|(?:ll?|LL?)[uU]?)? |
    0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*(?:[uU](?:ll?|LL?)?|(?:ll?|LL?)[uU]?)? |
    0[0-7]+(?:[uU](?:ll?|LL?)?|(?:ll?|LL?)[uU]?)? |
    \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?(?:[uU](?:ll?|LL?)?|(?:ll?|LL?)[uU]?|[fFlL])? |
    \.\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?[fFlL]?
)
(?![0-9A-Za-z_.$+\-])
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('//',),
    multiline_delimiters=(r'/\*',),
    multiline_end_delimiters={r'/\*': r'\*/'},
    state_token_map={r'/\*': TOKEN_COMMENT},
    token_color_map={
        TOKEN_KEYWORD: 'lightblue',
        'type_keyword': 'magenta',
        'red_keyword': 'lightred',
        'preprocessor': 'cyan',
        'symbols': 'yellow',
        'typedef': 'red',
        'charclass': 'yellow',
    }
)

SyntaxHighlighter.register(
    name='lua',
    extensions=(
        '.lua',
    ),
    lex_keywords=(
        'and', 'break', 'do', 'else', 'elseif',
        'end', 'false', 'for', 'function', 'global',
        'goto', 'if',
        'in', 'local', 'nil', 'not', 'or',
        'repeat', 'return', 'then', 'true', 'until', 'while',
    ),
    lex_builtins=(
        'dofile', 'dostring', 'next', 'nextvar', 'tostring',
        'print', 'tonumber', 'type', 'assert', 'error', 'setglobal',
        'getglobal', 'setfallback',
    ),
    extra_plain_patterns=(
        r"(?P<const>\<const\>)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\%\<\>\^\.\:\,\;\#\~\&\|])",
    ),
    extra_group_to_token={
        'symbols': 'symbols',
        'const': 'const',
    },
    number_pattern=r"""
(?<![0-9A-Za-z_.])
(?:
    0[xX][0-9a-fA-F]+ |
    \d+(?:\.\d*)?(?:[eE][+-]?\d+)? |
    \.\d+(?:[eE][+-]?\d+)?
)
(?![0-9A-Za-z_.])
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('--',),
    multiline_delimiters=(r'--\[(=*)\[',),
    multiline_end_delimiters={r'--\[(=*)\[': lambda m: r'\]' + re.escape(m.group(1)) + r'\]'},
    state_token_map={r'--\[(=*)\[': TOKEN_COMMENT},
    token_color_map={
        TOKEN_KEYWORD: 'lightblue',
        'symbols': 'yellow',
        'const': 'lightmagenta',
    }
)

SyntaxHighlighter.register(
    name='rust',
    extensions=('.rs',),
    lex_keywords=(
        'as', 'await', 'break', 'continue',
        'else', 'extern', 'false', 'for', 'if', 'in',
        'loop', 'match', 'mod', 'move',
        'return', 'self', 'Self', 'static', 'super',
        'true', 'type', 'union', 'while',
        'abstract', 'do', 'macro',
        'try', 'yield', 'raw',
        'macro_rules',
    ),
    lex_builtins=(
        'drop', 'Some', 'None', 'Ok', 'Err',
        'Box', 'Vec', 'String', 'Option', 'Result',
        'panic', 'assert', 'assert_eq', 'assert_ne',
        'println', 'print', 'eprintln', 'eprint',
        'format', 'write', 'writeln',
        'todo', 'unimplemented', 'unreachable',
        'clone', 'copy', 'default',
        'len', 'push', 'pop', 'contains', 'iter', 'map', 'filter',
        'unwrap', 'expect', 'into', 'from', 'into_iter',
        'min', 'max', 'abs', 'pow', 'sqrt',
    ),
    extra_plain_patterns=(
        r"(?P<decl_keyword>\b(?:let|mut|struct|trait|enum|const)\b)",
        r"(?P<fn_keyword>\b(?:async|crate|safe|unsafe|use|pub|priv|impl|dyn|where|fn|ref|become|box|final|gen|override|typeof|unsized|virtual)\b)",
        r"(?P<type_keyword>\b(?:bool|char|str|i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|f32|f64)\b)",
        r"(?P<char>'.')",
        r"(?P<lifetime>'[A-Za-z_][A-Za-z0-9_]*\b)",
        r"(?P<macro_call>\b[A-Za-z_][A-Za-z0-9_]*!)",
        r"(?P<symbols>[\[\]\{\}\(\)\+\-\*\/\=\%\<\>\&\|\^\~\.\!\?\:\,\;\@\#])",
    ),
    extra_group_to_token={
        'decl_keyword': 'decl_keyword',
        'fn_keyword': 'fn_keyword',
        'type_keyword': 'type_keyword',
        'char': 'char',
        'lifetime': 'lifetime',
        'macro_call': 'macro_call',
        'symbols': 'symbols',
    },
    number_pattern=r"""
(?<![0-9A-Za-z_.])
(?:
    0[bB][01][01_]*(?:_?(?:i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize))? |
    0[oO][0-7][0-7_]*(?:_?(?:i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize))? |
    0[xX][0-9a-fA-F][0-9a-fA-F_]*(?:_?(?:i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize))? |
    \d[\d_]*(?:\.[\d_]+)?(?:[eE][+-]?[\d_]+)?(?:_?(?:f32|f64|i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize))?
)
(?![0-9A-Za-z_.])
""",
    simple_string_pattern=r'"(?:\\.|[^"\\\n])*"',
    line_comment_prefixes=('//',),
    multiline_delimiters=(r'/\*',),
    multiline_end_delimiters={r'/\*': r'\*/'},
    state_token_map={r'/\*': TOKEN_COMMENT},
    delimiter_escape_char='',
    token_color_map={
        TOKEN_KEYWORD: 'lightblue',
        'decl_keyword': 'magenta',
        'fn_keyword': 'red',
        'type_keyword': 'yellow',
        'char': 'lightgreen',
        'lifetime': 'yellow',
        'macro_call': 'blue',
        'symbols': 'lightcyan',
    }
)
