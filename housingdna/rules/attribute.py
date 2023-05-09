from typing import Dict, List, Mapping, Sequence, Set
from .type import N


import housingdna.file as hdna
import numpy as np
from ..model import (
    Direction,
    Glazing,
    House,
    RevitObject,
    Room,
    RoomGlazingRelation,
    multiple_sides,
)
from .name import (is_main, is_semi_outdoor, is_main, is_bedroom,
                   judge_by_name)
from .glazing_network import analyze_sun_order
from collections import Counter
import networkx as nx


def dnas_attribute(
    model: House,
) -> List[N]:

    main_list = [room.element_id for room in model.rooms if is_main(room)]

    room_heights = {room.element_id: room.height.mm for room in model.rooms}

    outmost_list = [g.element_id for g in model.glazings if g.outmost]

    dna: List[N] = []
    for key, eval in [
        ("dna55", dna55_higher_main(room_heights, main_list)),
        ("dna61", dna61_windows_on_two_sides(
            model)),
        # ("dna61", dna61_windows_on_two_sides(
        #     model.room_glazing_relations, semi_out_list)), #first code
        ("dna64", dna64_window_to_outdoor(
            model.room_glazing_relations, outmost_list)),
        ("dna68", dna68_window_interior(model.glazings, model.room_glazing_relations)),
        ("dna67", dna67_Windows_overlooking_Life(
            model.glazings, model.room_glazing_relations)),
        ("dna54", dna54_Independent_rooms(model)),
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def is_mbr(room: Room) -> bool:
    # TODO: should include virtually main bedroom without these exact names.
    exact_list = ["안방", "부부 침실", "main bedroom", "master bedroom", "mbr"]
    return judge_by_name(room.name, exact_list)


def room_outmost_win_count(model: House,
                           ) -> List[N]:
    G: nx.DiGraph = nx.DiGraph()
    # assuming mid-latitude northern hemisphere
    sun_directions = [Direction.SOUTH,
                      Direction.SOUTHEAST, Direction.SOUTHWEST, Direction.EAST, Direction.WEST]
    opposite_directions = [d.opposite() for d in sun_directions]
    edges = [
        (rel.room_id, rel.glazing_id)
        for rel in model.room_glazing_relations
        if any((facing in sun_directions) for facing in rel.facings)
    ] + [
        (rel.glazing_id, rel.room_id)
        for rel in model.room_glazing_relations
        if any((facing in opposite_directions) for facing in rel.facings)
    ]
    G.add_edges_from(edges)

    outmost_list = [g.element_id for g in model.glazings if g.outmost]
    sun_dict_win = {win.element_id: analyze_sun_order(
        G, outmost_list, win.element_id) for win in model.glazings}
    except_open = [g.element_id for g in model.glazings if g.outmost ==
                   True and g.type_ != RevitObject.ROOM_SEPARATION_LINE]
    glazing_list = [g.element_id for g in model.glazings if g.type_ !=
                    RevitObject.ROOM_SEPARATION_LINE]
    sunlit2_list = [
        win for win in glazing_list if sun_dict_win[win] == 2]
    room_list_2sides = [
        win.room_id for win in model.room_glazing_relations if win.glazing_id in except_open + sunlit2_list]
    return Counter(room_list_2sides)


def dna55_higher_main(
    heights: Mapping[int, float], main_list: Sequence[int]
) -> List[int]:
    """생활공간 중 다른 생활공간들보다 층고가 높은 (차이나는) 실이 있는지를 판단"""

    main_heights = {room: heights[room] for room in main_list}
    main_median: float = float(np.median(list(main_heights.values())))
    return [room for room, height in main_heights.items() if height > main_median]

# dna61__windows_on_two_sides: first code @dr. ahn
# def dna61_windows_on_two_sides(rels: Sequence[RoomGlazingRelation], outmost_list: List[int]) -> List[int]:
#     room_facings: Dict[int, Set[Direction]] = dict()
#     for rel in rels:
#         room_facings.setdefault(rel.room_id, set()).update(rel.facings)
#     return [room for room, facings in room_facings.items() if multiple_sides(facings) and not outmost_list]


def dna61_windows_on_two_sides(model: House,
                               ) -> List[N]:
    all_room_list = [
        room.element_id for room in model.rooms]
    win_count_dict = room_outmost_win_count(model)
    two_sides_room_list = [
        room for room in all_room_list if win_count_dict[room] >= 2]
    return two_sides_room_list


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


def dna67_Windows_overlooking_Life(model: House,
                                   glazings: Sequence[Glazing], rels: Sequence[RoomGlazingRelation]
                                   ) -> List[int]:
    # windows, curtain walls, and glass doors
    # between rooms (not at the outmost boundary of the house)
    # excluding imaginary separation lines

    semi_out_list = [
        room.element_id for room in model.rooms if is_semi_outdoor(room)]
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


# 54_독립된 방
def dna54_Independent_rooms(
    model: House,
) -> List[N]:
    conn_types_door = [RevitObject.DOOR]
    bed_list = [
        room.element_id for room in model.rooms if is_bedroom(room)]

    independent_rooms1 = [(conn.a_id, conn.type_)
                          for conn in model.room_connections if conn.a_id in bed_list and conn.type_ in conn_types_door]
    independent_rooms2 = [(conn.b_id, conn.type_)
                          for conn in model.room_connections if conn.b_id in bed_list and conn.type_ in conn_types_door]

    return set(independent_rooms1) - set(independent_rooms2)
