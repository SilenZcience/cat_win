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
        plain_pattern: re.Pattern,
        plain_group_to_token: dict,
        simple_string_pattern: re.Pattern,
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
            lex_builtins: tuple = (),
            number_pattern: str = None,
            extra_plain_patterns: tuple = (),
            extra_group_to_token: dict = None,
            simple_string_pattern=None,
            line_comment_prefixes: tuple = (),
            multiline_delimiters: tuple = (),
            multiline_end_delimiters: dict = None,
            state_token_map: dict = None,
            delimiter_escape_char: str = '\\',
            token_color_map: dict = None,
    ):
        if not name:
            raise ValueError("register requires 'name'")
        if not extensions:
            raise ValueError("register requires 'extensions'")

        plain_pattern, group_to_token = SyntaxHighlighter._build_plain_regex_and_tokens(
            lex_keywords=lex_keywords,
            lex_builtins=lex_builtins,
            number_pattern=number_pattern,
            extra_plain_patterns=extra_plain_patterns,
            extra_group_to_token=extra_group_to_token or {}
        )

        multiline_end_delimiters = multiline_end_delimiters or {}
        if not multiline_delimiters and multiline_end_delimiters:
            multiline_delimiters = tuple(multiline_end_delimiters.keys())

        tokenizer = SyntaxHighlighter(
            plain_pattern=plain_pattern,
            plain_group_to_token=group_to_token,
            multiline_delimiters=multiline_delimiters,
            multiline_end_map={
                delimiter: multiline_end_delimiters.get(delimiter, delimiter)
                for delimiter in multiline_delimiters
            },
            line_comment_prefixes=line_comment_prefixes,
            simple_string_pattern=re.compile(simple_string_pattern) if simple_string_pattern else None,
            state_token_map=state_token_map or {},
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
        return SyntaxHighlighter._plugins_by_name, SyntaxHighlighter._extensions_by_name

    @staticmethod
    def _build_plain_regex_and_tokens(
            lex_keywords: tuple = (),
            lex_builtins: tuple = (),
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
            parts.append(r"(?P<keyword>\b(?:" + word_pattern + r")\b)")

        if lex_builtins:
            word_pattern = '|'.join(sorted(lex_builtins, key=len, reverse=True))
            parts.append(r"(?P<builtin>\b(?:" + word_pattern + r")\b(?=\s*\())")

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

    def tokenize_line(self, line: str, state: str = None) -> tuple:
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

        if not line and active_state in multiline_delimiters:
            return tokens, active_state

        while idx < len(line):
            if active_state in multiline_delimiters:
                end_delimiter = multiline_end_map.get(active_state, active_state)
                end_idx = line.find(end_delimiter, idx)
                state_token = state_token_map.get(active_state, TOKEN_STRING)
                if end_idx < 0:
                    tokens.append((idx, len(line), state_token))
                    return tokens, active_state
                tokens.append((idx, end_idx + len(end_delimiter), state_token))
                idx = end_idx + len(end_delimiter)
                active_state = None
                continue

            next_special = len(line)
            next_type = None
            next_value = None

            for delimiter in multiline_delimiters:
                delimiter_idx = line.find(delimiter, idx)
                if delimiter_idx >= 0 and delimiter_idx < next_special:
                    if delimiter_escape_char and delimiter_idx > 0 and line[delimiter_idx - 1] == delimiter_escape_char:
                        continue
                    next_special = delimiter_idx
                    next_type = TYPE_DELIMITER
                    next_value = delimiter

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
                end_delimiter = multiline_end_map.get(next_value, next_value)
                end_idx = line.find(end_delimiter, idx + len(next_value))
                state_token = state_token_map.get(next_value, TOKEN_STRING)
                if end_idx < 0:
                    tokens.append((idx, len(line), state_token))
                    return tokens, next_value
                tokens.append((idx, end_idx + len(end_delimiter), state_token))
                idx = end_idx + len(end_delimiter)
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
\b(?:
    0[bB][01](?:_?[01])* |
    0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])* |
    \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)? |
    (?:
        (?:\d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?)?
        [+-]?
        \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?
        [jJ]
    )
)\b
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('#',),
    multiline_delimiters=('"""', "'''"),
    state_token_map={
        '"""': TOKEN_STRING,
        "'''": TOKEN_STRING,
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
\b(?:
    0[bB][01](?:_?[01])*[lL]? |
    0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*[lL]? |
    \d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?[fFdDlL]? |
    \.\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?[fFdD]?
)\b
""",
    simple_string_pattern=r"(['\"])(?:\\.|(?!\1)[^\\\n])*\1",
    line_comment_prefixes=('//',),
    multiline_delimiters=('/*', '"""'),
    multiline_end_delimiters={
        '/*': '*/',
    },
    state_token_map={
        '/*' : TOKEN_COMMENT,
        '"""': TOKEN_STRING,
    },
    token_color_map={
        'import_keyword': 'red',
        'object_keyword': 'magenta',
        'symbols': 'yellow',
    }
)
