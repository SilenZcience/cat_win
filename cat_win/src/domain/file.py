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

        Parameters:
        contains_queried (bool):
            or-set the contains_queried attribute
        """
        self.contains_queried |= contains_queried

    def set_plaintext(self, plain: bool = False) -> None:
        """
        set if the file is a plain text file

        Parameters:
        plaintext (bool):
            set the plaintext attribute
        """
        self.plaintext = plain

    def set_file_size(self, file_size: int) -> None:
        """
        set the file size

        Parameters:
        file_size (bool):
            set the file_size attribute
        """
        self.file_size = file_size

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, value: object) -> bool:
        return self.path == value.path
