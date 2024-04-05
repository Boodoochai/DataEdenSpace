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

    def __init__(self):
        self.universe = None
        self.ship = None

    def start(self):
        # TODO : complete function
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
        self.fully_update_universe()

        self.go_from_earth_to_eden()

        while self.is_have_planets_to_clean():
            self.clean_most_distant_planet()

    def is_have_planets_to_clean(self) -> bool:
        for planet in self.universe.graph.keys():
            if not planet.is_cleaned:
                return True
        return False

    def clean_most_distant_planet(self) -> None:
        # TODO : write function
        path = self.make_path_to_most_distant_not_cleaned_planet()
        most_distant_not_cleaned_planet = path[-1]
        garbage_on_planet = Interactor.go_by_path(path)

        is_collected, is_cleaned = self.collect_garbage_from_plannet(garbage_on_planet)
        if is_collected and is_cleaned:
            most_distant_not_cleaned_planet.is_cleaned = True

        if not is_cleaned:
            # TODO
            pass

    def position_garbage(self, garbage_on_planet: list[Garbage]) -> tuple[list[Garbage], bool, bool]:
        """
        also must rewrite garbage in ship inventory

        (second thing to return)
        if it can not position return false
        else return true

        (third thing to return)
        if planet now cleaned
        """
        # TODO : write function
        pass

    @staticmethod
    def make_garbage_for_request(garbage: Garbage) -> list[list[int]]:
        garbage_for_request = list()
        for point in garbage.shape:
            garbage_for_request.append([point.x, point.y])
        return garbage_for_request

    @staticmethod
    def make_garbage_layout_for_request(garbage_layout: list[Garbage]) -> dict[str, list[list[int]]]:
        garbage_layout_for_request: dict[str, list[list[int]]] = dict()
        for garbage in garbage_layout:
            garbage_layout_for_request[garbage.name] = Interactor.make_garbage_for_request(garbage)
        return garbage_layout_for_request

    def collect_garbage_from_plannet(self, garbage_on_planet: list[Garbage]) -> tuple[bool, bool]:
        # TODO : write function
        garbage_layout, is_positioned, is_cleaned = self.position_garbage(garbage_on_planet)
        payload = Interactor.make_garbage_layout_for_request(garbage_layout)
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response: requests.Response = requests.post(Config.POST_COLLECT_URL, json=payload, headers=headers)
        response_json = response.json()

        return is_positioned, is_cleaned

    def make_path_to_most_distant_not_cleaned_planet(self) -> list[Planet]:
        # TODO : write function
        pass

    def make_path_between_planets(self, start_planet: Planet, end_planet: Planet) -> list[Planet]:
        # TODO : write function
        pass

    def go_from_earth_to_eden(self) -> None:
        # TODO : probably update to optimize main algorithm
        path_to_eden = self.make_path_between_planets(self.ship.position, Config.EDEN_PLANET_NAME)

        Interactor.go_by_path(path_to_eden)

    @staticmethod
    def make_planets_name_list_from_path(path: list[Planet]):
        name_list: list[str] = list()
        for planet in path:
            name_list.append(planet.name)
        return name_list

    @staticmethod
    def go_by_path(path: list[Planet]) -> list[Garbage]:
        planets_names_list = Interactor.make_planets_name_list_from_path(path)
        payload = {"planets": planets_names_list}
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response = requests.post(Config.POST_TRAVEL_URL, json=payload, headers=headers)
        response_json = response.json()

        garbage = Interactor.parce_garbage(response_json["planetGarbage"])

        return garbage

    @staticmethod
    def add_auth_token_to_headers(headers: dict) -> None:
        headers[Config.AUTH_TOKEN_HEADER_NAME] = Config.AUTH_TOKEN

    @staticmethod
    def parce_garbage(raw_garbage_dict: dict[str, list[list[int]]]) -> list[Garbage]:
        garbage_list: list[Garbage] = list()
        for name, raw_garbage in raw_garbage_dict:
            garbage_shape: list[Point] = list()
            for raw_point in raw_garbage:
                point = Point(raw_point[0], raw_point[1])
                garbage_shape.append(point)
            garbage: Garbage = Garbage(name, garbage_shape)
            garbage_list.append(garbage)
        return garbage_list

    def fully_update_universe(self) -> None:
        # Make request
        headers = {}
        Interactor.add_auth_token_to_headers(headers)
        response = requests.get(Config.GET_UNIVERSE_URL, headers)
        response_json: dict[any] = response.json()

        # Make and set universe
        universe = Universe()
        for raw_edge in response_json["universe"]:
            new_edge = UniverseEdge(raw_edge[0], raw_edge[1], raw_edge[2])
            universe.add_edge(new_edge)
        for planet in universe.graph.keys():
            if planet.name == Config.EDEN_PLANET_NAME:
                planet.is_cleaned = True
            elif planet.name == Config.EARTH_PlANET_NAME:
                planet.is_cleaned = True
        self.universe = universe

        # Make and set ship
        # TODO : may be useful?
        '''
        ship_position_planet_garbage: list[Garbage] = Interactor.parce_garbage(response_json["ship"]["planet"]["garbage"])
        '''
        ship_position_planet_name: str = response_json["ship"]["planet"]["name"]
        ship_position_planet: Planet = Planet(ship_position_planet_name)
        ship_capacity_x: int = response_json["ship"]["capacityX"]
        ship_capacity_y: int = response_json["ship"]["capacityY"]
        self.ship = Ship(ship_capacity_x, ship_capacity_y, ship_position_planet)
