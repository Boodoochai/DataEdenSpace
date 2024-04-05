from Planet import Planet


class UniverseEdge:
    start: Planet
    end: Planet
    transfer_cost: int

    def __init__(self, start_planet: Planet, end_planet: Planet, transfer_cost: int):
        self.start = start_planet
        self.end = end_planet
        self.transfer_cost = transfer_cost

