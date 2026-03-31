from unittest import TestCase
from unittest.mock import patch
import re
import cat_win.src.curses.helper.syntaxhighlight as syntaxhighlight_module

from cat_win.src.curses.helper.syntaxhighlight import (
    SyntaxHighlighter,
    TOKEN_KEYWORD,
    TOKEN_BUILTIN,
    TOKEN_NUMBER,
    TOKEN_COMMENT,
    TOKEN_STRING,
)


class TestSyntaxHighlighter(TestCase):
    def setUp(self):
        self._plugins_by_name = dict(SyntaxHighlighter._plugins_by_name)
        self._plugins_by_extension = dict(SyntaxHighlighter._plugins_by_extension)
        self._extensions_by_name = dict(SyntaxHighlighter._extensions_by_name)
        self.python = SyntaxHighlighter.get_plugin('python')

    def tearDown(self):
        SyntaxHighlighter._plugins_by_name = self._plugins_by_name
        SyntaxHighlighter._plugins_by_extension = self._plugins_by_extension
        SyntaxHighlighter._extensions_by_name = self._extensions_by_name

    def test_python_plugin_tokenize_line(self):
        tokens, _ = self.python.tokenize_line("if int(value) == 10: print('x') # c")
        token_types = [token_type for _, _, token_type in tokens]
        self.assertIn('keyword', token_types)
        self.assertIn('builtin', token_types)
        self.assertIn('number', token_types)
        self.assertIn('string', token_types)
        self.assertIn('comment', token_types)

    def test_python_plugin_multiline_string(self):
        line_a_tokens, state_a = self.python.tokenize_line('x = """hello')
        line_b_tokens, state_b = self.python.tokenize_line('world""" + str(1)', state_a)

        self.assertIsNotNone(state_a)
        self.assertIsNone(state_b)
        self.assertTrue(any(token_type == 'string' for _, _, token_type in line_a_tokens))
        self.assertTrue(any(token_type == 'string' for _, _, token_type in line_b_tokens))
        self.assertTrue(any(token_type == 'builtin' for _, _, token_type in line_b_tokens))

    def test_python_plugin_multiline_string_across_empty_line(self):
        _, state_a = self.python.tokenize_line('x = """hello')
        empty_tokens, state_b = self.python.tokenize_line('', state_a)
        line_c_tokens, state_c = self.python.tokenize_line('world""" + int(2)', state_b)

        self.assertIsNotNone(state_a)
        self.assertIsNotNone(state_b)
        self.assertListEqual(empty_tokens, [])
        self.assertIsNone(state_c)
        self.assertTrue(any(token_type == 'string' for _, _, token_type in line_c_tokens))
        self.assertTrue(any(token_type == 'builtin' for _, _, token_type in line_c_tokens))

    def test_register_language(self):
        SyntaxHighlighter.register(
            name='toy_lang_simple',
            extensions=('.toys',),
            lex_keywords=('let', 'fn'),
            lex_builtins=('len',),
            number_pattern=r"\b\d+\b",
            line_comment_prefixes=('//',),
            multiline_delimiters=(r'/\*',),
            multiline_end_delimiters={r'/\*': r'\*/'},
            state_token_map={r'/\*': 'comment'},
            simple_string_pattern=r'"(?:\\.|[^"\\\n])*"',
        )
        toy = SyntaxHighlighter.get_plugin('toy_lang_simple')

        tokens_a, state_a = toy.tokenize_line('let x = len(a) /* hello')
        tokens_b, state_b = toy.tokenize_line('world */ fn y = 3', state_a)

        self.assertIsNotNone(state_a)
        self.assertIsNone(state_b)
        self.assertTrue(any(token_type == 'keyword' for _, _, token_type in tokens_a))
        self.assertTrue(any(token_type == 'builtin' for _, _, token_type in tokens_a))
        self.assertTrue(any(token_type == 'comment' for _, _, token_type in tokens_a))
        self.assertTrue(any(token_type == 'comment' for _, _, token_type in tokens_b))

    def test_python_tokenize_numbers(self):
        tokens, _ = self.python.tokenize_line('x = 1234 + 0xFF + 3.14')
        types = [t for _, _, t in tokens]
        self.assertIn('number', types)

    def test_python_tokenize_keywords_and_builtins(self):
        tokens, _ = self.python.tokenize_line('if isinstance(x, int): print("ok")')
        types = [t for _, _, t in tokens]
        self.assertIn('keyword', types)
        self.assertIn('builtin', types)

    def test_python_tokenize_comment(self):
        tokens, _ = self.python.tokenize_line('x = 1 # comment here')
        self.assertTrue(any(t == 'comment' for _, _, t in tokens))

    def test_python_tokenize_string(self):
        tokens, _ = self.python.tokenize_line('s = "hello"')
        self.assertTrue(any(t == 'string' for _, _, t in tokens))

    def test_python_multiline_string_state(self):
        _, state = self.python.tokenize_line('s = """hello')
        self.assertIsNotNone(state)
        tokens2, state2 = self.python.tokenize_line('world"""', state)
        self.assertIsNone(state2)
        self.assertTrue(any(t == 'string' for _, _, t in tokens2))

    def test_register_requires_name_and_extensions(self):
        with self.assertRaises(ValueError):
            SyntaxHighlighter.register('', ('.x',))
        with self.assertRaises(ValueError):
            SyntaxHighlighter.register('xlang', ())

    def test_build_plain_regex_and_tokens_empty(self):
        plain, group_map = SyntaxHighlighter._build_plain_regex_and_tokens()
        self.assertIsNone(plain)
        self.assertEqual(group_map[TOKEN_KEYWORD], TOKEN_KEYWORD)
        self.assertEqual(group_map[TOKEN_BUILTIN], TOKEN_BUILTIN)
        self.assertEqual(group_map[TOKEN_NUMBER], TOKEN_NUMBER)

    def test_build_plain_regex_and_tokens_with_patterns(self):
        plain, group_map = SyntaxHighlighter._build_plain_regex_and_tokens(
            lex_keywords=('if',),
            lex_builtins=('print',),
            number_pattern=r'\d+',
            extra_plain_patterns=(r'(?P<extra>x+)',),
            extra_group_to_token={'extra': 'extra'}
        )

        self.assertIsNotNone(plain)
        self.assertEqual(group_map['extra'], 'extra')
        self.assertIsNotNone(plain.search('if'))
        self.assertIsNotNone(plain.search('print('))
        self.assertIsNotNone(plain.search('123'))
        self.assertIsNotNone(plain.search('xxx'))

    def test_register_and_get_plugin(self):
        SyntaxHighlighter.register(
            name='xlang',
            extensions=('.x',),
            lex_keywords=('if',),
            simple_string_pattern=r'"(?:\\.|[^"\\\n])*"',
            line_comment_prefixes=('#',),
            multiline_delimiters=(r'/\*',),
            multiline_end_delimiters={r'/\*': r'\*/'},
            state_token_map={r'/\*': TOKEN_COMMENT},
        )

        self.assertIsNone(SyntaxHighlighter.get_plugin(None))
        plugin_by_name = SyntaxHighlighter.get_plugin('xlang')
        plugin_by_ext = SyntaxHighlighter.get_plugin('.x')
        self.assertIsNotNone(plugin_by_name)
        self.assertIs(plugin_by_name, plugin_by_ext)

    def test_register_uses_end_delimiters_as_start_when_missing(self):
        SyntaxHighlighter.register(
            name='endmap-only',
            extensions=('.em',),
            multiline_end_delimiters={r'/\*': r'\*/'},
        )

        plugin = SyntaxHighlighter.get_plugin('.em')
        self.assertIsNotNone(plugin)
        self.assertEqual(len(plugin.multiline_delimiters), 1)
        self.assertIsNotNone(plugin.multiline_delimiters[0].search('/*'))

    def test_get_available_plugins_sorted(self):
        SyntaxHighlighter.register('zz-test', ('.zz',))
        SyntaxHighlighter.register('aa-test', ('.aa',))

        plugins, ext_map = SyntaxHighlighter.get_available_plugins()
        keys = list(plugins.keys())
        self.assertEqual(keys, sorted(keys))
        self.assertIn('aa-test', ext_map)
        self.assertIn('zz-test', ext_map)

    def test_tokenize_line_active_state_no_end(self):
        start = re.compile(r'/\*')
        end = re.compile(r'\*/')
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=None,
            line_comment_prefixes=(),
            multiline_delimiters=(start,),
            multiline_end_map={start: end},
            delimiter_escape_char='\\',
            state_token_map={start: TOKEN_COMMENT},
            token_color_map={},
        )

        tokens, new_state = highlighter.tokenize_line('still open', (start, end))
        self.assertEqual(tokens, [(0, len('still open'), TOKEN_COMMENT)])
        self.assertEqual(new_state, (start, end))

    def test_tokenize_line_empty_with_active_state(self):
        start = re.compile(r'/\*')
        end = re.compile(r'\*/')
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=None,
            line_comment_prefixes=(),
            multiline_delimiters=(start,),
            multiline_end_map={start: end},
            delimiter_escape_char='\\',
            state_token_map={start: TOKEN_COMMENT},
            token_color_map={},
        )

        tokens, state = highlighter.tokenize_line('', (start, end))
        self.assertEqual(tokens, [])
        self.assertEqual(state, (start, end))

    def test_tokenize_line_active_state_with_end(self):
        start = re.compile(r'/\*')
        end = re.compile(r'\*/')
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=None,
            line_comment_prefixes=(),
            multiline_delimiters=(start,),
            multiline_end_map={start: end},
            delimiter_escape_char='\\',
            state_token_map={start: TOKEN_COMMENT},
            token_color_map={},
        )

        tokens, new_state = highlighter.tokenize_line('close */ text', (start, end))
        self.assertEqual(tokens[0], (0, 8, TOKEN_COMMENT))
        self.assertIsNone(new_state)

    def test_tokenize_line_comment_and_plain_tokens(self):
        plain, token_map = SyntaxHighlighter._build_plain_regex_and_tokens(
            lex_keywords=('if',),
            number_pattern=r'\d+'
        )
        highlighter = SyntaxHighlighter(
            plain_pattern=plain,
            plain_group_to_token=token_map,
            simple_string_pattern=None,
            line_comment_prefixes=('#',),
            multiline_delimiters=(),
            multiline_end_map={},
            delimiter_escape_char='\\',
            state_token_map={},
            token_color_map={},
        )

        tokens, new_state = highlighter.tokenize_line('if 12 # comment')
        self.assertIn((0, 2, TOKEN_KEYWORD), tokens)
        self.assertIn((3, 5, TOKEN_NUMBER), tokens)
        self.assertEqual(tokens[-1], (6, len('if 12 # comment'), TOKEN_COMMENT))
        self.assertIsNone(new_state)

    def test_tokenize_line_simple_string(self):
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=re.compile(r'"(?:\\.|[^"\\\n])*"'),
            line_comment_prefixes=(),
            multiline_delimiters=(),
            multiline_end_map={},
            delimiter_escape_char='\\',
            state_token_map={},
            token_color_map={},
        )

        tokens, _ = highlighter.tokenize_line('x = "ab"')
        self.assertIn((4, 8, TOKEN_STRING), tokens)

    def test_tokenize_line_multiline_delimiter_and_escape(self):
        start = re.compile(r'"""')
        end = re.compile(r'"""')
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=None,
            line_comment_prefixes=(),
            multiline_delimiters=(start,),
            multiline_end_map={start: end},
            delimiter_escape_char='\\',
            state_token_map={start: TOKEN_STRING},
            token_color_map={},
        )

        # Escaped delimiter should be ignored as a start delimiter.
        tokens, state = highlighter.tokenize_line('\\""" not-a-start')
        self.assertEqual(tokens, [])
        self.assertIsNone(state)

        # Real start without end should keep state active.
        tokens, state = highlighter.tokenize_line('"""open')
        self.assertEqual(tokens, [(0, len('"""open'), TOKEN_STRING)])
        self.assertIsNotNone(state)

    def test_tokenize_line_skips_invalid_or_empty_matches(self):
        class _FakeMatch:
            def __init__(self, group_name, span_tuple):
                self.lastgroup = group_name
                self._span = span_tuple

            def span(self):
                return self._span

        class _FakePattern:
            def finditer(self, _segment):
                # Cover all skip paths deterministically:
                # - unnamed group -> line 253 continue
                # - unknown mapped token -> line 256 continue
                # - zero-length mapped token -> line 259 continue
                return iter(
                    [
                        _FakeMatch(None, (0, 0)),
                        _FakeMatch('unknown', (0, 1)),
                        _FakeMatch('known', (1, 1)),
                    ]
                )

        highlighter = SyntaxHighlighter(
            plain_pattern=_FakePattern(),
            plain_group_to_token={'known': 'known'},
            simple_string_pattern=None,
            line_comment_prefixes=('#',),
            multiline_delimiters=(),
            multiline_end_map={},
            delimiter_escape_char='\\',
            state_token_map={},
            token_color_map={},
        )

        tokens, state = highlighter.tokenize_line('ab#')
        # unknown token and unnamed groups are dropped, zero-length known is dropped.
        self.assertEqual(tokens, [(2, 3, TOKEN_COMMENT)])
        self.assertIsNone(state)

    def test_tokenize_line_delimiter_callable_end_same_line(self):
        start = re.compile(r'/\*')
        highlighter = SyntaxHighlighter(
            plain_pattern=None,
            plain_group_to_token={},
            simple_string_pattern=None,
            line_comment_prefixes=(),
            multiline_delimiters=(start,),
            multiline_end_map={start: lambda _m: r'\*/'},
            delimiter_escape_char='\\',
            state_token_map={start: TOKEN_COMMENT},
            token_color_map={},
        )

        tokens, state = highlighter.tokenize_line('/*abc*/x')
        self.assertEqual(tokens[0], (0, 7, TOKEN_COMMENT))
        self.assertIsNone(state)

    def test_tokenize_line_fallback_index_increment(self):
        # Force the safety fallback path by mutating TYPE_SIMPLE_STRING between
        # next_type assignment and the next_type branch checks.
        class _MutatingPattern:
            def finditer(self, _segment):
                syntaxhighlight_module.TYPE_SIMPLE_STRING = 'mutated-simple'
                return iter(())

        highlighter = SyntaxHighlighter(
            plain_pattern=_MutatingPattern(),
            plain_group_to_token={},
            simple_string_pattern=re.compile(r'x'),
            line_comment_prefixes=(),
            multiline_delimiters=(),
            multiline_end_map={},
            delimiter_escape_char='\\',
            state_token_map={},
            token_color_map={},
        )

        with patch('cat_win.src.curses.helper.syntaxhighlight.TYPE_SIMPLE_STRING', 'simple_string'):
            tokens, state = highlighter.tokenize_line('abcx')
        self.assertEqual(tokens, [])
        self.assertIsNone(state)
