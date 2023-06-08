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


import networkx as nx
import housingdna.file as hdna
from itertools import chain
from typing import List, Tuple, Dict, Mapping, Sequence, Set
from ..model import (
    House,
    RevitObject,
    Glazing,
    Direction,
    Room,
    RoomGlazingRelation,
    multiple_sides,
)
from .type import N, E, A
from .nodes import node_names
from .edges import white_edges, gray_edges
from .name import (
    dna34_ent_transition,
    dna33_main_entrance,
    is_main,
    dnas_room_name,
    is_bedroom,
    is_kitchen,
    is_semi_outdoor,
    is_entrance,
    is_dining,
    is_bathroom,
    is_storage,
    is_dressroom,
    is_corridor,
    is_public,
    is_ancillary,
    is_living,
    is_semi_outdoor,
)
from .attribute import (
    is_mbr,
    dnas_attribute,
    room_outmost_win_count,
    dna68_window_interior,
    dna67_Windows_overlooking_Life,
    analyze_sun_order,
)
from .room_network import (
    dnas_room_network,
    dna36_pub_priv_gradient,
    dna38_direct_connection,
    dna41_central_public,
    dna44_couples_realm,
    dna45_childrens_realm,
)
from .glazing_network import (
    dnas_glazing_network,
    dna37_indoor_for_sunlight,
    dna52_bedroom_for_sunlight,
)
from .test_complex import dnas_complex
from housingdna.rules import edges
from test_model import sample_model

# TODO: 추후 sample_model --> House로 변경
model = sample_model

# 공간 분류 리스트 정리
rooms = [room.element_id for room in model.rooms]
pub_list = [room.element_id for room in model.rooms if is_public(room)]
mbr_list = [room.element_id for room in model.rooms if is_mbr(room)]
ancill_list = [room.element_id for room in model.rooms if is_ancillary(room)]
semi_out_list = [room.element_id for room in model.rooms if is_semi_outdoor(room)]
ent_list = [room.element_id for room in model.rooms if is_entrance(room)]
living_list = [room.element_id for room in model.rooms if is_living(room)]
dining_list = [room.element_id for room in model.rooms if is_dining(room)]
kit_list = [room.element_id for room in model.rooms if is_kitchen(room)]
bath_list = [room.element_id for room in model.rooms if is_bathroom(room)]
sto_list = [room.element_id for room in model.rooms if is_storage(room)]
dress_list = [room.element_id for room in model.rooms if is_dressroom(room)]
corr_list = [room.element_id for room in model.rooms if is_corridor(room)]
bed_list = [room.element_id for room in model.rooms if is_bedroom(room)]
living_list = [room.element_id for room in model.rooms if is_living(room)]
main_list = [room.element_id for room in model.rooms if is_main(room)]
indoor_ancill_list = [
    room.element_id
    for room in model.rooms
    if is_ancillary(room) and not is_semi_outdoor(room)
]
bedonly_list = list(set(bed_list) - set(mbr_list))
win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]


outmost_list = [g.element_id for g in model.glazings if g.outmost]
outmost_room = [
    room.room_id
    for room in model.room_glazing_relations
    if room.glazing_id in outmost_list
]

G: nx.DiGraph = nx.DiGraph()
sun_dict = {
    room.element_id: analyze_sun_order(G, outmost_list, room.element_id)
    for room in model.rooms
}
sunlit_order: int = 3


# print(outmost_room)
# print(two_sides_room_list)
