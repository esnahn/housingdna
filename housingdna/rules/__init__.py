if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys, pathlib

    dir_level = 2

    assert dir_level >= 1
    file_path = pathlib.PurePath(__file__)
    sys.path.append(str(file_path.parents[dir_level]))

    package_path = ""
    for level in range(dir_level - 1, 0 - 1, -1):
        package_path += file_path.parents[level].name
        if level > 0:
            package_path += "."
    __package__ = package_path

from itertools import chain
from typing import List, Tuple

from ..model import House
from .type import N, E, A
from .nodes import node_names
from .edges import all_possible_edges
from .name import dnas_room_name
from .attribute import dnas_attribute
from .room_network import dnas_room_network
from .glazing_network import dnas_glazing_network


def analyze_housing_dna(
    model: House,
) -> Tuple[List[Tuple[N, A]], List[Tuple[E, A]]]:
    node_ids: List[N] = list(
        chain(
            dnas_obvious(model),
            dnas_room_name(model),
            dnas_attribute(model),
            dnas_room_network(model),
            dnas_glazing_network(model),
        )
    )
    nodes: List[Tuple[N, A]] = [(n, {"name": node_names[n]}) for n in node_ids]
    edges: List[Tuple[E, A]] = [
        ((a, b), {}) for a, b in all_possible_edges if a in node_ids and b in node_ids
    ]
    return nodes, edges


def dnas_obvious(model: House) -> List[N]:
    dna: List[N] = []
    for key, eval in [("dna1", dna1_is_house(model))]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def dna1_is_house(model: House) -> List[int]:
    # Every house is a house
    # return a list of ids of every rooms
    return [room.element_id for room in model.rooms]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
