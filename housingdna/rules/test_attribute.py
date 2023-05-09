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


from typing import Dict, List, Mapping, Sequence, Set
from .type import N
from collections import Counter

import housingdna.file as hdna
import numpy as np
import networkx as nx

from ..model import (
    Direction,
    Glazing,
    House,
    RevitObject,
    Room,
    RoomGlazingRelation,
    multiple_sides,
)
from .name import (
    is_ancillary, is_main, is_semi_outdoor, judge_by_name, is_entrance, is_living
)

from .glazing_network import analyze_sun_order

# # 분석 대상 불러오기: revit file 명 ""에 추가할 것
# test_model = hdna.get_model(
#     "housingdna/models/Japan_01_Sato Kogyo Co._81.58(수정).json")

test_model = hdna.get_model(
    "housingdna/models/Korea_01_위례자연앤셑트럴자이_98.79(완성).json"
)


def dnas_attribute(
    test_model: House,
) -> List[N]:

    main_list = [
        room.element_id for room in test_model.rooms if is_main(room)]

    room_heights = {
        room.element_id: room.height.mm for room in test_model.rooms}

    outmost_list = [g.element_id for g in test_model.glazings if g.outmost]

    outmost_room = [
        room.room_id for room in test_model.room_glazing_relations if room.glazing_id in outmost_list]

    semi_out_list = [
        room.element_id for room in test_model.rooms if is_semi_outdoor(room)]

    dna: List[N] = []
    for key, eval in [
        ("dna55", dna55_higher_main(room_heights, main_list)),
        ("dna61", dna61_windows_on_two_sides(
            test_model.room_glazing_relations, outmost_list)),
        ("dna61-2", dna61_windows_on_two_sides_v2(
            test_model)),
        ("dna64", dna64_window_to_outdoor(
            test_model.room_glazing_relations, outmost_list)),
        ("dna68", dna68_window_interior(
            test_model.glazings, test_model.room_glazing_relations)),
        ("dna67", dna67_Windows_overlooking_Life(
            test_model.glazings, test_model.room_glazing_relations)),
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def is_mbr(room: Room) -> bool:
    # TODO: should include virtually main bedroom without these exact names.
    exact_list = ["안방", "부부 침실", "main bedroom", "master bedroom", "mbr"]
    return judge_by_name(room.name, exact_list)


def dna55_higher_main(
    heights: Mapping[int, float], main_list: Sequence[int]
) -> List[int]:
    """생활공간 중 다른 생활공간들보다 층고가 높은 (차이나는) 실이 있는지를 판단"""
    main_heights = {room: heights[room] for room in main_list}
    main_median: float = float(np.median(list(main_heights.values())))
    return [room for room, height in main_heights.items() if height > main_median]


# print(dna55_higher_main(test_models))


# def dna61_windows_on_two_sides1(rels: Sequence[RoomGlazingRelation], outmost_list: List[int]) -> List[int]:
#     outmost_list: Dict[int, Set[Glazing]] = dict()

#     outmost_lists = [g.element_id for g in test_model.glazings if g.outmost]
#     for rel in rels:
#         outmost_list.setdefault(rel.room_id, set()).update(rel.outmost)
#     return [room for room, outmost in outmost_list.items() if multiple_sides(outmost)]


def dna61_windows_on_two_sides(rels: Sequence[RoomGlazingRelation], outmost_list: List[int]) -> List[int]:
    room_facings: Dict[int, Set[Direction]] = dict()

    outmost_list = [g.element_id for g in test_model.glazings if g.outmost]

    for rel in rels:
        room_facings.setdefault(rel.room_id, set()).update(rel.facings)
    return [room for room, facings in room_facings.items() if multiple_sides(facings) and outmost_list]


def dna64_window_to_outdoor(
    rels: Sequence[RoomGlazingRelation], outmost_list: List[int]
) -> List[int]:
    return [rel.room_id for rel in rels if rel.glazing_id in outmost_list]


def dna68_window_interior(
    glazings: Sequence[Glazing], rels: Sequence[RoomGlazingRelation]
) -> List[int]:
    # windows, curtain walls, and glass doors
    # between rooms (not at the outmost boundary of the house)
    # excluding imaginary separation lines
    inner_window_list = [
        g.element_id
        for g in glazings
        if (not g.outmost) and g.type_ != RevitObject.ROOM_SEPARATION_LINE
    ]
    window_facings: Dict[int, Set[Direction]] = dict()
    for rel in rels:
        if rel.glazing_id in inner_window_list:
            window_facings.setdefault(
                rel.glazing_id, set()).update(rel.facings)
    real_inner_window_list = [
        window for window, facings in window_facings.items() if multiple_sides(facings)
    ]
    # real_inner_room = [
    #     room.room_id for room in test_model.room_glazing_relations if not is_semi_outdoor(room)]
    return [rel.room_id for rel in rels if not rel.glazing_id in real_inner_window_list]


def dna67_Windows_overlooking_Life(
    glazings: Sequence[Glazing], rels: Sequence[RoomGlazingRelation]
) -> List[int]:
    # windows, curtain walls, and glass doors
    # between rooms (not at the outmost boundary of the house)
    # excluding imaginary separation lines

    semi_out_list = [
        room.element_id for room in test_model.rooms if is_semi_outdoor(room)]
    inner_window_list = [
        g.element_id
        for g in glazings
        if (not g.outmost) and g.type_ != RevitObject.ROOM_SEPARATION_LINE
    ]
    window_facings: Dict[int, Set[Direction]] = dict()
    for rel in rels:
        if rel.glazing_id in inner_window_list:
            window_facings.setdefault(
                rel.glazing_id, set()).update(rel.facings)
    real_inner_window_list = [
        window for window, facings in window_facings.items() if multiple_sides(facings) and semi_out_list
    ]
    return [rel.room_id for rel in rels if rel.glazing_id in real_inner_window_list]


G: nx.DiGraph = nx.DiGraph()
sun_directions = [Direction.SOUTH, Direction.EAST,
                  Direction.SOUTHEAST, Direction.SOUTHWEST]
opposite_directions = [d.opposite() for d in sun_directions]
edges = [
    (rel.room_id, rel.glazing_id)
    for rel in test_model.room_glazing_relations
    if any((facing in sun_directions) for facing in rel.facings)
] + [
    (rel.glazing_id, rel.room_id)
    for rel in test_model.room_glazing_relations
    if any((facing in opposite_directions) for facing in rel.facings)
]


G.add_edges_from(edges)
ent_list = [room.element_id for room in test_model.rooms if is_entrance(room)]
living_list = [room.element_id for room in test_model.rooms if is_living(room)]

except_open = [g.element_id for g in test_model.glazings if g.outmost == True and g.type_ !=
               RevitObject.ROOM_SEPARATION_LINE]
main_list = [
    room.element_id for room in test_model.rooms if is_main(room)]

room_heights = {
    room.element_id: room.height.mm for room in test_model.rooms}

outmost_list = [g.element_id for g in test_model.glazings if g.outmost]

glazing_list = [g.element_id for g in test_model.glazings if g.type_ !=
                RevitObject.ROOM_SEPARATION_LINE]

semi_out_list = [
    room.element_id for room in test_model.rooms if is_semi_outdoor(room)]

outmost_room = [
    room.room_id for room in test_model.room_glazing_relations if room.glazing_id in outmost_list]

room_list = [
    win.room_id for win in test_model.room_glazing_relations if win.glazing_id in except_open]
win_list = [
    win.glazing_id for win in test_model.room_glazing_relations if outmost_list]


sun_dict = {win.element_id: analyze_sun_order(
    G, outmost_list, win.element_id) for win in test_model.rooms}
sunlit_order: int = 2

room_win_count2 = {win.room_id: win.glazing_id
                   for win in test_model.room_glazing_relations}
sun_dict_win = {win.element_id: analyze_sun_order(
    G, outmost_list, win.element_id) for win in test_model.glazings}

sunlit2_list = [
    win for win in glazing_list if sun_dict_win[win] == sunlit_order]

room_list22 = [
    win.room_id for win in test_model.room_glazing_relations if win.glazing_id in except_open + sunlit2_list]
all_room_list = [
    room.element_id for room in test_model.rooms]
all = [rel for rel in outmost_room if rel in living_list]


# TODO: 추후 gethub에 추가할 것


def room_outmost_win_count(model: House,
                           ) -> List[N]:
    except_open = [g.element_id for g in test_model.glazings if g.outmost == True and g.type_ !=
                   RevitObject.ROOM_SEPARATION_LINE]
    glazing_list = [g.element_id for g in test_model.glazings if g.type_ !=
                    RevitObject.ROOM_SEPARATION_LINE]
    sunlit2_list = [
        win for win in glazing_list if sun_dict_win[win] == 2]
    room_list_2sides = [
        win.room_id for win in test_model.room_glazing_relations if win.glazing_id in except_open + sunlit2_list]
    return Counter(room_list_2sides)


# TODO: 추후 gethub에 추가할 것


def dna61_windows_on_two_sides_v2(model: House,
                                  ) -> List[N]:
    all_room_list = [
        room.element_id for room in test_model.rooms]
    win_count_dict = room_outmost_win_count(test_model)
    two_sides_room_list = [
        room for room in all_room_list if win_count_dict[room] >= 2]
    return two_sides_room_list


# win_count: int = 2
# win_count_dict = room_outmost_win_count(test_model)
# two_sides_room_list = [
#     room for room in all_room_list if win_count_dict[room] >= 2]

# print(win_count_dict)
# print(two_sides_room_list)

# print(dnas_attribute(test_model))
# print(dna55_higher_main(room_heights, main_list))
# print(dna61_windows_on_two_sides(test_model.room_glazing_relations, semi_out_list))
# print(dna64_window_to_outdoor(test_model.room_glazing_relations, outmost_list))
# print(dna68_window_interior(test_model.glazings, test_model.room_glazing_relations))
# print(dna67_Windows_overlooking_Life(
#     test_model.glazings, test_model.room_glazing_relations))

# print(room_win_count)
