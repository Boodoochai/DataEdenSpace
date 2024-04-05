import Garbage
from Planet import Planet


class Ship:
    capacity_x: int
    capacity_y: int
    garbage: list[Garbage]
    position: Planet

    def __init__(self, capacity_x: int, capacity_y: int, position: Planet):
        self.capacity_x = capacity_x
        self.capacity_y = capacity_y
        self.garbage = list()
        self.position = position
