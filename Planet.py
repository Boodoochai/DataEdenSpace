class Planet:
    name: str
    is_cleaned: bool

    def __init__(self, name: str):
        self.name = name
        self.is_cleaned = False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Planet.__class__):
            return False
        return self.name == other.name

    def __lt__(self, other):
        return True
