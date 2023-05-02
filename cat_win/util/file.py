
class File:
    """
    defines a file.
    """
    def __init__(self, path: str, display_name: str) -> None:
        self.path = path
        self.displayname = display_name

        self.contains_queried = False

    def set_contains_queried(self, contains_queried) -> None:
        self.contains_queried = self.contains_queried or contains_queried
