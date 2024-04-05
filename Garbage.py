from Point import Point


class Garbage:
    name: str
    shape: list[Point]

    def __init__(self, name: str, shape: list[Point]):
        self.name = name
        self.shape = shape
