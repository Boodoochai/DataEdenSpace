"""
graph that represents universe
"""

from Planet import Planet
from UniverseEdge import UniverseEdge


class Universe:
    graph: dict[Planet, list[UniverseEdge]]

    def __init__(self):
        self.graph = dict()

    def add_edge(self, edge: UniverseEdge) -> None:
        if edge.start not in self.graph:
            self.graph[edge.start] = list()
        if edge.end not in self.graph:
            self.graph[edge.end] = list()
        self.graph[edge.start].append(edge)

    def remove_edge(self, edge: UniverseEdge) -> None:
        self.graph[edge.start].remove(edge)

    def add_planet(self, planet: Planet) -> None:
        self.graph[planet] = list()
