"""
logger
"""

import logging


class LoggerStub:
    """
    logger stub with the same call shape as iohelper.StatusLogger.
    It captures rendered output lines instead of writing to stderr.
    """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self) -> None:
        self.lines = []
        self.log_to_file = False
        self.level = self.ERROR
        self.colors = {}

    def __call__(self, *args, priority: int = ERROR, **kwargs):
        sep = kwargs.pop('sep', ' ')
        end = kwargs.pop('end', '\n')
        kwargs.pop('file', None)
        kwargs.pop('flush', None)
        # if kwargs:
        #     raise TypeError(f"Unsupported keyword arguments: {', '.join(kwargs.keys())}")

        message = sep.join(str(arg) for arg in args)
        self.lines.append(f"{message}{end}")

    def output(self) -> str:
        """
        return all captured output exactly as it would have been rendered
        """
        return ''.join(self.lines)

    def set_log_to_file(self, value: bool) -> None:
        self.log_to_file = value

    def set_level(self, value: int) -> None:
        self.level = value

    def clear_colors(self) -> None:
        self.colors = {}

    def set_colors(self, colors: dict) -> None:
        self.colors = dict(colors)

    def clear(self) -> None:
        """
        clear all captured output
        """
        self.lines.clear()
