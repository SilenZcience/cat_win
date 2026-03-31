"""
argument-related test mocks
"""

from cat_win.src.const.argconstants import (
    ARGS_BINVIEW,
    ARGS_B64D,
    ARGS_CLIP,
    ARGS_CCONFIG,
    ARGS_CCONFIG_FLUSH,
    ARGS_CONFIG,
    ARGS_CONFIG_FLUSH,
    ARGS_CONFIG_REMOVE,
    ARGS_DEBUG,
    ARGS_DIFF,
    ARGS_HELP,
    ARGS_HEXVIEW,
    ARGS_ONELINE,
    ARGS_PLAIN_ONLY,
    ARGS_RAW,
    ARGS_REVERSE,
    ARGS_VERSION,
    ARGS_WATCH,
)


class DummyArgs(dict):
    def __init__(self, overrides=None):
        super().__init__(
            {
                ARGS_RAW: False,
                ARGS_PLAIN_ONLY: False,
                ARGS_REVERSE: False,
                ARGS_HEXVIEW: False,
                ARGS_BINVIEW: False,
                ARGS_WATCH: False,
                ARGS_DIFF: False,
            }
        )
        if overrides:
            self.update(overrides)

    def find_first(self, *keys):
        for key in keys:
            if self.get(key):
                return (key, self.get(key))
        return None


class DummyStartupArgs(dict):
    def __init__(self, overrides=None, ordered_args=None):
        super().__init__(
            {
                ARGS_HELP: False,
                ARGS_VERSION: False,
                ARGS_DEBUG: False,
                ARGS_CONFIG_REMOVE: False,
                ARGS_CONFIG_FLUSH: False,
                ARGS_CCONFIG_FLUSH: False,
                ARGS_CONFIG: False,
                ARGS_CCONFIG: False,
            }
        )
        if overrides:
            self.update(overrides)

        if ordered_args is None:
            self.args = [(k, self[k]) for k in dict.keys(self) if self[k]]
        else:
            self.args = list(ordered_args)

    def __iter__(self):
        return iter(self.args)

    def __len__(self):
        return len(self.args)

    def set_args(self, args):
        self.args = list(args)

    def find_first(self, *keys):
        for key in keys:
            if self.get(key):
                return (key, self.get(key))
        return None


class DummyReplArgs(dict):
    def __init__(self, active_args=None, overrides=None):
        super().__init__(
            {
                ARGS_ONELINE: False,
                ARGS_B64D: False,
                ARGS_CLIP: False,
            }
        )
        if overrides:
            self.update(overrides)

        self.args = list(active_args) if active_args is not None else []

    def __iter__(self):
        return iter(self.args)

    def __len__(self):
        return len(self.args)

    def add_args(self, args_to_add):
        self.args.extend(args_to_add)

    def delete_args(self, args_to_delete):
        for arg in args_to_delete:
            if arg in self.args:
                self.args.remove(arg)
