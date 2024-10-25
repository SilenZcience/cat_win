"""
file
"""

from pathlib import Path


class File:
    """
    defines a file.
    """
    def __init__(self, path: Path, display_name: str) -> None:
        self.path = path
        self.displayname = display_name
        self.file_size = -1
        self.contains_queried = False
        self.plaintext = True

    def set_contains_queried(self, contains_queried: bool) -> None:
        """
        or-set the indicator if the file contains a queried token
        """
        self.contains_queried |= contains_queried

    def set_plaintext(self, plain: bool = False) -> None:
        """
        set if the file is a plain text file
        """
        self.plaintext = plain

    def set_file_size(self, file_size: int) -> None:
        """
        set the file size
        """
        self.file_size = file_size

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, value: object) -> bool:
        return self.path == value.path
