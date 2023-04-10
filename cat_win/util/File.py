
class File:
    def __init__(self, path: str, displayName: str) -> None:
        self.path = path
        self.displayname = displayName
        
        self.containsQueried = False
        
    def setContainsQueried(self, containsQueried) -> None:
        self.containsQueried = self.containsQueried or containsQueried