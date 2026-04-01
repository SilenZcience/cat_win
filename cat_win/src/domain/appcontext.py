"""
catcontext

AppContext bundles every piece of mutable per-run state that was previously
scattered as module-level globals in cat.py.  A single module-level instance
(_ctx) is created when cat.py is imported; setup() re-initialises it before
each run so there are no global-statement mutations anywhere.
"""

from cat_win.src.argparser import ArgParser
from cat_win.src.const.defaultconstants import DKW
from cat_win.src.domain.arguments import Arguments
from cat_win.src.domain.files import Files
from cat_win.src.persistence.cconfig import CConfig
from cat_win.src.persistence.config import Config


class AppContext:
    """Holds all mutable objects that belong to one catw / cats invocation."""

    __slots__ = (
        'cconfig', 'config',
        'default_color_dic', 'color_dic', 'const_dic',
        'arg_parser', 'u_args', 'u_files',
        'args', 'unknown_args',
        'known_files', 'unknown_files', 'valid_urls',
        'known_dirs', 'echo_args',
        'content',
    )

    def __init__(self) -> None:
        self.cconfig = CConfig()
        self.config = Config()
        # These are populated by setup(); kept as empty sentinels until then.
        self.default_color_dic: dict = {}
        self.color_dic: dict = {}
        self.const_dic: dict = {}

        self.u_args: Arguments = Arguments()
        self.u_files: Files = Files()

        self.arg_parser: ArgParser = None

        self.args: list = []
        self.unknown_args: list = []
        self.known_files: list = []
        self.unknown_files: list = []
        self.valid_urls: list = []
        self.known_dirs: list = []
        self.echo_args: str = ''
        # This will be populated during edit_content()/edit_raw_content()
        self.content = None

    def init(self) -> None:
        """Reload configs and create fresh per-run objects and runtime lists."""
        self.default_color_dic = self.cconfig.load_config()
        self.color_dic = self.default_color_dic.copy()
        self.const_dic = self.config.load_config()

        self.arg_parser = ArgParser(
            self.const_dic[DKW.DEFAULT_FILE_ENCODING],
            self.const_dic[DKW.UNICODE_ESCAPED_ECHO],
            self.const_dic[DKW.UNICODE_ESCAPED_FIND],
            self.const_dic[DKW.UNICODE_ESCAPED_REPLACE],
            self.config.custom_commands,
        )
