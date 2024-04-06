import copy
import heapq
import math
import random
from collections import deque

import requests

from Config import Config
from Garbage import Garbage
from Planet import Planet
from Point import Point
from Ship import Ship
from Universe import Universe
from UniverseEdge import UniverseEdge


class Interactor:
    universe: Universe | None
    ship: Ship | None
    eden: Planet | None
    planet_by_name: dict[str, Planet]

    def __init__(self):
        self.universe = None
        self.ship = None
        self.eden = None
        self.planet_by_name = dict()

    def start(self):
        """
        Here will be main algorithm

        For now:
        0) somehow go to eden from earth and do something while going
        1) find most distant planet
        2) go there
        3) collect all
        4) if collected all flag it as emptied
        5) go eden
        6) while going eden collect garbage from all planets on path if our inventory filled less then some percent
        7) repeat
        """

        while True:
            try:
                self.fully_update_universe()
            except ConnectionError:
                continue
            break

        print('Read universe. Some info:')
        print('Universe planets number:', len(self.universe.graph))
        print('Current position:', self.ship.position.name)
        print('Current garbage num:', len(self.ship.garbage))

        if self.ship.position.name != Config.EDEN_PLANET_NAME:
            print('Trying to travel to Eden from:', self.ship.position.name)
            while True:
                try:
                    self.go_to_eden()
                except ConnectionError:
                    continue
                break
            print('Traveled from planet to Eden. Current position:', self.ship.position.name)
        else:
            print('Already on Eden.')

        # self.filter_universe()
        print('Filtered unreachable planets. Some info:')
        print('Universe planets number:', len(self.universe.graph))

        while self.count_planets_to_clean() > 0:
            print('Some info:')
            print('Current position:', self.ship.position.name)
            print('Current garbage num:', len(self.ship.garbage))
            print('Planets left to clean:', self.count_planets_to_clean())
            while True:
                try:
                    self.clean_most_distant_planet()
                except ConnectionError:
                    continue
                break

    def filter_universe(self):
        comp = self.get_comp()
        comp = set(comp)
        for planet in self.universe.graph.keys():
            for edge in self.universe.graph[planet]:
                if edge.start not in comp or edge.end not in comp:
                    self.universe.remove_edge(edge)

        for planet in self.universe.graph.keys():
            if planet not in comp:
                self.universe.graph.pop(planet)

    def count_planets_to_clean(self) -> int:
        number = 0
        for planet in self.universe.graph.keys():
            if not planet.is_cleaned:
                number += 1
        return number

    def clean_most_distant_planet(self) -> None:
        used: set[Planet] = set()

        path = self.make_path_to_nearest_planet(self.ship.position, set())
        path = self.make_path_between_planets(self.ship.position, path)
        most_distant_not_cleaned_planet = path[-1]
        garbage_on_planet = self.go_by_path(path)

        used.add(most_distant_not_cleaned_planet)

        planet_from_go = most_distant_not_cleaned_planet

        while len(garbage_on_planet) == 0:
            planet_to_go = self.make_path_to_nearest_planet(planet_from_go, used)
            path = self.make_path_between_planets(planet_from_go, planet_to_go)
            garbage_on_planet = self.go_by_path(path)
            used.add(planet_to_go)
            planet_from_go = planet_to_go

        is_collected, is_cleaned = self.collect_garbage_from_plannet(garbage_on_planet)
        if is_collected and is_cleaned:
            most_distant_not_cleaned_planet.is_cleaned = True

        path_to_eden = self.make_path_between_planets(most_distant_not_cleaned_planet, self.eden)
        self.go_by_path(path_to_eden)
        self.ship.garbage = list()

    def make_path_to_nearest_planet(self, start_planet: Planet, visited_planets: set[Planet]) -> Planet:
        dists: dict[Planet, int] = dict()
        dists[start_planet] = 0
        que = []
        heapq.heappush(que, [dists[start_planet], start_planet])
        parent = dict()
        parent[start_planet] = -1
        best_planet = ''
        dust_of_best_planet = 10 ** 9
        while len(que) > 0:
            q = heapq.heappop(que)
            planet_dist = q[0]
            cur_planet = q[1]
            if planet_dist != dists[cur_planet]:
                continue
            for edge in self.universe.graph[cur_planet]:
                if edge.end not in dists or dists[edge.end] > dists[cur_planet] + edge.transfer_cost:
                    dists[edge.end] = dists[cur_planet] + edge.transfer_cost
                    heapq.heappush(que, [dists[edge.end], edge.end])
                    parent[edge.end] = cur_planet
                    if edge.end not in visited_planets and not edge.end.is_cleaned and dists[
                        edge.end] < dust_of_best_planet:
                        dust_of_best_planet = dists[edge.end]
                        best_planet = edge.end
        return best_planet

    def position_garbage(self, garbage_on_planet: list[Garbage]) -> tuple[list[Garbage], bool, bool]:
        """
        also must rewrite garbage in ship inventory

        (second thing to return)
        if it can not position return false
        else return true

        (third thing to return)
        if planet now cleaned
        """
        print('Positioning garbage:')
        inventory_volume = self.ship.capacity_y * self.ship.capacity_x
        garb_in_inv_before = 0
        for garbage in self.ship.garbage:
            garb_in_inv_before += len(garbage.shape)

        copy_inv = copy.deepcopy(self.ship.garbage)

        all_garbage: list[Garbage] = garbage_on_planet.copy() + self.ship.garbage.copy()
        self.ship.garbage = list()

        for garb in all_garbage:
            print(garb.name, end=' ')
        print()

        max_placed_gab_num = 0
        ans = None
        for _ in range(100):
            random.shuffle(all_garbage)
            placed_garb_num = 0
            for garbage in all_garbage:
                flag = False
                for x in range(0, self.ship.capacity_x - 4 + 1):
                    for y in range(0, self.ship.capacity_y - 4 + 1):
                        if self.is_fit_garbage(x, y, garbage):
                            self.place_garbage(garbage, x, y)
                            placed_garb_num += 1
                            flag = True
                            break
                    if flag:
                        break
            if placed_garb_num > max_placed_gab_num:
                max_placed_gab_num = placed_garb_num
                ans = copy.deepcopy(self.ship.garbage)
                self.ship.garbage = list()

        self.ship.garbage = ans
        placed_garb_num = max_placed_gab_num

        garb_in_inv_after = 0
        for garbage in self.ship.garbage:
            garb_in_inv_after += len(garbage.shape)

        if garb_in_inv_before == 0:
            need_to_put_garb = math.ceil(0.3 * inventory_volume)
        else:
            need_to_put_garb = math.ceil(0.05 * inventory_volume)

        if placed_garb_num == len(all_garbage) and len(garbage_on_planet) != 0:
            is_cleaned = True
        else:
            is_cleaned = False

        print('Garbage before:', garb_in_inv_before)
        print('Garbage after:', garb_in_inv_after)
        print('Number of collected garbage', placed_garb_num)
        print('Inventory:', self.ship.garbage)

        if (not is_cleaned) and (garb_in_inv_after - garb_in_inv_before < need_to_put_garb):
            self.ship.garbage = copy_inv
            return self.ship.garbage, False, False

        return self.ship.garbage, True, is_cleaned

    def place_garbage(self, garbage: Garbage, pos_x: int, pos_y: int) -> None:
        garbage = Interactor.normalized_garbage(garbage)
        for point in garbage.shape:
            point.x += pos_x
            point.y += pos_y
        self.ship.garbage.append(garbage)

    @staticmethod
    def normalized_garbage(garbage: Garbage) -> Garbage:
        normalized_garbage = copy.deepcopy(garbage)
        min_point = Point(9999999999999, 99999999999)
        for point in normalized_garbage.shape:
            min_point.x = min(min_point.x, point.x)
            min_point.y = min(min_point.y, point.y)

        for point in normalized_garbage.shape:
            point.x -= min_point.x
            point.y -= min_point.y

        return normalized_garbage

    def is_four_by_four_contains_garbage(self, x_cord: int, y_cord):
        for garbage in self.ship.garbage:
            for point in garbage.shape:
                if (x_cord <= point.x < x_cord + 4) and (y_cord <= point.y < y_cord + 4):
                    return True
        return False

    def is_fit_garbage(self, x_cord: int, y_cord: int, garbage_to_fit: Garbage):
        for garbage in self.ship.garbage:
            for point in garbage.shape:
                for point_gar in garbage_to_fit.shape:
                    if point.x == point_gar.x + x_cord and point.y == point_gar.y + y_cord:
                        return False
        return True

    def collect_garbage_from_plannet(self, garbage_on_planet: list[Garbage]) -> tuple[bool, bool]:
        # TODO : may be needs to return something more
        print('Trying to collect garbage:', garbage_on_planet)
        print('Our Inventory:', self.ship.garbage)
        garbage_layout, is_positioned, is_cleaned = self.position_garbage(garbage_on_planet)
        payload = {"garbage": Interactor.make_garbage_layout_for_request(garbage_layout)}
        print('Collecting garbage, json payload:', payload)
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response: requests.Response = requests.post(Config.POST_COLLECT_URL, json=payload, headers=headers)
        response_json = response.json()

        return is_positioned, is_cleaned

    def get_obr_graph(self):
        obr_graph = Universe()
        for planet in self.universe.graph.keys():
            for edge in self.universe.graph[planet]:
                new_edge = UniverseEdge(edge.end, edge.start, edge.transfer_cost)
                obr_graph.add_edge(new_edge)
        return obr_graph

    @staticmethod
    def make_garbage_for_request(garbage: Garbage) -> list[list[int]]:
        garbage_for_request = list()
        for point in garbage.shape:
            garbage_for_request.append([point.x, point.y])
        return garbage_for_request

    @staticmethod
    def make_garbage_layout_for_request(garbage_layout: list[Garbage]) -> dict[str, list[list[int]]]:
        garbage_layout_for_request: dict[str, list[list[int]]] = dict()
        print('Forming json payload from:', end=' ')
        for garbage in garbage_layout:
            print(garbage.name, end=' ')
        print()
        for garbage in garbage_layout:
            garbage_layout_for_request[garbage.name] = Interactor.make_garbage_for_request(garbage)
        return garbage_layout_for_request

    def make_path_to_most_distant_not_cleaned_planet(self) -> list[Planet]:
        most_distant_planet = self.find_most_distant_not_cleaned_planet(self.ship.position)

        path = self.make_path_between_planets(self.ship.position, most_distant_planet)

        return path

    def find_most_distant_not_cleaned_planet(self, start_planet: Planet) -> Planet:
        dists: dict[Planet, int] = dict()
        dists[start_planet] = 0
        que = deque()
        que.append(start_planet)
        while len(que) > 0:
            cur_planet = que.popleft()
            for edge in self.universe.graph[cur_planet]:
                if edge.end not in dists:
                    dists[edge.end] = dists[cur_planet] + 1
                    que.append(edge.end)

        max_dist = 0
        most_distant_planet = None
        for planet in dists.keys():
            if dists[planet] > max_dist and not planet.is_cleaned:
                max_dist = dists[planet]
                most_distant_planet = planet

        return most_distant_planet

    def make_path_between_planets(self, start_planet: Planet, end_planet: Planet) -> list[Planet]:
        dists: dict[Planet, int] = dict()
        dists[start_planet] = 0
        que = []
        heapq.heappush(que, [dists[start_planet], start_planet])
        parent = dict()
        parent[start_planet] = -1
        while len(que) > 0:
            q = heapq.heappop(que)
            planet_dist = q[0]
            cur_planet = q[1]
            if planet_dist != dists[cur_planet]:
                continue
            for edge in self.universe.graph[cur_planet]:
                if (edge.end not in dists or dists[edge.end] > dists[cur_planet] + edge.transfer_cost):
                    dists[edge.end] = dists[cur_planet] + edge.transfer_cost
                    heapq.heappush(que, [dists[edge.end], edge.end])
                    parent[edge.end] = cur_planet
        planet_list = [end_planet]
        if end_planet in dists:
            planet_now = end_planet
            while parent[planet_now] != -1:
                planet_list.append(parent[planet_now])
                planet_now = parent[planet_now]
            for pl in planet_list:
                print(pl.name, end=' ')
            print()
            planet_list.pop()
            planet_list.reverse()
            return planet_list
        else:
            return []

    def go_to_eden(self) -> None:
        # TODO : probably update to optimize main algorithm
        print('Building path to eden from', self.ship.position.name)
        path_to_eden = self.make_path_between_planets(self.planet_by_name[self.ship.position.name],
                                                      self.planet_by_name[Config.EDEN_PLANET_NAME])
        self.go_by_path(path_to_eden)

    def dfs1(self, planet: Planet, used: set[Planet], order):
        used.add(planet)
        for edge in self.universe.graph[planet]:
            if edge.end not in used:
                self.dfs1(edge.end, used, order)
        order.append(planet)

    def dfs2(self, planet: Planet, used: set[Planet], component, gr):
        used.add(planet)
        component.append(planet)
        for edge in gr[planet]:
            if edge.end not in used:
                self.dfs2(edge.end, used, component, gr)

    def get_comp(self) -> list[Planet]:
        used: set[Planet] = set()
        order: list[Planet] = []
        component: list[Planet] = []
        tr_graf = self.get_obr_graph().graph
        self.dfs1(self.planet_by_name["Eden"], used, order)
        used: set[Planet] = set()
        n = len(order)
        for i in range(n):
            v = order[n - 1 - i]
            if v not in used or not used[v]:
                self.dfs2(self.planet_by_name[v.name], used, component, tr_graf)
                if self.planet_by_name["Eden"] in component:
                    return component

    @staticmethod
    def make_planets_name_list_from_path(path: list[Planet]):
        name_list: list[str] = list()
        for planet in path:
            name_list.append(planet.name)
        return name_list

    def go_by_path(self, path: list[Planet]) -> list[Garbage]:
        for edge in self.universe.graph[self.ship.position]:
            if edge.start == self.ship.position and edge.end == path[0]:
                edge.transfer_cost += 10
        for i in range(len(path) - 1):
            for edge in self.universe.graph[path[i]]:
                if edge.start == path[i] and edge.end == path[i + 1]:
                    edge.transfer_cost += 10
        print('Going by path: ', end='')
        for planet in path:
            print(planet.name, end=' ')
        print()
        planets_names_list = Interactor.make_planets_name_list_from_path(path)
        payload = {"planets": planets_names_list}
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response = requests.post(Config.POST_TRAVEL_URL, json=payload, headers=headers)
        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError:
            return list()

        if response.status_code != 200:
            print('FAILED post:', Config.POST_TRAVEL_URL)
            print(response.status_code)
            print(response.json())
            raise ConnectionError

        garbage = Interactor.parce_garbage(response_json["planetGarbage"])

        self.ship.position = path[-1]

        return garbage

    @staticmethod
    def add_auth_token_to_headers(headers: dict) -> None:
        headers[Config.AUTH_TOKEN_HEADER_NAME] = Config.AUTH_TOKEN

    @staticmethod
    def parce_garbage(raw_garbage_dict: dict[str, list[list[int]]]) -> list[Garbage]:
        garbage_list: list[Garbage] = list()
        print(raw_garbage_dict)
        for name in raw_garbage_dict.keys():
            garbage_shape: list[Point] = list()
            for raw_point in raw_garbage_dict[name]:
                point = Point(raw_point[0], raw_point[1])
                garbage_shape.append(point)
            garbage: Garbage = Garbage(name, garbage_shape)
            garbage_list.append(garbage)
        return garbage_list

    def fully_update_universe(self) -> None:
        # Make request
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response = requests.get(Config.GET_UNIVERSE_URL, headers=headers)
        response_json: dict[any] = response.json()

        if response.status_code != 200:
            print('FAILED: get:', Config.GET_UNIVERSE_URL)
            print(response.status_code)
            print(response.json())
            raise ConnectionError

        # Make and set universe
        universe = Universe()
        for raw_edge in response_json["universe"]:
            if raw_edge[0] not in self.planet_by_name:
                self.planet_by_name[raw_edge[0]] = Planet(raw_edge[0])
            if raw_edge[1] not in self.planet_by_name:
                self.planet_by_name[raw_edge[1]] = Planet(raw_edge[1])
            new_edge = UniverseEdge(self.planet_by_name[raw_edge[0]], self.planet_by_name[raw_edge[1]], raw_edge[2])
            universe.add_edge(new_edge)
        for planet in universe.graph.keys():
            if planet.name == Config.EDEN_PLANET_NAME:
                planet.is_cleaned = True
            elif planet.name == Config.EARTH_PlANET_NAME:
                planet.is_cleaned = True
        self.universe = universe
        self.eden = self.planet_by_name[Config.EDEN_PLANET_NAME]

        '''print(self.universe.graph)
        for planet in self.universe.graph.keys():
            if planet.name == Config.EARTH_PlANET_NAME:
                print(planet.name)
                print(self.universe.graph[planet][0].start.name)
                print(self.universe.graph[planet][0].end.name)
                print(self.universe.graph[planet][0].transfer_cost)'''

        # Make and set ship
        # TODO : may be useful?
        '''
        ship_position_planet_garbage: list[Garbage] = Interactor.parce_garbage(response_json["ship"]["planet"]["garbage"])
        '''
        ship_position_planet_name: str = response_json["ship"]["planet"]["name"]
        ship_position_planet: Planet = self.planet_by_name[ship_position_planet_name]
        ship_capacity_x: int = response_json["ship"]["capacityX"]
        ship_capacity_y: int = response_json["ship"]["capacityY"]
        self.ship = Ship(ship_capacity_x, ship_capacity_y, ship_position_planet)
