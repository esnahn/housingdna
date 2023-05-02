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
    is_ancillary, is_main, is_semi_outdoor, judge_by_name,
)

from .glazing_network import analyze_sun_order

# # 분석 대상 불러오기: revit file 명 ""에 추가할 것
test_model = hdna.get_model(
    "housingdna/models/Japan_01_Sato Kogyo Co._81.58(수정).json")


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
    return [rel.room_id for rel in rels if rel.glazing_id in real_inner_window_list]


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


except_open = [g.element_id for g in test_model.glazings if g.type_ !=
               RevitObject.ROOM_SEPARATION_LINE]


main_list = [
    room.element_id for room in test_model.rooms if is_main(room)]

room_heights = {
    room.element_id: room.height.mm for room in test_model.rooms}

outmost_list = [g.element_id for g in test_model.glazings if g.outmost]

semi_out_list = [
    room.element_id for room in test_model.rooms if is_semi_outdoor(room)]

outmost_room = [
    room.room_id for room in test_model.room_glazing_relations if room.glazing_id in outmost_list]

room_list = [
    win.room_id for win in test_model.room_glazing_relations if win.glazing_id in except_open]
win_list = [
    win.glazing_id for win in test_model.room_glazing_relations if outmost_list]

(Counter(room_list))


room_win_count2 = {win.room_id: win.glazing_id
                   for win in test_model.room_glazing_relations}

# print(outmost_room)

print(room_list)
# print(room_list2)

# print(room_win)


def room_win_count(test_model: House,
                   ) -> List[N]:

    except_open = [g.element_id for g in test_model.glazings if g.type_ !=
                   RevitObject.ROOM_SEPARATION_LINE]
    room_list = [
        win.room_id for win in test_model.room_glazing_relations if win.glazing_id in except_open]
    return Counter(room_list)


print(room_win_count(test_model))


print(dnas_attribute(test_model))
# print(dna55_higher_main(room_heights, main_list))
print(dna61_windows_on_two_sides(test_model.room_glazing_relations, semi_out_list))
# print(dna64_window_to_outdoor(test_model.room_glazing_relations, outmost_list))
print(dna68_window_interior(test_model.glazings, test_model.room_glazing_relations))
print(dna67_Windows_overlooking_Life(
    test_model.glazings, test_model.room_glazing_relations))

# print(room_win)
# print(room_win_count)
