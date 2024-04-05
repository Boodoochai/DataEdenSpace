"""
graph that represents universe
"""
from collections import defaultdict

from Planet import Planet
from UniverseEdge import UniverseEdge


class Universe:
    graph: defaultdict[Planet, set[UniverseEdge]]

    def __init__(self):
        self.graph = defaultdict(set)

    def add_edge(self, edge: UniverseEdge) -> None:
        self.graph[edge.start].add(edge)

    def add_planet(self, planet: Planet) -> None:
        self.graph[planet] = set()
