
class File:
    """
    defines a file.
    """
    def __init__(self, path: str, display_name: str) -> None:
        self.path = path
        self.displayname = display_name
        self.file_size = -1
        self.contains_queried = False
        self.plaintext = True

    def set_contains_queried(self, contains_queried: bool) -> None:
        self.contains_queried = self.contains_queried or contains_queried

    def set_plaintext(self, plain: bool = False) -> None:
        self.plaintext = plain

    def set_file_size(self, file_size: int) -> None:
        self.file_size = file_size
