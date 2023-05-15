if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys
    import pathlib

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
from .edges import white_edges
from .name import dnas_room_name
from .attribute import dnas_attribute
from .room_network import dnas_room_network
from .glazing_network import dnas_glazing_network, analyze_sun_order
from .test_gray_edges import gray_edges_list

from test_model import sample_model


print(dnas_attribute(sample_model))
# print(dnas_room_name(sample_model))
# print(dnas_room_network(sample_model))
# print(dnas_glazing_network(sample_model))
# print(gray_edges_list(sample_model))
