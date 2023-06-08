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
from .test_room_list import (
    rooms,
    pub_list,
    mbr_list,
    ancill_list,
    semi_out_list,
    ent_list,
    living_list,
    dining_list,
    kit_list,
    bath_list,
    sto_list,
    dress_list,
    corr_list,
    bed_list,
    main_list,
    indoor_ancill_list,
    bedonly_list,
    outmost_room,
    two_sides_room_list,
    sun_dict,
    sunlit_order,
    outmost_list,
)
from .test_complex import dnas_complex
from housingdna.rules import edges
from test_model import sample_model


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


dnas_2: List[N] = list(
    chain(
        dnas_obvious(sample_model),
        dnas_room_name(sample_model),
        dnas_attribute(sample_model),
        dnas_room_network(sample_model),
        dnas_glazing_network(sample_model),
        dnas_complex(sample_model),
    )
)

dnas = dnas_2


# TODO: gray_edges_list를 실행시키기.
def gray_edges_list(
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            edge_name_1_1(dnas),
            edge_name_1_2(dnas, model),
            edge_name_2_1(dnas, model),
            edge_name_2_2(dnas, model),
            edge_name_4_1(model),
            edge_name_4_2(model),
            edge_name_6(dnas, model),
        )
    )
    return node_ids


def edge_name_1_1(
    dnas: Sequence[N],
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna36_dna46(dnas),
            dna36_dna47(dnas),
            dna36_dna48(dnas),
            dna36_dna51(dnas),
        )
    )
    return node_ids


def edge_name_1_2(
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna40_dna41(dnas, model),
            dna40_dna44(dnas, model),
            dna40_dna45(dnas, model),
            dna40_dna46(dnas, model),
            dna40_dna47(dnas, model),
            dna40_dna48(dnas, model),
            dna40_dna49(dnas, model),
            dna40_dna51(dnas, model),
        )
    )
    return node_ids


def edge_name_2_1(
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna42_dna48(dnas, model),
            dna42_dna49(dnas, model),
            dna46_dna48(dnas, model),
            dna46_dna49(dnas, model),
            dna51_dna48(dnas, model),
        )
    )
    return node_ids


def edge_name_2_2(
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna41_dna43(model),
            dna41_dna46(dnas, model),
            dna41_dna47(dnas, model),
            dna44_dna48(dnas, model),
            dna44_dna49(dnas, model),
            dna44_dna51(dnas, model),
            dna45_dna48(dnas, model),
            dna45_dna49(dnas, model),
            dna45_dna51(dnas, model),
        )
    )
    return node_ids


def edge_name_4_1(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna42_dna61(model),
            dna42_dna64(model),
            dna42_dna67(model),
            dna42_dna68(model),
            dna43_dna61(model),
            dna43_dna64(model),
            dna43_dna67(model),
            dna43_dna68(model),
            dna46_dna61(model),
            dna46_dna64(model),
            dna46_dna67(model),
            dna46_dna68(model),
            # dna46_dna69(model),
            dna47_dna61(model),
            dna47_dna64(model),
            dna47_dna67(model),
            dna47_dna68(model),
            # dna47_dna69(model),
            dna48_dna61(model),
            dna48_dna64(model),
            dna48_dna67(model),
            dna48_dna68(model),
            # dna48_dna69(model),
            dna49_dna64(model),
            # dna49_dna69(model),
            dna51_dna61(model),
            dna51_dna64(model),
            # dna51_dna69(model),
        )
    )
    return node_ids


def edge_name_4_2(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna41_dna61(model),
            dna41_dna64(model),
            dna41_dna67(model),
            dna41_dna68(model),
            # dna41_dna69(model),
            dna44_dna61(model),
            dna44_dna64(model),
            dna44_dna67(model),
            dna44_dna68(model),
            # dna44_dna69(model),
            dna45_dna61(model),
            dna45_dna64(model),
            dna45_dna67(model),
            dna45_dna68(model),
            # dna45_dna69(model),
        )
    )
    return node_ids


def edge_name_6(
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna44_dna29(dnas, model),
            dna45_dna29(dnas, model),
            dna46_dna29(dnas, model),
            dna47_dna29(dnas, model),
        )
    )
    return node_ids


# [basic logic] edge name 1_1
def dna_edge_by_name(
    dna_vector: Tuple[N, N],
    dnas: Sequence[N],
) -> List[Tuple[E, A]]:
    # 아무 dna들 중에서 dnas에 존재하는 dna들의 튜플들

    d1, d2 = dna_vector

    if d1 not in dnas:
        return []

    if d2 not in dnas:
        return []

    conn_logic = [d1 in dnas and d2 in dnas]
    if conn_logic:
        return [(d1, d2)]
    else:
        return []


# [basic logic] edge_name_2_1
def dna_edge_by_room_conn(
    dna_vector: Tuple[N, N],
    room_type_ids_pair: Tuple[Sequence[int], Sequence[int]],
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[E, A]]:
    # 아무 방 중에서 room_type_ids_pair의 방끼리 서로 이어진 곳이 있으면
    # dna_vector의 한 방향 연결 있어

    d1, d2 = dna_vector

    if d1 not in dnas:
        return []

    if d2 not in dnas:
        return []

    rt1, rt2 = room_type_ids_pair

    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in model.room_connections
        if conn.a_id in rt1 and conn.b_id in rt2
    ] + [
        (conn.a_id, conn.b_id)
        for conn in model.room_connections
        if conn.a_id in rt2 and conn.b_id in rt1
    ]
    if conn_logic:
        return [(d1, d2)]
    else:
        return []


# [basic logic]
def dna_edge_by_sun_direct_room(
    dna_vector: Tuple[N, N],
    room_type_ids: Sequence[N],
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[E, A]]:
    # 1. d1과 d2가 동시에 존재
    # 2. 아무 방 중에서 rt1 방이 채광이 잘되는지
    d1, d2 = dna_vector

    if d1 not in dnas:
        return []

    if d2 not in dnas:
        return []

    rt1 = room_type_ids
    sun_directions = [
        Direction.SOUTH,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTHWEST,
    ]
    conn_logic = [
        room.room_id
        for room in model.room_glazing_relations
        if (room.room_id in rt1)
        and any(facing in sun_directions for facing in room.facings)
    ]

    if conn_logic:
        return [(d1, d2)]
    else:
        return []


# [basic logic]
def dna_edge_by_opposit_sun_room(
    dna_vector: Tuple[N, N],
    room_type_ids: Sequence[N],
    dnas: Sequence[N],
    model: House,
) -> List[Tuple[E, A]]:
    # 1. d1과 d2가 동시에 존재
    # 2. 아무 방 중에서 rt1 방 채광이 잘 안되는지를 판단

    d1, d2 = dna_vector

    if d1 not in dnas:
        return []

    if d2 not in dnas:
        return []

    rt1 = room_type_ids
    sun_directions = [
        Direction.SOUTH,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTHWEST,
    ]
    opposite_directions = [d.opposite() for d in sun_directions]

    conn_logic = [
        room.room_id
        for room in model.room_glazing_relations
        if (room.room_id in rt1)
        and any(facing in opposite_directions for facing in room.facings)
    ]

    if conn_logic:
        return [(d1, d2)]
    else:
        return []


# edge name 1_1 logic
def dna36_dna46(dnas):
    return dna_edge_by_name(("dna36", "dna46"), dnas)


def dna36_dna47(dnas):
    return dna_edge_by_name(("dna36", "dna47"), dnas)


def dna36_dna48(dnas):
    return dna_edge_by_name(("dna36", "dna48"), dnas)


def dna36_dna51(dnas):
    return dna_edge_by_name(("dna36", "dna51"), dnas)


# edge_name_2_1 logic
def dna42_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna42", "dna48"), (ent_list, bath_list), dnas, model)


def dna42_dna49(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna42", "dna49"), (ent_list, sto_list), dnas, model)


def dna46_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna46", "dna48"), (kit_list, bath_list), dnas, model)


def dna46_dna49(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna46", "dna49"), (kit_list, sto_list), dnas, model)


def dna51_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna51", "dna48"), (dress_list, bath_list), dnas, model
    )


# edge_name_2_2 logic
# TODO: 지루하지 않은 복도와의 연결 논리
def dna41_dna43(model: House):
    # 거실이 존재하고 거실과 연결되어 있는 다른 공간이 오픈되어 있는 경우

    conn_types_open = [RevitObject.ROOM_SEPARATION_LINE]
    fun_corr1 = [
        (conn.b_id)
        for conn in model.room_connections
        if conn.a_id in living_list
        and conn.type_ in conn_types_open
        and not conn.b_id in ancill_list
    ] + [
        (conn.a_id)
        for conn in model.room_connections
        if conn.b_id in living_list
        and conn.type_ in conn_types_open
        and not conn.a_id in ancill_list
    ]
    fun_corr2 = [
        (conn.b_id)
        for conn in model.room_connections
        if conn.a_id in living_list
        and conn.type_ in conn_types_open
        and conn.b_id in corr_list
    ] + [
        (conn.a_id)
        for conn in model.room_connections
        if conn.b_id in living_list
        and conn.type_ in conn_types_open
        and conn.a_id in corr_list
    ]

    if fun_corr1 or fun_corr2:
        return ("dna41", "dna43")
    else:
        return []


def dna41_dna46(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna41", "dna46"), (living_list, kit_list), dnas, model
    )


def dna41_dna47(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna41", "dna47"), (living_list, dining_list), dnas, model
    )


def dna41_dna46(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna41", "dna46"), (living_list, kit_list), dnas, model
    )


def dna44_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna44", "dna48"), (mbr_list, bath_list), dnas, model)


def dna44_dna49(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(("dna44", "dna49"), (mbr_list, sto_list), dnas, model)


def dna44_dna51(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna44", "dna51"), (mbr_list, dress_list), dnas, model
    )


def dna45_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna45", "dna48"), (bedonly_list, bath_list), dnas, model
    )


def dna45_dna49(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna45", "dna49"), (bedonly_list, sto_list), dnas, model
    )


def dna45_dna51(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna45", "dna51"), (bedonly_list, dress_list), dnas, model
    )


def dna40_dna41(dnas: Sequence[N], model: House):
    return dna_edge_by_sun_direct_room(("dna40", "dna41"), main_list, dnas, model)


def dna40_dna44(dnas: Sequence[N], model: House):
    return dna_edge_by_sun_direct_room(("dna40", "dna44"), mbr_list, dnas, model)


def dna40_dna45(dnas: Sequence[N], model: House):
    return dna_edge_by_sun_direct_room(("dna40", "dna45"), bedonly_list, dnas, model)


def dna40_dna46(dnas: Sequence[N], model: House):
    return dna_edge_by_sun_direct_room(("dna40", "dna46"), kit_list, dnas, model)


def dna40_dna47(dnas: Sequence[N], model: House):
    return dna_edge_by_sun_direct_room(("dna40", "dna47"), dining_list, dnas, model)


def dna40_dna48(dnas: Sequence[N], model: House):
    return dna_edge_by_opposit_sun_room(("dna40", "dna48"), bath_list, dnas, model)


def dna40_dna49(dnas: Sequence[N], model: House):
    return dna_edge_by_opposit_sun_room(("dna40", "dna49"), sto_list, dnas, model)


def dna40_dna51(dnas: Sequence[N], model: House):
    return dna_edge_by_opposit_sun_room(("dna40", "dna51"), dress_list, dnas, model)


# edge_name_4_1
def dna42_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in ent_list)

    if dna_edge_by_name(("dna42", "dna61"), dnas) and conn_logic:
        return [("dna42", "dna61")]
    else:
        return []


def dna42_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )
    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]
    conn_logic = any(room for room in real_outmost_room if room in ent_list)

    if dna_edge_by_name(("dna42", "dna64"), dnas) and conn_logic:
        return [("dna42", "dna64")]
    else:
        return []


def dna42_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in ent_list)

    if dna_edge_by_name(("dna42", "dna67"), dnas) and conn_logic:
        return [("dna42", "dna67")]
    else:
        return []


def dna42_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in ent_list)

    if dna_edge_by_name(("dna42", "dna68"), dnas) and conn_logic:
        return [("dna42", "dna68")]
    else:
        return []


# edge_name_4_1  part2


def dna43_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in corr_list)

    if dna_edge_by_name(("dna43", "dna61"), dnas) and conn_logic:
        return [("dna43", "dna61")]
    else:
        return []


def dna43_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in corr_list)

    if dna_edge_by_name(("dna43", "dna64"), dnas) and conn_logic:
        return [("dna43", "dna64")]
    else:
        return []


def dna43_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in corr_list)

    if dna_edge_by_name(("dna43", "dna67"), dnas) and conn_logic:
        return [("dna43", "dna67")]
    else:
        return []


def dna43_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in corr_list)

    if dna_edge_by_name(("dna43", "dna68"), dnas) and conn_logic:
        return [("dna43", "dna68")]
    else:
        return []


def dna46_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in kit_list)

    if dna_edge_by_name(("dna46", "dna61"), dnas) and conn_logic:
        return [("dna46", "dna61")]
    else:
        return []


def dna46_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in kit_list)

    if dna_edge_by_name(("dna46", "dna64"), dnas) and conn_logic:
        return [("dna46", "dna64")]
    else:
        return []


def dna46_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in kit_list)

    if dna_edge_by_name(("dna46", "dna67"), dnas) and conn_logic:
        return [("dna46", "dna67")]
    else:
        return []


def dna46_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in kit_list)

    if dna_edge_by_name(("dna46", "dna68"), dnas) and conn_logic:
        return [("dna46", "dna68")]
    else:
        return []


def dna47_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in dining_list)

    if dna_edge_by_name(("dna47", "dna61"), dnas) and conn_logic:
        return [("dna47", "dna61")]
    else:
        return []


def dna47_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in dining_list)

    if dna_edge_by_name(("dna47", "dna64"), dnas) and conn_logic:
        return [("dna47", "dna64")]
    else:
        return []


def dna47_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in dining_list)

    if dna_edge_by_name(("dna47", "dna67"), dnas) and conn_logic:
        return [("dna47", "dna67")]
    else:
        return []


def dna47_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in dining_list)

    if dna_edge_by_name(("dna47", "dna68"), dnas) and conn_logic:
        return [("dna47", "dna68")]
    else:
        return []


def dna48_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in bath_list)

    if dna_edge_by_name(("dna48", "dna61"), dnas) and conn_logic:
        return [("dna48", "dna61")]
    else:
        return []


def dna48_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in bath_list)

    if dna_edge_by_name(("dna48", "dna64"), dnas) and conn_logic:
        return [("dna48", "dna64")]
    else:
        return []


def dna48_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in bath_list)

    if dna_edge_by_name(("dna48", "dna67"), dnas) and conn_logic:
        return [("dna48", "dna67")]
    else:
        return []


def dna48_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in bath_list)

    if dna_edge_by_name(("dna48", "dna68"), dnas) and conn_logic:
        return [("dna48", "dna68")]
    else:
        return []


def dna49_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in sto_list)

    if dna_edge_by_name(("dna49", "dna64"), dnas) and conn_logic:
        return [("dna49", "dna64")]
    else:
        return []


def dna51_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in dress_list)

    if dna_edge_by_name(("dna51", "dna61"), dnas) and conn_logic:
        return [("dna51", "dna61")]
    else:
        return []


def dna51_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in dress_list)

    if dna_edge_by_name(("dna51", "dna64"), dnas) and conn_logic:
        return [("dna51", "dna64")]
    else:
        return []


# edge_name_4_2
def dna41_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in living_list)

    if dna_edge_by_name(("dna41", "dna61"), dnas) and conn_logic:
        return [("dna41", "dna61")]
    else:
        return []


def dna41_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in living_list)

    if dna_edge_by_name(("dna41", "dna64"), dnas) and conn_logic:
        return [("dna41", "dna64")]
    else:
        return []


def dna41_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in living_list)

    if dna_edge_by_name(("dna41", "dna67"), dnas) and conn_logic:
        return [("dna41", "dna67")]
    else:
        return []


def dna41_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in living_list)

    if dna_edge_by_name(("dna41", "dna68"), dnas) and conn_logic:
        return [("dna41", "dna68")]
    else:
        return []


def dna44_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in mbr_list)

    if dna_edge_by_name(("dna44", "dna61"), dnas) and conn_logic:
        return [("dna44", "dna61")]
    else:
        return []


def dna44_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in mbr_list)

    if dna_edge_by_name(("dna44", "dna64"), dnas) and conn_logic:
        return [("dna44", "dna64")]
    else:
        return []


def dna44_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in mbr_list)

    if dna_edge_by_name(("dna44", "dna67"), dnas) and conn_logic:
        return [("dna44", "dna67")]
    else:
        return []


def dna44_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in mbr_list)

    if dna_edge_by_name(("dna44", "dna68"), dnas) and conn_logic:
        return [("dna44", "dna68")]
    else:
        return []


def dna45_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    win_count_dict = room_outmost_win_count(model, model.room_glazing_relations)
    two_sides_room_list = [room for room in rooms if win_count_dict[room] >= 2]
    conn_logic = any(room for room in two_sides_room_list if room in bedonly_list)

    if dna_edge_by_name(("dna45", "dna61"), dnas) and conn_logic:
        return [("dna45", "dna61")]
    else:
        return []


def dna45_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    outmost_rooms = set(
        (
            [room for room in rooms if sun_dict[room] <= sunlit_order]
            + [room for room in outmost_room]
        )
    )

    real_outmost_room = [room for room in outmost_rooms if not room in semi_out_list]

    conn_logic = any(room for room in real_outmost_room if room in bedonly_list)

    if dna_edge_by_name(("dna45", "dna64"), dnas) and conn_logic:
        return [("dna45", "dna64")]
    else:
        return []


def dna45_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna67_Windows_overlooking_Life(model)

    conn_logic = any(a for a in room_logic if a in bedonly_list)

    if dna_edge_by_name(("dna45", "dna67"), dnas) and conn_logic:
        return [("dna45", "dna67")]
    else:
        return []


def dna45_dna68(
    model: House,
) -> List[Tuple[E, A]]:
    room_logic = dna68_window_interior(
        model, model.glazings, model.room_glazing_relations
    )

    conn_logic = any(a for a in room_logic if a in bedonly_list)

    if dna_edge_by_name(("dna45", "dna68"), dnas) and conn_logic:
        return [("dna45", "dna68")]
    else:
        return []


# edge_name_6_logic
def dna44_dna29(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna44", "dna29"), (mbr_list, semi_out_list), dnas, model
    )


def dna45_dna29(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna45", "dna29"), (bedonly_list, semi_out_list), dnas, model
    )


def dna46_dna29(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna46", "dna29"), (kit_list, semi_out_list), dnas, model
    )


def dna47_dna29(dnas: Sequence[N], model: House):
    return dna_edge_by_room_conn(
        ("dna47", "dna29"), (dining_list, semi_out_list), dnas, model
    )


# print(gray_edges_list(dnas, sample_model))
