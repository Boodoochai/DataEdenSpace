class Planet:
    name: str
    is_cleaned: bool

    def __init__(self, name: str):
        self.name = name
        self.is_cleaned = False
